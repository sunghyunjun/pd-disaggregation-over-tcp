#!/usr/bin/env bash
# 세션 E1 · g6e(L40S) vs g7e(RTX PRO 6000) 같은 체크포인트 정면 비교
# L40S는 NVFP4 미지원 → 공통 정밀도는 FP8. 앵커로 BF16 8B도 함께.
# 두 GPU 노드를 동시에 띄우고 각각 스윕(클라이언트 1대에서 순차 호출)
set -u
export PATH=~/venv/bin:~/.local/bin:$PATH; cd ~/pd
: "${E_PRIV:?g6e 사설 IP}" "${G_PRIV:?g7e 사설 IP}"
export RESULTS_DIR=$HOME/pd/results RESULTS_DIR_IN_CONTAINER=$HOME/pd/results ENV_JSON=$HOME/pd/results/env_E.json
export SHAREGPT_JSON=$HOME/pd/data/ShareGPT_V3_unfiltered_cleaned_split.json TRACES_DIR=$HOME/pd/data/traces
log(){ echo "[$(date -u +%T)] $*"; }
bench(){ harness/run_bench.sh "$@" 2>&1 | grep -E "Successful requests|Output token throughput|Median TTFT|P90 TTFT|P99 ITL|wrote|rror" | sed 's/^/    /'; }
rsh(){ ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 ubuntu@"$1" "export PATH=~/.local/bin:\$PATH; cd ~/pd; $2"; }
serve_one(){ # host port model chunk gpu_util
  rsh "$1" "CHUNK=$4 PREFIX=on PORT=$2 GPU_UTIL=${5:-0.90} harness/serve.sh $3" | sed 's/^/    /'
}
sweep(){ # host port tag model rates...
  local host=$1 port=$2 tag=$3 m=$4; shift 4
  export BASE_URL=http://$host:$port METRICS_URL=http://$host:$port/metrics MODEL=$m CHUNK=2560 PREFIX=on
  for r in "$@"; do log "  $tag r$r"; bench E "$tag" N0 sharegpt "$r"; done
}
MODELS_FP8=("RedHatAI/gemma-4-26B-A4B-it-FP8-dynamic" "RedHatAI/gemma-4-31B-it-FP8-block")
ANCHOR=Qwen/Qwen3-8B
RATES=${RATES:-"1 4 8 12"}

for m in "${MODELS_FP8[@]}"; do
  short=$(basename "$m" | tr 'A-Z' 'a-z' | sed 's/gemma-4-//;s/-it-fp8.*//')
  log "E1 g6e(L40S) $m"
  serve_one "$E_PRIV" 8100 "$m" 2560 && sweep "$E_PRIV" 8100 "l40s_${short}_fp8" "$m" $RATES
  log "E1 g7e(PRO6000) $m"
  serve_one "$G_PRIV" 8200 "$m" 2560 && sweep "$G_PRIV" 8200 "pro6000_${short}_fp8" "$m" $RATES
done

log "E1 앵커 $ANCHOR (BF16, 양쪽)"
serve_one "$E_PRIV" 8100 "$ANCHOR" 2560 && sweep "$E_PRIV" 8100 "l40s_q8_bf16" "$ANCHOR" $RATES
serve_one "$G_PRIV" 8200 "$ANCHOR" 2560 && sweep "$G_PRIV" 8200 "pro6000_q8_bf16" "$ANCHOR" $RATES

for h in $E_PRIV $G_PRIV; do rsh $h "docker rm -f vllm >/dev/null 2>&1"; done
log "E1 DONE"
