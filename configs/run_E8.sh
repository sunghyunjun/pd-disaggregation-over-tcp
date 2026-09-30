#!/usr/bin/env bash
# 세션 E8 · g7e.2xlarge 두 대(클러스터 배치 그룹) + c6i.2xlarge 클라이언트. 영어 원고 v0 모의 심사(paper/reviews/2026-09-30_v0) 대응.
#   1  B1 26B NVFP4 복제본 청크 스윕(4K 입력): 같은 날 2560 대조 + CHUNKS26 각각 GPU당 1~4건, 한계 근처 반복
#   2  B2(i)+B3 1P1D, 계측 toy 프록시, UCX 조정 묶음: 합계 8건 ×3, 6건, 0.5건(ss 샘플링)
#   3  B2(ii) 1P1D, aiohttp 프록시(pd_proxy.py): 합계 8건 ×3, 6건
#   4  B3 UCX 절제: 세그먼트만 256k(0.5건 ss, 1건), UCX 기본값(0.5건 ss)
#   5  B1 31B NVFP4 복제본 대화형: 2560 대조, CHUNK31(과 CHUNK31B) / B3 31B 1P1D 4K 0.25건 ss
#   6  선택: 26B FP8 복제본 청크 C26F, 4K 합계 1·2건
# 환경변수: A_PRIV B_PRIV(필수), CHUNKS26(기본 "1024 1536 2048"), CHUNK31(기본 256), CHUNK31B(비우면 생략), C26F(기본 1024),
#          PHASES(기본 "1 2 3 4 5 6"), MM_LIMIT(0단계 결과에 따라)
: "${A_PRIV:?}" "${B_PRIV:?}"; ALL="$A_PRIV $B_PRIV"
source configs/lib_E8.sh
CHUNKS26=${CHUNKS26:-"1024 1536 2048"}; CHUNK31=${CHUNK31:-256}; CHUNK31B=${CHUNK31B:-}; C26F=${C26F:-1024}; PHASES=${PHASES:-"1 2 3 4 5 6"}
has(){ case " $PHASES " in *" $1 "*) return 0;; esac; return 1; }
log "E8 시작 PHASES=[$PHASES] CHUNKS26=[$CHUNKS26] CHUNK31=$CHUNK31 CHUNK31B=$CHUNK31B C26F=$C26F MM_LIMIT=${MM_LIMIT:-기본}"
collectors_start e8
echo "    단일 흐름 $(rsh $A_PRIV "iperf3 -c $B_PRIV -P 1 -t 5 -J 2>/dev/null | jq -r '.end.sum_sent.bits_per_second/1e9'") Gbps"

if has 1; then
  log "E8-1 26B NVFP4 복제본 둘 · 청크 스윕 (4K 입력, 합계 요청률 2/4/6/8 = GPU당 1~4)"
  serve_rep 26_B2_c2560 $M26 2560 $A_PRIV $B_PRIV && { pt random 2 0 $K4; pt random 4 0 $K4; }
  for C in $CHUNKS26; do
    serve_rep 26_B2_c$C $M26 $C $A_PRIV $B_PRIV || { log "  청크 $C 기동 실패 — 건너뜀"; continue; }
    pt random 2 0 $K4; pt random 4 0 $K4; pt random 6 0 $K4; a6=$(attv)
    # GPU당 3건이 절반도 못 지키면 4건은 대기열만 쌓이므로 생략
    if python3 -c "import sys; sys.exit(0 if float('${a6:-0}'.replace('?','0'))>=0.5 else 1)"; then pt random 8 0 $K4; else log "  청크 $C: 합계 6에서 ${a6} → 8 생략"; fi
    pt random 4 1 $K4; pt random 6 1 $K4
  done
fi

if has 2; then
  log "E8-2 26B NVFP4 1P1D · 계측 toy 프록시 · UCX 조정 묶음 (B2 i, B3)"
  PROXY_KIND=toyi UCXSET=TUNED serve_pd 26_1P1D_toyi $M26 "$A_PRIV" "$B_PRIV" && {
    SNAP_D=1 pt random 8 0 $K4; SNAP_D=1 pt random 8 1 $K4; SNAP_D=1 pt random 8 2 $K4; SNAP_D=1 pt random 6 0 $K4
    SS=1 pt random 0.5 0 $K4; }
fi

if has 3; then
  log "E8-3 26B NVFP4 1P1D · aiohttp 프록시 (B2 ii)"
  PROXY_KIND=aio UCXSET=TUNED serve_pd 26_1P1D_aio $M26 "$A_PRIV" "$B_PRIV" && {
    SNAP_D=1 pt random 8 0 $K4; SNAP_D=1 pt random 8 1 $K4; SNAP_D=1 pt random 8 2 $K4; SNAP_D=1 pt random 6 0 $K4; }
fi

if has 4; then
  log "E8-4 26B NVFP4 1P1D · UCX 절제 (B3)"
  PROXY_KIND=toyi UCXSET=SEG serve_pd 26_1P1D_seg $M26 "$A_PRIV" "$B_PRIV" && { SS=1 pt random 0.5 0 $K4; pt random 1 0 $K4; }
  PROXY_KIND=toyi UCXSET=DEFAULT serve_pd 26_1P1D_def $M26 "$A_PRIV" "$B_PRIV" && { SS=1 pt random 0.5 0 $K4; }
fi

if has 5; then
  log "E8-5 31B NVFP4 복제본 둘 · 대화형 청크 (B1), 1P1D 4K 연결 수 (B3)"
  serve_rep 31_B2_c2560 $M31 2560 $A_PRIV $B_PRIV && { pt sharegpt 2 0; }
  serve_rep 31_B2_c$CHUNK31 $M31 $CHUNK31 $A_PRIV $B_PRIV && { pt sharegpt 2 0; pt sharegpt 2 1; pt sharegpt 4 0; }
  [ -n "$CHUNK31B" ] && serve_rep 31_B2_c$CHUNK31B $M31 $CHUNK31B $A_PRIV $B_PRIV && { pt sharegpt 2 0; }
  PROXY_KIND=toyi UCXSET=TUNED serve_pd 31_1P1D_ss $M31 "$A_PRIV" "$B_PRIV" && { SS=1 pt random 0.25 0 $K4; }
fi

if has 6; then
  log "E8-6 26B FP8 복제본 둘 · 청크 $C26F (선택)"
  serve_rep 26F_B2_c$C26F $M26F $C26F $A_PRIV $B_PRIV && { pt random 1 0 $K4; pt random 2 0 $K4; }
fi

stop_all; collectors_stop
log "E8 DONE"
