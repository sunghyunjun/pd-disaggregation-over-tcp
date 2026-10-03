#!/usr/bin/env bash
# Round E7b · three g7e nodes (placement group): repeats of the three-node configurations, real trace, 26B 4K limit
: "${A_PRIV:?}" "${B_PRIV:?}" "${C_PRIV:?}"; ALL="$A_PRIV $B_PRIV $C_PRIV"
source configs/lib_E7.sh
log "E7b-0 collectors"
collectors_start b
log "E7b-1 26B NVFP4 · three replicas"
serve_rep 26_B3 $M26 $A_PRIV $B_PRIV $C_PRIV && { pt3 random 3 $K4; trace3 0.000667; }
log "E7b-2 26B NVFP4 · 1P2D"
serve_pd 26_1P2D $M26 "$A_PRIV" "$B_PRIV $C_PRIV" && { pt3 random 6 $K4; trace3 0.000667; pt random 9 0 $K4; pt random 12 0 $K4; pt random 18 0 $K4; }
log "E7b-3 26B NVFP4 · 2P1D"
serve_pd 26_2P1D $M26 "$A_PRIV $B_PRIV" "$C_PRIV" && { pt3 random 6 $K4; trace3 0.000667; pt random 9 0 $K4; pt random 12 0 $K4; pt random 18 0 $K4; }
log "E7b-4 31B NVFP4 · 2P1D"
serve_pd 31_2P1D $M31 "$A_PRIV $B_PRIV" "$C_PRIV" && { pt3 random 0.75 $K4; }
stop_all; collectors_stop
log "E7b DONE"
