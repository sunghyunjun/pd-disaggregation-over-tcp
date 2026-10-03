#!/usr/bin/env bash
# 1-second collector on a GPU node. v2 (2026-09-27): fixes friction #12.
#   - The previous version scraped /metrics with curl --max-time 1 and assembled JSON on the fly, which left every value empty.
#   - Now the filtered raw text is kept as TSV and parsing happens offline (analysis/parse_prom.py).
# Usage: node_collect.sh [start|stop|verify]   env: PORTS (default "8100 8200"), INTERVAL (default 1)
set -u
PORTS=${PORTS:-"8100 8200"}; INTERVAL=${INTERVAL:-1}; OUT=${OUT:-~/pd/results}; H=$(hostname -s); mkdir -p "$OUT"; TAG=${TAG:-$(date -u +%Y%m%dT%H%M%SZ)}
# Metrics to collect (actual v0.30.0 names). Counters may carry a _total suffix, so they are matched by prefix.
PAT='^vllm:(num_requests_running|num_requests_waiting|kv_cache_usage_perc|num_preemptions|prefix_cache_hits|prefix_cache_queries|prompt_tokens_cached|prompt_tokens|generation_tokens|iteration_tokens_total_sum|iteration_tokens_total_count|request_decode_time_seconds_sum|inter_token_latency_seconds_sum|inter_token_latency_seconds_count)'

case "${1:-start}" in
stop)
  pkill -f node_collect_prom; pkill -f "[s]ar -n DEV"; pkill -f "[n]vidia-smi dmon"; echo "stopped on $H"; exit 0;;
verify)
  for p in $PORTS; do
    n=$(curl -s --max-time 10 "http://127.0.0.1:$p/metrics" | grep -Ec "$PAT" || true)
    echo "port $p: matching metric lines $n"
    [ "${n:-0}" -gt 0 ] && curl -s --max-time 10 "http://127.0.0.1:$p/metrics" | grep -E "$PAT" | grep -v '^#' | head -4 | sed 's/^/    /'
  done
  exit 0;;
esac

cat > /tmp/node_collect_prom.sh <<EOP
#!/bin/bash
# TSV: ts <tab> port <tab> metric (labels stripped) <tab> value        on failure metric=_scrape_error
while true; do
  ts=\$(date -u +%s)
  for p in $PORTS; do
    body=\$(curl -s --max-time 10 "http://127.0.0.1:\$p/metrics" 2>/dev/null)
    if [ -z "\$body" ]; then printf '%s\t%s\t_scrape_error\t1\n' "\$ts" "\$p"; continue; fi
    printf '%s' "\$body" | grep -E '$PAT' | grep -v '^#' | \
      awk -v T="\$ts" -v P="\$p" '{name=\$1; sub(/\{.*/,"",name); print T"\t"P"\t"name"\t"\$2}'
  done
  sleep $INTERVAL
done
EOP
chmod +x /tmp/node_collect_prom.sh
setsid nohup /tmp/node_collect_prom.sh > "$OUT/collect_${H}_${TAG}_prom.tsv" 2>/dev/null < /dev/null & disown
setsid nohup bash -c "IF=\$(ip -o -4 route show to default | awk '{print \$5}'); stdbuf -oL sar -n DEV 1 | stdbuf -oL grep --line-buffered \"\$IF\"" > "$OUT/collect_${H}_${TAG}_sar.txt" 2>/dev/null < /dev/null & disown
setsid nohup bash -c "nvidia-smi dmon -s um -d 1 | awk '{print strftime(\"%s\"), \$0; fflush()}'" > "$OUT/collect_${H}_${TAG}_dmon.txt" 2>/dev/null < /dev/null & disown
sleep 3
n=$(wc -l < "$OUT/collect_${H}_${TAG}_prom.tsv" 2>/dev/null || echo 0)
echo "collectors started on $H (ports $PORTS, ${INTERVAL}s). prom lines after 3 s: $n"
[ "$n" -eq 0 ] && echo "warning: prom collection is empty. Check with node_collect.sh verify."
