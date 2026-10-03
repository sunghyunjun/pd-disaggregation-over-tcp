#!/usr/bin/env bash
# Check spare G-family vCPU quota before starting a measurement round, in case another round is still using g5 instances etc.
# Usage: harness/preflight_quota.sh 24        (number of vCPUs needed as the argument)
set -u
NEED=${1:-0}
export AWS_PROFILE=${AWS_PROFILE:-default} AWS_REGION=${AWS_REGION:-us-east-1}
LIMIT=${G_VCPU_LIMIT:-32}   # manual constant because there is no servicequotas permission. Update when the quota changes.
USED=$(aws ec2 describe-instances --region "$AWS_REGION" \
  --filters "Name=instance-state-name,Values=running,pending" \
  --query 'Reservations[].Instances[?starts_with(InstanceType,`g`)].[InstanceType,CpuOptions.CoreCount,CpuOptions.ThreadsPerCore]' \
  --output json | python3 -c "
import json,sys
rs=json.load(sys.stdin); n=0; rows=[]
for grp in rs:
    for t,cores,tpc in grp:
        v=(cores or 0)*(tpc or 1); n+=v; rows.append(f'{t} {v}vCPU')
print(n); print(' | '.join(rows) if rows else '(none)', file=sys.stderr)
")
echo "G-family vCPUs in use: $USED / limit $LIMIT (spare $((LIMIT-USED)))"
if [ "$NEED" -gt 0 ]; then
  if [ $((USED+NEED)) -le "$LIMIT" ]; then
    echo "OK: requested $NEED vCPUs fit (total $((USED+NEED)))"
  else
    echo "STOP: requesting $NEED vCPUs would bring the total to $((USED+NEED)), over the limit. Wait for the other round's instances to terminate or split the round."
    exit 1
  fi
fi
