#!/usr/bin/env bash
# 세션 E5b · E5 보충: 26_B3 ShareGPT 48 재측정 (본편에서 프록시 파일 한도로 9.3% 실패 → 폐기)
# 질문: 노드를 늘릴 때 분리(xPyD)가 복제본보다 나은가, 어느 비율이 맞는가. 31B도 분리가 첫 토큰 예산 안에 드는가.
# NVFP4 체크포인트는 KV가 FP8로 내장(26B 28.8 KB/tok, 31B 115 KB/tok). 모든 분리 구성은 튜닝 UCX.
set -u
export PATH=~/venv/bin:~/.local/bin:$PATH; cd ~/pd
ulimit -n 65536 2>/dev/null || true   # 마찰 #20: 높은 요청률에서 프록시가 기본 한도 1,024에 걸림
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

# 복제본: serve_rep 이름 모델 호스트...
serve_rep(){ CFG=$1; local M=$2; shift 2; stop_all; DECODERS=""
  for h in "$@"; do rsh $h "CHUNK=2560 PREFIX=off PORT=8100 GPU_UTIL=0.90 harness/serve.sh $M" >/dev/null & done; wait
  local ups=() ok=1 hs=""; for h in "$@"; do ups+=("http://$h:8100"); done
  setsid nohup python3 harness/rr_proxy.py --port 8000 --upstreams "${ups[@]}" > results/rr_proxy_E5_$CFG.log 2>&1 </dev/null & disown
  sleep 4; for h in "$@"; do c=$(health $h 8100); hs="$hs ${h##*.}=$c"; [ "$c" = 200 ] || ok=0; done
  log "  [$CFG] health$hs"; [ $ok = 1 ] || return 1
  export BASE_URL=http://127.0.0.1:8000 METRICS_URL=http://$1:8100/metrics MODEL=$M CHUNK=2560 PREFIX=off
  RESET_URLS=""; for h in "$@"; do RESET_URLS="$RESET_URLS http://$h:8100"; done; export RESET_URLS; }

# 분리: serve_pd 이름 모델 "프리필 호스트" "디코드 호스트"
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

# 한 지점: pt 워크로드 요청률 [추가 인자]. 시드는 지점(워크로드·요청률)으로만 정해 구성 간 같은 요청열을 쓴다. 분리 구성이면 이 지점 구간의 전송 지표 원문을 디코드 노드마다 저장한다.
pt(){ local WL=$1 R=$2; shift 2; local t0; t0=$(date -u +%s)
  log "  $CFG $WL r$R"
  SEED=$(python3 -c "print(int(float('$R')*1000)+(7 if '$WL'=='random' else 0))") harness/run_bench.sh E5 "$CFG" N0 "$WL" "$R" "$@" 2>&1 \
    | grep -E "Successful requests|Median TTFT|P99 ITL|wrote|rror" | sed 's/^/    /'
  for h in $DECODERS; do rsh $h "docker logs vllm --since $t0 2>&1 | grep 'KV Transfer metrics'" > results/xfer_E5/${CFG}_${WL}_r${R}_${h##*.}.log 2>/dev/null; done
  [ -n "$DECODERS" ] && log "    전송 원문 저장: $(cat results/xfer_E5/${CFG}_${WL}_r${R}_*.log 2>/dev/null | wc -l)줄"; }
K4="--random-input-len 4096 --random-output-len 512"

log "E5b-0 수집기 (세 노드)"
for h in $ALL; do rsh $h "PORTS='8100 8200' harness/node_collect.sh start" | sed 's/^/    /'; done
log "E5b 26_B3 sharegpt 48 재측정"
serve_rep 26_B3 $M26 $A_PRIV $B_PRIV $C_PRIV && pt sharegpt 48
stop_all
for h in $ALL; do rsh $h "harness/node_collect.sh stop" >/dev/null 2>&1; done
log "E5b DONE"
