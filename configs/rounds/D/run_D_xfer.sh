#!/usr/bin/env bash
# 세션 D-1 · KV 전송 경로만 분리해서 측정 (모델 없이 → vLLM 부하 제거)
# 목적: (1) 라이브러리 순수 천장, (2) UCX 노브별 변화, (3) 흐름 수 효과
# 사용: A_PRIV, B_PRIV 환경변수에 두 GPU 노드 사설 IP를 넣고 실행
set -u
: "${A_PRIV:?}"; : "${B_PRIV:?}"
OUT=${OUT:-~/pd/results/D1}
rsh(){ ssh -o StrictHostKeyChecking=no ubuntu@"$1" "${@:2}"; }
log(){ echo "[$(date -u +%H:%M:%S)] $*"; }
mkdir -p "$OUT"

# --- 0. 기준점: iperf 흐름 수별 ---
log "iperf 1/2/4/8 흐름"
for P in 1 2 4 8; do
  rsh "$A_PRIV" "iperf3 -c $B_PRIV -P $P -t 10 -J" | jq -r "\"P=$P \(.end.sum_sent.bits_per_second/1e9) Gbps\"" | tee -a "$OUT/iperf.txt"
done

# --- 1. NIXL 단독 전송 (nixlbench 또는 파이썬 하네스) ---
# 이미지 안에 nixlbench가 있는지 먼저 확인
rsh "$A_PRIV" "docker run --rm --gpus all vllm/vllm-openai:v0.30.0 bash -lc 'which nixlbench || python -c \"import nixl; print(nixl.__file__)\"'" | tee "$OUT/nixl_probe.txt"

# 파이썬 하네스: VRAM 버퍼를 64 KiB 디스크립터 N개로 READ 전송
# harness/xfer_probe.py 를 두 노드에 두고 target/initiator로 실행
# 인자: 총 전송량 MB, 디스크립터 KiB, num_threads, split_batch_size
for MB in 24 140 260 412; do
  for DESC in 64 256; do
    for NT in 0 8 16; do
      for SBS in 128 1024; do
        log "xfer MB=$MB desc=${DESC}KiB num_threads=$NT split=$SBS"
        rsh "$B_PRIV" "cd ~/pd && nohup python3 harness/xfer_probe.py target --mb $MB --desc-kib $DESC --num-threads $NT --split $SBS > /tmp/t.log 2>&1 &"
        sleep 3
        rsh "$A_PRIV" "cd ~/pd && python3 harness/xfer_probe.py initiator --peer $B_PRIV --mb $MB --desc-kib $DESC --num-threads $NT --split $SBS" \
          | tee -a "$OUT/xfer_matrix.txt"
      done
    done
  done
done

# --- 2. UCX 노브 스윕 (가장 유망한 조합만) ---
# 기본값: TX_SEG_SIZE 8k, RX_SEG_SIZE 64k, MAX_IOV 6, ZCOPY_THRESH auto, RNDV_THRESH auto
KNOBS=(
  "기본"
  "UCX_TCP_TX_SEG_SIZE=64k"
  "UCX_TCP_TX_SEG_SIZE=256k UCX_TCP_RX_SEG_SIZE=256k"
  "UCX_TCP_TX_SEG_SIZE=256k UCX_TCP_RX_SEG_SIZE=256k UCX_TCP_MAX_IOV=16"
  "UCX_TCP_SNDBUF=8m UCX_TCP_RCVBUF=8m"
  "UCX_ZCOPY_THRESH=0"
  "UCX_RNDV_SCHEME=get_zcopy"
  "UCX_RNDV_SCHEME=put_zcopy"
  "UCX_MAX_RNDV_RAILS=4"
)
for K in "${KNOBS[@]}"; do
  log "knob: $K"
  rsh "$B_PRIV" "cd ~/pd && ${K/기본/} nohup python3 harness/xfer_probe.py target --mb 140 --desc-kib 64 --num-threads 8 --split 1024 > /tmp/t.log 2>&1 &"
  sleep 3
  rsh "$A_PRIV" "cd ~/pd && ${K/기본/} python3 harness/xfer_probe.py initiator --peer $B_PRIV --mb 140 --desc-kib 64 --num-threads 8 --split 1024" \
    | sed "s/^/[$K] /" | tee -a "$OUT/knob_sweep.txt"
done

# --- 3. 대역폭 쉐이핑 재측정 (마찰 #9 수정판) ---
# burst = rate × 10 ms, 프리필(송신) 노드에만, 설정마다 iperf 검증
for BW in 1gbit 2gbit 3gbit 5gbit; do
  BURST=$(python3 -c "print(int(${BW%gbit}*1e9/8*0.01))")   # 10 ms 분량 바이트
  rsh "$A_PRIV" "IF=\$(ip -o -4 route show to default | awk '{print \$5}'); sudo tc qdisc replace dev \$IF root tbf rate $BW burst ${BURST} latency 50ms"
  rsh "$A_PRIV" "iperf3 -c $B_PRIV -P 1 -t 8 -J" | jq -r "\"$BW 검증 \(.end.sum_sent.bits_per_second/1e9) Gbps\"" | tee -a "$OUT/tc_verify.txt"
  rsh "$A_PRIV" "cd ~/pd && python3 harness/xfer_probe.py initiator --peer $B_PRIV --mb 140 --desc-kib 64 --num-threads 8 --split 1024" | sed "s/^/[$BW] /" | tee -a "$OUT/tc_xfer.txt"
done
rsh "$A_PRIV" "IF=\$(ip -o -4 route show to default | awk '{print \$5}'); sudo tc qdisc del dev \$IF root 2>/dev/null || true"
log "D1 DONE"
