#!/usr/bin/env bash
# Round E7c · real-trace supplement for the three-node configurations (the part that failed in E7b from the missing request count). Run before the third node is removed
: "${A_PRIV:?}" "${B_PRIV:?}" "${C_PRIV:?}"; ALL="$A_PRIV $B_PRIV $C_PRIV"
source configs/lib_E7.sh
collectors_start c
log "E7c-1 26B three replicas · trace"
serve_rep 26_B3 $M26 $A_PRIV $B_PRIV $C_PRIV && trace3 0.000667
log "E7c-2 26B 1P2D · trace"
serve_pd 26_1P2D $M26 "$A_PRIV" "$B_PRIV $C_PRIV" && trace3 0.000667
log "E7c-3 26B 2P1D · trace"
serve_pd 26_2P1D $M26 "$A_PRIV $B_PRIV" "$C_PRIV" && trace3 0.000667
stop_all; collectors_stop
log "E7c DONE"
