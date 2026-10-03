#!/usr/bin/env bash
# E4b · knob (b) rerun: TX and RX segments both set to 1 MB.
# In the main E4 run only TX was raised to 1m and UCX rejected it ("RX segment size must be >= TX segment size").
set -u
export PATH=~/venv/bin:~/.local/bin:$PATH; cd ~/pd
: "${A_PRIV:?}" "${B_PRIV:?}"
export RESULTS_DIR=$HOME/pd/results RESULTS_DIR_IN_CONTAINER=$HOME/pd/results ENV_JSON=$HOME/pd/results/env_E4.json
MAIN=${MAIN:-RedHatAI/gemma-4-26B-A4B-it-FP8-dynamic}
TUNED_1M="UCX_TLS=tcp,cuda_copy,cuda_ipc UCX_NET_DEVICES=all UCX_TCP_TX_SEG_SIZE=1m UCX_TCP_RX_SEG_SIZE=1m UCX_TCP_MAX_IOV=16 UCX_TCP_MAX_POLL=-1 UCX_TCP_SNDBUF=8m UCX_TCP_RCVBUF=8m UCX_RNDV_FRAG_SIZE=host:4M,cuda:8M"
log(){ echo "[$(date -u +%T)] $*"; }
bench(){ harness/run_bench.sh "$@" 2>&1 | grep -E "Successful requests|Output token throughput|Median TTFT|P90 TTFT|P99 ITL|wrote|rror" | sed 's/^/    /'; }
rsh(){ ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 ubuntu@"$1" "export PATH=\$HOME/.local/bin:\$PATH; cd ~/pd; $2"; }
health(){ curl -s -o /dev/null -w "%{http_code}" --max-time 10 "http://$1:$2/health"; }
xfer(){ rsh $B_PRIV "docker logs vllm 2>&1 | grep 'KV Transfer metrics' | tail -1" | sed 's/.*KV Transfer/    xfer: KV Transfer/'; }

log "E4b server start (TX=RX=1m)"
pkill -f "[t]oy_proxy" 2>/dev/null; sleep 1
rsh $A_PRIV "UCX_EXTRA='$TUNED_1M' CHUNK=2560 PREFIX=off PORT=8100 GPU_UTIL=0.90 CONNECTOR=producer OWN_IP=$A_PRIV harness/serve.sh $MAIN" >/dev/null &
rsh $B_PRIV "UCX_EXTRA='$TUNED_1M' CHUNK=2560 PREFIX=off PORT=8200 GPU_UTIL=0.90 CONNECTOR=consumer OWN_IP=$B_PRIV harness/serve.sh $MAIN" >/dev/null & wait
setsid nohup python3 vllm-src/tests/v1/kv_connector/nixl_integration/toy_proxy_server.py --host 0.0.0.0 --port 8000 \
  --prefiller-hosts $A_PRIV --prefiller-ports 8100 --decoder-hosts $B_PRIV --decoder-ports 8200 > results/toy_proxy_E4b.log 2>&1 </dev/null & disown
sleep 6; log "health A=$(health $A_PRIV 8100) B=$(health $B_PRIV 8200)"
if [ "$(health $A_PRIV 8100)" = 200 ] && [ "$(health $B_PRIV 8200)" = 200 ]; then
  export BASE_URL=http://127.0.0.1:8000 METRICS_URL=http://$A_PRIV:8100/metrics MODEL=$MAIN CHUNK=2560 PREFIX=off
  export RESET_URLS="http://$A_PRIV:8100 http://$B_PRIV:8200"
  log "E4b 4K 0.5 (knob b, 1m segments in both directions)"
  SEED=2 bench E4 xfer_b_seg1m N0 random 0.5 --random-input-len 4096 --random-output-len 512; xfer
else
  log "E4b start failed, check the logs"
  rsh $A_PRIV "docker logs vllm 2>&1 | grep -iE 'UCX  ERROR|Failed to create' | head -5"
fi
pkill -f "[t]oy_proxy" 2>/dev/null
for h in $A_PRIV $B_PRIV; do rsh $h "docker rm -f vllm >/dev/null 2>&1"; done
log "E4b DONE"
