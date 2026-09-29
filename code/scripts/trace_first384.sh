#!/usr/bin/env bash
python3 - <<'PY'
import csv
base = '/home/administrator/vidur-fast/data/processed_traces/'
for name in ('splitwise_conv.csv', 'arxiv_summarization_stats_llama2_tokenizer_filtered_v2.csv', 'splitwise_code.csv'):
    vals = []
    with open(base + name, encoding='utf-8') as f:
        for i, r in enumerate(csv.DictReader(f)):
            if i >= 384:
                break
            try:
                vals.append(int(float(r['num_prefill_tokens'])))
            except Exception:
                pass
    vals.sort()
    print(f'{name}: first384 n={len(vals)} max={vals[-1]} p90={vals[int(len(vals)*.9)]} p50={vals[len(vals)//2]}')
PY
