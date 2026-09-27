#!/usr/bin/env bash
# Start (or restart) the vLLM server container and wait for readiness. Usage:
#   serve.sh MODEL [extra vllm args...]      env: CHUNK (2048), PORT (8000), MAXLEN (32768), GPU_UTIL (0.90), PREFIX (on|off), CONNECTOR (none|producer|consumer), OWN_IP, IMAGE
#   선택(비어 있으면 기존과 완전히 같음): ENV_EXTRA(컨테이너 환경변수 K=V 목록), EXTRA_MOUNTS(host:container[:ro] 목록),
#   KV_CONNECTOR_NAME(기본 NixlConnector), KV_ENGINE_ID(kv-transfer-config의 engine_id)
# Prints the memory-profile lines and returns 0 when "Application startup complete" appears, 1 on failure (log saved to results/serve_fail_<ts>.log).
set -u
MODEL=$1; shift
CHUNK=${CHUNK:-2048}; PORT=${PORT:-8000}; MAXLEN=${MAXLEN:-32768}; GPU_UTIL=${GPU_UTIL:-0.90}; PREFIX=${PREFIX:-on}; CONNECTOR=${CONNECTOR:-none}
IMAGE=${IMAGE:-vllm/vllm-openai:v0.30.0}; OWN_IP=${OWN_IP:-$(hostname -I | awk '{print $1}')}
ENVS=(-e HF_TOKEN="$(cat ~/.hf_token 2>/dev/null)" -e VLLM_SSM_CONV_STATE_LAYOUT=DS -e VLLM_SERVER_DEV_MODE=1)
# UCX_EXTRA: space-separated K=V pairs passed into the container (transfer-path tuning)
for kv in ${UCX_EXTRA:-}; do ENVS+=(-e "$kv"); done
for kv in ${ENV_EXTRA:-}; do ENVS+=(-e "$kv"); done
MOUNTS=(); for m in ${EXTRA_MOUNTS:-}; do MOUNTS+=(-v "$m"); done
ARGS=(--port "$PORT" --max-model-len "$MAXLEN" --gpu-memory-utilization "$GPU_UTIL" --max-num-batched-tokens "$CHUNK" --max-num-seqs 256 --seed 0 --limit-mm-per-prompt '{"image":0}')
[ "$PREFIX" = off ] && ARGS+=(--no-enable-prefix-caching)
if [ "$CONNECTOR" != none ]; then
  ENVS+=(-e VLLM_NIXL_SIDE_CHANNEL_HOST="$OWN_IP" -e VLLM_NIXL_SIDE_CHANNEL_PORT=5600 -e UCX_TLS=tcp,cuda_copy,cuda_ipc -e UCX_NET_DEVICES=all)
  ROLE=$([ "$CONNECTOR" = producer ] && echo kv_producer || echo kv_consumer)
  KVCFG="{\"kv_connector\":\"${KV_CONNECTOR_NAME:-NixlConnector}\",\"kv_role\":\"$ROLE\""
  [ -n "${KV_ENGINE_ID:-}" ] && KVCFG="$KVCFG,\"engine_id\":\"$KV_ENGINE_ID\""
  [ -n "${KV_BUFFER_DEVICE:-}" ] && KVCFG="$KVCFG,\"kv_buffer_device\":\"$KV_BUFFER_DEVICE\""
  [ -n "${NIXL_THREADS:-}" ] && KVCFG="$KVCFG,\"kv_connector_extra_config\":{\"num_threads\":$NIXL_THREADS}"
  ARGS+=(--kv-transfer-config "$KVCFG}")
fi
docker rm -f vllm >/dev/null 2>&1 || true
docker run -d --name vllm --gpus all --ipc=host --network host -v ~/pd:/pd -v ~/.cache/huggingface:/root/.cache/huggingface -v ~/.cache/vllm:/root/.cache/vllm \
  ${MOUNTS[@]+"${MOUNTS[@]}"} "${ENVS[@]}" "$IMAGE" "$MODEL" "${ARGS[@]}" "$@" >/dev/null || { echo "docker run failed"; exit 1; }
for i in $(seq 1 90); do
  if docker logs vllm 2>&1 | grep -q "Application startup complete"; then
    docker logs vllm 2>&1 | grep -E "Available KV cache memory|GPU KV cache size|Loading weights took" | tail -3 | sed 's/^.*INFO [0-9: -]*\[[a-z_.]*:[0-9]*\] //'
    echo "READY $MODEL chunk=$CHUNK prefix=$PREFIX connector=$CONNECTOR"; exit 0
  fi
  if ! docker ps --format '{{.Names}}' | grep -q '^vllm$'; then
    ts=$(date -u +%Y%m%dT%H%M%SZ); docker logs vllm > ~/pd/results/serve_fail_${ts}.log 2>&1
    echo "FAILED $MODEL — see results/serve_fail_${ts}.log"; docker logs vllm 2>&1 | grep -E "Error|Traceback" | tail -3 | cut -c1-200; exit 1
  fi
  sleep 10
done
echo "TIMEOUT waiting for $MODEL"; exit 1
