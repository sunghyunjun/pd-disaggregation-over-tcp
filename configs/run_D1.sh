#!/usr/bin/env bash
# 세션 D-1 · KV 전송 처리량 끌어올리기 (P1 고정, 주 모델, prefix off)
# 가설: 천장은 AWS 흐름 상한이 아니라 UCX GPU 스테이징 경로. 호스트 버퍼 전환이 최대 8배(llm-d CPU↔CPU 4.0 GB/s 근거).
# 클라이언트 노드에서 실행. env: A_PRIV, B_PRIV
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
  rsh $A_PRIV "UCX_EXTRA='${UCX_EXTRA:-}' KV_BUFFER_DEVICE='${KV_BUFFER_DEVICE:-}' NIXL_THREADS='${NIXL_THREADS:-}' CHUNK=2560 PREFIX=off PORT=8100 CONNECTOR=producer OWN_IP=$A_PRIV harness/serve.sh $MAIN $extra" &
  rsh $B_PRIV "UCX_EXTRA='${UCX_EXTRA:-}' KV_BUFFER_DEVICE='${KV_BUFFER_DEVICE:-}' NIXL_THREADS='${NIXL_THREADS:-}' CHUNK=2560 PREFIX=off PORT=8200 CONNECTOR=consumer OWN_IP=$B_PRIV harness/serve.sh $MAIN $extra" &
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

log "D0 기준점 iperf 1/2/4/8 흐름"
rsh $A_PRIV "for P in 1 2 4 8; do iperf3 -c $B_PRIV -P \$P -t 8 -J | jq -r \"\\\"P=\$P \\(.end.sum_sent.bits_per_second/1e9) Gbps\\\"\"; done" | sed 's/^/    /'
log "nixlbench 존재 확인"
rsh $A_PRIV "docker run --rm vllm/vllm-openai:v0.30.0 bash -lc 'which nixlbench 2>/dev/null; python -c \"import nixl,os;print(os.path.dirname(nixl.__file__))\" 2>/dev/null' " | sed 's/^/    /'

log "D1a 기준선 (현재 설정: GPU 등록, 스레드 4, UCX 기본)"
unset UCX_EXTRA KV_BUFFER_DEVICE NIXL_THREADS BLOCK; serve_p1 a && points d1a

log "D1b 호스트 버퍼 (kv_buffer_device=cpu)"
unset UCX_EXTRA NIXL_THREADS BLOCK; export KV_BUFFER_DEVICE=cpu; serve_p1 b && points d1b

log "D1c 스레드 16"
unset UCX_EXTRA KV_BUFFER_DEVICE BLOCK; export NIXL_THREADS=16; serve_p1 c && points d1c

log "D1d UCX 세그먼트·버퍼·조각 크기"
unset KV_BUFFER_DEVICE NIXL_THREADS BLOCK
export UCX_EXTRA="UCX_TLS=tcp,cuda_copy,cuda_ipc UCX_NET_DEVICES=all UCX_TCP_TX_SEG_SIZE=256k UCX_TCP_RX_SEG_SIZE=256k UCX_TCP_MAX_IOV=16 UCX_TCP_MAX_POLL=-1 UCX_TCP_SNDBUF=8m UCX_TCP_RCVBUF=8m UCX_RNDV_FRAG_SIZE=host:4M,cuda:8M"
serve_p1 d && points d1d

log "D1e 블록 크기 32 (디스크립터 128 KiB)"
unset UCX_EXTRA KV_BUFFER_DEVICE NIXL_THREADS; export BLOCK=32; serve_p1 e && points d1e

log "D1f 조합 (D1d UCX 노브 + 스레드 16 + 블록 32)"
export NIXL_THREADS=16 BLOCK=32
export UCX_EXTRA="UCX_TLS=tcp,cuda_copy,cuda_ipc UCX_NET_DEVICES=all UCX_TCP_TX_SEG_SIZE=256k UCX_TCP_RX_SEG_SIZE=256k UCX_TCP_MAX_IOV=16 UCX_TCP_MAX_POLL=-1 UCX_TCP_SNDBUF=8m UCX_TCP_RCVBUF=8m UCX_RNDV_FRAG_SIZE=host:4M,cuda:8M"
unset KV_BUFFER_DEVICE; serve_p1 f && points d1f

log "D1g ShareGPT 4 req/s 재확인 (기준선 설정 대비 최적 후보는 결과 보고 수동)"
unset UCX_EXTRA KV_BUFFER_DEVICE NIXL_THREADS BLOCK; serve_p1 g && { bench D d1g_base N0 sharegpt 4; xfer; }

pkill -f toy_proxy 2>/dev/null; for h in $A_PRIV $B_PRIV; do rsh $h "docker rm -f vllm >/dev/null 2>&1"; done
log "D1 DONE"
