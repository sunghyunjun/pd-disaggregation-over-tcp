#!/usr/bin/env bash
# 세션 E1 · 단일 노드 교차 GPU 비교 (L40S vs RTX PRO 6000), 공통 정밀도 FP8
# 방법론: 접두어 캐시 OFF (마찰 #11 회피), 시드 고정, GPU별 순차 측정으로 클라이언트 경합 배제
# KV 예산 맞춤: L40S util 0.90 == PRO 6000 util 0.42 (가중치+오버헤드 후 KV 용량 동일)
set -u
export PATH=~/venv/bin:~/.local/bin:$PATH; cd ~/pd
: "${E_PRIV:?g6e 사설IP}" "${G_PRIV:?g7e 사설IP}"
export RESULTS_DIR=$HOME/pd/results RESULTS_DIR_IN_CONTAINER=$HOME/pd/results ENV_JSON=$HOME/pd/results/env_E1.json
export SHAREGPT_JSON=$HOME/pd/data/ShareGPT_V3_unfiltered_cleaned_split.json TRACES_DIR=$HOME/pd/data/traces
log(){ echo "[$(date -u +%T)] $*"; }
bench(){ harness/run_bench.sh "$@" 2>&1 | grep -E "Successful requests|Output token throughput|Median TTFT|P90 TTFT|P99 ITL|wrote|rror" | sed 's/^/    /'; }
rsh(){ ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 ubuntu@"$1" "export PATH=~/.local/bin:\$PATH; cd ~/pd; $2"; }
kvinfo(){ rsh "$1" "docker logs vllm 2>&1 | grep -E 'GPU KV cache size|Available KV cache' | tail -2" | sed 's/^/    /'; }

serve(){ # host port model util
  rsh "$1" "CHUNK=2560 PREFIX=off PORT=$2 GPU_UTIL=$4 harness/serve.sh $3" | sed 's/^/    /'
  local code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 http://$1:$2/health)
  echo "    health=$code"; [ "$code" = 200 ] || return 1
  export BASE_URL=http://$1:$2 METRICS_URL=http://$1:$2/metrics MODEL=$3 CHUNK=2560 PREFIX=off
}
sweep(){ local tag=$1; shift; for r in "$@"; do log "  $tag r$r"; bench E1 "$tag" N0 sharegpt "$r"; done; }

MODELS=("RedHatAI/gemma-4-26B-A4B-it-FP8-dynamic:26b_fp8" "RedHatAI/gemma-4-31B-it-FP8-block:31b_fp8")
RATES=${RATES:-"1 4 8 12"}

for entry in "${MODELS[@]}"; do
  m=${entry%%:*}; short=${entry##*:}
  log "E1 · $short · L40S(g6e) util 0.90 [KV 맞춤 기준]"
  serve "$E_PRIV" 8100 "$m" 0.90 && { kvinfo "$E_PRIV"; sweep "l40s_${short}_kvmatch" $RATES; }
  log "E1 · $short · PRO6000(g7e) util 0.42 [KV 맞춤]"
  serve "$G_PRIV" 8200 "$m" 0.42 && { kvinfo "$G_PRIV"; sweep "pro6000_${short}_kvmatch" $RATES; }
  log "E1 · $short · PRO6000(g7e) util 0.90 [최대 KV]"
  serve "$G_PRIV" 8200 "$m" 0.90 && { kvinfo "$G_PRIV"; sweep "pro6000_${short}_kvmax" $RATES; }
done

log "E1b · 26B FP8 고부하 확장 (PRO6000 최대 KV, 16·24 req/s)"
serve "$G_PRIV" 8200 "RedHatAI/gemma-4-26B-A4B-it-FP8-dynamic" 0.90 && sweep "pro6000_26b_fp8_kvmax" 16 24
log "E1b · 26B FP8 고부하 (L40S, 16 req/s — 한계 확인)"
serve "$E_PRIV" 8100 "RedHatAI/gemma-4-26B-A4B-it-FP8-dynamic" 0.90 && sweep "l40s_26b_fp8_kvmatch" 16

for h in $E_PRIV $G_PRIV; do rsh $h "docker rm -f vllm >/dev/null 2>&1"; done
log "E1 DONE"
