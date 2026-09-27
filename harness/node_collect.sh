#!/usr/bin/env bash
# GPU 노드의 1초 수집기. v2(2026-09-27): 마찰 #12 수정.
#   - 이전 판은 curl --max-time 1로 /metrics를 긁고 JSON을 즉석 조립했다가 전부 빈 값을 남겼다.
#   - 이제 원문을 필터링한 TSV로 남기고 파싱은 오프라인(harness/parse_prom.py)에서 한다.
# 사용: node_collect.sh [start|stop|verify]   env: PORTS(기본 "8100 8200"), INTERVAL(기본 1)
set -u
PORTS=${PORTS:-"8100 8200"}; INTERVAL=${INTERVAL:-1}; OUT=${OUT:-~/pd/results}; H=$(hostname -s); mkdir -p "$OUT"
# 수집할 지표(v0.30.0 실제 이름). 카운터는 _total 접미사가 붙을 수 있어 접두 일치로 잡는다.
PAT='^vllm:(num_requests_running|num_requests_waiting|kv_cache_usage_perc|num_preemptions|prefix_cache_hits|prefix_cache_queries|prompt_tokens_cached|prompt_tokens|generation_tokens|iteration_tokens_total_sum|iteration_tokens_total_count|request_decode_time_seconds_sum|inter_token_latency_seconds_sum|inter_token_latency_seconds_count)'

case "${1:-start}" in
stop)
  pkill -f node_collect_prom; pkill -f "sar -n DEV"; pkill -f "nvidia-smi dmon"; echo "stopped on $H"; exit 0;;
verify)
  for p in $PORTS; do
    n=$(curl -s --max-time 10 "http://127.0.0.1:$p/metrics" | grep -Ec "$PAT" || true)
    echo "port $p: 매칭 지표 줄 $n"
    [ "${n:-0}" -gt 0 ] && curl -s --max-time 10 "http://127.0.0.1:$p/metrics" | grep -E "$PAT" | grep -v '^#' | head -4 | sed 's/^/    /'
  done
  exit 0;;
esac

cat > /tmp/node_collect_prom.sh <<EOP
#!/bin/bash
# TSV: ts <tab> port <tab> metric(라벨 제거) <tab> value        실패 시 metric=_scrape_error
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
setsid nohup /tmp/node_collect_prom.sh > "$OUT/collect_${H}_prom.tsv" 2>/dev/null < /dev/null & disown
setsid nohup bash -c "sar -n DEV 1 | awk '/ens5|eth0/{print strftime(\"%s\"), \$0; fflush()}'" > "$OUT/collect_${H}_sar.txt" 2>/dev/null < /dev/null & disown
setsid nohup bash -c "nvidia-smi dmon -s um -d 1 | awk '{print strftime(\"%s\"), \$0; fflush()}'" > "$OUT/collect_${H}_dmon.txt" 2>/dev/null < /dev/null & disown
sleep 3
n=$(wc -l < "$OUT/collect_${H}_prom.tsv" 2>/dev/null || echo 0)
echo "collectors started on $H (ports $PORTS, ${INTERVAL}s). 3초 후 prom 줄 수: $n"
[ "$n" -eq 0 ] && echo "경고: prom 수집이 비어 있습니다. node_collect.sh verify 로 확인하세요."
