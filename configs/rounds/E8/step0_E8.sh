#!/usr/bin/env bash
# 세션 E8 0단계: 청크를 2560 아래로 내려도 서버가 뜨는지 확인한다(마찰 #4: 2048이 멀티모달 예산 검사로 거부됐던 기록).
# 두 노드에서 동시에: A는 26B NVFP4, B는 31B NVFP4. 각 청크 값마다 MM_LIMIT 후보를 차례로 시도하고, 처음 뜬 조합을 적는다.
# 사용(클라이언트에서): A_PRIV=.. B_PRIV=.. bash configs/step0_E8.sh
: "${A_PRIV:?}" "${B_PRIV:?}"; ALL="$A_PRIV $B_PRIV"
source configs/lib_E8.sh
# 후보: (MM_LIMIT, 추가 인자). 2026-09-24 세션 A에서 image:0만으로는 2048이 거부됐다
#   "Chunked MM input disabled but max_tokens_per_mm_item (2496) is larger than max_num_batched_tokens (2048)"
CANDS=("|" '{"image":0,"audio":0}|' '{"image":0,"audio":0,"video":0}|' '|--language-model-only')
try(){ local H=$1 M=$2 C=$3; local c mm ex; for c in "${CANDS[@]}"; do mm=${c%%|*}; ex=${c#*|}
    local out; out=$(rsh $H "MM_LIMIT='$mm' CHUNK=$C PREFIX=off PORT=8100 GPU_UTIL=0.90 harness/serve.sh $M $ex" 2>&1)
    if echo "$out" | grep -q "^READY"; then echo "OK   ${M##*/} chunk=$C MM_LIMIT='${mm:-기본}' EXTRA='$ex'"; echo "$out" | grep -E "KV cache|Loading" | sed 's/^/     /'; rsh $H "docker rm -f vllm >/dev/null 2>&1"; return 0; fi
    echo "FAIL ${M##*/} chunk=$C MM_LIMIT='${mm:-기본}' EXTRA='$ex': $(echo "$out" | grep -E 'Error|error|must|FAILED|unrecognized' | tail -2 | tr '\n' ' ' | cut -c1-300)"
  done; return 1; }
stop_all
( for C in 1024 1536 2048; do try $A_PRIV $M26 $C; done ) > results/step0_E8_A.txt 2>&1 &
( for C in 256 512; do try $B_PRIV $M31 $C; done ) > results/step0_E8_B.txt 2>&1 &
wait
cat results/step0_E8_A.txt results/step0_E8_B.txt
