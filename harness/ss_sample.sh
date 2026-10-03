#!/usr/bin/env bash
# Round E8 (B3): sample the number of TCP connections between P and D and the bytes carried by each (to see how many connections the KV transfer uses).
# Usage: ss_sample.sh start PEER_IP OUT_FILE [INTERVAL_S(0.1)] | ss_sample.sh stop
# Output: for every sample, a "# <epoch.ns>" line followed by the raw output of `ss -tinH dst PEER_IP` (includes bytes_acked, bytes_received and delivery_rate per connection).
# Analysis happens offline (analysis/ss_parse.py). ssh (22), iperf (5201) and the NIXL side channel (5600) are excluded at the analysis stage.
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
