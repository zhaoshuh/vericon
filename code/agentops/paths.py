"""路径解析：同一套代码在 Windows 与 WSL 两边都能跑。

可通过环境变量覆盖：
- AGENTOPS_ROOT     项目根目录（默认 F:\\文献\\AgentOps 或 /mnt/f/文献/AgentOps）
- AGENTOPS_RECORDS  实验记录目录（默认 <root>/实验记录）
- AGENTOPS_VIDUR    Vidur 仓库目录（默认 <root>/代码/third_party/vidur）
"""
from __future__ import annotations

import os
from pathlib import Path

_WIN_ROOT = Path(r"F:\文献\AgentOps")
_WSL_ROOT = Path("/mnt/f/文献/AgentOps")


def project_root() -> Path:
    env = os.environ.get("AGENTOPS_ROOT")
    if env:
        return Path(env)
    if os.name == "nt":
        return _WIN_ROOT
    return _WSL_ROOT


def code_dir() -> Path:
    return project_root() / "代码"


def records_dir() -> Path:
    env = os.environ.get("AGENTOPS_RECORDS")
    if env:
        return Path(env)
    return project_root() / "实验记录"


def vidur_dir() -> Path:
    env = os.environ.get("AGENTOPS_VIDUR")
    if env:
        return Path(env)
    return code_dir() / "third_party" / "vidur"


def canonical_vidur_dir() -> Path:
    """带 .git 的规范仓库（用于记录 commit）。

    运行时可能指向 WSL 本地快照副本（提速用，见 scripts/setup_env_miniconda.sh），
    快照没有 .git → 回退到项目内的克隆，保证 provenance 不丢。
    """
    runtime = vidur_dir()
    if (runtime / ".git").exists():
        return runtime
    fallback = code_dir() / "third_party" / "vidur"
    return fallback if (fallback / ".git").exists() else runtime


def runs_jsonl() -> Path:
    return records_dir() / "runs.jsonl"


def runs_csv() -> Path:
    return records_dir() / "runs.csv"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_wsl() -> bool:
    if os.name == "nt":
        return False
    try:
        return "microsoft" in Path("/proc/version").read_text(encoding="utf-8").lower()
    except OSError:
        return False


def windows_path(path: Path | str) -> str:
    """把 WSL 路径转成 Windows 风格（方便在 Windows 侧打开产物）；非 WSL 路径原样返回。"""
    s = Path(path).as_posix()
    if s.startswith("/mnt/") and len(s) > 7 and s[6] == "/":
        drive = s[5].upper()
        return f"{drive}:\\" + s[7:].replace("/", "\\")
    return str(path)
