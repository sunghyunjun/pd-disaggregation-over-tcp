#!/usr/bin/env bash
# Session C1 (g7e.2xlarge x1, single node, quota 8): the B1 half of the quantization axis and KV-capacity axis.
# For each model/precision: serve (chunk 2560, prefix on) -> kvinfo -> single step -> ShareGPT sweep 6 rates.
# Then KV fp8 on/off for the main pair. Logs to results/run_C1.log. Each step independent.
set -u
export PATH=~/.local/bin:$PATH
cd ~/pd
export BASE_URL=http://127.0.0.1:8000 RESULTS_DIR=$HOME/pd/results RESULTS_DIR_IN_CONTAINER=/pd/results ENV_JSON=$HOME/pd/results/env_C1.json METRICS_URL=http://127.0.0.1:8000/metrics
export SHAREGPT_JSON=/pd/data/ShareGPT_V3_unfiltered_cleaned_split.json TRACES_DIR=/pd/data/traces
RATES=${RATES:-"0.5 1 2 4 6 8"}
log(){ echo "[$(date -u +%T)] $*"; }
bench(){ harness/run_bench.sh "$@" 2>&1 | grep -E "Successful requests|Request throughput|Output token throughput|Median TTFT|P90 TTFT|P99 TTFT|Mean TPOT|Median ITL|P99 ITL|wrote|rror" | sed 's/^/    /'; }
bash harness/env_snapshot.sh results/env_C1.json >/dev/null 2>&1

one_model(){ # tag model [extra serve args]
  local tag=$1 m=$2; shift 2
  log "== $tag  $m $*"
  CHUNK=2560 PREFIX=on harness/serve.sh "$m" "$@" || { log "   serve failed, skipping $tag"; return; }
  harness/kvinfo.sh | sed "s|^|$tag |" | tee -a results/kvinfo_C1.txt
  export MODEL=$m
  NUM_PROMPTS=8 bench C1 B1_$tag N0 random inf --max-concurrency 1 --random-input-len 1024 --random-output-len 512 --ignore-eos
  for r in $RATES; do log "   $tag sharegpt rate $r"; bench C1 B1_$tag N0 sharegpt $r; done
}
one_model g31_nvfp4  nvidia/Gemma-4-31B-IT-NVFP4
one_model g26_bf16   google/gemma-4-26B-A4B-it
one_model g26_nvfp4  nvidia/Gemma-4-26B-A4B-NVFP4
one_model q35_fp8    Qwen/Qwen3.6-35B-A3B-FP8
one_model g31_bf16   google/gemma-4-31B-it
one_model g31_fp8    RedHatAI/gemma-4-31B-it-FP8-block
one_model q8_bf16    Qwen/Qwen3-8B
log "== KV fp8 on/off for main pair (26B-A4B NVFP4, 31B NVFP4)"
one_model g26_nvfp4_kvfp8 nvidia/Gemma-4-26B-A4B-NVFP4 --kv-cache-dtype fp8
one_model g31_nvfp4_kvfp8 nvidia/Gemma-4-31B-IT-NVFP4 --kv-cache-dtype fp8
docker rm -f vllm >/dev/null 2>&1
log "SESSION C1 DONE"
