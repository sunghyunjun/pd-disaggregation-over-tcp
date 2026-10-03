#!/usr/bin/env bash
# 세션 E7a · g7e 두 대(배치 그룹) + 한 대: 실제 트레이스, 핵심 지점 3회 반복, 26B 4K 상한(1P1D), 같은 세션 양자화, KV 맞춘 단일 노드
: "${A_PRIV:?}" "${B_PRIV:?}"; ALL="$A_PRIV $B_PRIV"
source configs/lib_E7.sh
log "E7a-0 수집기, iperf"
collectors_start a
echo "    단일 흐름 $(rsh $A_PRIV "iperf3 -c $B_PRIV -P 1 -t 5 -J 2>/dev/null | jq -r '.end.sum_sent.bits_per_second/1e9'") Gbps"

log "E7a-1 26B NVFP4 · 복제본 둘"
serve_rep 26_B2 $M26 $A_PRIV $B_PRIV && { pt3 random 2 $K4; pt3 random 4 $K4; pt3 sharegpt 16; trace3 0.001; pt random 1 0 $K4; }
log "E7a-2 26B NVFP4 · 1P1D"
serve_pd 26_1P1D $M26 "$A_PRIV" "$B_PRIV" && { pt3 random 2 $K4; pt3 random 4 $K4; pt3 sharegpt 16; trace3 0.001; pt random 1 0 $K4; pt random 6 0 $K4; pt random 8 0 $K4; pt random 12 0 $K4; }
log "E7a-3 31B NVFP4 · 복제본 둘"
serve_rep 31_B2 $M31 $A_PRIV $B_PRIV && { pt3 sharegpt 2; trace3 0.001; }
log "E7a-4 31B NVFP4 · 1P1D"
serve_pd 31_1P1D $M31 "$A_PRIV" "$B_PRIV" && { pt3 sharegpt 8; pt3 random 0.25 $K4; trace3 0.001; }
log "E7a-5 26B FP8 · 복제본 둘과 1P1D (같은 세션 양자화)"
serve_rep 26F_B2 $M26F $A_PRIV $B_PRIV && { pt random 1 0 $K4; pt random 2 0 $K4; pt sharegpt 16 0; }
serve_pd 26F_1P1D $M26F "$A_PRIV" "$B_PRIV" && { pt random 1 0 $K4; pt random 2 0 $K4; pt sharegpt 16 0; }
log "E7a-6 26B FP8 · 단일 노드 KV 맞춤(GPU 점유율 0.42, E1과 같은 설정)"
serve_single 26F_single_kvmatch $M26F $A_PRIV 0.42 && { pt3 sharegpt 16; pt sharegpt 20 0; pt sharegpt 24 0; }
log "E7a-7 26B BF16 · 복제본 둘과 1P1D (같은 세션 양자화)"
serve_rep 26H_B2 $M26H $A_PRIV $B_PRIV && { pt random 1 0 $K4; pt random 2 0 $K4; pt sharegpt 16 0; }
serve_pd 26H_1P1D $M26H "$A_PRIV" "$B_PRIV" && { pt random 1 0 $K4; pt random 2 0 $K4; pt sharegpt 16 0; }

stop_all; collectors_stop
log "E7a DONE"
