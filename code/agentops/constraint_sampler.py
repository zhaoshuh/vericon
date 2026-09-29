# -*- coding: utf-8 -*-
"""通用 ConstraintSampler：约束图 JSON → 采样域/区间（P5 方法抽象化的核心实现）

设计目标
--------
把"约束知识注入调优器"从**硬编码**（tune.py 里写死 mtib ≥ max(mns, tokens_min)）升级为
**数据驱动**：读约束图 JSON，解析表达式，在顺序采样时自动推导每个参数的合法区间。

支持的表达式子集（覆盖约束图主要形态）
--------------------------------------
    x >= y            x > y            x <= y            x < y
    x >= c            x > c            ...（c 为常数）
    x % y == 0        （整除 → 离散域步长）
    x in {a, b, c}    （枚举 → 候选集合）
    implication:      （前置条件类，v1 仅记录，不参与区间推导）

推导规则（目标参数 x，其余参数已赋值）
--------------------------------------
    x >= y  且 y 已赋值  →  lo(x) = max(lo(x), y_val)
    x <  y  且 y 已赋值  →  hi(x) = min(hi(x), y_val - 1)      （整数语义）
    x >= c              →  lo(x) = max(lo(x), c)
    x % y == 0          →  步长 step(x) = y_val（离散倍数过滤）
    x in {..}           →  候选集合（由调用方决定是否 categorical）

若某约束的其它参数未赋值 → 该约束暂不生效（顺序采样时按依赖序处理）。

用法
----
    from agentops.constraint_sampler import ConstraintSampler, load_graph
    cs = ConstraintSampler(load_graph(path))
    bounds = cs.bounds_for("max_num_batched_tokens", assigned={"max_num_seqs": 64})
    # → {"lo": 64, "hi": None, "step": None, "sources": ["C001", ...]}
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 表达式解析
# ---------------------------------------------------------------------------

_CMP_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_.\[\]']*)\s*(>=|<=|==|>|<)\s*([A-Za-z_][A-Za-z0-9_.\[\]']*|\d+(?:\.\d+)?)\s*$")
_CMP_MUL_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_.\[\]']*)\s*(>=|<=|==|>|<)\s*(\d+(?:\.\d+)?)\s*\*\s*([A-Za-z_][A-Za-z0-9_.\[\]']*)\s*$")
_MOD_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_.\[\]']*)\s*%\s*([A-Za-z_][A-Za-z0-9_.\[\]']*|\d+)\s*==\s*0\s*$")
_ENUM_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_.\[\]']*)\s+(?:in|∈)\s*[\{\[]([^\}\]]+)[\}\]]\s*$")

# 字段名 → 参数名归一化（去掉 self./config. 等前缀与引号）
def _norm(name: str) -> str:
    name = name.strip().strip("'\"")
    for prefix in ("self.", "config.", "scheduler_config.", "cache_config.", "model_config.", "parallel_config."):
        if name.startswith(prefix):
            name = name[len(prefix):]
    if "." in name:
        name = name.split(".")[-1]
    return name


def _to_number(tok: str) -> Optional[float]:
    try:
        return float(tok)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------

@dataclass
class ParsedConstraint:
    cid: str
    ctype: str
    expr: str
    params: List[str]
    op: Optional[str] = None            # >= <= == > <
    lhs: Optional[str] = None           # 归一化字段名
    rhs: Optional[str] = None           # 归一化字段名或 None（常数）
    rhs_const: Optional[float] = None
    mul_coeff: Optional[float] = None   # 形如 x >= c * y 的系数 c
    mod_lhs: Optional[str] = None       # x % y == 0 的 x
    mod_rhs: Optional[str] = None       # 的 y
    enum_lhs: Optional[str] = None
    enum_vals: Optional[List[str]] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def validated(self) -> bool:
        v = self.raw.get("validation") or {}
        return v.get("status") in ("confirmed", "confirmed_cross_model")


def parse_constraint(node: Dict[str, Any]) -> ParsedConstraint:
    cid = str(node.get("id") or "?")
    ctype = str(node.get("type") or "unknown")
    expr = str(node.get("expr") or "")
    params = [str(p) for p in (node.get("params") or [])]
    pc = ParsedConstraint(cid=cid, ctype=ctype, expr=expr, params=params, raw=node)

    m = _CMP_MUL_RE.match(expr)
    if m:
        pc.lhs, pc.op = _norm(m.group(1)), m.group(2)
        pc.mul_coeff = float(m.group(3))
        pc.rhs = _norm(m.group(4))
        return pc

    m = _CMP_RE.match(expr)
    if m:
        lhs, op, rhs = _norm(m.group(1)), m.group(2), m.group(3)
        pc.lhs, pc.op = lhs, op
        num = _to_number(rhs)
        if num is None:
            pc.rhs = _norm(rhs)
        else:
            pc.rhs_const = num
        return pc

    m = _MOD_RE.match(expr)
    if m:
        pc.mod_lhs = _norm(m.group(1))
        pc.mod_rhs = _norm(m.group(2))
        return pc

    m = _ENUM_RE.match(expr)
    if m:
        pc.enum_lhs = _norm(m.group(1))
        pc.enum_vals = [v.strip().strip("'\"") for v in m.group(2).split(",")]
        return pc

    return pc


def load_graph(path: str) -> List[ParsedConstraint]:
    data = json.load(open(path, encoding="utf-8"))
    nodes = data.get("nodes") if isinstance(data, dict) else data
    out = []
    for n in nodes or []:
        out.append(parse_constraint(n))
    return out


# ---------------------------------------------------------------------------
# 采样器
# ---------------------------------------------------------------------------

@dataclass
class Bounds:
    lo: Optional[float] = None
    hi: Optional[float] = None
    step: Optional[float] = None
    candidates: Optional[List[str]] = None
    sources: List[str] = field(default_factory=list)

    def add_lo(self, v: float, cid: str) -> None:
        if self.lo is None or v > self.lo:
            self.lo = v
        self.sources.append(cid)

    def add_hi(self, v: float, cid: str) -> None:
        if self.hi is None or v < self.hi:
            self.hi = v
        self.sources.append(cid)

    def feasible(self) -> bool:
        if self.lo is not None and self.hi is not None and self.lo > self.hi:
            return False
        return True


class ConstraintSampler:
    """数据驱动采样器：把约束图投影为逐参数区间/域。"""

    def __init__(self, constraints: Iterable[ParsedConstraint], only_validated: bool = False):
        self.constraints = [c for c in constraints if (not only_validated) or c.validated]
        self.by_param: Dict[str, List[ParsedConstraint]] = {}
        for c in self.constraints:
            for p in self._touched_params(c):
                self.by_param.setdefault(p, []).append(c)

    @staticmethod
    def _touched_params(c: ParsedConstraint) -> List[str]:
        names = set()
        for x in (c.lhs, c.rhs, c.mod_lhs, c.mod_rhs, c.enum_lhs):
            if x:
                names.add(x)
        names.update(c.params)
        return sorted(names)

    def bounds_for(self, param: str, assigned: Dict[str, float]) -> Bounds:
        """为 param 推导合法区间；assigned 中为已采样的其它参数值。"""
        b = Bounds()
        for c in self.by_param.get(param, []):
            if c.enum_lhs == param and c.enum_vals:
                b.candidates = list(c.enum_vals)
                b.sources.append(c.cid)
                continue
            if c.mod_lhs == param and c.mod_rhs:
                y = assigned.get(c.mod_rhs)
                if y is None:
                    n = _to_number(c.mod_rhs)
                    y = n
                if y:
                    b.step = y
                    b.sources.append(c.cid)
                continue
            if c.lhs != param or c.op is None:
                continue
            if c.rhs is None:
                # x op const
                if c.rhs_const is None:
                    continue
                v = c.rhs_const
            else:
                v = assigned.get(c.rhs)
                if v is None:
                    continue  # 依赖未赋值 → 暂不生效
                if c.mul_coeff is not None:
                    v = c.mul_coeff * v
            if c.op == ">=":
                b.add_lo(v, c.cid)
            elif c.op == ">":
                b.add_lo(v + 1, c.cid)      # 整数语义
            elif c.op == "<=":
                b.add_hi(v, c.cid)
            elif c.op == "<":
                b.add_hi(v - 1, c.cid)
            # == 不直接给区间（双向约束，交给调用方）
        return b

    def sample(self, trial: Any, spec: Dict[str, Any], order: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """按依赖序采样一组配置。

        spec: {param: {"kind": "int"|"float"|"categorical",
                       "lo":..,"hi":..,"log":bool,"choices":[..]}}
        order: 采样顺序（默认按 spec 的键序；建议把"被依赖"的参数放前面）
        返回 None 表示当前约束下不可满足（调用方可跳过该 trial）。
        """
        order = order or list(spec.keys())
        cfg: Dict[str, Any] = {}
        for p in order:
            s = spec[p]
            kind = s.get("kind", "float")
            if kind == "categorical":
                choices = s.get("choices") or []
                b = self.bounds_for(p, cfg)
                if b.candidates:
                    choices = [c for c in choices if str(c) in b.candidates] or choices
                cfg[p] = trial.suggest_categorical(p, choices)
                continue
            b = self.bounds_for(p, cfg)
            lo = max(x for x in [s.get("lo"), b.lo] if x is not None)
            hi = min(x for x in [s.get("hi"), b.hi] if x is not None)
            if lo > hi:
                return None
            if b.step and b.step > 0 and kind == "int":
                # 离散倍数过滤：先采样再对齐（保持 Optuna 参数独立）
                v = trial.suggest_int(p, int(lo), int(hi), log=bool(s.get("log")))
                step = int(b.step)
                if v % step:
                    v = (v // step) * step
                    if v < lo:
                        v += step
                cfg[p] = int(v)
            elif kind == "int":
                cfg[p] = trial.suggest_int(p, int(lo), int(hi), log=bool(s.get("log")))
            else:
                cfg[p] = trial.suggest_float(p, float(lo), float(hi), log=bool(s.get("log")))
        return cfg

    # ---- 分析工具 ----

    def satisfies(self, cfg: Dict[str, Any]) -> bool:
        """检查赋值是否满足所有"可求值"的约束（参数不全的约束跳过）。"""
        for c in self.constraints:
            if c.op and c.lhs in cfg:
                rhs_val = None
                if c.rhs in cfg:
                    rhs_val = cfg[c.rhs]
                    if c.mul_coeff is not None:
                        rhs_val = c.mul_coeff * rhs_val
                elif c.rhs is None and c.rhs_const is not None:
                    rhs_val = c.rhs_const
                if rhs_val is None:
                    continue
                a = cfg[c.lhs]
                if c.op == ">=" and not a >= rhs_val:
                    return False
                if c.op == ">" and not a > rhs_val:
                    return False
                if c.op == "<=" and not a <= rhs_val:
                    return False
                if c.op == "<" and not a < rhs_val:
                    return False
                if c.op == "==" and not a == rhs_val:
                    return False
            elif c.mod_lhs in cfg and c.mod_rhs in cfg:
                if cfg[c.mod_rhs] and cfg[c.mod_lhs] % cfg[c.mod_rhs] != 0:
                    return False
            elif c.enum_lhs in cfg and c.enum_vals:
                if str(cfg[c.enum_lhs]) not in c.enum_vals:
                    return False
        return True

    def space_reduction(self, spec: Dict[str, Any], n_mc: int = 200_000, seed: int = 42) -> Dict[str, Any]:
        """数值估计：均匀网格剪枝率 + 对数均匀采样违反率（P5 解析关系的数据点）。"""
        import random
        rng = random.Random(seed)

        def sample_uniform() -> Dict[str, float]:
            cfg = {}
            for p, s in spec.items():
                if s.get("kind") == "categorical":
                    cfg[p] = rng.choice(s.get("choices") or [None])
                else:
                    cfg[p] = rng.uniform(s["lo"], s["hi"])
            return cfg

        def sample_log() -> Dict[str, float]:
            import math
            cfg = {}
            for p, s in spec.items():
                if s.get("kind") == "categorical":
                    cfg[p] = rng.choice(s.get("choices") or [None])
                elif s.get("log"):
                    import math as _m
                    cfg[p] = _m.exp(rng.uniform(_m.log(s["lo"]), _m.log(s["hi"])))
                else:
                    cfg[p] = rng.uniform(s["lo"], s["hi"])
            return cfg

        def satisfied(cfg: Dict[str, float]) -> bool:
            for c in self.constraints:
                if c.op and c.lhs in cfg and c.rhs in cfg:
                    a, b = cfg[c.lhs], cfg[c.rhs]
                    if c.mul_coeff is not None:
                        b = c.mul_coeff * b
                    if c.op == ">=" and not a >= b:
                        return False
                    if c.op == ">" and not a > b:
                        return False
                    if c.op == "<=" and not a <= b:
                        return False
                    if c.op == "<" and not a < b:
                        return False
                    if c.op == "==" and not a == b:
                        return False
                elif c.op and c.lhs in cfg and c.rhs_const is not None:
                    a = cfg[c.lhs]
                    if c.op == ">=" and not a >= c.rhs_const:
                        return False
                    if c.op == ">" and not a > c.rhs_const:
                        return False
                    if c.op == "<=" and not a <= c.rhs_const:
                        return False
                    if c.op == "<" and not a < c.rhs_const:
                        return False
                elif c.mod_lhs in cfg and c.mod_rhs in cfg:
                    if cfg[c.mod_rhs] and cfg[c.mod_lhs] % cfg[c.mod_rhs] != 0:
                        return False
            return True

        n_ok_u = sum(1 for _ in range(n_mc) if satisfied(sample_uniform()))
        n_ok_l = sum(1 for _ in range(n_mc) if satisfied(sample_log()))
        return {
            "n_mc": n_mc,
            "violation_rate_uniform": round(1 - n_ok_u / n_mc, 4),
            "violation_rate_loguniform": round(1 - n_ok_l / n_mc, 4),
            "constraints_active": len(self.constraints),
        }


# ---------------------------------------------------------------------------
# 解析关系（P5 §3）：覆盖率 → 剪枝率 → 成本节省
# ---------------------------------------------------------------------------

def cost_saving(r_before: float, r_after: float, c_invalid: float) -> float:
    """E[cost] = n(1 + c·r) → 节省 = c(r_b − r_a) / (1 + c·r_b)。"""
    denom = 1 + c_invalid * r_before
    if denom <= 0:
        return 0.0
    return c_invalid * (r_before - r_after) / denom
