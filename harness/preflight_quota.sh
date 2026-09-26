#!/usr/bin/env bash
# 세션 시작 전 G 계열 vCPU 여유 확인. 다른 세션이 g5 등을 쓰는 경우를 대비.
# 사용: harness/preflight_quota.sh 24        (필요 vCPU 수를 인자로)
set -u
NEED=${1:-0}
export AWS_PROFILE=${AWS_PROFILE:-default} AWS_REGION=${AWS_REGION:-us-east-1}
LIMIT=${G_VCPU_LIMIT:-32}   # servicequotas 권한이 없어 수동 상수. 쿼타 변경 시 갱신.
USED=$(aws ec2 describe-instances --region "$AWS_REGION" \
  --filters "Name=instance-state-name,Values=running,pending" \
  --query 'Reservations[].Instances[?starts_with(InstanceType,`g`)].[InstanceType,CpuOptions.CoreCount,CpuOptions.ThreadsPerCore]' \
  --output json | python3 -c "
import json,sys
rs=json.load(sys.stdin); n=0; rows=[]
for grp in rs:
    for t,cores,tpc in grp:
        v=(cores or 0)*(tpc or 1); n+=v; rows.append(f'{t} {v}vCPU')
print(n); print(' | '.join(rows) if rows else '(없음)', file=sys.stderr)
")
echo "G 계열 실행 중 vCPU: $USED / 한도 $LIMIT (여유 $((LIMIT-USED)))"
if [ "$NEED" -gt 0 ]; then
  if [ $((USED+NEED)) -le "$LIMIT" ]; then
    echo "OK: 요청 $NEED vCPU 수용 가능 (합계 $((USED+NEED)))"
  else
    echo "STOP: 요청 $NEED vCPU면 합계 $((USED+NEED))로 한도 초과. 다른 세션 인스턴스 종료를 기다리거나 세션을 쪼개세요."
    exit 1
  fi
fi
