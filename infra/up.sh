#!/usr/bin/env bash
# Usage: infra/up.sh PROFILE GPU_COUNT [--client] [--pg] [--hours N]   e.g. up.sh g5_2x 1 ; up.sh g5_4x 2 --client ; up.sh g5_4x 2 --client --pg
set -euo pipefail
P=$1; N=$2; shift 2; CLIENT=false; PG=false; HOURS=3
while [ $# -gt 0 ]; do case $1 in --client) CLIENT=true;; --pg) PG=true;; --hours) HOURS=$2; shift;; esac; shift; done
cd "$(dirname "$0")/terraform"
terraform init -input=false >/dev/null
terraform apply -auto-approve -var="gpu_profile=$P" -var="gpu_count=$N" -var="client=$CLIENT" -var="placement_group=$PG" -var="auto_shutdown_hours=$HOURS"
terraform output -json > ../last-outputs.json
terraform output ssh
