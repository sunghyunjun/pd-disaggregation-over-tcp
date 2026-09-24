#!/usr/bin/env bash
# One measurement point. Usage:
#   run_bench.sh STAGE CONFIG NETWORK WORKLOAD RATE [extra bench args...]
#   e.g. run_bench.sh A B1 N0 sharegpt 2.0
#        run_bench.sh B P1 N0 random 1.0 --random-input-len 4096 --random-output-len 512
#        run_bench.sh C P1 N0 azure_conv self   (self-timed trace replay)
# Env: MODEL, TOKENIZER, BASE_URL (proxy or server), RESULTS_DIR, SEED, POINT_SEC (default 180), MIN_PROMPTS (100),
#      ENV_JSON (from env_snapshot.sh), SHAREGPT_JSON, TRACES_DIR, SLO_CHAT, SLO_DOC, TRACE_SEC_MULT (0.001 = real time; 0.002 = 2x slower)
set -euo pipefail
STAGE=$1; CONFIG=$2; NET=$3; WL=$4; RATE=$5; shift 5
MODEL=${MODEL:?}; BASE_URL=${BASE_URL:-http://127.0.0.1:8000}; RESULTS_DIR=${RESULTS_DIR:-results}
# When `vllm` is the docker wrapper, the container sees ~/pd at /pd. RESULTS_DIR is the HOST path; the
# container-side path for --result-dir is derived via RESULTS_DIR_IN_CONTAINER (default: same as host).
RESULTS_DIR_IN_CONTAINER=${RESULTS_DIR_IN_CONTAINER:-$RESULTS_DIR}
SEED=${SEED:-0}; POINT_SEC=${POINT_SEC:-180}; MIN_PROMPTS=${MIN_PROMPTS:-100}; TRACE_SEC_MULT=${TRACE_SEC_MULT:-0.001}
TS=$(date -u +%Y-%m-%dT%H%M%SZ); RUN_ID="${TS}_${STAGE}_${CONFIG}_${NET}_${WL}_r${RATE}"
mkdir -p "$RESULTS_DIR/$RUN_ID"; OUT="$RESULTS_DIR/$RUN_ID"; OUT_C="$RESULTS_DIR_IN_CONTAINER/$RUN_ID"

case "$WL" in
  sharegpt) DS=(--dataset-name sharegpt --dataset-path "${SHAREGPT_JSON:?}") ;;
  random)   DS=(--dataset-name random --ignore-eos) ;;
  azure_conv|azure_code|mooncake_conv|mooncake_toolagent)
            DS=(--dataset-name timed_trace --dataset-path "${TRACES_DIR:?}/${WL}.jsonl" --timed-trace-sec-multiplier "$TRACE_SEC_MULT")
            [[ $WL == mooncake_* ]] && DS+=(--timed-trace-chunk-hash-size 512) ;;
  *) echo "unknown workload $WL"; exit 2 ;;
esac
if [[ "$RATE" == "self" ]]; then
  LOAD=(--num-prompts "${NUM_PROMPTS:-0}")           # self-timed: trace timestamps drive arrivals; 0 = all
elif [[ "$RATE" == "inf" ]]; then
  LOAD=(--request-rate inf --num-prompts "${NUM_PROMPTS:-100}")   # closed-loop / max-throughput reference; pass --max-concurrency via extra args
else
  NP=$(python3 -c "import math;print(max(${MIN_PROMPTS}, math.ceil(${RATE}*${POINT_SEC})))")
  LOAD=(--request-rate "$RATE" --burstiness 1.0 --num-prompts "$NP")
  [[ $WL == azure_* || $WL == mooncake_* ]] && LOAD+=(--no-self-timed)
fi

# side collectors (1s): NIC, GPU, vLLM prometheus
( sar -n DEV 1 > "$OUT/sar.txt" 2>/dev/null ) & SAR=$!
( command -v nvidia-smi >/dev/null && nvidia-smi dmon -s um -d 1 > "$OUT/dmon.txt" 2>/dev/null ) & DMON=$!
( while true; do echo "$(date -u +%s) $(curl -s ${METRICS_URL:-$BASE_URL/metrics} | grep -E '^vllm:(num_requests_(running|waiting)|kv_cache_usage_perc|gpu_cache_usage_perc)' | tr '\n' ' ')"; sleep 1; done > "$OUT/prom.txt" ) & PROM=$!
trap 'kill $SAR $DMON $PROM 2>/dev/null || true' EXIT

vllm bench serve --backend vllm --base-url "$BASE_URL" --model "$MODEL" ${TOKENIZER:+--tokenizer "$TOKENIZER"} \
  "${DS[@]}" "${LOAD[@]}" --seed "$SEED" \
  --percentile-metrics ttft,tpot,itl,e2el --metric-percentiles 50,90,99 \
  --goodput ttft:${SLO_CHAT_TTFT:-1000} tpot:${SLO_CHAT_TPOT:-50} \
  --save-result --save-detailed --result-dir "$OUT_C" --result-filename bench.json "$@" 2>&1 | tee "$OUT/bench.log"

python3 - "$OUT" "$RUN_ID" "$STAGE" "$CONFIG" "$NET" "$WL" "$RATE" <<'PY'
import json, sys, os
out, run_id, stage, config, net, wl, rate = sys.argv[1:]
bench = json.load(open(os.path.join(out, "bench.json")))
env = json.load(open(os.environ["ENV_JSON"])) if os.environ.get("ENV_JSON") and os.path.exists(os.environ["ENV_JSON"]) else {}
meta = {"run_id": run_id, "stage": stage, "config": config, "network": net, "workload": wl, "rate": rate,
        "seed": os.environ.get("SEED", "0"), "point_sec": os.environ.get("POINT_SEC", "180"),
        "vllm_flags": os.environ.get("VLLM_FLAGS", ""), "env": env, "discarded": False, "discard_reason": ""}
json.dump({"meta": meta, "bench": bench}, open(os.path.join(out, "result.json"), "w"))
print("wrote", os.path.join(out, "result.json"))
PY
