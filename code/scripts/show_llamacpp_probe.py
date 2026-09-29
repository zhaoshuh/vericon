# -*- coding: utf-8 -*-
import json
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
d = json.load(open(r"F:\文献\AgentOps\实验记录\llamacpp_constraints.json", encoding="utf-8"))
for r in d["results"]:
    print("=" * 78)
    print(r["case"], "| exit=", r["exit_code"], "| status=", r["status"], "| wall=", r["wall_s"])
    tail = (r["stderr_tail"] or "").strip()
    if tail:
        print("--- stderr tail ---")
        print(tail[-600:])
    out = (r["stdout_tail"] or "").strip()
    if out and r["status"] != "no_error":
        print("--- stdout tail ---")
        print(out[-300:])