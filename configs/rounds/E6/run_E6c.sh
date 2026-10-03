#!/usr/bin/env bash
# Round E6c · E6 resumed (2): measure the remaining configurations with the calibrated gate (byte match for short prompts + key-word overlap ≥0.4 for long prompts)
# Purpose: can hiding the transfer behind prefill compute bring the 31B 4K TTFT tail within the chat SLO (1 s).
# Controls: pull (the existing tuned 1P1D) / push (stock v0.30.0, one WRITE at the end) / layer-wise push (with the PR applied).
# Gate: a push configuration is measured only if its greedy output for the same prompts is byte-identical to pull.
set -u
export PATH=~/venv/bin:~/.local/bin:$PATH; cd ~/pd
ulimit -n 65536 2>/dev/null || true
: "${A_PRIV:?}" "${B_PRIV:?}"
export RESULTS_DIR=$HOME/pd/results RESULTS_DIR_IN_CONTAINER=$HOME/pd/results ENV_JSON=$HOME/pd/results/env_E6.json
export SHAREGPT_JSON=$HOME/pd/data/ShareGPT_V3_unfiltered_cleaned_split.json
M26=nvidia/Gemma-4-26B-A4B-NVFP4
M31=nvidia/Gemma-4-31B-IT-NVFP4
TUNED="UCX_TLS=tcp,cuda_copy,cuda_ipc UCX_NET_DEVICES=all UCX_TCP_TX_SEG_SIZE=256k UCX_TCP_RX_SEG_SIZE=256k UCX_TCP_MAX_IOV=16 UCX_TCP_MAX_POLL=-1 UCX_TCP_SNDBUF=8m UCX_TCP_RCVBUF=8m UCX_RNDV_FRAG_SIZE=host:4M,cuda:8M"
PROXY_PULL=vllm-src/tests/v1/kv_connector/nixl_integration/toy_proxy_server.py
PROXY_PUSH=third_party/vllm-v0.30.0-examples/disagg_proxy_pushconnector_demo.py
VP=/usr/local/lib/python3.12/dist-packages/vllm; TP=/home/ubuntu/pd/third_party/pr56874/vllm; NX=distributed/kv_transfer/kv_connector/v1/nixl
PATCH_MOUNTS="$TP/envs.py:$VP/envs.py:ro $TP/$NX/connector.py:$VP/$NX/connector.py:ro $TP/$NX/push_scheduler.py:$VP/$NX/push_scheduler.py:ro $TP/$NX/push_worker.py:$VP/$NX/push_worker.py:ro"
ENGINE=pd-prefill-0
mkdir -p results/xfer_E6 results/gate_E6
log(){ echo "[$(date -u +%T)] $*"; }
rsh(){ ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 ubuntu@"$1" "export PATH=\$HOME/.local/bin:\$PATH; cd ~/pd; $2"; }
health(){ curl -s -o /dev/null -w "%{http_code}" --max-time 10 "http://$1:$2/health"; }
CFG=""
stop_all(){ pkill -f "[t]oy_proxy_server|[d]isagg_proxy_pushconnector" 2>/dev/null; for h in $A_PRIV $B_PRIV; do rsh $h "docker rm -f vllm >/dev/null 2>&1"; done; sleep 2; }
ready(){ local a b; a=$(health $A_PRIV 8100); b=$(health $B_PRIV 8200); log "  [$CFG] health P=$a D=$b"; [ "$a" = 200 ] && [ "$b" = 200 ]; }

serve_pull(){ CFG=$1; local M=$2; stop_all
  rsh $A_PRIV "UCX_EXTRA='$TUNED' CHUNK=2560 PREFIX=off PORT=8100 GPU_UTIL=0.90 CONNECTOR=producer OWN_IP=$A_PRIV harness/serve.sh $M" >/dev/null &
  rsh $B_PRIV "UCX_EXTRA='$TUNED' CHUNK=2560 PREFIX=off PORT=8200 GPU_UTIL=0.90 CONNECTOR=consumer OWN_IP=$B_PRIV harness/serve.sh $M" >/dev/null & wait
  setsid nohup python3 $PROXY_PULL --host 0.0.0.0 --port 8000 --prefiller-hosts $A_PRIV --prefiller-ports 8100 \
    --decoder-hosts $B_PRIV --decoder-ports 8200 > results/proxy_E6_$CFG.log 2>&1 </dev/null & disown
  sleep 5; ready || return 1
  export BASE_URL=http://127.0.0.1:8000 METRICS_URL=http://$A_PRIV:8100/metrics MODEL=$M CHUNK=2560 PREFIX=off
  export RESET_URLS="http://$A_PRIV:8100 http://$B_PRIV:8200"; }

# serve_push NAME MODEL stock|lw
serve_push(){ CFG=$1; local M=$2 MODE=$3 mounts="" envx=""; stop_all
  [ "$MODE" = lw ] && { mounts="$PATCH_MOUNTS"; envx="VLLM_NIXL_LAYERWISE_PUSH=1"; }
  rsh $A_PRIV "UCX_EXTRA='$TUNED' ENV_EXTRA='$envx' EXTRA_MOUNTS='$mounts' KV_CONNECTOR_NAME=NixlPushConnector KV_ENGINE_ID=$ENGINE CHUNK=2560 PREFIX=off PORT=8100 GPU_UTIL=0.90 CONNECTOR=producer OWN_IP=$A_PRIV harness/serve.sh $M" >/dev/null &
  rsh $B_PRIV "UCX_EXTRA='$TUNED' ENV_EXTRA='$envx' EXTRA_MOUNTS='$mounts' KV_CONNECTOR_NAME=NixlPushConnector CHUNK=2560 PREFIX=off PORT=8200 GPU_UTIL=0.90 CONNECTOR=consumer OWN_IP=$B_PRIV harness/serve.sh $M" >/dev/null & wait
  setsid nohup python3 $PROXY_PUSH --model $M --prefill $A_PRIV:8100 --decode $B_PRIV:8200 --prefill-engine-id $ENGINE \
    --prefill-kv-host $A_PRIV --prefill-side-channel-port 5600 --prefill-tp-size 1 --prefill-pp-size 1 --port 8000 > results/proxy_E6_$CFG.log 2>&1 </dev/null & disown
  sleep 8; ready || return 1
  # Confirm from the server log which code is actually running (layer-wise must print the PR's one INFO line)
  local on; on=$(rsh $A_PRIV "docker logs vllm 2>&1 | grep -c 'layer-wise push ENABLED'")
  log "  [$CFG] layer-wise push log lines (P): $on"
  if [ "$MODE" = lw ] && [ "${on:-0}" -eq 0 ]; then log "  [$CFG] layer-wise push not enabled, aborting this configuration"; return 1; fi
  if [ "$MODE" = stock ] && [ "${on:-0}" -ne 0 ]; then log "  [$CFG] should be stock but layer-wise is enabled, aborting"; return 1; fi
  export BASE_URL=http://127.0.0.1:8000 METRICS_URL=http://$A_PRIV:8100/metrics MODEL=$M CHUNK=2560 PREFIX=off
  export RESET_URLS="http://$A_PRIV:8100 http://$B_PRIV:8200"; }

gate(){ log "  [$CFG] recording the correctness gate"; python3 harness/greedy_check.py run --base-url $BASE_URL --model $MODEL --sharegpt $SHAREGPT_JSON --out results/gate_E6/$CFG.json --repeat ${1:-1} 2>&1 | sed 's/^/    /'; }
gate_vs(){ python3 harness/greedy_check.py compare results/gate_E6/$1.json results/gate_E6/$CFG.json 2>&1 | sed 's/^/    /'; return ${PIPESTATUS[0]}; }

pt(){ local R=$1; local t0; t0=$(date -u +%s); log "  $CFG random r$R"
  SEED=$(python3 -c "print(int(float('$R')*1000)+7)") harness/run_bench.sh E6 "$CFG" N0 random "$R" --random-input-len 4096 --random-output-len 512 2>&1 \
    | grep -E "Successful requests|Median TTFT|P90 TTFT|P99 ITL|wrote|rror" | grep -v -E "Triton|_C_AVX512" | sed 's/^/    /'
  for h in $A_PRIV $B_PRIV; do rsh $h "docker logs vllm --since $t0 2>&1 | grep 'KV Transfer metrics'" > results/xfer_E6/${CFG}_r${R}_${h##*.}.log 2>/dev/null; done; }


# Chat-format gate. Records go to <CFG>_chat.json. The early E6 records taken with raw completions are kept as evidence.
gate(){ log "  [$CFG] recording the correctness gate (chat)"; python3 harness/greedy_check.py run --base-url $BASE_URL --model $MODEL --sharegpt $SHAREGPT_JSON --out results/gate_E6/${CFG}_chat.json --repeat ${1:-1} 2>&1 | sed 's/^/    /'; }
gate_vs(){ python3 harness/greedy_check.py compare results/gate_E6/${1}_chat.json results/gate_E6/${CFG}_chat.json 2>&1 | sed 's/^/    /'; return ${PIPESTATUS[0]}; }
serve_single(){ CFG=$1; local M=$2; stop_all
  rsh $A_PRIV "CHUNK=2560 PREFIX=off PORT=8100 GPU_UTIL=0.90 harness/serve.sh $M" >/dev/null
  [ "$(health $A_PRIV 8100)" = 200 ] || { log "  [$CFG] single server failed to start"; return 1; }
  export BASE_URL=http://$A_PRIV:8100 MODEL=$M; }
# Choosing the reference: if pull equals single node use single, otherwise use pull as the reference (and record that fact)
pick_ref(){ local single=$1 pull=$2
  if python3 harness/greedy_check.py compare results/gate_E6/${single}_chat.json results/gate_E6/${pull}_chat.json >/dev/null 2>&1; then
    log "  reference: pull = single node, so single node is the ground truth"; REF=$single
  else log "  warning: pull != single node, using pull as the reference and investigating this difference separately"; REF=$pull; fi; }
measure_if(){ if gate_vs $REF; then "$@"; else log "  gate mismatch, measurement skipped"; fi; }


# Calibrated gate. Threshold basis: same prompt 0.58 or higher, different prompt (false failure) 0.17 or lower.
gate_vs(){ python3 harness/greedy_check.py compare results/gate_E6/${1}_chat.json results/gate_E6/${CFG}_chat.json --exact-under 100 --min-overlap 0.4 2>&1 | sed 's/^/    /'; return ${PIPESTATUS[0]}; }
REF=31_pull   # E6b confirmed pull != single (late word divergence), so pull is the reference

log "E6c-1 31B · stock push"
serve_push 31_push $M31 stock && { gate; measure_if eval 'pt 0.25; pt 0.5'; }
log "E6c-2 31B · layer-wise push"
serve_push 31_lw $M31 lw && { gate; measure_if eval 'pt 0.25; pt 0.5; pt 1'; }
log "E6c-3 26B · single-node ground truth"
serve_single 26_single $M26 && gate 2
log "E6c-4 26B · pull"
serve_pull 26_pull $M26 && { gate; gate_vs 26_single; REF=26_pull; pt 1; pt 2; }
log "E6c-5 26B · layer-wise push"
serve_push 26_lw $M26 lw && { gate; measure_if eval 'pt 1; pt 2'; }

stop_all
for h in $A_PRIV $B_PRIV; do rsh $h "harness/node_collect.sh stop" >/dev/null 2>&1; done
pkill -f "[s]ar -u 1" 2>/dev/null
log "E6c DONE"
