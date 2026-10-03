#!/usr/bin/env bash
# Run one rate ladder with `vllm bench sweep serve`. Replaces the older run_bench.sh loop.
#   Gains: cache reset between points is guaranteed by upstream (friction #11), --num-runs repeats, --resume, standard output layout
#   Kept: results are converted with harness/sweep_to_runs.py into results/<RUN_ID>/{result,bench}.json and attached to the existing aggregation
# Usage: sweep_ladder.sh STAGE CONFIG WORKLOAD "RATE..." [extra bench args...]
#   e.g. STAGE=E5 CONFIG=P1tuned  sweep_ladder.sh E5 P1tuned sharegpt "4 8 12"
#        sweep_ladder.sh E5 P1tuned random "0.5 1" --random-input-len 4096 --random-output-len 512
# Env: MODE (pd|solo), A_PRIV, B_PRIV, MODEL, UCX_EXTRA, NIXL_THREADS, GPU_UTIL, MAXLEN, CHUNK, PREFIX,
#      POINT_SEC (180), MIN_PROMPTS (100), NUM_RUNS (1), SWEEP_DIR (results/sweep), SHAREGPT_JSON, TRACES_DIR
set -euo pipefail
STAGE=$1; CONFIG=$2; WL=$3; RATES=$4; shift 4
MODEL=${MODEL:?}; POINT_SEC=${POINT_SEC:-180}; MIN_PROMPTS=${MIN_PROMPTS:-100}; NUM_RUNS=${NUM_RUNS:-1}
SWEEP_DIR=${SWEEP_DIR:-results/sweep}; EXP="${STAGE}_${CONFIG}_${WL}"
PORT=${PORT:-8000}; HOST=${HOST:-127.0.0.1}

case "$WL" in
  sharegpt) DS=(--dataset-name sharegpt --dataset-path "${SHAREGPT_JSON:?}") ;;
  random)   DS=(--dataset-name random --ignore-eos) ;;
  azure_conv|azure_code|mooncake_conv|mooncake_toolagent)
            DS=(--dataset-name timed_trace --dataset-path "${TRACES_DIR:?}/${WL}.jsonl" --timed-trace-sec-multiplier "${TRACE_SEC_MULT:-0.001}" --no-self-timed)
            [[ $WL == mooncake_* ]] && DS+=(--timed-trace-chunk-hash-size 512) ;;
  *) echo "unknown workload $WL"; exit 2 ;;
esac

# Each point sets request_rate, num_prompts and the seed together (a fixed seed invites prefix reuse, so the seed changes per point)
PARAMS=$(python3 - "$POINT_SEC" "$MIN_PROMPTS" $RATES <<'PY'
import json,math,sys
point,minp,*rates=sys.argv[1:]
out=[]
for r in rates:
    n=max(int(minp), math.ceil(float(r)*float(point)))
    out.append({"_benchmark_name":f"r{r}","request_rate":float(r),"num_prompts":n,"burstiness":1.0,"seed":int(float(r)*1000)})
print(json.dumps(out,indent=2))
PY
)
mkdir -p "$SWEEP_DIR"
# --resume is only valid when the experiment folder already exists (vllm rejects it otherwise)
[ -d "$SWEEP_DIR/$EXP" ] && RESUME=1 || RESUME=""
PF="$SWEEP_DIR/params_${EXP}.json"; printf '%s\n' "$PARAMS" > "$PF"
echo "ladder points: $(python3 -c "import json;print([d['_benchmark_name'] for d in json.load(open('$PF'))])")"

RESET_URLS="http://${A_PRIV:?}:8100"; [ "${MODE:-pd}" = pd ] && RESET_URLS="$RESET_URLS http://${B_PRIV:?}:8200"

vllm bench sweep serve \
  --serve-cmd "harness/serve_pair.sh --host $HOST --port $PORT" \
  --bench-cmd "vllm bench serve --backend vllm --base-url http://$HOST:$PORT --model $MODEL ${TOKENIZER:+--tokenizer $TOKENIZER} $(printf '%s ' "${DS[@]}") --metric-percentiles 50,90,99 --save-detailed --goodput ttft:${SLO_CHAT_TTFT:-1000} tpot:${SLO_CHAT_TPOT:-50} $*" \
  --after-bench-cmd "harness/reset_caches.sh $RESET_URLS" \
  --bench-params "$PF" --num-runs "$NUM_RUNS" ${RESUME:+--resume} \
  --server-ready-timeout 900 -o "$SWEEP_DIR" -e "$EXP" "${DRY_RUN:+--dry-run}"

echo "convert: harness/sweep_to_runs.py $SWEEP_DIR/$EXP --stage $STAGE --config $CONFIG --workload $WL"
