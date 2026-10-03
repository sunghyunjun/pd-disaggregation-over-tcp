#!/usr/bin/env bash
# 세션 E7b · g7e 세 대(배치 그룹): 세 대 구성의 반복, 실제 트레이스, 26B 4K 상한
: "${A_PRIV:?}" "${B_PRIV:?}" "${C_PRIV:?}"; ALL="$A_PRIV $B_PRIV $C_PRIV"
source configs/lib_E7.sh
log "E7b-0 수집기"
collectors_start b
log "E7b-1 26B NVFP4 · 복제본 셋"
serve_rep 26_B3 $M26 $A_PRIV $B_PRIV $C_PRIV && { pt3 random 3 $K4; trace3 0.000667; }
log "E7b-2 26B NVFP4 · 1P2D"
serve_pd 26_1P2D $M26 "$A_PRIV" "$B_PRIV $C_PRIV" && { pt3 random 6 $K4; trace3 0.000667; pt random 9 0 $K4; pt random 12 0 $K4; pt random 18 0 $K4; }
log "E7b-3 26B NVFP4 · 2P1D"
serve_pd 26_2P1D $M26 "$A_PRIV $B_PRIV" "$C_PRIV" && { pt3 random 6 $K4; trace3 0.000667; pt random 9 0 $K4; pt random 12 0 $K4; pt random 18 0 $K4; }
log "E7b-4 31B NVFP4 · 2P1D"
serve_pd 31_2P1D $M31 "$A_PRIV $B_PRIV" "$C_PRIV" && { pt3 random 0.75 $K4; }
stop_all; collectors_stop
log "E7b DONE"
