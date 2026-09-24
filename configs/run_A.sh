#!/usr/bin/env bash
# Session A (g7.2xlarge x1): fully scripted. Logs to results/run_A.log. Each step is independent (continues on failure).
set -u
export PATH=~/.local/bin:$PATH
cd ~/pd
export BASE_URL=http://127.0.0.1:8000 RESULTS_DIR=$HOME/pd/results RESULTS_DIR_IN_CONTAINER=/pd/results ENV_JSON=$HOME/pd/results/env_A.json METRICS_URL=http://127.0.0.1:8000/metrics
export SHAREGPT_JSON=/pd/data/ShareGPT_V3_unfiltered_cleaned_split.json TRACES_DIR=/pd/data/traces
MAIN=${MAIN:-nvidia/Gemma-4-26B-A4B-NVFP4}
log(){ echo "[$(date -u +%T)] $*"; }
bench(){ # stage config net workload rate extra...
  harness/run_bench.sh "$@" 2>&1 | grep -E "Successful requests|Request throughput|Output token throughput|Median TTFT|P90 TTFT|P99 TTFT|Mean TPOT|Median ITL|P99 ITL|Request goodput|wrote|rror" | sed 's/^/    /'
}
bash harness/env_snapshot.sh results/env_A.json >/dev/null 2>&1

log "A1 serve main model $MAIN (chunk 2560: Gemma 4 mm item 2496 > 2048 rejected by vLLM, prefix on)"
CHUNK=2560 PREFIX=on harness/serve.sh "$MAIN" || { log "main model failed; falling back to RedHatAI/gemma-4-12B-it-FP8-Dynamic"; MAIN=RedHatAI/gemma-4-12B-it-FP8-Dynamic; CHUNK=2560 PREFIX=on harness/serve.sh "$MAIN" || exit 1; }
harness/kvinfo.sh | tee results/kvinfo_A_main.txt
export MODEL=$MAIN

log "A2 single step (conc 1, 1K in / 512 out)"
NUM_PROMPTS=8 bench A B1 N0 random inf --max-concurrency 1 --random-input-len 1024 --random-output-len 512 --ignore-eos
STEP=$(python3 harness/analyze.py $(ls -td results/*_A_B1_N0_random_rinf | head -1)/bench.json | python3 -c 'import sys; h,v=[l.rstrip("\n").split("\t") for l in sys.stdin][:2]; print(dict(zip(h,v))["tbt_p50_ms"])')
log "single step ms = $STEP"; echo "$STEP" > results/step_A_main.txt

log "A3 ShareGPT sweep, chunk 2560"
for r in 0.5 1 2 4 6 8; do log " rate $r"; bench A B1c2k5 N0 sharegpt $r; done
log "A3b max throughput reference"
NUM_PROMPTS=300 bench A B1c2k5 N0 sharegpt inf

log "A4 ShareGPT sweep, chunk 8192"
CHUNK=8192 PREFIX=on harness/serve.sh "$MAIN" && for r in 0.5 1 2 4 6 8; do log " rate $r"; bench A B1c8k N0 sharegpt $r; done

log "A5 synthetic partial, chunk 2560, prefix off"
CHUNK=2560 PREFIX=off harness/serve.sh "$MAIN" && for L in 4096 16384; do for r in 0.25 0.5 1; do log " L=$L rate $r"; bench A B1c2k5 N0 random $r --random-input-len $L --random-output-len 512; done; done

log "A6 Azure-conv replay (2x slower, first 600 req), prefix on"
CHUNK=2560 PREFIX=on harness/serve.sh "$MAIN" && TRACE_SEC_MULT=0.002 NUM_PROMPTS=600 bench A B1c2k5 N0 azure_conv self

log "A7 other models: kvinfo + single step"
for m in google/gemma-4-12B-it RedHatAI/gemma-4-12B-it-FP8-Dynamic Qwen/Qwen3-8B; do
  log " $m"; CHUNK=2560 PREFIX=on harness/serve.sh "$m" || continue
  harness/kvinfo.sh | tee -a results/kvinfo_A_others.txt | sed "s|^|$m |"
  MODEL=$m NUM_PROMPTS=8 bench A B1 N0 random inf --max-concurrency 1 --random-input-len 1024 --random-output-len 512 --ignore-eos
done
docker rm -f vllm >/dev/null 2>&1
log "SESSION A DONE"
