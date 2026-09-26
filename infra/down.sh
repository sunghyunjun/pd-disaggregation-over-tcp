#!/usr/bin/env bash
# Usage: down.sh [--ws NAME]
set -u
WS=""; while [ $# -gt 0 ]; do case $1 in --ws) WS=$2; shift;; esac; shift; done
cd "$(dirname "$0")/terraform"
[ -n "$WS" ] && terraform workspace select "$WS"
terraform destroy -auto-approve -refresh=false
