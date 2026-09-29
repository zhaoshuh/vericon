#!/usr/bin/env bash
python3 - <<'PY'
import csv
base = '/home/administrator/vidur-fast/data/processed_traces/'
for name, col in (('splitwise_conv.csv', 'num_prefill_tokens'),
                  ('arxiv_summarization_stats_llama2_tokenizer_filtered_v2.csv', 'num_prefill_tokens'),
                  ('splitwise_code.csv', 'num_prefill_tokens')):
    vals = []
    with open(base + name, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            try:
                vals.append(int(float(r[col])))
            except Exception:
                pass
    vals.sort()
    n = len(vals)
    def pct(p):
        return vals[min(n - 1, int(n * p))]
    print(f'{name}: n={n} min={vals[0]} p50={pct(.5)} p90={pct(.9)} p99={pct(.99)} max={vals[-1]}')
PY
