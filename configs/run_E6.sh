#!/usr/bin/env bash
# 세션 E6 · 레이어별 푸시(vLLM PR #56874) 시험. g7e 쌍 + 클러스터 배치 그룹, 26B·31B NVFP4, 4K 입력.
# 목적: 전송을 프리필 계산 뒤에 숨겨 31B 4K의 첫 토큰 꼬리를 대화 SLO(1초) 안으로 넣을 수 있는가.
# 대조: 끌어오기(기존 튜닝 1P1D) / 푸시(v0.30.0 원본, 한 번에 WRITE) / 레이어별 푸시(PR 적용본).
# 관문: 각 푸시 구성은 같은 프롬프트의 그리디 출력이 끌어오기와 바이트 단위로 같아야 측정한다.
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

# serve_push 이름 모델 stock|lw
serve_push(){ CFG=$1; local M=$2 MODE=$3 mounts="" envx=""; stop_all
  [ "$MODE" = lw ] && { mounts="$PATCH_MOUNTS"; envx="VLLM_NIXL_LAYERWISE_PUSH=1"; }
  rsh $A_PRIV "UCX_EXTRA='$TUNED' ENV_EXTRA='$envx' EXTRA_MOUNTS='$mounts' KV_CONNECTOR_NAME=NixlPushConnector KV_ENGINE_ID=$ENGINE CHUNK=2560 PREFIX=off PORT=8100 GPU_UTIL=0.90 CONNECTOR=producer OWN_IP=$A_PRIV harness/serve.sh $M" >/dev/null &
  rsh $B_PRIV "UCX_EXTRA='$TUNED' ENV_EXTRA='$envx' EXTRA_MOUNTS='$mounts' KV_CONNECTOR_NAME=NixlPushConnector CHUNK=2560 PREFIX=off PORT=8200 GPU_UTIL=0.90 CONNECTOR=consumer OWN_IP=$B_PRIV harness/serve.sh $M" >/dev/null & wait
  setsid nohup python3 $PROXY_PUSH --model $M --prefill $A_PRIV:8100 --decode $B_PRIV:8200 --prefill-engine-id $ENGINE \
    --prefill-kv-host $A_PRIV --prefill-side-channel-port 5600 --prefill-tp-size 1 --prefill-pp-size 1 --port 8000 > results/proxy_E6_$CFG.log 2>&1 </dev/null & disown
  sleep 8; ready || return 1
  # 실제로 어떤 코드가 돌고 있는지 서버 로그로 확인(레이어별은 PR의 INFO 한 줄이 떠야 한다)
  local on; on=$(rsh $A_PRIV "docker logs vllm 2>&1 | grep -c 'layer-wise push ENABLED'")
  log "  [$CFG] 레이어별 푸시 로그 줄 수(P): $on"
  if [ "$MODE" = lw ] && [ "${on:-0}" -eq 0 ]; then log "  [$CFG] 레이어별 푸시가 켜지지 않음 → 이 구성 중단"; return 1; fi
  if [ "$MODE" = stock ] && [ "${on:-0}" -ne 0 ]; then log "  [$CFG] 원본이어야 하는데 레이어별이 켜짐 → 중단"; return 1; fi
  export BASE_URL=http://127.0.0.1:8000 METRICS_URL=http://$A_PRIV:8100/metrics MODEL=$M CHUNK=2560 PREFIX=off
  export RESET_URLS="http://$A_PRIV:8100 http://$B_PRIV:8200"; }

gate(){ log "  [$CFG] 정확성 관문 기록"; python3 harness/greedy_check.py run --base-url $BASE_URL --model $MODEL --sharegpt $SHAREGPT_JSON --out results/gate_E6/$CFG.json --repeat ${1:-1} 2>&1 | sed 's/^/    /'; }
gate_vs(){ python3 harness/greedy_check.py compare results/gate_E6/$1.json results/gate_E6/$CFG.json 2>&1 | sed 's/^/    /'; return ${PIPESTATUS[0]}; }

pt(){ local R=$1; local t0; t0=$(date -u +%s); log "  $CFG random r$R"
  SEED=$(python3 -c "print(int(float('$R')*1000)+7)") harness/run_bench.sh E6 "$CFG" N0 random "$R" --random-input-len 4096 --random-output-len 512 2>&1 \
    | grep -E "Successful requests|Median TTFT|P90 TTFT|P99 ITL|wrote|rror" | grep -v -E "Triton|_C_AVX512" | sed 's/^/    /'
  for h in $A_PRIV $B_PRIV; do rsh $h "docker logs vllm --since $t0 2>&1 | grep 'KV Transfer metrics'" > results/xfer_E6/${CFG}_r${R}_${h##*.}.log 2>/dev/null; done; }

log "E6-0 수집기와 iperf"
for h in $A_PRIV $B_PRIV; do rsh $h "PORTS='8100 8200' harness/node_collect.sh start" | sed 's/^/    /'; done
setsid nohup bash -c "stdbuf -oL sar -u 1" > results/client_cpu_E6.txt 2>/dev/null </dev/null & disown
echo "    단일 흐름 $(rsh $A_PRIV "iperf3 -c $B_PRIV -P 1 -t 5 -J 2>/dev/null | jq -r '.end.sum_sent.bits_per_second/1e9'") Gbps"

log "E6-1 31B · 끌어오기(기준, 같은 서버 반복으로 결정성 확인)"
serve_pull 31_pull $M31 && { gate 2; pt 0.25; pt 0.5; pt 1; }
log "E6-2 31B · 푸시 원본(한 번에 WRITE) — 푸시 자체의 효과를 가르는 대조"
serve_push 31_push $M31 stock && { gate; if gate_vs 31_pull; then pt 0.25; pt 0.5; else log "  관문 불일치 → 측정 생략"; fi; }
log "E6-3 31B · 레이어별 푸시(PR 적용본)"
serve_push 31_lw $M31 lw && { gate; if gate_vs 31_pull; then pt 0.25; pt 0.5; pt 1; else log "  관문 불일치 → 측정 생략"; fi; }
log "E6-4 26B · 끌어오기"
serve_pull 26_pull $M26 && { gate; pt 1; pt 2; }
log "E6-5 26B · 레이어별 푸시"
serve_push 26_lw $M26 lw && { gate; if gate_vs 26_pull; then pt 1; pt 2; else log "  관문 불일치 → 측정 생략"; fi; }

stop_all
for h in $A_PRIV $B_PRIV; do rsh $h "harness/node_collect.sh stop" >/dev/null 2>&1; done
pkill -f "[s]ar -u 1" 2>/dev/null
log "E6 DONE"
