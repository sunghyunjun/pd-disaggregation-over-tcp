#!/usr/bin/env bash
# Run `vllm ...` inside the running server container with ~/pd mounted at /pd, so
# `vllm bench serve --result-dir /pd/results/...` lands on the host. Usage: put this on PATH as `vllm`.
#   ln -sf ~/pd/harness/vllm-docker.sh ~/.local/bin/vllm
# Server container must be started with:  -v ~/pd:/pd  (see configs/sat_A.md)
exec docker exec -w /pd -e HF_TOKEN="${HF_TOKEN:-}" "${VLLM_CONTAINER:-vllm}" vllm "$@"
