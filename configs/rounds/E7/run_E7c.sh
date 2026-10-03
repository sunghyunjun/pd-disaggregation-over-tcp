#!/usr/bin/env bash
# 세션 E7c · 세 대 구성의 실제 트레이스 보충(E7b에서 요청 수 누락으로 실패한 부분). 세 번째 노드를 지우기 전에 실행
: "${A_PRIV:?}" "${B_PRIV:?}" "${C_PRIV:?}"; ALL="$A_PRIV $B_PRIV $C_PRIV"
source configs/lib_E7.sh
collectors_start c
log "E7c-1 26B 복제본 셋 · 트레이스"
serve_rep 26_B3 $M26 $A_PRIV $B_PRIV $C_PRIV && trace3 0.000667
log "E7c-2 26B 1P2D · 트레이스"
serve_pd 26_1P2D $M26 "$A_PRIV" "$B_PRIV $C_PRIV" && trace3 0.000667
log "E7c-3 26B 2P1D · 트레이스"
serve_pd 26_2P1D $M26 "$A_PRIV $B_PRIV" "$C_PRIV" && trace3 0.000667
stop_all; collectors_stop
log "E7c DONE"
