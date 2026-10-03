#!/usr/bin/env bash
# Usage: infra/up.sh PROFILE GPU_COUNT [--client] [--pg] [--hours N]   (optional env CLIENT_TYPE: client instance type)   e.g. up.sh g5_2x 1 ; up.sh g5_4x 2 --client ; up.sh g5_4x 2 --client --pg
set -euo pipefail
P=$1; N=$2; shift 2; CLIENT=false; PG=false; HOURS=3; PB=""; WS=""
while [ $# -gt 0 ]; do case $1 in --client) CLIENT=true;; --pg) PG=true;; --hours) HOURS=$2; shift;; --profile-b) PB=$2; shift;; --ws) WS=$2; shift;; esac; shift; done
cd "$(dirname "$0")/terraform"
terraform init -input=false >/dev/null
[ -n "$WS" ] && { terraform workspace select "$WS" 2>/dev/null || terraform workspace new "$WS"; }
terraform apply -auto-approve -var="allowed_ssh_cidr=${ALLOWED_SSH_CIDR:?set ALLOWED_SSH_CIDR, e.g. your IP as 203.0.113.4/32}" -var="gpu_profile=$P" -var="gpu_profile_b=$PB" -var="gpu_count=$N" -var="client=$CLIENT" -var="placement_group=$PG" -var="auto_shutdown_hours=$HOURS" ${CLIENT_TYPE:+-var="client_type=$CLIENT_TYPE"}
terraform output -json > "../last-outputs${WS:+-$WS}.json"
terraform output ssh
