#!/usr/bin/env bash
# After run_B.sh: rerun the B2 32K points (input clamped to 32000) so the B2 vs P1 grid is complete.
set -u; export PATH=~/venv/bin:~/.local/bin:$PATH; cd ~/pd
: "${A_PRIV:?}" "${B_PRIV:?}"
export RESULTS_DIR=$HOME/pd/results RESULTS_DIR_IN_CONTAINER=$HOME/pd/results ENV_JSON=$HOME/pd/results/env_B.json
MAIN=nvidia/Gemma-4-26B-A4B-NVFP4
log(){ echo "[$(date -u +%T)] $*"; }
bench(){ harness/run_bench.sh "$@" 2>&1 | grep -E "Successful requests|Median TTFT|P90 TTFT|P99 ITL|wrote|rror" | grep -v -E "Triton|AVX512" | sed 's/^/    /'; }
rsh(){ ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 ubuntu@"$1" "export PATH=~/.local/bin:\$PATH; cd ~/pd; $2"; }
log "T1 B2 32K rerun (prefix off)"
pkill -f "rr_proxy|toy_proxy" 2>/dev/null; sleep 1
rsh $A_PRIV "CHUNK=2560 PREFIX=off PORT=8100 harness/serve.sh $MAIN" & rsh $B_PRIV "CHUNK=2560 PREFIX=off PORT=8100 harness/serve.sh $MAIN" & wait
setsid nohup python3 harness/rr_proxy.py --port 8000 --upstreams http://$A_PRIV:8100 http://$B_PRIV:8100 > results/rr_proxy_Bt.log 2>&1 < /dev/null & disown; sleep 4
export BASE_URL=http://127.0.0.1:8000 METRICS_URL=http://$A_PRIV:8100/metrics MODEL=$MAIN CHUNK=2560 PREFIX=off
for r in 0.25 0.5 1; do log "  L=32K r=$r"; bench B B2 N0 random $r --random-input-len 32768 --random-output-len 512; done
pkill -f "rr_proxy" 2>/dev/null; for h in $A_PRIV $B_PRIV; do rsh $h "docker rm -f vllm >/dev/null 2>&1"; done
log "B TAIL DONE"
