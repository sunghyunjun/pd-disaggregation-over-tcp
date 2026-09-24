#!/usr/bin/env bash
# Toggle ENA Express (SRD) on the primary ENI of the given instance IDs. N2 network setting.
# Usage: ena-express.sh on|off i-aaa i-bbb   (requires ec2:DescribeNetworkInterfaces, ec2:ModifyNetworkInterfaceAttribute)
set -euo pipefail
MODE=$1; shift; FLAG=$([ "$MODE" = on ] && echo true || echo false)
for IID in "$@"; do
  ENI=$(aws ec2 describe-instances --instance-ids "$IID" --query 'Reservations[0].Instances[0].NetworkInterfaces[0].NetworkInterfaceId' --output text)
  aws ec2 modify-network-interface-attribute --network-interface-id "$ENI" --ena-srd-specification "EnaSrdEnabled=$FLAG,EnaSrdUdpSpecification={EnaSrdUdpEnabled=$FLAG}"
  echo "$IID $ENI ena_srd=$FLAG"
done
