#!/usr/bin/env bash
# Session-long 1 s collectors on a GPU node (run once per session; stop with node_collect.sh stop).
# Writes results/collect_<host>_{prom.jsonl,dmon.txt,sar.txt}; slice by timestamp against each run's start/duration.
# PORT = local vLLM port to scrape (8100 or 8200).
set -u
PORTS=${PORTS:-"8100 8200"}; OUT=~/pd/results; H=$(hostname -s); mkdir -p $OUT
if [ "${1:-start}" = stop ]; then pkill -f "node_collect_prom" ; pkill -f "sar -n DEV 1" ; pkill -f "nvidia-smi dmon" ; echo stopped; exit 0; fi
cat > /tmp/node_collect_prom.sh <<EOP
#!/bin/bash
while true; do ts=\$(date -u +%s); m=""; for p in $PORTS; do m="\$m\$(curl -s --max-time 1 http://127.0.0.1:\$p/metrics | grep -E '^vllm:(num_requests_(running|waiting)|kv_cache_usage_perc|gpu_cache_usage_perc|num_preemptions_total|kv_transfer)' | grep -v '^#' | awk -v P=\$p '{printf "\\"%s@%s\\":%s,", \$1, P, \$2}')"; done; echo "{\\"ts\\":\$ts,\${m%,}}"; sleep 1; done
EOP
chmod +x /tmp/node_collect_prom.sh
setsid nohup /tmp/node_collect_prom.sh > $OUT/collect_${H}_prom.jsonl 2>/dev/null < /dev/null & disown
setsid nohup bash -c "sar -n DEV 1 | awk '/ens5|eth0/{print strftime(\"%s\"), \$0; fflush()}'" > $OUT/collect_${H}_sar.txt 2>/dev/null < /dev/null & disown
setsid nohup bash -c "nvidia-smi dmon -s um -d 1 | awk '{print strftime(\"%s\"), \$0; fflush()}'" > $OUT/collect_${H}_dmon.txt 2>/dev/null < /dev/null & disown
echo "collectors started on $H (ports $PORTS)"
