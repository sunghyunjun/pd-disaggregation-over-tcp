#!/usr/bin/env bash
# Knee refinement: ShareGPT 6 / 12 req/s for B2 and P1 (fix: SHAREGPT_JSON was not exported in run_B_tail.sh).
set -u; export PATH=~/venv/bin:~/.local/bin:$PATH; cd ~/pd
: "${A_PRIV:?}" "${B_PRIV:?}"
export RESULTS_DIR=$HOME/pd/results RESULTS_DIR_IN_CONTAINER=$HOME/pd/results ENV_JSON=$HOME/pd/results/env_B.json
export SHAREGPT_JSON=$HOME/pd/data/ShareGPT_V3_unfiltered_cleaned_split.json TRACES_DIR=$HOME/pd/data/traces
MAIN=nvidia/Gemma-4-26B-A4B-NVFP4
log(){ echo "[$(date -u +%T)] $*"; }
bench(){ harness/run_bench.sh "$@" 2>&1 | grep -E "Successful requests|Median TTFT|P90 TTFT|P99 ITL|wrote|rror|not set" | grep -v -E "Triton|AVX512" | sed 's/^/    /'; }
rsh(){ ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 ubuntu@"$1" "export PATH=~/.local/bin:\$PATH; cd ~/pd; $2"; }
log "K1 B2 6/12"
pkill -f "rr_proxy|toy_proxy" 2>/dev/null; rsh $A_PRIV "CHUNK=2560 PREFIX=on PORT=8100 harness/serve.sh $MAIN" & rsh $B_PRIV "CHUNK=2560 PREFIX=on PORT=8100 harness/serve.sh $MAIN" & wait
setsid nohup python3 harness/rr_proxy.py --port 8000 --upstreams http://$A_PRIV:8100 http://$B_PRIV:8100 > results/rr_proxy_Bk.log 2>&1 < /dev/null & disown; sleep 4
export BASE_URL=http://127.0.0.1:8000 METRICS_URL=http://$A_PRIV:8100/metrics MODEL=$MAIN CHUNK=2560 PREFIX=on
for r in 6 12; do log "  B2 rate $r"; bench B B2 N0 sharegpt $r; done
log "K2 P1 6/12"
pkill -f "rr_proxy" 2>/dev/null; rsh $A_PRIV "CHUNK=2560 PREFIX=on PORT=8100 CONNECTOR=producer OWN_IP=$A_PRIV harness/serve.sh $MAIN" & rsh $B_PRIV "CHUNK=2560 PREFIX=on PORT=8200 CONNECTOR=consumer OWN_IP=$B_PRIV harness/serve.sh $MAIN" & wait
setsid nohup python3 vllm-src/tests/v1/kv_connector/nixl_integration/toy_proxy_server.py --host 0.0.0.0 --port 8000 --prefiller-hosts $A_PRIV --prefiller-ports 8100 --decoder-hosts $B_PRIV --decoder-ports 8200 > results/toy_proxy_Bk.log 2>&1 < /dev/null & disown; sleep 4
for r in 6 12; do log "  P1 rate $r"; bench B P1 N0 sharegpt $r; rsh $B_PRIV "docker logs vllm 2>&1 | grep 'KV Transfer metrics' | tail -1 | cut -c1-240" | sed 's/^/    xfer: /'; done
pkill -f "rr_proxy|toy_proxy" 2>/dev/null; for h in $A_PRIV $B_PRIV; do rsh $h "docker rm -f vllm >/dev/null 2>&1"; done
log "KNEE DONE"
