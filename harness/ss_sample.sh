#!/usr/bin/env bash
# 세션 E8(B3): P–D 사이 TCP 연결 수와 연결별 전송량을 샘플링한다(KV 전송이 몇 개의 연결로 나가는지 확인).
# 사용: ss_sample.sh start PEER_IP OUT_FILE [INTERVAL_S(0.1)] | ss_sample.sh stop
# 출력: 샘플마다 "# <epoch.ns>" 줄 다음에 `ss -tinH dst PEER_IP`의 원문(연결별 bytes_acked·bytes_received·delivery_rate 포함).
# 분석은 오프라인에서 한다(harness/ss_parse.py). ssh(22)·iperf(5201)·NIXL 사이드 채널(5600)은 분석 단계에서 뺀다.
set -u
case "${1:-}" in
start)
  PEER=$2; OUT=$3; IV=${4:-0.1}
  setsid nohup bash -c "while true; do echo \"# \$(date +%s.%N)\"; ss -tinH dst $PEER; sleep $IV; done" > "$OUT" 2>/dev/null < /dev/null & disown
  echo "ss sampling → $OUT (peer $PEER, ${IV}s)";;
stop)
  pkill -f "[s]s -tinH dst" ; pkill -f "while true; do echo \"# \$(date" 2>/dev/null; echo "ss sampling stopped";;
*) echo "usage: ss_sample.sh start PEER_IP OUT_FILE [INTERVAL] | stop"; exit 2;;
esac
