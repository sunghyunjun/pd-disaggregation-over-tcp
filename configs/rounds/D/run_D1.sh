#!/usr/bin/env bash
# Round D-1 · raising KV transfer throughput (P1 fixed, main model, prefix off)
# Hypothesis: the ceiling is the UCX GPU staging path, not the AWS per-flow cap. Switching to a host buffer could give up to 8x (based on llm-d CPU↔CPU 4.0 GB/s).
# Run on the client node. env: A_PRIV, B_PRIV
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

serve_p1(){ # $1 = tag ; env: UCX_EXTRA KV_BUFFER_DEVICE NIXL_THREADS BLOCK
  local extra=""; [ -n "${BLOCK:-}" ] && extra="--block-size $BLOCK"
  pkill -f "toy_proxy" 2>/dev/null; sleep 1
  rsh $A_PRIV "UCX_EXTRA='${UCX_EXTRA:-}' KV_BUFFER_DEVICE='${KV_BUFFER_DEVICE:-}' NIXL_THREADS='${NIXL_THREADS:-}' GPU_UTIL='${GPU_UTIL:-0.90}' CHUNK=2560 PREFIX=off PORT=8100 CONNECTOR=producer OWN_IP=$A_PRIV harness/serve.sh $MAIN $extra" &
  rsh $B_PRIV "UCX_EXTRA='${UCX_EXTRA:-}' KV_BUFFER_DEVICE='${KV_BUFFER_DEVICE:-}' NIXL_THREADS='${NIXL_THREADS:-}' GPU_UTIL='${GPU_UTIL:-0.90}' CHUNK=2560 PREFIX=off PORT=8200 CONNECTOR=consumer OWN_IP=$B_PRIV harness/serve.sh $MAIN $extra" &
  wait
  setsid nohup python3 vllm-src/tests/v1/kv_connector/nixl_integration/toy_proxy_server.py --host 0.0.0.0 --port 8000 \
    --prefiller-hosts $A_PRIV --prefiller-ports 8100 --decoder-hosts $B_PRIV --decoder-ports 8200 > results/toy_proxy_D_$1.log 2>&1 < /dev/null & disown
  sleep 4; curl -s -o /dev/null -w "    proxy %{http_code}\n" localhost:8000/v1/models
  export BASE_URL=http://127.0.0.1:8000 METRICS_URL=http://$A_PRIV:8100/metrics MODEL=$MAIN CHUNK=2560 PREFIX=off
}
points(){ # $1 = config tag
  bench D "$1" N0 random 0.25 --random-input-len 4096 --random-output-len 512; xfer
  bench D "$1" N0 random 1    --random-input-len 4096 --random-output-len 512; xfer
}

log "D0 baseline iperf 1/2/4/8 flows"
rsh $A_PRIV "for P in 1 2 4 8; do iperf3 -c $B_PRIV -P \$P -t 8 -J | jq -r \"\\\"P=\$P \\(.end.sum_sent.bits_per_second/1e9) Gbps\\\"\"; done" | sed 's/^/    /'
log "check whether nixlbench exists"
rsh $A_PRIV "docker run --rm vllm/vllm-openai:v0.30.0 bash -lc 'which nixlbench 2>/dev/null; python -c \"import nixl,os;print(os.path.dirname(nixl.__file__))\" 2>/dev/null' " | sed 's/^/    /'

log "D1a baseline (current settings: GPU registration, 4 threads, UCX defaults)"
unset UCX_EXTRA KV_BUFFER_DEVICE NIXL_THREADS BLOCK; serve_p1 a && points d1a

log "D1b host buffer (kv_buffer_device=cpu)"
unset UCX_EXTRA NIXL_THREADS BLOCK; export KV_BUFFER_DEVICE=cpu; serve_p1 b && points d1b

log "D1c 16 threads"
unset UCX_EXTRA KV_BUFFER_DEVICE BLOCK; export NIXL_THREADS=16; serve_p1 c && points d1c

log "D1d UCX segment, buffer and fragment sizes"
unset KV_BUFFER_DEVICE NIXL_THREADS BLOCK
export UCX_EXTRA="UCX_TLS=tcp,cuda_copy,cuda_ipc UCX_NET_DEVICES=all UCX_TCP_TX_SEG_SIZE=256k UCX_TCP_RX_SEG_SIZE=256k UCX_TCP_MAX_IOV=16 UCX_TCP_MAX_POLL=-1 UCX_TCP_SNDBUF=8m UCX_TCP_RCVBUF=8m UCX_RNDV_FRAG_SIZE=host:4M,cuda:8M"
serve_p1 d && points d1d

log "D1e block size 32 (128 KiB descriptors)"
unset UCX_EXTRA KV_BUFFER_DEVICE NIXL_THREADS; export BLOCK=32; serve_p1 e && points d1e

log "D1f combination (D1d UCX knobs + 16 threads + block 32)"
export NIXL_THREADS=16 BLOCK=32
export UCX_EXTRA="UCX_TLS=tcp,cuda_copy,cuda_ipc UCX_NET_DEVICES=all UCX_TCP_TX_SEG_SIZE=256k UCX_TCP_RX_SEG_SIZE=256k UCX_TCP_MAX_IOV=16 UCX_TCP_MAX_POLL=-1 UCX_TCP_SNDBUF=8m UCX_TCP_RCVBUF=8m UCX_RNDV_FRAG_SIZE=host:4M,cuda:8M"
unset KV_BUFFER_DEVICE; serve_p1 f && points d1f

log "D1g ShareGPT 4 req/s re-check (the best candidate vs the baseline is picked by hand after seeing the results)"
unset UCX_EXTRA KV_BUFFER_DEVICE NIXL_THREADS BLOCK; serve_p1 g && { bench D d1g_base N0 sharegpt 4; xfer; }

pkill -f toy_proxy 2>/dev/null; for h in $A_PRIV $B_PRIV; do rsh $h "docker rm -f vllm >/dev/null 2>&1"; done
log "D1 DONE"
