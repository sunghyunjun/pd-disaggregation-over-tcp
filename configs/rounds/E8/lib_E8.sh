#!/usr/bin/env bash
# Round E8 shared functions (derived from lib_E7.sh). Review-response measurements: B1 replica chunk sweep, B2 cause of the global pause in disaggregated configurations, B3 P–D connection count.
# Changes from E7
#   - serve_rep takes the chunk size as an argument (fixed at 2560 through E7). MM_LIMIT, if set, is passed to serve.sh.
#   - serve_pd selects the proxy kind (PROXY_KIND: toy=vLLM's test proxy as is, toyi=instrumented copy, aio=harness/pd_proxy.py) and the UCX setting bundle (UCXSET: TUNED|SEG|DEFAULT).
#   - Optional records around pt: SNAP_D=1 snapshots the ITL histogram from the decode node's /metrics, SS=1 samples ss on both P and D.
#   - att: computes the per-request chat SLO attainment of the point just finished (TTFT ≤1 s, longest gap per request ≤50 ms) on the spot.
set -u
export PATH=~/venv/bin:~/.local/bin:$PATH; cd ~/pd
ulimit -n 65536 2>/dev/null || true
export RESULTS_DIR=$HOME/pd/results RESULTS_DIR_IN_CONTAINER=$HOME/pd/results ENV_JSON=$HOME/pd/results/env_E8.json
export SHAREGPT_JSON=$HOME/pd/data/ShareGPT_V3_unfiltered_cleaned_split.json TRACES_DIR=$HOME/pd/data/traces
M26=nvidia/Gemma-4-26B-A4B-NVFP4
M31=nvidia/Gemma-4-31B-IT-NVFP4
M26F=RedHatAI/gemma-4-26B-A4B-it-FP8-dynamic
TUNED="UCX_TLS=tcp,cuda_copy,cuda_ipc UCX_NET_DEVICES=all UCX_TCP_TX_SEG_SIZE=256k UCX_TCP_RX_SEG_SIZE=256k UCX_TCP_MAX_IOV=16 UCX_TCP_MAX_POLL=-1 UCX_TCP_SNDBUF=8m UCX_TCP_RCVBUF=8m UCX_RNDV_FRAG_SIZE=host:4M,cuda:8M"
SEG="UCX_TLS=tcp,cuda_copy,cuda_ipc UCX_NET_DEVICES=all UCX_TCP_TX_SEG_SIZE=256k UCX_TCP_RX_SEG_SIZE=256k"
DEFAULT=""
TOY=vllm-src/tests/v1/kv_connector/nixl_integration/toy_proxy_server.py
K4="--random-input-len 4096 --random-output-len 512"
mkdir -p results/xfer_E8 results/metrics_E8
log(){ echo "[$(date -u +%T)] $*"; }
rsh(){ ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 ubuntu@"$1" "export PATH=\$HOME/.local/bin:\$PATH; cd ~/pd; $2"; }
health(){ curl -s -o /dev/null -w "%{http_code}" --max-time 10 "http://$1:$2/health"; }
PREFILLERS=""; DECODERS=""; CFG=""; ALL=${ALL:-}; LAST_OUT=""
stop_all(){ pkill -f "[r]r_proxy.py|[t]oy_proxy_server|[t]oy_proxy_instr|[p]d_proxy.py" 2>/dev/null; for h in $ALL; do rsh $h "docker rm -f vllm >/dev/null 2>&1"; done; sleep 2; }

warm(){ vllm bench serve --backend vllm --base-url "$BASE_URL" --model "$MODEL" --dataset-name sharegpt --dataset-path "$SHAREGPT_JSON" \
          --num-prompts 30 --request-rate 4 --seed 999 >/dev/null 2>&1; log "  [$CFG] warm-up of 30 requests done"; }

# serve_rep CFG MODEL CHUNK host...
serve_rep(){ CFG=$1; local M=$2 C=$3; shift 3; stop_all; PREFILLERS=""; DECODERS=""
  # Use the MM_LIMIT and SERVE_EXTRA found in step 0 only when the chunk goes below 2560 (the 2560 control uses exactly the E7 command)
  # With FORCE_MM=1 the same MM_LIMIT is used at 2560 too (supplementary check: is the 2048 outlier due to the MM setting)
  local mm="" ex=""; { [ "$C" -lt 2560 ] || [ "${FORCE_MM:-0}" = 1 ]; } && { mm=${MM_LIMIT:-}; ex=${SERVE_EXTRA:-}; }
  for h in "$@"; do rsh $h "MM_LIMIT='$mm' CHUNK=$C PREFIX=off PORT=8100 GPU_UTIL=0.90 harness/serve.sh $M $ex" | sed 's/^/    /' & done; wait
  local ups=() ok=1 hs=""; for h in "$@"; do ups+=("http://$h:8100"); done
  setsid nohup python3 harness/rr_proxy.py --port 8000 --upstreams "${ups[@]}" > results/rr_proxy_E8_$CFG.log 2>&1 </dev/null & disown
  sleep 4; for h in "$@"; do c=$(health $h 8100); hs="$hs ${h##*.}=$c"; [ "$c" = 200 ] || ok=0; done
  log "  [$CFG] chunk=$C health$hs"; [ $ok = 1 ] || return 1
  export BASE_URL=http://127.0.0.1:8000 METRICS_URL=http://$1:8100/metrics MODEL=$M CHUNK=$C PREFIX=off
  RESET_URLS=""; for h in "$@"; do RESET_URLS="$RESET_URLS http://$h:8100"; done; export RESET_URLS; warm; }

# PROXY_KIND=toy|toyi|aio UCXSET=TUNED|SEG|DEFAULT serve_pd CFG MODEL "P..." "D..."
serve_pd(){ CFG=$1; local M=$2 P="$3" D="$4"; stop_all; PREFILLERS="$P"; DECODERS="$D"
  local kind=${PROXY_KIND:-toyi} set=${UCXSET:-TUNED}; local ucx=${!set}
  for h in $P; do rsh $h "UCX_EXTRA='$ucx' CHUNK=2560 PREFIX=off PORT=8100 GPU_UTIL=0.90 CONNECTOR=producer OWN_IP=$h harness/serve.sh $M" | sed 's/^/    /' & done
  for h in $D; do rsh $h "UCX_EXTRA='$ucx' CHUNK=2560 PREFIX=off PORT=8200 GPU_UTIL=0.90 CONNECTOR=consumer OWN_IP=$h harness/serve.sh $M" | sed 's/^/    /' & done
  wait
  local pp="" dp="" pu=() du=() ok=1 hs=""
  for h in $P; do pp="$pp 8100"; pu+=("http://$h:8100"); done; for h in $D; do dp="$dp 8200"; du+=("http://$h:8200"); done
  local tr=results/proxy_trace_E8_$CFG.jsonl
  case $kind in
    toy)  setsid nohup python3 $TOY --host 0.0.0.0 --port 8000 --prefiller-hosts $P --prefiller-ports $pp --decoder-hosts $D --decoder-ports $dp > results/proxy_E8_$CFG.log 2>&1 </dev/null & disown ;;
    toyi) PROXY_TRACE=$tr setsid nohup python3 harness/toy_proxy_instr.py --host 0.0.0.0 --port 8000 --prefiller-hosts $P --prefiller-ports $pp --decoder-hosts $D --decoder-ports $dp > results/proxy_E8_$CFG.log 2>&1 </dev/null & disown ;;
    aio)  PROXY_TRACE=$tr setsid nohup python3 harness/pd_proxy.py --port 8000 --prefill "${pu[@]}" --decode "${du[@]}" > results/proxy_E8_$CFG.log 2>&1 </dev/null & disown ;;
  esac
  sleep 5
  for h in $P; do c=$(health $h 8100); hs="$hs P${h##*.}=$c"; [ "$c" = 200 ] || ok=0; done
  for h in $D; do c=$(health $h 8200); hs="$hs D${h##*.}=$c"; [ "$c" = 200 ] || ok=0; done
  log "  [$CFG] proxy=$kind ucx=$set health$hs"; [ $ok = 1 ] || return 1
  local first; first=$(echo $P | awk '{print $1}')
  export BASE_URL=http://127.0.0.1:8000 METRICS_URL=http://$first:8100/metrics MODEL=$M CHUNK=2560 PREFIX=off
  RESET_URLS=""; for h in $P; do RESET_URLS="$RESET_URLS http://$h:8100"; done; for h in $D; do RESET_URLS="$RESET_URLS http://$h:8200"; done; export RESET_URLS; warm; }

snap_d(){ local tag=$1; for h in $DECODERS; do curl -s --max-time 10 "http://$h:8200/metrics" | grep -E '^vllm:(inter_token_latency_seconds|time_per_output_token_seconds|request_time_per_output_token_seconds)_(bucket|count|sum)' > results/metrics_E8/${tag}_${h##*.}.txt; done; }

# One point: pt WORKLOAD RATE REP [extra args]. Seed = point base + 1000 × REP (same rule as E5 and E7, so the same rate and rep give the same prompts)
pt(){ local WL=$1 R=$2 REP=$3; shift 3; local t0; t0=$(date -u +%s); local tag=${CFG}_${WL}_r${R}_n${REP}
  local base; base=$(python3 -c "print(int(float('$R')*1000)+(7 if '$WL'=='random' else 0))")
  log "  $CFG $WL r$R #$REP"
  [ "${SNAP_D:-0}" = 1 ] && snap_d ${tag}_pre
  if [ "${SS:-0}" = 1 ]; then local p d; p=$(echo $PREFILLERS | awk '{print $1}'); d=$(echo $DECODERS | awk '{print $1}')
    rsh $p "harness/ss_sample.sh start $d ~/pd/results/ss_E8_${tag}_P.txt" >/dev/null; rsh $d "harness/ss_sample.sh start $p ~/pd/results/ss_E8_${tag}_D.txt" >/dev/null; fi
  SEED=$((base+1000*REP)) timeout 1500 harness/run_bench.sh E8 "$CFG" N0 "$WL" "$R" "$@" 2>&1 \
    | grep -E "Successful requests|Median TTFT|wrote|rror" | grep -vE "Triton|_C_AVX512|^\s*Error [1-9]" | sed 's/^/    /'
  if [ "${SS:-0}" = 1 ]; then for h in $PREFILLERS $DECODERS; do rsh $h "harness/ss_sample.sh stop" >/dev/null; done; fi
  [ "${SNAP_D:-0}" = 1 ] && snap_d ${tag}_post
  for h in $DECODERS; do rsh $h "docker logs vllm --since $t0 2>&1 | grep 'KV Transfer metrics'" > results/xfer_E8/${tag}_${h##*.}.log 2>/dev/null; done
  LAST_OUT=$(ls -td results/*_E8_${CFG}_N0_${WL}_r${R} 2>/dev/null | head -1); log "    attainment $(att)"; }

# Per-request chat SLO attainment of the point just finished (an on-the-spot value for deciding how to proceed; the report numbers are recomputed by aggregate.py)
att(){ [ -n "$LAST_OUT" ] && [ -f "$LAST_OUT/bench.json" ] || { echo "?"; return; }
  python3 - "$LAST_OUT/bench.json" <<'PY'
import json,sys
b=json.load(open(sys.argv[1])); t=b["ttfts"]; I=b["itls"]; E=b.get("errors") or [""]*len(t); n=len(t)
ok=[(not e) and (tt is not None and tt<=1.0) and (not l or max(l)<=0.05) for tt,l,e in zip(t,I,E)]
print(f"{sum(ok)/max(n,1):.3f} (n={n})")
PY
}
attv(){ att | awk '{print $1}'; }

collectors_start(){ for h in $ALL; do rsh $h "TAG=$1 PORTS='8100 8200' harness/node_collect.sh start" | sed 's/^/    /'; done
  setsid nohup bash -c "stdbuf -oL sar -u 1" > results/client_cpu_E8_${1}.txt 2>/dev/null </dev/null & disown; }
collectors_stop(){ for h in $ALL; do rsh $h "harness/node_collect.sh stop" >/dev/null 2>&1; done; pkill -f "[s]ar -u 1" 2>/dev/null; }
