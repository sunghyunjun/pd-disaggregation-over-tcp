#!/usr/bin/env bash
# D-1b 재시도 · 호스트 버퍼(kv_buffer_device=cpu)
# 마찰 #10: g7.2xlarge는 호스트 메모리 30 GiB뿐. KV 미러 8.7 GiB + 가중치 로드로 OOM(dmesg oom-kill 확인).
# 대응: GPU 점유율을 낮춰 KV 캐시(=호스트 미러)를 줄인다. 같은 조건의 GPU 등록 대조군도 함께 측정.
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
mem(){ for h in $A_PRIV $B_PRIV; do rsh $h "free -g | awk 'NR==2{print \"    ram used \" \$3 \" / \" \$2 \" GiB\"}'"; done; }
serve_p1(){ local tag=$1
  local extra=""; [ -n "${BLOCK:-}" ] && extra="--block-size $BLOCK"
  pkill -f "toy_proxy" 2>/dev/null; sleep 1
  rsh $A_PRIV "UCX_EXTRA='${UCX_EXTRA:-}' KV_BUFFER_DEVICE='${KV_BUFFER_DEVICE:-}' NIXL_THREADS='${NIXL_THREADS:-}' GPU_UTIL='${GPU_UTIL:-0.90}' CHUNK=2560 PREFIX=off PORT=8100 CONNECTOR=producer OWN_IP=$A_PRIV harness/serve.sh $MAIN $extra" &
  rsh $B_PRIV "UCX_EXTRA='${UCX_EXTRA:-}' KV_BUFFER_DEVICE='${KV_BUFFER_DEVICE:-}' NIXL_THREADS='${NIXL_THREADS:-}' GPU_UTIL='${GPU_UTIL:-0.90}' CHUNK=2560 PREFIX=off PORT=8200 CONNECTOR=consumer OWN_IP=$B_PRIV harness/serve.sh $MAIN $extra" &
  wait
  setsid nohup python3 vllm-src/tests/v1/kv_connector/nixl_integration/toy_proxy_server.py --host 0.0.0.0 --port 8000 \
    --prefiller-hosts $A_PRIV --prefiller-ports 8100 --decoder-hosts $B_PRIV --decoder-ports 8200 > results/toy_proxy_D1b_$tag.log 2>&1 < /dev/null & disown
  sleep 4; curl -s -o /dev/null -w "    proxy %{http_code}\n" localhost:8000/v1/models
  export BASE_URL=http://127.0.0.1:8000 METRICS_URL=http://$A_PRIV:8100/metrics MODEL=$MAIN CHUNK=2560 PREFIX=off
}
points(){ bench D "$1" N0 random 0.25 --random-input-len 4096 --random-output-len 512; xfer
          bench D "$1" N0 random 1    --random-input-len 4096 --random-output-len 512; xfer; }

log "D1b1 대조군: GPU 등록, 점유율 0.55 (호스트 버퍼와 같은 KV 용량)"
unset UCX_EXTRA KV_BUFFER_DEVICE NIXL_THREADS BLOCK; export GPU_UTIL=0.55
serve_p1 ctl && points d1b_ctl_gpu; mem

log "D1b2 호스트 버퍼, 점유율 0.55"
export KV_BUFFER_DEVICE=cpu GPU_UTIL=0.55
serve_p1 host && points d1b_host; mem

log "D1b3 호스트 버퍼 + UCX 노브"
export UCX_EXTRA="UCX_TLS=tcp,cuda_copy,cuda_ipc UCX_NET_DEVICES=all UCX_TCP_TX_SEG_SIZE=256k UCX_TCP_RX_SEG_SIZE=256k UCX_TCP_MAX_IOV=16 UCX_TCP_MAX_POLL=-1 UCX_TCP_SNDBUF=8m UCX_TCP_RCVBUF=8m UCX_RNDV_FRAG_SIZE=host:4M,cuda:8M"
serve_p1 hostucx && points d1b_host_ucx; mem

log "D1b4 호스트 버퍼 + UCX 노브 + 스레드 16"
export NIXL_THREADS=16
serve_p1 hostucxth && points d1b_host_ucx_th16; mem

pkill -f toy_proxy 2>/dev/null; for h in $A_PRIV $B_PRIV; do rsh $h "docker rm -f vllm >/dev/null 2>&1"; done
log "D1b DONE"
