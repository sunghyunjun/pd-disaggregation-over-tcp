#!/usr/bin/env bash
# Round E2 · disaggregation (P1) vs replicas (B2) on a g7e pair, transfer tuning applied by default
# Hypothesis: a faster GPU leaves more decode-step headroom, so the gain from disaggregation shrinks
set -u
export PATH=~/venv/bin:~/.local/bin:$PATH; cd ~/pd
: "${A_PRIV:?}" "${B_PRIV:?}"
export RESULTS_DIR=$HOME/pd/results RESULTS_DIR_IN_CONTAINER=$HOME/pd/results ENV_JSON=$HOME/pd/results/env_E2.json
export SHAREGPT_JSON=$HOME/pd/data/ShareGPT_V3_unfiltered_cleaned_split.json
MAIN=${MAIN:-RedHatAI/gemma-4-26B-A4B-it-FP8-dynamic}
TUNED="UCX_TLS=tcp,cuda_copy,cuda_ipc UCX_NET_DEVICES=all UCX_TCP_TX_SEG_SIZE=256k UCX_TCP_RX_SEG_SIZE=256k UCX_TCP_MAX_IOV=16 UCX_TCP_MAX_POLL=-1 UCX_TCP_SNDBUF=8m UCX_TCP_RCVBUF=8m UCX_RNDV_FRAG_SIZE=host:4M,cuda:8M"
log(){ echo "[$(date -u +%T)] $*"; }
bench(){ harness/run_bench.sh "$@" 2>&1 | grep -E "Successful requests|Output token throughput|Median TTFT|P90 TTFT|P99 ITL|wrote|rror" | sed 's/^/    /'; }
rsh(){ ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 ubuntu@"$1" "export PATH=~/.local/bin:\$PATH; cd ~/pd; $2"; }
xfer(){ rsh $B_PRIV "docker logs vllm 2>&1 | grep 'KV Transfer metrics' | tail -1 | cut -c1-240" | sed 's/^/    xfer: /'; }
health(){ curl -s -o /dev/null -w "%{http_code}" --max-time 10 "http://$1:$2/health"; }

serve_b2(){ # 2 replicas + round robin
  pkill -f "rr_proxy|toy_proxy" 2>/dev/null; sleep 1
  rsh $A_PRIV "CHUNK=2560 PREFIX=off PORT=8100 GPU_UTIL=0.90 harness/serve.sh $MAIN" >/dev/null &
  rsh $B_PRIV "CHUNK=2560 PREFIX=off PORT=8100 GPU_UTIL=0.90 harness/serve.sh $MAIN" >/dev/null &
  wait
  setsid nohup python3 harness/rr_proxy.py --port 8000 --upstreams http://$A_PRIV:8100 http://$B_PRIV:8100 > results/rr_proxy_E2.log 2>&1 < /dev/null & disown
  sleep 4; echo "    health A=$(health $A_PRIV 8100) B=$(health $B_PRIV 8100)"
  [ "$(health $A_PRIV 8100)" = 200 ] && [ "$(health $B_PRIV 8100)" = 200 ] || return 1
  export BASE_URL=http://127.0.0.1:8000 METRICS_URL=http://$A_PRIV:8100/metrics MODEL=$MAIN CHUNK=2560 PREFIX=off
}
serve_p1(){ # prefill A -> decode B, tuning applied
  pkill -f "rr_proxy|toy_proxy" 2>/dev/null; sleep 1
  rsh $A_PRIV "UCX_EXTRA='$TUNED' CHUNK=2560 PREFIX=off PORT=8100 GPU_UTIL=0.90 CONNECTOR=producer OWN_IP=$A_PRIV harness/serve.sh $MAIN" >/dev/null &
  rsh $B_PRIV "UCX_EXTRA='$TUNED' CHUNK=2560 PREFIX=off PORT=8200 GPU_UTIL=0.90 CONNECTOR=consumer OWN_IP=$B_PRIV harness/serve.sh $MAIN" >/dev/null &
  wait
  setsid nohup python3 vllm-src/tests/v1/kv_connector/nixl_integration/toy_proxy_server.py --host 0.0.0.0 --port 8000 \
    --prefiller-hosts $A_PRIV --prefiller-ports 8100 --decoder-hosts $B_PRIV --decoder-ports 8200 > results/toy_proxy_E2.log 2>&1 < /dev/null & disown
  sleep 4; echo "    health A=$(health $A_PRIV 8100) B=$(health $B_PRIV 8200)"
  [ "$(health $A_PRIV 8100)" = 200 ] && [ "$(health $B_PRIV 8200)" = 200 ] || return 1
  export BASE_URL=http://127.0.0.1:8000 METRICS_URL=http://$A_PRIV:8100/metrics MODEL=$MAIN CHUNK=2560 PREFIX=off
}
RATES=${RATES:-"4 8 12 16 24"}
log "E2-0 iperf (g7e pair)"
rsh $A_PRIV "for P in 1 4; do echo -n \"P=\$P \"; iperf3 -c $B_PRIV -P \$P -t 6 -J 2>/dev/null | jq -r '.end.sum_sent.bits_per_second/1e9'; done" | sed 's/^/    /'
log "E2-1 B2 replica ladder"
serve_b2 && for r in $RATES; do log "  B2 r$r"; bench E2 B2 N0 sharegpt $r; done
log "E2-2 P1 disaggregation (tuned) ladder"
serve_p1 && for r in $RATES; do log "  P1 r$r"; bench E2 P1tuned N0 sharegpt $r; xfer; done
log "E2-3 input 4K row (0.5·1 req/s, B2 vs P1)"
serve_b2 && for r in 0.5 1; do bench E2 B2 N0 random $r --random-input-len 4096 --random-output-len 512; done
serve_p1 && for r in 0.5 1; do bench E2 P1tuned N0 random $r --random-input-len 4096 --random-output-len 512; xfer; done
pkill -f "rr_proxy|toy_proxy" 2>/dev/null; for h in $A_PRIV $B_PRIV; do rsh $h "docker rm -f vllm >/dev/null 2>&1"; done
log "E2 DONE"
