#!/usr/bin/env bash
# 세션 E8 보충(본 측정 결과를 보고 추가). run_E8.sh가 끝난 뒤 같은 노드에서 실행.
#   x1 26B 복제본 청크 1024의 한계: 합계 10·12(GPU당 5·6)
#   x2 26B 청크 2560을 청크 스윕과 같은 MM_LIMIT로(2048 이상치가 MM 설정 때문인지)
#   x3 26B 1P1D aiohttp 프록시의 한계: 합계 10·12, 그리고 UCX 조정 묶음의 연결 수(0.5건 ss, 본편 2단계에서 권한 문제로 빠짐)
: "${A_PRIV:?}" "${B_PRIV:?}"; ALL="$A_PRIV $B_PRIV"
source configs/lib_E8.sh
log "E8x 시작 MM_LIMIT=${MM_LIMIT:-기본}"
log "E8x-1 26B 복제본 청크 1024 · GPU당 5·6"
serve_rep 26_B2_c1024 $M26 1024 $A_PRIV $B_PRIV && { pt random 10 0 $K4; a=$(attv); python3 -c "import sys; sys.exit(0 if float('${a:-0}'.replace('?','0'))>=0.5 else 1)" && pt random 12 0 $K4; }
log "E8x-2 26B 복제본 청크 2560 · MM_LIMIT 동일"
FORCE_MM=1 serve_rep 26_B2_c2560mm $M26 2560 $A_PRIV $B_PRIV && { pt random 2 0 $K4; }
log "E8x-3 26B 1P1D aiohttp · GPU당 5·6, 조정 묶음 연결 수"
PROXY_KIND=aio UCXSET=TUNED serve_pd 26_1P1D_aio $M26 "$A_PRIV" "$B_PRIV" && {
  SNAP_D=1 pt random 10 0 $K4; a=$(attv); python3 -c "import sys; sys.exit(0 if float('${a:-0}'.replace('?','0'))>=0.5 else 1)" && SNAP_D=1 pt random 12 0 $K4
  SS=1 pt random 0.5 0 $K4; }
stop_all
log "E8x DONE"
