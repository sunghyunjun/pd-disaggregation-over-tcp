#!/usr/bin/env bash
# Round E8 step 0: check that the server still starts with the chunk below 2560 (friction #4: 2048 was once rejected by the multimodal budget check).
# On both nodes at once: A runs 26B NVFP4, B runs 31B NVFP4. For each chunk value try the MM_LIMIT candidates in order and record the first combination that starts.
# Usage (on the client): A_PRIV=.. B_PRIV=.. bash configs/step0_E8.sh
: "${A_PRIV:?}" "${B_PRIV:?}"; ALL="$A_PRIV $B_PRIV"
source configs/lib_E8.sh
# Candidates: (MM_LIMIT, extra args). In round A on 2026-09-24, image:0 alone was not enough and 2048 was rejected
#   "Chunked MM input disabled but max_tokens_per_mm_item (2496) is larger than max_num_batched_tokens (2048)"
CANDS=("|" '{"image":0,"audio":0}|' '{"image":0,"audio":0,"video":0}|' '|--language-model-only')
try(){ local H=$1 M=$2 C=$3; local c mm ex; for c in "${CANDS[@]}"; do mm=${c%%|*}; ex=${c#*|}
    local out; out=$(rsh $H "MM_LIMIT='$mm' CHUNK=$C PREFIX=off PORT=8100 GPU_UTIL=0.90 harness/serve.sh $M $ex" 2>&1)
    if echo "$out" | grep -q "^READY"; then echo "OK   ${M##*/} chunk=$C MM_LIMIT='${mm:-default}' EXTRA='$ex'"; echo "$out" | grep -E "KV cache|Loading" | sed 's/^/     /'; rsh $H "docker rm -f vllm >/dev/null 2>&1"; return 0; fi
    echo "FAIL ${M##*/} chunk=$C MM_LIMIT='${mm:-default}' EXTRA='$ex': $(echo "$out" | grep -E 'Error|error|must|FAILED|unrecognized' | tail -2 | tr '\n' ' ' | cut -c1-300)"
  done; return 1; }
stop_all
( for C in 1024 1536 2048; do try $A_PRIV $M26 $C; done ) > results/step0_E8_A.txt 2>&1 &
( for C in 256 512; do try $B_PRIV $M31 $C; done ) > results/step0_E8_B.txt 2>&1 &
wait
cat results/step0_E8_A.txt results/step0_E8_B.txt
