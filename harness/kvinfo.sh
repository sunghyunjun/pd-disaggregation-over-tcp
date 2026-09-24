#!/usr/bin/env bash
# Print KB/token (vLLM accounting) for the running server: available KV bytes / KV cache tokens.
docker logs vllm 2>&1 | python3 -c '
import sys,re
mem=tok=None
for l in sys.stdin:
    m=re.search(r"Available KV cache memory: ([\d.]+) GiB", l); mem=float(m.group(1)) if m else mem
    m=re.search(r"GPU KV cache size: ([\d,]+) tokens", l); tok=int(m.group(1).replace(",","")) if m else tok
    m=re.search(r"Maximum concurrency for ([\d,]+) tokens per request: ([\d.]+)x", l); conc=(m.group(1),m.group(2)) if m else None
if mem and tok: print(f"kv_mem_gib={mem} kv_tokens={tok} kb_per_tok={mem*1024**3/tok/1024:.1f}")
'
