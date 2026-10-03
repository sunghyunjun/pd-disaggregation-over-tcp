#!/usr/bin/env bash
# 세션 E9 · g7e.2xlarge 두 대(클러스터 배치 그룹) + c6i.2xlarge. 2차 모의 심사 좌장 권고 1~5순위(paper/reviews/2026-09-30_v1/r6_chair.md 3절).
# 복제본 프록시는 연결 상한 없이(RR_CONN_LIMIT=0). 예측은 측정 전에 RESULTS.md "세션 E9 · 측정 전 예측"에 커밋했다.
# 순서(모델 교체를 줄이려고 1·2·5를 26B NVFP4로 묶음):
#   1  26B NVFP4 복제본 청크 512: 4K, 합계 2/4/6/8(GPU당 1~4) + 합계 4 반복(30 ms 판정점)
#   2  26B NVFP4 복제본 청크 1024: 4K, 합계 8 ×3(시드 8007/9007/10007), 10 ×2, 12 ×1
#   5  26B NVFP4 1P1D aiohttp, P 청크 8192, UCX 세그먼트 두 변수만: 4K, 합계 8 ×2, 10 ×1
#   3  26B FP8 복제본 청크 512: 4K, 합계 1, 2(GPU당 0.5, 1)
#   4  31B NVFP4: 복제본 청크 256 대화형 합계 16(GPU당 8), 1P1D aiohttp 대화형 합계 12(GPU당 6)와 8(시드 10000)
# 환경변수: A_PRIV B_PRIV(필수), MM_LIMIT(청크<2560 기동용), PHASES(기본 "1 2 5 3 4")
: "${A_PRIV:?}" "${B_PRIV:?}"; ALL="$A_PRIV $B_PRIV"
source configs/lib_E9.sh
PHASES=${PHASES:-"1 2 5 3 4"}
has(){ case " $PHASES " in *" $1 "*) return 0;; esac; return 1; }
log "E9 시작 PHASES=[$PHASES] MM_LIMIT=${MM_LIMIT:-기본} RR_CONN_LIMIT=${RR_CONN_LIMIT:-0}"
collectors_start e9
echo "    단일 흐름 $(rsh $A_PRIV "iperf3 -c $B_PRIV -P 1 -t 5 -J 2>/dev/null | jq -r '.end.sum_sent.bits_per_second/1e9'") Gbps"

for P_ in $PHASES; do case $P_ in
1) log "E9-1 26B NVFP4 복제본 청크 512 (4K, GPU당 1~4)"
   serve_rep 26_B2_c512 $M26 512 $A_PRIV $B_PRIV && { pt random 2 0 $K4; pt random 4 0 $K4; pt random 6 0 $K4; pt random 8 0 $K4; pt random 4 1 $K4; } ;;
2) log "E9-2 26B NVFP4 복제본 청크 1024, 프록시 상한 해제 (4K, GPU당 4·5·6)"
   serve_rep 26_B2_c1024 $M26 1024 $A_PRIV $B_PRIV && { pt random 8 0 $K4; pt random 8 1 $K4; pt random 8 2 $K4; pt random 10 0 $K4; pt random 10 1 $K4; pt random 12 0 $K4; } ;;
5) log "E9-5 26B NVFP4 1P1D aiohttp, P 청크 8192, UCX 세그먼트만 (4K, GPU당 4·5)"
   PCHUNK=8192 PROXY_KIND=aio UCXSET=SEG serve_pd 26_1P1D_aio_p8192 $M26 "$A_PRIV" "$B_PRIV" && {
     SNAP_D=1 pt random 8 0 $K4; SNAP_D=1 pt random 8 1 $K4; SNAP_D=1 pt random 10 0 $K4; } ;;
3) log "E9-3 26B FP8 복제본 청크 512 (4K, GPU당 0.5·1)"
   serve_rep 26F_B2_c512 $M26F 512 $A_PRIV $B_PRIV && { pt random 1 0 $K4; pt random 2 0 $K4; } ;;
4) log "E9-4 31B NVFP4 복제본 청크 256 대화형 GPU당 8, 1P1D aiohttp GPU당 6·4"
   serve_rep 31_B2_c256 $M31 256 $A_PRIV $B_PRIV && { pt sharegpt 16 0; }
   PROXY_KIND=aio UCXSET=TUNED serve_pd 31_1P1D_aio $M31 "$A_PRIV" "$B_PRIV" && { SNAP_D=1 pt sharegpt 12 0; SNAP_D=1 pt sharegpt 8 2; } ;;
esac; done

stop_all; collectors_stop
log "E9 DONE"
