#!/usr/bin/env bash
# E1b · 31B FP8 cross comparison (L40S is short on KV, so both sides use max-model-len 16384) + 26B high-load extension
set -u
export PATH=~/venv/bin:~/.local/bin:$PATH; cd ~/pd
: "${E_PRIV:?}" "${G_PRIV:?}"
export RESULTS_DIR=$HOME/pd/results RESULTS_DIR_IN_CONTAINER=$HOME/pd/results ENV_JSON=$HOME/pd/results/env_E1.json
export SHAREGPT_JSON=$HOME/pd/data/ShareGPT_V3_unfiltered_cleaned_split.json
log(){ echo "[$(date -u +%T)] $*"; }
bench(){ harness/run_bench.sh "$@" 2>&1 | grep -E "Successful requests|Output token throughput|Median TTFT|P90 TTFT|P99 ITL|wrote|rror" | sed 's/^/    /'; }
rsh(){ ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 ubuntu@"$1" "export PATH=~/.local/bin:\$PATH; cd ~/pd; $2"; }
kvinfo(){ rsh "$1" "docker logs vllm 2>&1 | grep -E 'GPU KV cache size' | tail -1" | sed 's/^/    /'; }
serve(){ # host port model util maxlen
  rsh "$1" "CHUNK=2560 PREFIX=off PORT=$2 GPU_UTIL=$4 MAXLEN=$5 harness/serve.sh $3" | sed 's/^/    /'
  local code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 http://$1:$2/health); echo "    health=$code"
  [ "$code" = 200 ] || return 1
  export BASE_URL=http://$1:$2 METRICS_URL=http://$1:$2/metrics MODEL=$3 CHUNK=2560 PREFIX=off
}
sweep(){ local tag=$1; shift; for r in "$@"; do log "  $tag r$r"; bench E1 "$tag" N0 sharegpt "$r"; done; }
M31=RedHatAI/gemma-4-31B-it-FP8-block
M26=RedHatAI/gemma-4-26B-A4B-it-FP8-dynamic
RATES=${RATES:-"1 4 8 12"}

# L40S 31B FP8 confirmed saturated at 1·4 req/s (KV 16,471 tokens), so 8·12 are skipped
log "E1b · 31B FP8 · PRO6000 util 0.42, maxlen 16384 [KV matching attempt]"
serve "$G_PRIV" 8200 "$M31" 0.42 16384 && { kvinfo "$G_PRIV"; sweep "pro6000_31b_fp8_len16k_kvmatch" $RATES; }
log "E1b · 31B FP8 · PRO6000 util 0.90, maxlen 16384 [max KV]"
serve "$G_PRIV" 8200 "$M31" 0.90 16384 && { kvinfo "$G_PRIV"; sweep "pro6000_31b_fp8_len16k_kvmax" $RATES; }

log "E1b · 26B FP8 high load · PRO6000 max KV (16·24·32)"
serve "$G_PRIV" 8200 "$M26" 0.90 32768 && sweep "pro6000_26b_fp8_kvmax" 16 24 32
log "E1b · 26B FP8 high load · L40S (16, limit check)"
serve "$E_PRIV" 8100 "$M26" 0.90 32768 && sweep "l40s_26b_fp8_kvmatch" 16

for h in $E_PRIV $G_PRIV; do rsh $h "docker rm -f vllm >/dev/null 2>&1"; done
log "E1b DONE"
