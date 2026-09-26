#!/usr/bin/env bash
# 세션 D-2 · (1) 수정된 대역폭 축, (2) D-1 최적 설정의 종단 이득
# 마찰 #9 수정: burst = rate × 10 ms, 프리필(송신) 노드에만, 설정마다 iperf 검증
# env: A_PRIV, B_PRIV, 그리고 최적 설정 BEST_UCX_EXTRA / BEST_KV_BUFFER_DEVICE / BEST_NIXL_THREADS / BEST_BLOCK
set -u
export PATH=~/venv/bin:~/.local/bin:$PATH; cd ~/pd
: "${A_PRIV:?}" "${B_PRIV:?}"
export RESULTS_DIR=$HOME/pd/results RESULTS_DIR_IN_CONTAINER=$HOME/pd/results ENV_JSON=$HOME/pd/results/env_D.json
export SHAREGPT_JSON=$HOME/pd/data/ShareGPT_V3_unfiltered_cleaned_split.json TRACES_DIR=$HOME/pd/data/traces
MAIN=${MAIN:-nvidia/Gemma-4-26B-A4B-NVFP4}
log(){ echo "[$(date -u +%T)] $*"; }
bench(){ harness/run_bench.sh "$@" 2>&1 | grep -E "Successful requests|Request throughput|Output token throughput|Median TTFT|P90 TTFT|P99 ITL|wrote|rror" | sed 's/^/    /'; }
rsh(){ ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 ubuntu@"$1" "export PATH=~/.local/bin:\$PATH; cd ~/pd; $2"; }
xfer(){ rsh $B_PRIV "docker logs vllm 2>&1 | grep 'KV Transfer metrics' | tail -2 | cut -c1-260" | sed 's/^/    xfer: /'; }
serve_p1(){ local tag=$1
  local extra=""; [ -n "${BLOCK:-}" ] && extra="--block-size $BLOCK"
  pkill -f "toy_proxy" 2>/dev/null; sleep 1
  rsh $A_PRIV "UCX_EXTRA='${UCX_EXTRA:-}' KV_BUFFER_DEVICE='${KV_BUFFER_DEVICE:-}' NIXL_THREADS='${NIXL_THREADS:-}' CHUNK=2560 PREFIX=off PORT=8100 CONNECTOR=producer OWN_IP=$A_PRIV harness/serve.sh $MAIN $extra" &
  rsh $B_PRIV "UCX_EXTRA='${UCX_EXTRA:-}' KV_BUFFER_DEVICE='${KV_BUFFER_DEVICE:-}' NIXL_THREADS='${NIXL_THREADS:-}' CHUNK=2560 PREFIX=off PORT=8200 CONNECTOR=consumer OWN_IP=$B_PRIV harness/serve.sh $MAIN $extra" &
  wait
  setsid nohup python3 vllm-src/tests/v1/kv_connector/nixl_integration/toy_proxy_server.py --host 0.0.0.0 --port 8000 \
    --prefiller-hosts $A_PRIV --prefiller-ports 8100 --decoder-hosts $B_PRIV --decoder-ports 8200 > results/toy_proxy_D2_$tag.log 2>&1 < /dev/null & disown
  sleep 4; local code=$(curl -s -o /dev/null -w "%{http_code}" localhost:8000/v1/models); echo "    proxy $code"
  export BASE_URL=http://127.0.0.1:8000 METRICS_URL=http://$A_PRIV:8100/metrics MODEL=$MAIN CHUNK=2560 PREFIX=off
  [ "$code" = 200 ] || { echo "    SKIP: 서버가 준비되지 않음"; return 1; }
}
tc_set(){ local bw=$1; local burst=$(python3 -c "print(int(${bw%gbit}*1e9/8*0.01))")
  rsh $A_PRIV "IF=\$(ip -o -4 route show to default | awk '{print \$5}'); sudo tc qdisc replace dev \$IF root tbf rate $bw burst $burst latency 50ms"
  echo -n "    iperf 검증 $bw: "; rsh $A_PRIV "iperf3 -c $B_PRIV -P 1 -t 8 -J 2>/dev/null | jq -r '.end.sum_sent.bits_per_second/1e9'"; }
tc_clear(){ rsh $A_PRIV "IF=\$(ip -o -4 route show to default | awk '{print \$5}'); sudo tc qdisc del dev \$IF root 2>/dev/null || true"; }

# ---- 1. 최적 설정의 종단 이득 (기준선과 정면 비교) ----
for variant in base best; do
  if [ "$variant" = base ]; then unset UCX_EXTRA KV_BUFFER_DEVICE NIXL_THREADS BLOCK
  else export UCX_EXTRA="${BEST_UCX_EXTRA:-}" KV_BUFFER_DEVICE="${BEST_KV_BUFFER_DEVICE:-}" NIXL_THREADS="${BEST_NIXL_THREADS:-}" BLOCK="${BEST_BLOCK:-}"; fi
  log "D2-1 $variant 종단: ShareGPT 4·8, 4K 0.5, 16K 0.5, Azure"
  serve_p1 "$variant" || continue
  bench D "p1_$variant" N0 sharegpt 4; xfer
  bench D "p1_$variant" N0 sharegpt 8; xfer
  bench D "p1_$variant" N0 random 0.5 --random-input-len 4096 --random-output-len 512; xfer
  bench D "p1_$variant" N0 random 0.5 --random-input-len 16384 --random-output-len 512; xfer
  TRACE_SEC_MULT=0.001 NUM_PROMPTS=600 bench D "p1_$variant" N0 azure_conv self; xfer
done

# ---- 2. 수정된 대역폭 축 (최적 설정으로, 4K 0.5 고정) ----
export UCX_EXTRA="${BEST_UCX_EXTRA:-}" KV_BUFFER_DEVICE="${BEST_KV_BUFFER_DEVICE:-}" NIXL_THREADS="${BEST_NIXL_THREADS:-}" BLOCK="${BEST_BLOCK:-}"
log "D2-2 대역폭 축 재측정 (burst = rate × 10 ms, 송신 노드만)"
serve_p1 bw
for bw in 5gbit 3gbit 2gbit 1gbit; do
  tc_set $bw
  bench D "p1_tcfix_$bw" N0 random 0.5 --random-input-len 4096 --random-output-len 512; xfer
done
tc_clear
log "D2 DONE"
