#!/usr/bin/env bash
# Reset server caches between runs. Uses the same endpoints as clear_cache() in vllm bench sweep serve.
# The server must be running with VLLM_SERVER_DEV_MODE=1 (serve.sh sets it).
# Usage: reset_caches.sh http://10.0.0.1:8100 [http://10.0.0.2:8200 ...]
set -u
rc=0
for base in "$@"; do
  for ep in /reset_prefix_cache /reset_mm_cache /reset_encoder_cache; do
    code=$(curl -s -o /dev/null -w "%{http_code}" -X POST --max-time 15 "${base}${ep}" 2>/dev/null)
    case "$code" in
      200|204) ;;                      # ok
      404) ;;                          # configuration without that cache (e.g. no multimodal), ignored
      *) echo "    cache reset failed ${base}${ep} -> ${code:-no-response}"; rc=1;;
    esac
  done
done
exit $rc
