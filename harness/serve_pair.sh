#!/usr/bin/env bash
# Foreground server wrapper used as the --serve-cmd of `vllm bench sweep serve`.
# sweep SIGKILLs this process together with its process group, so no trap is relied on. Container cleanup happens at startup instead.
# Args: --host H --port P  (sweep reads the /health and cache-reset address from these)
# Env: MODE=pd|solo, A_PRIV, B_PRIV (pd), MODEL, UCX_EXTRA, NIXL_THREADS, GPU_UTIL, MAXLEN, CHUNK, PREFIX
set -uo pipefail
HOST=127.0.0.1; PORT=8000
while [ $# -gt 0 ]; do case $1 in --host) HOST=$2; shift;; --port|-p) PORT=$2; shift;; esac; shift; done
MODE=${MODE:-pd}; MODEL=${MODEL:?}; GPU_UTIL=${GPU_UTIL:-0.90}; CHUNK=${CHUNK:-2560}; PREFIX=${PREFIX:-off}
rsh(){ ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 ubuntu@"$1" "export PATH=\$HOME/.local/bin:\$PATH; cd ~/pd; $2"; }
health(){ curl -s -o /dev/null -w "%{http_code}" --max-time 10 "http://$1:$2/health"; }
wait_health(){ for _ in $(seq 1 120); do [ "$(health "$1" "$2")" = 200 ] && return 0; sleep 5; done; return 1; }

for h in ${A_PRIV:-} ${B_PRIV:-}; do rsh "$h" "docker rm -f vllm >/dev/null 2>&1"; done
pkill -f "[t]oy_proxy_server" 2>/dev/null; pkill -f "[r]r_proxy" 2>/dev/null; sleep 1

COMMON="UCX_EXTRA='${UCX_EXTRA:-}' NIXL_THREADS='${NIXL_THREADS:-}' CHUNK=$CHUNK PREFIX=$PREFIX GPU_UTIL=$GPU_UTIL ${MAXLEN:+MAXLEN=$MAXLEN}"
if [ "$MODE" = solo ]; then
  : "${A_PRIV:?}"
  rsh "$A_PRIV" "$COMMON PORT=8100 OWN_IP=$A_PRIV harness/serve.sh $MODEL" >/dev/null 2>&1 &
  wait_health "$A_PRIV" 8100 || { echo "serve_pair: A failed to start"; exit 1; }
  # Exposing the single node directly without a proxy would need a socket relay. A simple pass-through proxy is used here instead.
  exec python3 harness/rr_proxy.py --port "$PORT" --upstreams "http://$A_PRIV:8100"
else
  : "${A_PRIV:?}" "${B_PRIV:?}"
  rsh "$A_PRIV" "$COMMON PORT=8100 CONNECTOR=producer OWN_IP=$A_PRIV harness/serve.sh $MODEL" >/dev/null 2>&1 &
  rsh "$B_PRIV" "$COMMON PORT=8200 CONNECTOR=consumer OWN_IP=$B_PRIV harness/serve.sh $MODEL" >/dev/null 2>&1 &
  wait_health "$A_PRIV" 8100 || { echo "serve_pair: prefill failed to start"; exit 1; }
  wait_health "$B_PRIV" 8200 || { echo "serve_pair: decode failed to start"; exit 1; }
  exec python3 vllm-src/tests/v1/kv_connector/nixl_integration/toy_proxy_server.py \
    --host 0.0.0.0 --port "$PORT" \
    --prefiller-hosts "$A_PRIV" --prefiller-ports 8100 \
    --decoder-hosts "$B_PRIV" --decoder-ports 8200
fi
