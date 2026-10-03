#!/usr/bin/env bash
# Round E7a · two g7e nodes (placement group) + one node: real trace, key points repeated 3 times, 26B 4K limit (1P1D), same-round quantization, KV-matched single node
: "${A_PRIV:?}" "${B_PRIV:?}"; ALL="$A_PRIV $B_PRIV"
source configs/lib_E7.sh
log "E7a-0 collectors, iperf"
collectors_start a
echo "    single flow $(rsh $A_PRIV "iperf3 -c $B_PRIV -P 1 -t 5 -J 2>/dev/null | jq -r '.end.sum_sent.bits_per_second/1e9'") Gbps"

log "E7a-1 26B NVFP4 · two replicas"
serve_rep 26_B2 $M26 $A_PRIV $B_PRIV && { pt3 random 2 $K4; pt3 random 4 $K4; pt3 sharegpt 16; trace3 0.001; pt random 1 0 $K4; }
log "E7a-2 26B NVFP4 · 1P1D"
serve_pd 26_1P1D $M26 "$A_PRIV" "$B_PRIV" && { pt3 random 2 $K4; pt3 random 4 $K4; pt3 sharegpt 16; trace3 0.001; pt random 1 0 $K4; pt random 6 0 $K4; pt random 8 0 $K4; pt random 12 0 $K4; }
log "E7a-3 31B NVFP4 · two replicas"
serve_rep 31_B2 $M31 $A_PRIV $B_PRIV && { pt3 sharegpt 2; trace3 0.001; }
log "E7a-4 31B NVFP4 · 1P1D"
serve_pd 31_1P1D $M31 "$A_PRIV" "$B_PRIV" && { pt3 sharegpt 8; pt3 random 0.25 $K4; trace3 0.001; }
log "E7a-5 26B FP8 · two replicas and 1P1D (same-round quantization)"
serve_rep 26F_B2 $M26F $A_PRIV $B_PRIV && { pt random 1 0 $K4; pt random 2 0 $K4; pt sharegpt 16 0; }
serve_pd 26F_1P1D $M26F "$A_PRIV" "$B_PRIV" && { pt random 1 0 $K4; pt random 2 0 $K4; pt sharegpt 16 0; }
log "E7a-6 26B FP8 · single node, KV matched (GPU utilization 0.42, same setting as E1)"
serve_single 26F_single_kvmatch $M26F $A_PRIV 0.42 && { pt3 sharegpt 16; pt sharegpt 20 0; pt sharegpt 24 0; }
log "E7a-7 26B BF16 · two replicas and 1P1D (same-round quantization)"
serve_rep 26H_B2 $M26H $A_PRIV $B_PRIV && { pt random 1 0 $K4; pt random 2 0 $K4; pt sharegpt 16 0; }
serve_pd 26H_1P1D $M26H "$A_PRIV" "$B_PRIV" && { pt random 1 0 $K4; pt random 2 0 $K4; pt sharegpt 16 0; }

stop_all; collectors_stop
log "E7a DONE"
