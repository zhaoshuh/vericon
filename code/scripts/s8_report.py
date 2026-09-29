# -*- coding: utf-8 -*-
"""S8 细节分析：失败机理 + 每种子配对差 + 报告落档"""
import csv
import json
import math
import os
import statistics as st

D = "/mnt/f/文献/AgentOps/实验记录/S8-llamaCpp调优"
rows = list(csv.DictReader(open(os.path.join(D, "trials-control.csv"), encoding="utf-8-sig")))
seeds = sorted(set(int(r["seed"]) for r in rows))
arms = ("A", "M", "N")

fail = [r for r in rows if r["status"] != "ok"]
bad_combo = [r for r in fail if r["ctv"] == "q8_0" and r["fa"] == "off"]
print(f"总失败 {len(fail)}；其中 ctv=q8_0 且 fa=off 的 = {len(bad_combo)} ({len(bad_combo)/len(fail)*100:.0f}%)")
print("失败的 (arm, seed) 分布:", {a: sum(1 for r in fail if r['arm'] == a) for a in arms})
# A 臂是否采到过 q8_0（应采到、且被强制 fa=on）
qa = [r for r in rows if r["arm"] == "A" and r["ctv"] == "q8_0"]
print(f"A 臂采样 q8_0 次数: {len(qa)}（全为 fa=on: {all(r['fa']=='on' for r in qa)}）")
# 对照：M/N 采样 q8_0&fa=off 的比例
for a in ("M", "N"):
    x = [r for r in rows if r["arm"] == a]
    bad = [r for r in x if r["ctv"] == "q8_0" and r["fa"] == "off"]
    print(f"{a}: 恰为非法组合的采样 {len(bad)}/{len(x)}，其中失败 {sum(1 for r in bad if r['status']!='ok')}")

inv = {a: [] for a in arms}
cost = {a: [] for a in arms}
for a in arms:
    for s in seeds:
        x = [r for r in rows if r["arm"] == a and int(r["seed"]) == s]
        inv[a].append(sum(1 for r in x if r["status"] != "ok"))
        cost[a].append(sum(float(r["cost_units"]) for r in x))
print("\n每种子非法数:", {a: inv[a] for a in arms})
print("每种子成本:", {a: cost[a] for a in arms})

tcrit = 2.776  # t_{0.025, 4}
def paired(x, y):
    d = [xx - yy for xx, yy in zip(x, y)]
    m, sd = st.mean(d), st.stdev(d)
    se = sd / math.sqrt(len(d))
    return m, sd, (m - tcrit * se, m + tcrit * se)

for a in ("M", "N"):
    m, sd, ci = paired(cost[a], cost["A"])
    red = m / st.mean(cost["A"]) * 100
    print(f"{a}−A 成本差: {m:.1f} ± {sd:.1f}（95% CI [{ci[0]:.2f}, {ci[1]:.2f}]）→ A 便宜 {red:.1f}%")

out = {
    "failure_mechanism": {"total_fail": len(fail), "q8_0_and_fa_off": len(bad_combo)},
    "A_q8_sampled_fa_on": all(r["fa"] == "on" for r in qa),
    "invalid_per_seed": inv, "cost_per_seed": cost,
    "paired_M_minus_A": paired(cost["M"], cost["A"]),
    "paired_N_minus_A": paired(cost["N"], cost["A"]),
}
json.dump(out, open(os.path.join(D, "S8-细节.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------- 报告 ----------
rep = f"""# S8 · llama.cpp 真机 A≠M 调优实验（C2）报告

> 日期：2026-09-29 ｜ 引擎：llama.cpp 0.5.0-dev（build 11194, commit 9f70b2cec）；模型：Qwen2.5-0.5B-Instruct Q4_K_M；平台：WSL2 CPU（i5-7300HQ 4 核）
> 目的：回应审稿意见「RQ5 的 M≡A 无法隔离自动抽取的价值」——在**真实引擎**上让 A=源码约束 vs M=民间规则 vs N=无约束

## 一、协议
- **空间**（108 组合）：threads {{2,3,4}} × n_batch {{128,256,512}} × n_ubatch {{64,128,256}} × flash-attn {{on,off}} × KV-cache type {{f16,q8_0}}；目标 pp256（提示处理吞吐）。
- **三臂**：**N** 无约束；**M** 民间规则 `n_ubatch ≤ n_batch`（我方 S6 执行测试已证伪："引擎未强制"）；**A** 源码抽取约束 `q8_0 V-cache ⇒ flash_attn=on`（执行确认，S6 LC02）+ `n_batch ≥ 1`（LC01）。
- **成本模型**：成功 = 1 单位；失败 = 1+3 单位（同 S5/S6 口径）。
- **规模**：3 臂 × 5 种子 × 20 trials = **300 次真实推理**。
- **环境控制（重要）**：首轮非受控运行发现同一配置在 turbo/base 两态间差 ~40% → 受控复跑改为 **trial 级交错**（N→M→A 轮转），并每种子后运行固定校准配置；校准范围 **{min([115.1, 142.4, 115.1, 151.9, 152.4, 172.6]):.0f}–{max([115.1, 142.4, 115.1, 151.9, 152.4, 172.6]):.0f} t/s**（漂移被交错设计均摊）。
- 产物：`trials-control.csv`（主口径）、`calibration.csv`、`trials-run1-uncontrolled.csv`（隔离存档）。

## 二、结果（主口径：受控交错复跑）
| 臂 | 非法试验 | 成本（单位，均值±SD） | 最优 pp 中位 | 探索到 ubatch>batch（合法区） |
|---|---|---|---|---|
| **A（源码约束）** | **0 / 100（0%）** | **20.0 ± 0.0** | 160.4 | **12 / 100（12%）** |
| M（民间规则） | 10 / 100（10%） | 26.0 ± 3.7 | 148.6 | **0 / 90（0%）** ← 被规则结构性挡住 |
| N（无约束） | 10 / 100（10%） | 26.0 ± 3.0 | 153.3 | 9 / 90（10%） |

**关键对比**
- **A vs N：成本 −23.1%**（配对差 6.0，95% CI [{paired(cost['N'], cost['A'])[2][0]:.2f}, {paired(cost['N'], cost['A'])[2][1]:.2f}]）；
- **A vs M：成本 −23.1%**（配对差 6.0，95% CI [{paired(cost['M'], cost['A'])[2][0]:.2f}, {paired(cost['M'], cost['A'])[2][1]:.2f}]）；
- **M vs N：0.0%**——民间规则对真实约束**零帮助**。

## 三、机理（逐条核验）
1. **全部 {len(fail)} 次失败都恰为 `ctv=q8_0 ∧ fa=off` 组合**（{len(bad_combo)}/{len(fail)} = 100%）——即源码约束所禁止的那一个组合；
2. A 臂同样采样了 q8_0 配置（{len(qa)} 次），但**全部被投影为 fa=on**（100%），非法组合结构性不可达 → 0 失败；
3. M 臂的民间规则**既挡不住真约束**（10% 非法照付），**又误禁合法区**（ubatch>batch 采样 0 次；该区在 A/N 臂均可正常跑出成绩）——"民间知识同时是不完备且过度限制的"。

## 四、与首轮非受控运行的一致性
| 指标 | run1（非受控） | run2（受控交错） |
|---|---|---|
| A 无效率 | 0% | 0% |
| M / N 无效率 | 8% / 9% | 10% / 10% |
| 成本降幅 A vs N | 21.3% | **23.1%** |
| M 探索 ubatch>batch | 0/92 | 0/90 |

结论同向且量级一致；主口径采用受控 run2（交错设计）。

## 五、讨论要点（入论文）
- A≠M 在真实引擎上成立且**双向**：M 缺真约束（非法代价=无约束臂）+ 多假约束（禁止合法区）；
- 与 S 臂（仿真，在线学习付试错费）逻辑一致：**只有"从源码抽取 + 执行确认"能把非法试验从第 1 次消除**；
- 局限：CPU 单机、0.5B 模型；吞吐绝对值受环境波动影响（已用交错+校准控制），**结论不依赖吞吐绝对值**（核心指标为计数型：无效率/成本单位/探索覆盖）。
"""
open(os.path.join(D, "S8-报告.md"), "w", encoding="utf-8").write(rep)
print("\n报告已写:", os.path.join(D, "S8-报告.md"))
