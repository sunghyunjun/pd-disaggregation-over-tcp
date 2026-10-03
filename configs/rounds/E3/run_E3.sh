#!/usr/bin/env bash
# Round E3 · disaggregation on a g6e (L40S) pair, model 26B-A4B FP8 only
# Topic: the tuned transfer (7~8.5 Gbps) exceeds the g6e network baseline of 5 Gbps, so what happens once the credits are drained
# Method: cache reset (RESET_URLS) + a different seed per point + start only after the collectors are verified
set -u
export PATH=~/venv/bin:~/.local/bin:$PATH; cd ~/pd
: "${A_PRIV:?}" "${B_PRIV:?}"
export RESULTS_DIR=$HOME/pd/results RESULTS_DIR_IN_CONTAINER=$HOME/pd/results ENV_JSON=$HOME/pd/results/env_E3.json
export SHAREGPT_JSON=$HOME/pd/data/ShareGPT_V3_unfiltered_cleaned_split.json
MAIN=${MAIN:-RedHatAI/gemma-4-26B-A4B-it-FP8-dynamic}
TUNED="UCX_TLS=tcp,cuda_copy,cuda_ipc UCX_NET_DEVICES=all UCX_TCP_TX_SEG_SIZE=256k UCX_TCP_RX_SEG_SIZE=256k UCX_TCP_MAX_IOV=16 UCX_TCP_MAX_POLL=-1 UCX_TCP_SNDBUF=8m UCX_TCP_RCVBUF=8m UCX_RNDV_FRAG_SIZE=host:4M,cuda:8M"
log(){ echo "[$(date -u +%T)] $*"; }
bench(){ harness/run_bench.sh "$@" 2>&1 | grep -E "Successful requests|Output token throughput|Median TTFT|P90 TTFT|P99 ITL|wrote|rror|캐시 리셋" | sed 's/^/    /'; }
rsh(){ ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 ubuntu@"$1" "export PATH=~/.local/bin:\$PATH; cd ~/pd; $2"; }
xfer(){ rsh $B_PRIV "docker logs vllm 2>&1 | grep 'KV Transfer metrics' | tail -1 | cut -c1-230" | sed 's/^/    xfer: /'; }
health(){ curl -s -o /dev/null -w "%{http_code}" --max-time 10 "http://$1:$2/health"; }
serve_b2(){ pkill -f "rr_proxy|toy_proxy" 2>/dev/null; sleep 1
  rsh $A_PRIV "CHUNK=2560 PREFIX=$1 PORT=8100 GPU_UTIL=0.90 harness/serve.sh $MAIN" >/dev/null &
  rsh $B_PRIV "CHUNK=2560 PREFIX=$1 PORT=8100 GPU_UTIL=0.90 harness/serve.sh $MAIN" >/dev/null & wait
  setsid nohup python3 harness/rr_proxy.py --port 8000 --upstreams http://$A_PRIV:8100 http://$B_PRIV:8100 > results/rr_proxy_E3.log 2>&1 </dev/null & disown
  sleep 4; echo "    health A=$(health $A_PRIV 8100) B=$(health $B_PRIV 8100)"
  [ "$(health $A_PRIV 8100)" = 200 ] && [ "$(health $B_PRIV 8100)" = 200 ] || return 1
  export BASE_URL=http://127.0.0.1:8000 METRICS_URL=http://$A_PRIV:8100/metrics MODEL=$MAIN CHUNK=2560 PREFIX=$1
  export RESET_URLS="http://$A_PRIV:8100 http://$B_PRIV:8100"; }
serve_p1(){ pkill -f "rr_proxy|toy_proxy" 2>/dev/null; sleep 1
  rsh $A_PRIV "UCX_EXTRA='$TUNED' CHUNK=2560 PREFIX=$1 PORT=8100 GPU_UTIL=0.90 CONNECTOR=producer OWN_IP=$A_PRIV harness/serve.sh $MAIN" >/dev/null &
  rsh $B_PRIV "UCX_EXTRA='$TUNED' CHUNK=2560 PREFIX=$1 PORT=8200 GPU_UTIL=0.90 CONNECTOR=consumer OWN_IP=$B_PRIV harness/serve.sh $MAIN" >/dev/null & wait
  setsid nohup python3 vllm-src/tests/v1/kv_connector/nixl_integration/toy_proxy_server.py --host 0.0.0.0 --port 8000 \
    --prefiller-hosts $A_PRIV --prefiller-ports 8100 --decoder-hosts $B_PRIV --decoder-ports 8200 > results/toy_proxy_E3.log 2>&1 </dev/null & disown
  sleep 4; echo "    health A=$(health $A_PRIV 8100) B=$(health $B_PRIV 8200)"
  [ "$(health $A_PRIV 8100)" = 200 ] && [ "$(health $B_PRIV 8200)" = 200 ] || return 1
  export BASE_URL=http://127.0.0.1:8000 METRICS_URL=http://$A_PRIV:8100/metrics MODEL=$MAIN CHUNK=2560 PREFIX=$1
  export RESET_URLS="http://$A_PRIV:8100 http://$B_PRIV:8200"; }

log "E3-0 start and verify collectors (both nodes)"
for h in $A_PRIV $B_PRIV; do rsh $h "PORTS='8100 8200' harness/node_collect.sh start" | sed 's/^/    /'; done
log "E3-0 iperf baseline and sustained measurement (credit drain check: 10 s -> 120 s)"
rsh $A_PRIV "for t in 10 120; do echo -n \"single flow \${t}s: \"; iperf3 -c $B_PRIV -P 1 -t \$t -J 2>/dev/null | jq -r '.end.sum_sent.bits_per_second/1e9'; done; echo -n '4 flows 30s: '; iperf3 -c $B_PRIV -P 4 -t 30 -J 2>/dev/null | jq -r '.end.sum_sent.bits_per_second/1e9'" | sed 's/^/    /'

log "E3-1 ShareGPT ladder (prefix off, different seed per point)"
serve_b2 off && for r in 4 8 12; do SEED=$r log "  B2 r$r"; SEED=$r bench E3 B2 N0 sharegpt $r; done
serve_p1 off && for r in 4 8 12; do log "  P1 r$r"; SEED=$r bench E3 P1tuned N0 sharegpt $r; xfer; done

log "E3-2 input 4K (the region where disaggregation wins) B2 vs P1"
serve_b2 off && for r in 0.5 1; do SEED=1 bench E3 B2 N0 random $r --random-input-len 4096 --random-output-len 512; done
serve_p1 off && for r in 0.5 1; do SEED=1 bench E3 P1tuned N0 random $r --random-input-len 4096 --random-output-len 512; xfer; done

log "E3-3 drain network credits with sustained load (4K, 0.5 req/s, 15 min): does transfer throughput drop"
serve_p1 off && { POINT_SEC=900 MIN_PROMPTS=400 SEED=7 bench E3 P1tuned_drain N0 random 0.5 --random-input-len 4096 --random-output-len 512; xfer
  rsh $A_PRIV "docker logs vllm 2>&1 | grep -c 'KV Transfer' || true" | sed 's/^/    /'
  log "  iperf re-measurement right after the drain"; rsh $A_PRIV "iperf3 -c $B_PRIV -P 1 -t 20 -J 2>/dev/null | jq -r '.end.sum_sent.bits_per_second/1e9'" | sed 's/^/    single flow /'; }

for h in $A_PRIV $B_PRIV; do rsh $h "harness/node_collect.sh stop" >/dev/null 2>&1; rsh $h "docker rm -f vllm >/dev/null 2>&1"; done
pkill -f "rr_proxy|toy_proxy" 2>/dev/null
log "E3 DONE"
