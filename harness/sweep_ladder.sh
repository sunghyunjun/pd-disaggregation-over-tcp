#!/usr/bin/env bash
# 사다리 한 판을 `vllm bench sweep serve`로 돌린다. 기존 run_bench.sh 루프를 대체한다.
#   얻는 것: 지점 사이 캐시 리셋을 upstream이 보장(마찰 #11), --num-runs 반복, --resume, 표준 출력 배치
#   유지 대상: 결과는 harness/sweep_to_runs.py 로 results/<RUN_ID>/{result,bench}.json 으로 변환해 기존 집계에 붙인다
# 사용법: sweep_ladder.sh STAGE CONFIG WORKLOAD "RATE..." [extra bench args...]
#   예: STAGE=E5 CONFIG=P1tuned  sweep_ladder.sh E5 P1tuned sharegpt "4 8 12"
#       sweep_ladder.sh E5 P1tuned random "0.5 1" --random-input-len 4096 --random-output-len 512
# 환경: MODE(pd|solo), A_PRIV, B_PRIV, MODEL, UCX_EXTRA, NIXL_THREADS, GPU_UTIL, MAXLEN, CHUNK, PREFIX,
#       POINT_SEC(180), MIN_PROMPTS(100), NUM_RUNS(1), SWEEP_DIR(results/sweep), SHAREGPT_JSON, TRACES_DIR
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

# 지점마다 request_rate와 num_prompts, 시드를 함께 지정한다(시드 고정은 접두어 재사용을 부르므로 지점마다 바꾼다)
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
# --resume은 실험 폴더가 이미 있을 때만 유효하다(없으면 vllm이 거부한다)
[ -d "$SWEEP_DIR/$EXP" ] && RESUME=1 || RESUME=""
PF="$SWEEP_DIR/params_${EXP}.json"; printf '%s\n' "$PARAMS" > "$PF"
echo "사다리 지점: $(python3 -c "import json;print([d['_benchmark_name'] for d in json.load(open('$PF'))])")"

RESET_URLS="http://${A_PRIV:?}:8100"; [ "${MODE:-pd}" = pd ] && RESET_URLS="$RESET_URLS http://${B_PRIV:?}:8200"

vllm bench sweep serve \
  --serve-cmd "harness/serve_pair.sh --host $HOST --port $PORT" \
  --bench-cmd "vllm bench serve --backend vllm --base-url http://$HOST:$PORT --model $MODEL ${TOKENIZER:+--tokenizer $TOKENIZER} $(printf '%s ' "${DS[@]}") --metric-percentiles 50,90,99 --save-detailed --goodput ttft:${SLO_CHAT_TTFT:-1000} tpot:${SLO_CHAT_TPOT:-50} $*" \
  --after-bench-cmd "harness/reset_caches.sh $RESET_URLS" \
  --bench-params "$PF" --num-runs "$NUM_RUNS" ${RESUME:+--resume} \
  --server-ready-timeout 900 -o "$SWEEP_DIR" -e "$EXP" "${DRY_RUN:+--dry-run}"

echo "변환: harness/sweep_to_runs.py $SWEEP_DIR/$EXP --stage $STAGE --config $CONFIG --workload $WL"
