#!/usr/bin/env bash
# Round E5b · E5 supplement: re-measure 26_B3 ShareGPT 48 (9.3% of requests failed in the main run because of the proxy file limit, so that run was discarded)
# Question: as nodes are added, is disaggregation (xPyD) better than replicas, and which ratio fits. Does 31B disaggregation also fit within the TTFT budget.
# NVFP4 checkpoints have FP8 KV built in (26B 28.8 KB/tok, 31B 115 KB/tok). Every disaggregated configuration uses the tuned UCX.
set -u
export PATH=~/venv/bin:~/.local/bin:$PATH; cd ~/pd
ulimit -n 65536 2>/dev/null || true   # friction #20: at high request rates the proxy hits the default limit of 1,024
: "${A_PRIV:?}" "${B_PRIV:?}" "${C_PRIV:?}"
export RESULTS_DIR=$HOME/pd/results RESULTS_DIR_IN_CONTAINER=$HOME/pd/results ENV_JSON=$HOME/pd/results/env_E5.json
export SHAREGPT_JSON=$HOME/pd/data/ShareGPT_V3_unfiltered_cleaned_split.json
M26=nvidia/Gemma-4-26B-A4B-NVFP4
M31=nvidia/Gemma-4-31B-IT-NVFP4
TUNED="UCX_TLS=tcp,cuda_copy,cuda_ipc UCX_NET_DEVICES=all UCX_TCP_TX_SEG_SIZE=256k UCX_TCP_RX_SEG_SIZE=256k UCX_TCP_MAX_IOV=16 UCX_TCP_MAX_POLL=-1 UCX_TCP_SNDBUF=8m UCX_TCP_RCVBUF=8m UCX_RNDV_FRAG_SIZE=host:4M,cuda:8M"
PROXY=vllm-src/tests/v1/kv_connector/nixl_integration/toy_proxy_server.py
ALL="$A_PRIV $B_PRIV $C_PRIV"
mkdir -p results/xfer_E5
log(){ echo "[$(date -u +%T)] $*"; }
rsh(){ ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 ubuntu@"$1" "export PATH=\$HOME/.local/bin:\$PATH; cd ~/pd; $2"; }
health(){ curl -s -o /dev/null -w "%{http_code}" --max-time 10 "http://$1:$2/health"; }
DECODERS=""; CFG=""
stop_all(){ pkill -f "[r]r_proxy.py|[t]oy_proxy_server" 2>/dev/null; for h in $ALL; do rsh $h "docker rm -f vllm >/dev/null 2>&1"; done; sleep 2; }

# replicas: serve_rep NAME MODEL HOST...
serve_rep(){ CFG=$1; local M=$2; shift 2; stop_all; DECODERS=""
  for h in "$@"; do rsh $h "CHUNK=2560 PREFIX=off PORT=8100 GPU_UTIL=0.90 harness/serve.sh $M" >/dev/null & done; wait
  local ups=() ok=1 hs=""; for h in "$@"; do ups+=("http://$h:8100"); done
  setsid nohup python3 harness/rr_proxy.py --port 8000 --upstreams "${ups[@]}" > results/rr_proxy_E5_$CFG.log 2>&1 </dev/null & disown
  sleep 4; for h in "$@"; do c=$(health $h 8100); hs="$hs ${h##*.}=$c"; [ "$c" = 200 ] || ok=0; done
  log "  [$CFG] health$hs"; [ $ok = 1 ] || return 1
  export BASE_URL=http://127.0.0.1:8000 METRICS_URL=http://$1:8100/metrics MODEL=$M CHUNK=2560 PREFIX=off
  RESET_URLS=""; for h in "$@"; do RESET_URLS="$RESET_URLS http://$h:8100"; done; export RESET_URLS; }

# disaggregation: serve_pd NAME MODEL "PREFILL HOSTS" "DECODE HOSTS"
serve_pd(){ CFG=$1; local M=$2 P="$3" D="$4"; stop_all; DECODERS="$D"
  for h in $P; do rsh $h "UCX_EXTRA='$TUNED' CHUNK=2560 PREFIX=off PORT=8100 GPU_UTIL=0.90 CONNECTOR=producer OWN_IP=$h harness/serve.sh $M" >/dev/null & done
  for h in $D; do rsh $h "UCX_EXTRA='$TUNED' CHUNK=2560 PREFIX=off PORT=8200 GPU_UTIL=0.90 CONNECTOR=consumer OWN_IP=$h harness/serve.sh $M" >/dev/null & done
  wait
  local pp="" dp="" ok=1 hs=""; for h in $P; do pp="$pp 8100"; done; for h in $D; do dp="$dp 8200"; done
  setsid nohup python3 $PROXY --host 0.0.0.0 --port 8000 --prefiller-hosts $P --prefiller-ports $pp \
    --decoder-hosts $D --decoder-ports $dp > results/toy_proxy_E5_$CFG.log 2>&1 </dev/null & disown
  sleep 4
  for h in $P; do c=$(health $h 8100); hs="$hs P${h##*.}=$c"; [ "$c" = 200 ] || ok=0; done
  for h in $D; do c=$(health $h 8200); hs="$hs D${h##*.}=$c"; [ "$c" = 200 ] || ok=0; done
  log "  [$CFG] health$hs"; [ $ok = 1 ] || return 1
  local first; first=$(echo $P | awk '{print $1}')
  export BASE_URL=http://127.0.0.1:8000 METRICS_URL=http://$first:8100/metrics MODEL=$M CHUNK=2560 PREFIX=off
  RESET_URLS=""; for h in $P; do RESET_URLS="$RESET_URLS http://$h:8100"; done; for h in $D; do RESET_URLS="$RESET_URLS http://$h:8200"; done; export RESET_URLS; }

# One point: pt WORKLOAD RATE [extra args]. The seed depends only on the point (workload, rate) so every configuration sees the same request sequence. For a disaggregated configuration the raw transfer metrics of this point's window are saved per decode node.
pt(){ local WL=$1 R=$2; shift 2; local t0; t0=$(date -u +%s)
  log "  $CFG $WL r$R"
  SEED=$(python3 -c "print(int(float('$R')*1000)+(7 if '$WL'=='random' else 0))") harness/run_bench.sh E5 "$CFG" N0 "$WL" "$R" "$@" 2>&1 \
    | grep -E "Successful requests|Median TTFT|P99 ITL|wrote|rror" | sed 's/^/    /'
  for h in $DECODERS; do rsh $h "docker logs vllm --since $t0 2>&1 | grep 'KV Transfer metrics'" > results/xfer_E5/${CFG}_${WL}_r${R}_${h##*.}.log 2>/dev/null; done
  [ -n "$DECODERS" ] && log "    raw transfer lines saved: $(cat results/xfer_E5/${CFG}_${WL}_r${R}_*.log 2>/dev/null | wc -l)"; }
K4="--random-input-len 4096 --random-output-len 512"

log "E5b-0 collectors (three nodes)"
for h in $ALL; do rsh $h "PORTS='8100 8200' harness/node_collect.sh start" | sed 's/^/    /'; done
log "E5b 26_B3 sharegpt 48 re-measurement"
serve_rep 26_B3 $M26 $A_PRIV $B_PRIV $C_PRIV && pt sharegpt 48
stop_all
for h in $ALL; do rsh $h "harness/node_collect.sh stop" >/dev/null 2>&1; done
log "E5b DONE"
