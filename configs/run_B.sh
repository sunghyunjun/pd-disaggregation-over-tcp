#!/usr/bin/env bash
# Session B (g7.2xlarge x2 + c6i client): B2 (2 replicas, RR proxy) vs P1 (prefill A -> decode B, NixlConnector TCP).
# Runs ON THE CLIENT NODE. Requires: A_PRIV, B_PRIV env; ~/pd synced on all nodes; GPU nodes reachable by ssh from client (key copied).
# Steps are independent; each logs to results/run_B.log. Estimated 3.5 h.
set -u
export PATH=~/.local/bin:$PATH; cd ~/pd
: "${A_PRIV:?}" "${B_PRIV:?}"
export RESULTS_DIR=$HOME/pd/results RESULTS_DIR_IN_CONTAINER=$HOME/pd/results ENV_JSON=$HOME/pd/results/env_B.json
export SHAREGPT_JSON=$HOME/pd/data/ShareGPT_V3_unfiltered_cleaned_split.json TRACES_DIR=$HOME/pd/data/traces
MAIN=${MAIN:-nvidia/Gemma-4-26B-A4B-NVFP4}; ANCHOR=${ANCHOR:-Qwen/Qwen3-8B}
RATES_SG=${RATES_SG:-"0.5 1 2 4 8"}; SYN_L=${SYN_L:-"4096 16384 32768"}; SYN_R=${SYN_R:-"0.25 0.5 1"}
log(){ echo "[$(date -u +%T)] $*"; }
bench(){ harness/run_bench.sh "$@" 2>&1 | grep -E "Successful requests|Request throughput|Output token throughput|Median TTFT|P90 TTFT|P99 ITL|wrote|rror" | sed 's/^/    /'; }
rsh(){ ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 ubuntu@"$1" "export PATH=~/.local/bin:\$PATH; cd ~/pd; $2"; }
serve_pair(){ # mode(b2|p1) model chunk prefix [extra]
  local mode=$1 m=$2 chunk=$3 prefix=$4; shift 4
  pkill -f "rr_proxy|toy_proxy" 2>/dev/null; sleep 1
  if [ "$mode" = b2 ]; then
    rsh $A_PRIV "CHUNK=$chunk PREFIX=$prefix PORT=8100 harness/serve.sh $m $*" & rsh $B_PRIV "CHUNK=$chunk PREFIX=$prefix PORT=8100 harness/serve.sh $m $*" & wait
    setsid nohup python3 harness/rr_proxy.py --port 8000 --upstreams http://$A_PRIV:8100 http://$B_PRIV:8100 > results/rr_proxy_B.log 2>&1 < /dev/null & disown
  else
    rsh $A_PRIV "CHUNK=$chunk PREFIX=$prefix PORT=8100 CONNECTOR=producer OWN_IP=$A_PRIV harness/serve.sh $m $*" & rsh $B_PRIV "CHUNK=$chunk PREFIX=$prefix PORT=8200 CONNECTOR=consumer OWN_IP=$B_PRIV harness/serve.sh $m $*" & wait
    setsid nohup python3 vllm-src/tests/v1/kv_connector/nixl_integration/toy_proxy_server.py --host 0.0.0.0 --port 8000 --prefiller-hosts $A_PRIV --prefiller-ports 8100 --decoder-hosts $B_PRIV --decoder-ports 8200 > results/toy_proxy_B.log 2>&1 < /dev/null & disown
  fi
  sleep 4; curl -s -o /dev/null -w "proxy %{http_code}\n" localhost:8000/v1/models
  export BASE_URL=http://127.0.0.1:8000 METRICS_URL=http://$A_PRIV:8100/metrics MODEL=$m CHUNK=$chunk PREFIX=$prefix
}
xfer_metrics(){ rsh $B_PRIV "docker logs vllm 2>&1 | grep 'KV Transfer metrics' | tail -3 | cut -c1-260" | sed 's/^/    xfer: /'; }
tc_set(){ for h in $A_PRIV $B_PRIV; do rsh $h "IF=\$(ip -o -4 route show to default | awk '{print \$5}'); sudo tc qdisc replace dev \$IF root tbf rate $1 burst 128mb latency 50ms" ; done; }
tc_clear(){ for h in $A_PRIV $B_PRIV; do rsh $h "IF=\$(ip -o -4 route show to default | awk '{print \$5}'); sudo tc qdisc del dev \$IF root 2>/dev/null || true"; done; }

bash harness/env_snapshot.sh results/env_B.json $A_PRIV >/dev/null 2>&1
log "B0 iperf A<->B"; rsh $A_PRIV "iperf3 -c $B_PRIV -P 1 -t 8 -J | jq -r '.end.sum_sent.bits_per_second/1e9' ; iperf3 -c $B_PRIV -P 4 -t 8 -J | jq -r '.end.sum_sent.bits_per_second/1e9'" | sed 's/^/    A->B Gbps /'

log "B1 B2 main model: proxy overhead check (direct vs proxy, 1 req/s)"
serve_pair b2 $MAIN 2560 on
bench B B2 N0 sharegpt 1
BASE_URL=http://$A_PRIV:8100 bench B B2direct N0 sharegpt 1
log "B2 B2 main: ShareGPT sweep"; for r in $RATES_SG; do log "  rate $r"; bench B B2 N0 sharegpt $r; done
log "B3 B2 main: synthetic grid (prefix off)"; serve_pair b2 $MAIN 2560 off
for L in $SYN_L; do for r in $SYN_R; do log "  L=$L r=$r"; bench B B2 N0 random $r --random-input-len $L --random-output-len 512; done; done
log "B4 B2 main: Azure-conv real-time (mult 0.001, 600 req)"; serve_pair b2 $MAIN 2560 on; TRACE_SEC_MULT=0.001 NUM_PROMPTS=600 bench B B2 N0 azure_conv self

log "B5 P1 main: ShareGPT sweep (N0)"; serve_pair p1 $MAIN 2560 on
for r in $RATES_SG; do log "  rate $r"; bench B P1 N0 sharegpt $r; xfer_metrics; done
log "B6 P1 main: synthetic grid (prefix off)"; serve_pair p1 $MAIN 2560 off
for L in $SYN_L; do for r in $SYN_R; do log "  L=$L r=$r"; bench B P1 N0 random $r --random-input-len $L --random-output-len 512; xfer_metrics; done; done
log "B7 P1 main: Azure-conv real-time"; serve_pair p1 $MAIN 2560 on; TRACE_SEC_MULT=0.001 NUM_PROMPTS=600 bench B P1 N0 azure_conv self; xfer_metrics

log "B8 P1 main: tc bandwidth sweep (prefix off), L in $SYN_L at 0.5 req/s"
serve_pair p1 $MAIN 2560 off
for bw in 1gbit 2500mbit; do tc_set $bw; log "  tc $bw"; for L in $SYN_L; do bench B P1 tc$bw random 0.5 --random-input-len $L --random-output-len 512; xfer_metrics; done; done; tc_clear

log "B9 anchor $ANCHOR: B2 vs P1 ShareGPT (3 rates)"
serve_pair b2 $ANCHOR 2560 on; for r in 1 4 8; do bench B B2 N0 sharegpt $r; done
serve_pair p1 $ANCHOR 2560 on; for r in 1 4 8; do bench B P1 N0 sharegpt $r; xfer_metrics; done
pkill -f "rr_proxy|toy_proxy" 2>/dev/null; for h in $A_PRIV $B_PRIV; do rsh $h "docker rm -f vllm >/dev/null 2>&1"; done
log "SESSION B DONE"
