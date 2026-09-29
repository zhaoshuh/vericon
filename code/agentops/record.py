"""S2 · 统一实验记录格式 v1（schema s2.v1）。

一次实验 = 一条记录：**配置(config) → 指标(metrics) → 成本(cost)**，
外加环境(environment)与产物(artifacts)字段，保证可复现、可审计。

落盘形式（两个文件同时追加，互为镜像）：
- <记录目录>/runs.jsonl   嵌套结构，程序读取用
- <记录目录>/runs.csv     扁平结构，Excel / pandas 用

字段定义与含义见：<记录目录>/实验记录-格式-v1.md
"""
from __future__ import annotations

import csv
import json
import os
import platform
import socket
import subprocess
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .paths import ensure_dir, runs_csv, runs_jsonl

SCHEMA_VERSION = "s2.v1"


def utcnow_iso() -> str:
    """带本地时区偏移的 ISO 时间戳（含秒）。"""
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def new_run_id(prefix: str = "run") -> str:
    """形如 20260926-140233-vidur-a1b2c3，按时间可排序。"""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{prefix}-{uuid.uuid4().hex[:6]}"


@dataclass
class RunRecord:
    """一条实验记录。"""

    run_id: str
    schema_version: str = SCHEMA_VERSION
    created_at: str = field(default_factory=utcnow_iso)
    session: str = "S2"
    backend: str = "vidur_sim"          # vidur_sim | vllm
    mode: str = "simulate"              # simulate | serve
    status: str = "ok"                  # ok | failed
    study: Optional[str] = None         # Optuna study 名（调优时）
    trial: Optional[int] = None         # Optuna trial 号（调优时）
    config: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    cost: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# 环境信息
# ---------------------------------------------------------------------------

def _git_short_commit(repo: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=20,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:
        pass
    # 回退：直接读 .git/refs
    try:
        head = (repo / ".git" / "HEAD").read_text(encoding="utf-8").strip()
        if head.startswith("ref:"):
            ref = head.split(" ", 1)[1]
            return (repo / ".git" / ref).read_text(encoding="utf-8").strip()[:7]
        return head[:7]
    except Exception:
        return "unknown"


def collect_environment(*, backend: str, backend_repo: Optional[Path] = None,
                        extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """记录运行环境：跨机器/跨版本对比实验时的必要条件。"""
    env: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "hostname": socket.gethostname(),
        "cpu_count": os.cpu_count(),
        "backend": backend,
    }
    if backend == "vidur" and backend_repo is not None:
        env["vidur_git_commit"] = _git_short_commit(backend_repo)
    if extra:
        env.update(extra)
    return env


# ---------------------------------------------------------------------------
# 落盘：JSONL（嵌套）+ CSV（扁平）
# ---------------------------------------------------------------------------

def flatten(data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    """把嵌套 dict 压成 a.b.c 形式的扁平 dict，供 CSV 使用。"""
    out: Dict[str, Any] = {}
    for key, value in data.items():
        name = f"{prefix}{key}"
        if isinstance(value, dict):
            out.update(flatten(value, prefix=f"{name}."))
        elif isinstance(value, (list, tuple)):
            out[name] = json.dumps(value, ensure_ascii=False)
        else:
            out[name] = value
    return out


def _append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


try:  # 跨进程文件锁（WSL: fcntl；Windows: msvcrt 回退）
    import fcntl as _fcntl
except ImportError:  # pragma: no cover
    _fcntl = None

# CSV 字段上限提升（runs.csv 中可能含超长 error/JSON 字段；默认 131072 会崩）
try:
    csv.field_size_limit(min(sys.maxsize, 10 ** 9))
except Exception:  # pragma: no cover
    csv.field_size_limit(10 ** 9)


class _FileLock:
    """目录级互斥锁：防止并发进程同时 read-modify-write runs.csv 造成损坏。"""

    def __init__(self, lock_path: Path):
        self.lock_path = lock_path
        self._fh = None

    def __enter__(self):
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(self.lock_path, "a+")
        if _fcntl is not None:
            _fcntl.flock(self._fh.fileno(), _fcntl.LOCK_EX)
        else:  # pragma: no cover - Windows
            import msvcrt
            msvcrt.locking(self._fh.fileno(), msvcrt.LK_LOCK, 1)
        return self

    def __exit__(self, *exc):
        try:
            if _fcntl is not None:
                _fcntl.flock(self._fh.fileno(), _fcntl.LOCK_UN)
            else:  # pragma: no cover - Windows
                import msvcrt
                self._fh.seek(0)
                msvcrt.locking(self._fh.fileno(), msvcrt.LK_UNLCK, 1)
        finally:
            self._fh.close()


def _append_csv(path: Path, flat: Dict[str, Any]) -> None:
    """追加一行；若出现新列，则重写表头（旧行缺的列留空）。

    健壮性（2026-09-27 修复）：读取容错（errors="replace"）+ 临时文件原子替换，
    避免并发写入造成半字符损坏（见 scripts/repair_runs_csv.py）。
    """
    rows: List[Dict[str, Any]] = []
    fieldnames: List[str] = []
    if path.exists():
        with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as fh:
            reader = csv.DictReader(fh)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)
    for key in flat:
        if key not in fieldnames:
            fieldnames.append(key)
    rows.append(flat)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    os.replace(tmp, path)


def append_record(record: RunRecord | Dict[str, Any],
                  record_dir: Optional[Path] = None) -> Dict[str, Path]:
    """把一条记录追加到 runs.jsonl 与 runs.csv，返回两个文件路径。"""
    data = record.to_dict() if isinstance(record, RunRecord) else record
    if record_dir is not None:
        record_dir = ensure_dir(record_dir)
        jsonl = record_dir / "runs.jsonl"
        csv_path = record_dir / "runs.csv"
    else:
        ensure_dir(runs_jsonl().parent)
        jsonl, csv_path = runs_jsonl(), runs_csv()

    _append_jsonl(jsonl, data)
    with _FileLock(csv_path.parent / "runs.lock"):
        _append_csv(csv_path, flatten(data))
    return {"jsonl": jsonl, "csv": csv_path}


def read_records(record_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    path = (record_dir / "runs.jsonl") if record_dir is not None else runs_jsonl()
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def summarize(record: Dict[str, Any]) -> str:
    """给命令行打印用的一行摘要。"""
    cfg, met, cost = record.get("config", {}), record.get("metrics", {}), record.get("cost", {})
    parts = [
        f"[{record.get('status', '?')}] {record.get('run_id', '?')}",
        f"backend={record.get('backend')}",
        f"max_num_seqs={cfg.get('max_num_seqs')}",
        f"max_num_batched_tokens={cfg.get('max_num_batched_tokens')}",
    ]
    if record.get("status") == "ok":
        for label, value in (
            ("ttft_p90", met.get("ttft_p90_s")), ("tpot_p90", met.get("tpot_p90_s")),
            ("throughput", met.get("throughput_rps")), ("goodput", met.get("goodput_rps")),
            ("slo_ok", met.get("slo_ok")), ("wall", cost.get("wall_clock_s")),
            ("gpu_h", cost.get("gpu_hours")),
        ):
            if value is not None:
                parts.append(f"{label}={value}")
    else:
        parts.append(f"error={record.get('error')}")
    return " ".join(str(p) for p in parts)
