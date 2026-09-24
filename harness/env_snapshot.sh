#!/usr/bin/env bash
# Capture the environment block for one run. Usage: env_snapshot.sh OUT.json [PEER_IP]
# Runs on the GPU node (or client). Requires: curl, jq, nvidia-smi (GPU node), iperf3 server on PEER (iperf3 -s).
set -u
OUT=${1:?out.json}; PEER=${2:-}
TOK=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 60")
md() { curl -s -H "X-aws-ec2-metadata-token: $TOK" "http://169.254.169.254/latest/meta-data/$1"; }
IID=$(md instance-id); ITYPE=$(md instance-type); AZ=$(md placement/availability-zone); AMI=$(md ami-id); PG=$(md placement/group-name 2>/dev/null)
LIP=$(md local-ipv4)
GPU=$(command -v nvidia-smi >/dev/null && nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader | head -1 || echo "none")
VLLM=$(python3 -c "import vllm,sys;print(vllm.__version__)" 2>/dev/null || docker run --rm --entrypoint python3 vllm/vllm-openai:latest -c "import vllm;print(vllm.__version__)" 2>/dev/null || echo "unknown")
NIXL=$(python3 -c "import nixl,sys;print(getattr(nixl,'__version__','?'))" 2>/dev/null || echo "unknown")
IPERF1="null"; IPERF4="null"; PING="null"
if [ -n "$PEER" ] && command -v iperf3 >/dev/null; then
  IPERF1=$(iperf3 -c "$PEER" -P 1 -t 10 -J 2>/dev/null | jq '.end.sum_sent.bits_per_second/1e9' 2>/dev/null || echo null)
  IPERF4=$(iperf3 -c "$PEER" -P 4 -t 10 -J 2>/dev/null | jq '.end.sum_sent.bits_per_second/1e9' 2>/dev/null || echo null)
  PING=$(ping -c 5 -q "$PEER" 2>/dev/null | awk -F'/' '/^rtt|^round-trip/ {print $5}' || echo null)
fi
jq -n --arg iid "$IID" --arg itype "$ITYPE" --arg az "$AZ" --arg ami "$AMI" --arg pg "$PG" --arg lip "$LIP" --arg gpu "$GPU" \
      --arg vllm "$VLLM" --arg nixl "$NIXL" --arg peer "$PEER" --argjson i1 "${IPERF1:-null}" --argjson i4 "${IPERF4:-null}" --arg ping "${PING:-null}" \
      --arg date "$(date -u +%FT%TZ)" \
  '{date:$date, instance_id:$iid, instance_type:$itype, az:$az, ami:$ami, placement_group:$pg, local_ip:$lip, gpu:$gpu,
    vllm_version:$vllm, nixl_version:$nixl, peer:$peer, iperf_p1_gbps:$i1, iperf_p4_gbps:$i4, ping_avg_ms:$ping}' > "$OUT"
cat "$OUT"
