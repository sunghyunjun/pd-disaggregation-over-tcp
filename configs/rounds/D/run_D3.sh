#!/usr/bin/env bash
# 세션 D-3 · 튜닝 설정으로 ShareGPT 요청률 사다리 재측정 (세션 B 표와 직접 비교) + 32K 재시도
set -u
export PATH=~/venv/bin:~/.local/bin:$PATH; cd ~/pd
: "${A_PRIV:?}" "${B_PRIV:?}"
export RESULTS_DIR=$HOME/pd/results RESULTS_DIR_IN_CONTAINER=$HOME/pd/results ENV_JSON=$HOME/pd/results/env_D.json
export SHAREGPT_JSON=$HOME/pd/data/ShareGPT_V3_unfiltered_cleaned_split.json TRACES_DIR=$HOME/pd/data/traces
MAIN=${MAIN:-nvidia/Gemma-4-26B-A4B-NVFP4}
export UCX_EXTRA="UCX_TLS=tcp,cuda_copy,cuda_ipc UCX_NET_DEVICES=all UCX_TCP_TX_SEG_SIZE=256k UCX_TCP_RX_SEG_SIZE=256k UCX_TCP_MAX_IOV=16 UCX_TCP_MAX_POLL=-1 UCX_TCP_SNDBUF=8m UCX_TCP_RCVBUF=8m UCX_RNDV_FRAG_SIZE=host:4M,cuda:8M"
log(){ echo "[$(date -u +%T)] $*"; }
bench(){ harness/run_bench.sh "$@" 2>&1 | grep -E "Successful requests|Output token throughput|Median TTFT|P90 TTFT|P99 ITL|wrote|rror" | sed 's/^/    /'; }
rsh(){ ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 ubuntu@"$1" "export PATH=~/.local/bin:\$PATH; cd ~/pd; $2"; }
xfer(){ rsh $B_PRIV "docker logs vllm 2>&1 | grep 'KV Transfer metrics' | tail -1 | cut -c1-240" | sed 's/^/    xfer: /'; }
serve_p1(){ local tag=$1
  pkill -f "toy_proxy" 2>/dev/null; sleep 1
  rsh $A_PRIV "UCX_EXTRA='$UCX_EXTRA' CHUNK=2560 PREFIX=$2 PORT=8100 CONNECTOR=producer OWN_IP=$A_PRIV harness/serve.sh $MAIN" &
  rsh $B_PRIV "UCX_EXTRA='$UCX_EXTRA' CHUNK=2560 PREFIX=$2 PORT=8200 CONNECTOR=consumer OWN_IP=$B_PRIV harness/serve.sh $MAIN" &
  wait
  setsid nohup python3 vllm-src/tests/v1/kv_connector/nixl_integration/toy_proxy_server.py --host 0.0.0.0 --port 8000 \
    --prefiller-hosts $A_PRIV --prefiller-ports 8100 --decoder-hosts $B_PRIV --decoder-ports 8200 > results/toy_proxy_D3_$tag.log 2>&1 < /dev/null & disown
  sleep 4
  local ha=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 http://$A_PRIV:8100/health)
  local hb=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 http://$B_PRIV:8200/health)
  echo "    health A=$ha B=$hb"
  export BASE_URL=http://127.0.0.1:8000 METRICS_URL=http://$A_PRIV:8100/metrics MODEL=$MAIN CHUNK=2560 PREFIX=$2
  [ "$ha" = 200 ] && [ "$hb" = 200 ] || { echo "    SKIP"; return 1; }
}
log "D3a 튜닝 설정 ShareGPT 사다리 (prefix on, 세션 B E2와 동일 조건)"
serve_p1 ladder on && for r in 1 4 6 8 12; do log "  rate $r"; bench D p1_tuned N0 sharegpt $r; xfer; done

log "D3b 튜닝 설정 32K (prefix off) — 프리필 포화 구간에서 전송 개선이 통하는지"
serve_p1 long off && for r in 0.25 0.5; do log "  32K rate $r"; bench D p1_tuned N0 random $r --random-input-len 32000 --random-output-len 512; xfer; done

pkill -f toy_proxy 2>/dev/null; for h in $A_PRIV $B_PRIV; do rsh $h "docker rm -f vllm >/dev/null 2>&1"; done
log "D3 DONE"
