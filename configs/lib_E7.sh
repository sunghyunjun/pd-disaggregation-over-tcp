#!/usr/bin/env bash
# 세션 E7 공통 함수. run_E7a.sh(두 대·한 대)와 run_E7b.sh(세 대)가 source 한다.
# 새로 넣은 것: 서버 기동 뒤 워밍업 30요청(프로토콜 이행), 지점당 제한 시간 25분, 반복 측정용 시드 규칙.
set -u
export PATH=~/venv/bin:~/.local/bin:$PATH; cd ~/pd
ulimit -n 65536 2>/dev/null || true
export RESULTS_DIR=$HOME/pd/results RESULTS_DIR_IN_CONTAINER=$HOME/pd/results ENV_JSON=$HOME/pd/results/env_E7.json
export SHAREGPT_JSON=$HOME/pd/data/ShareGPT_V3_unfiltered_cleaned_split.json TRACES_DIR=$HOME/pd/data/traces
M26=nvidia/Gemma-4-26B-A4B-NVFP4
M31=nvidia/Gemma-4-31B-IT-NVFP4
M26F=RedHatAI/gemma-4-26B-A4B-it-FP8-dynamic
M26H=google/gemma-4-26B-A4B-it
TUNED="UCX_TLS=tcp,cuda_copy,cuda_ipc UCX_NET_DEVICES=all UCX_TCP_TX_SEG_SIZE=256k UCX_TCP_RX_SEG_SIZE=256k UCX_TCP_MAX_IOV=16 UCX_TCP_MAX_POLL=-1 UCX_TCP_SNDBUF=8m UCX_TCP_RCVBUF=8m UCX_RNDV_FRAG_SIZE=host:4M,cuda:8M"
PROXY=vllm-src/tests/v1/kv_connector/nixl_integration/toy_proxy_server.py
K4="--random-input-len 4096 --random-output-len 512"
mkdir -p results/xfer_E7
log(){ echo "[$(date -u +%T)] $*"; }
rsh(){ ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 ubuntu@"$1" "export PATH=\$HOME/.local/bin:\$PATH; cd ~/pd; $2"; }
health(){ curl -s -o /dev/null -w "%{http_code}" --max-time 10 "http://$1:$2/health"; }
DECODERS=""; CFG=""; ALL=${ALL:-}
stop_all(){ pkill -f "[r]r_proxy.py|[t]oy_proxy_server" 2>/dev/null; for h in $ALL; do rsh $h "docker rm -f vllm >/dev/null 2>&1"; done; sleep 2; }

# 워밍업: 기동 직후 첫 요청들의 첫 토큰이 평소의 약 30배라(9/28 점검) 기록하지 않는 30요청으로 데운다
warm(){ vllm bench serve --backend vllm --base-url "$BASE_URL" --model "$MODEL" --dataset-name sharegpt --dataset-path "$SHAREGPT_JSON" \
          --num-prompts 30 --request-rate 4 --seed 999 >/dev/null 2>&1; log "  [$CFG] 워밍업 30요청 완료"; }

serve_rep(){ CFG=$1; local M=$2; shift 2; stop_all; DECODERS=""
  for h in "$@"; do rsh $h "CHUNK=2560 PREFIX=off PORT=8100 GPU_UTIL=${GPU_UTIL_OVERRIDE:-0.90} harness/serve.sh $M" >/dev/null & done; wait
  local ups=() ok=1 hs=""; for h in "$@"; do ups+=("http://$h:8100"); done
  setsid nohup python3 harness/rr_proxy.py --port 8000 --upstreams "${ups[@]}" > results/rr_proxy_E7_$CFG.log 2>&1 </dev/null & disown
  sleep 4; for h in "$@"; do c=$(health $h 8100); hs="$hs ${h##*.}=$c"; [ "$c" = 200 ] || ok=0; done
  log "  [$CFG] health$hs"; [ $ok = 1 ] || return 1
  export BASE_URL=http://127.0.0.1:8000 METRICS_URL=http://$1:8100/metrics MODEL=$M CHUNK=2560 PREFIX=off
  RESET_URLS=""; for h in "$@"; do RESET_URLS="$RESET_URLS http://$h:8100"; done; export RESET_URLS; warm; }

serve_pd(){ CFG=$1; local M=$2 P="$3" D="$4"; stop_all; DECODERS="$D"
  for h in $P; do rsh $h "UCX_EXTRA='$TUNED' CHUNK=2560 PREFIX=off PORT=8100 GPU_UTIL=0.90 CONNECTOR=producer OWN_IP=$h harness/serve.sh $M" >/dev/null & done
  for h in $D; do rsh $h "UCX_EXTRA='$TUNED' CHUNK=2560 PREFIX=off PORT=8200 GPU_UTIL=0.90 CONNECTOR=consumer OWN_IP=$h harness/serve.sh $M" >/dev/null & done
  wait
  local pp="" dp="" ok=1 hs=""; for h in $P; do pp="$pp 8100"; done; for h in $D; do dp="$dp 8200"; done
  setsid nohup python3 $PROXY --host 0.0.0.0 --port 8000 --prefiller-hosts $P --prefiller-ports $pp \
    --decoder-hosts $D --decoder-ports $dp > results/toy_proxy_E7_$CFG.log 2>&1 </dev/null & disown
  sleep 5
  for h in $P; do c=$(health $h 8100); hs="$hs P${h##*.}=$c"; [ "$c" = 200 ] || ok=0; done
  for h in $D; do c=$(health $h 8200); hs="$hs D${h##*.}=$c"; [ "$c" = 200 ] || ok=0; done
  log "  [$CFG] health$hs"; [ $ok = 1 ] || return 1
  local first; first=$(echo $P | awk '{print $1}')
  export BASE_URL=http://127.0.0.1:8000 METRICS_URL=http://$first:8100/metrics MODEL=$M CHUNK=2560 PREFIX=off
  RESET_URLS=""; for h in $P; do RESET_URLS="$RESET_URLS http://$h:8100"; done; for h in $D; do RESET_URLS="$RESET_URLS http://$h:8200"; done; export RESET_URLS; warm; }

# 단일 노드(프록시 없이 직접). GPU_UTIL로 KV 용량을 맞춘다
serve_single(){ CFG=$1; local M=$2 H=$3 U=$4; stop_all; DECODERS=""
  rsh $H "CHUNK=2560 PREFIX=off PORT=8100 GPU_UTIL=$U harness/serve.sh $M" >/dev/null
  local c; c=$(health $H 8100); log "  [$CFG] health ${H##*.}=$c util=$U"; [ "$c" = 200 ] || return 1
  export BASE_URL=http://$H:8100 METRICS_URL=http://$H:8100/metrics MODEL=$M CHUNK=2560 PREFIX=off RESET_URLS="http://$H:8100"; warm; }

# 한 지점: pt 워크로드 요청률 반복번호 [추가 인자]. 시드 = 지점 기본값 + 1000 × 반복번호(0회차는 E5와 같은 시드)
pt(){ local WL=$1 R=$2 REP=$3; shift 3; local t0; t0=$(date -u +%s)
  local base; base=$(python3 -c "print(int(float('$R')*1000)+(7 if '$WL'=='random' else 0))")
  log "  $CFG $WL r$R #$REP"
  SEED=$((base+1000*REP)) timeout 1500 harness/run_bench.sh E7 "$CFG" N0 "$WL" "$R" "$@" 2>&1 \
    | grep -E "Successful requests|Median TTFT|wrote|rror" | grep -vE "Triton|_C_AVX512|^\s*Error [1-9]" | sed 's/^/    /'
  for h in $DECODERS; do rsh $h "docker logs vllm --since $t0 2>&1 | grep 'KV Transfer metrics'" > results/xfer_E7/${CFG}_${WL}_r${R}_n${REP}_${h##*.}.log 2>/dev/null; done; }
rep3(){ local k; for k in 0 1 2; do pt "$@" $k; done; }                 # rep3 워크로드 요청률 → 세 번
pt3(){ local WL=$1 R=$2; shift 2; local k; for k in 0 1 2; do pt $WL $R $k "$@"; done; }

# 실제 트레이스 재생(캐시 끔). MULT 0.001 = 실시간, 작을수록 빠르게
trace1(){ local MULT=$1 REP=$2; local t0; t0=$(date -u +%s); log "  $CFG azure_conv ×$MULT #$REP"
  SEED=$((4242+1000*REP)) TRACE_SEC_MULT=$MULT timeout 1500 harness/run_bench.sh E7 "$CFG" N0 azure_conv self 2>&1 \
    | grep -E "Successful requests|Median TTFT|wrote|rror" | grep -vE "Triton|_C_AVX512|^\s*Error [1-9]" | sed 's/^/    /'
  for h in $DECODERS; do rsh $h "docker logs vllm --since $t0 2>&1 | grep 'KV Transfer metrics'" > results/xfer_E7/${CFG}_trace_n${REP}_${h##*.}.log 2>/dev/null; done; }
trace3(){ local k; for k in 0 1 2; do trace1 $1 $k; done; }

collectors_start(){ for h in $ALL; do rsh $h "PORTS='8100 8200' harness/node_collect.sh start" | sed 's/^/    /'; done
  setsid nohup bash -c "stdbuf -oL sar -u 1" > results/client_cpu_E7_${1}.txt 2>/dev/null </dev/null & disown; }
collectors_stop(){ for h in $ALL; do rsh $h "harness/node_collect.sh stop" >/dev/null 2>&1; done; pkill -f "[s]ar -u 1" 2>/dev/null; }
