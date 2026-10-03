#!/usr/bin/env bash
# 세션 E4 · g7e 쌍 + 클러스터 배치 그룹: (1) 주장 C6 판정, (2) g7e 전송이 2.3 Gbps에 머문 원인 조사
# 비교 기준: 세션 E2의 같은 인스턴스·같은 설정(배치 그룹 없음) 수치
set -u
export PATH=~/venv/bin:~/.local/bin:$PATH; cd ~/pd
: "${A_PRIV:?}" "${B_PRIV:?}"
export RESULTS_DIR=$HOME/pd/results RESULTS_DIR_IN_CONTAINER=$HOME/pd/results ENV_JSON=$HOME/pd/results/env_E4.json
export SHAREGPT_JSON=$HOME/pd/data/ShareGPT_V3_unfiltered_cleaned_split.json
MAIN=${MAIN:-RedHatAI/gemma-4-26B-A4B-it-FP8-dynamic}
BASE_TUNED="UCX_TLS=tcp,cuda_copy,cuda_ipc UCX_NET_DEVICES=all UCX_TCP_TX_SEG_SIZE=256k UCX_TCP_RX_SEG_SIZE=256k UCX_TCP_MAX_IOV=16 UCX_TCP_MAX_POLL=-1 UCX_TCP_SNDBUF=8m UCX_TCP_RCVBUF=8m UCX_RNDV_FRAG_SIZE=host:4M,cuda:8M"
log(){ echo "[$(date -u +%T)] $*"; }
bench(){ harness/run_bench.sh "$@" 2>&1 | grep -E "Successful requests|Output token throughput|Median TTFT|P90 TTFT|P99 ITL|wrote|rror" | sed 's/^/    /'; }
rsh(){ ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 ubuntu@"$1" "export PATH=~/.local/bin:\$PATH; cd ~/pd; $2"; }
xfer(){ rsh $B_PRIV "docker logs vllm 2>&1 | grep 'KV Transfer metrics' | tail -1 | cut -c1-230" | sed 's/^/    xfer: /'; }
health(){ curl -s -o /dev/null -w "%{http_code}" --max-time 10 "http://$1:$2/health"; }
serve_p1(){ # $1 = UCX_EXTRA, $2 = NIXL_THREADS(빈 값이면 기본 4)
  pkill -f toy_proxy 2>/dev/null; sleep 1
  rsh $A_PRIV "UCX_EXTRA='$1' NIXL_THREADS='${2:-}' CHUNK=2560 PREFIX=off PORT=8100 GPU_UTIL=0.90 CONNECTOR=producer OWN_IP=$A_PRIV harness/serve.sh $MAIN" >/dev/null &
  rsh $B_PRIV "UCX_EXTRA='$1' NIXL_THREADS='${2:-}' CHUNK=2560 PREFIX=off PORT=8200 GPU_UTIL=0.90 CONNECTOR=consumer OWN_IP=$B_PRIV harness/serve.sh $MAIN" >/dev/null & wait
  setsid nohup python3 vllm-src/tests/v1/kv_connector/nixl_integration/toy_proxy_server.py --host 0.0.0.0 --port 8000 \
    --prefiller-hosts $A_PRIV --prefiller-ports 8100 --decoder-hosts $B_PRIV --decoder-ports 8200 > results/toy_proxy_E4.log 2>&1 </dev/null & disown
  sleep 4; echo "    health A=$(health $A_PRIV 8100) B=$(health $B_PRIV 8200)"
  [ "$(health $A_PRIV 8100)" = 200 ] && [ "$(health $B_PRIV 8200)" = 200 ] || return 1
  export BASE_URL=http://127.0.0.1:8000 METRICS_URL=http://$A_PRIV:8100/metrics MODEL=$MAIN CHUNK=2560 PREFIX=off
  export RESET_URLS="http://$A_PRIV:8100 http://$B_PRIV:8200"; }

log "E4-0 수집기 시작·검증 (양 노드)"
for h in $A_PRIV $B_PRIV; do rsh $h "PORTS='8100 8200' harness/node_collect.sh start" | sed 's/^/    /'; done
log "E4-0 배치 그룹 안에서의 iperf (단일 흐름 10 Gbps 기대, E2는 배치 그룹 없이 4.97)"
rsh $A_PRIV "for P in 1 2 4 8; do echo -n \"P=\$P \"; iperf3 -c $B_PRIV -P \$P -t 10 -J 2>/dev/null | jq -r '.end.sum_sent.bits_per_second/1e9'; done" | sed 's/^/    /'
log "E4-0 노드 환경 점검 (MTU·ENA·UCX 선택 경로)"
rsh $A_PRIV "ip -o link show | grep -E 'ens|eth' | sed 's/^/    링크: /'; ethtool -i \$(ip -o -4 route show to default | awk '{print \$5}') 2>/dev/null | head -3 | sed 's/^/    드라이버: /'" 

log "E4-1 주장 C6 · 배치 그룹에서의 분리 (E2와 같은 지점)"
serve_p1 "$BASE_TUNED" && { for r in 8 16; do log "  P1 pg r$r"; SEED=$r bench E4 P1tuned_pg N0 sharegpt $r; xfer; done
  for r in 0.5 1; do log "  P1 pg 4K r$r"; SEED=1 bench E4 P1tuned_pg N0 random $r --random-input-len 4096 --random-output-len 512; xfer; done; }

log "E4-2 전송 상한 원인 조사 (4K 0.5 고정, 노브 4종)"
# (a) 기준: 튜닝만
serve_p1 "$BASE_TUNED" && { SEED=2 bench E4 xfer_a_tuned N0 random 0.5 --random-input-len 4096 --random-output-len 512; xfer; }
# (b) 세그먼트를 1 MB로 더 키움
serve_p1 "${BASE_TUNED/UCX_TCP_TX_SEG_SIZE=256k/UCX_TCP_TX_SEG_SIZE=1m}" && { SEED=2 bench E4 xfer_b_seg1m N0 random 0.5 --random-input-len 4096 --random-output-len 512; xfer; }
# (c) NIXL 스레드 16 (기본 4)
serve_p1 "$BASE_TUNED" 16 && { SEED=2 bench E4 xfer_c_th16 N0 random 0.5 --random-input-len 4096 --random-output-len 512; xfer; }
# (d) 랑데부 조각을 16 MB로
serve_p1 "${BASE_TUNED/UCX_RNDV_FRAG_SIZE=host:4M,cuda:8M/UCX_RNDV_FRAG_SIZE=host:8M,cuda:16M}" && { SEED=2 bench E4 xfer_d_frag16m N0 random 0.5 --random-input-len 4096 --random-output-len 512; xfer; }

log "E4-3 배치 그룹 iperf 재측정 (부하 후, 시작값과 비교)"
rsh $A_PRIV "for P in 1 4; do echo -n \"부하후 P=\$P \"; iperf3 -c $B_PRIV -P \$P -t 10 -J 2>/dev/null | jq -r '.end.sum_sent.bits_per_second/1e9'; done" | sed 's/^/    /'
pkill -f toy_proxy 2>/dev/null
for h in $A_PRIV $B_PRIV; do rsh $h "harness/node_collect.sh stop" >/dev/null 2>&1; rsh $h "docker rm -f vllm >/dev/null 2>&1"; done
log "E4 DONE"
