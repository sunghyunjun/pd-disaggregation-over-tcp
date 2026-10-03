#!/usr/bin/env bash
# After run_C1.sh: (1) Azure-conv replay with fixed hash_ids on the main model, (2) extend NVFP4 sweeps to 12/16/24 req/s.
set -u; export PATH=~/.local/bin:$PATH; cd ~/pd
export BASE_URL=http://127.0.0.1:8000 RESULTS_DIR=$HOME/pd/results RESULTS_DIR_IN_CONTAINER=/pd/results ENV_JSON=$HOME/pd/results/env_C1.json METRICS_URL=http://127.0.0.1:8000/metrics
export SHAREGPT_JSON=/pd/data/ShareGPT_V3_unfiltered_cleaned_split.json TRACES_DIR=/pd/data/traces
log(){ echo "[$(date -u +%T)] $*"; }
bench(){ harness/run_bench.sh "$@" 2>&1 | grep -E "Successful requests|Request throughput|Output token throughput|Median TTFT|P90 TTFT|P99 ITL|wrote|rror" | sed 's/^/    /'; }
log "T1 main model 26B-A4B NVFP4: Azure-conv replay (hash_ids fixed), 2x slower, 600 req"
CHUNK=2560 PREFIX=on harness/serve.sh nvidia/Gemma-4-26B-A4B-NVFP4 && { export MODEL=nvidia/Gemma-4-26B-A4B-NVFP4; TRACE_SEC_MULT=0.002 NUM_PROMPTS=600 bench C1 B1_g26_nvfp4 N0 azure_conv self;
  log "T2 extend ShareGPT sweep 12/16/24 for 26B-A4B NVFP4"; for r in 12 16 24; do log "  rate $r"; bench C1 B1_g26_nvfp4 N0 sharegpt $r; done; }
log "T3 extend 31B NVFP4 to 12"
CHUNK=2560 PREFIX=on harness/serve.sh nvidia/Gemma-4-31B-IT-NVFP4 && { export MODEL=nvidia/Gemma-4-31B-IT-NVFP4; bench C1 B1_g31_nvfp4 N0 sharegpt 12; }
docker rm -f vllm >/dev/null 2>&1; log "TAIL DONE"
