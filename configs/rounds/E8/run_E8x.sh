#!/usr/bin/env bash
# Round E8 supplement (added after seeing the main results). Run on the same nodes after run_E8.sh finishes.
#   x1 limit of 26B replicas at chunk 1024: total 10·12 (5·6 per GPU)
#   x2 26B chunk 2560 with the same MM_LIMIT as the chunk sweep (is the 2048 outlier due to the MM setting)
#   x0 31B replicas at chunk 256, chat workload, 4 (·6) per GPU
#   x3 limit of 26B 1P1D with the aiohttp proxy: total 10·12, plus the connection count of the tuned UCX bundle (0.5 with ss; dropped from phase 2 of the main run by a permission problem)
#   x4 31B 1P1D aiohttp, chat workload, 4 per GPU ×2
: "${A_PRIV:?}" "${B_PRIV:?}"; ALL="$A_PRIV $B_PRIV"
source configs/lib_E8.sh
log "E8x start MM_LIMIT=${MM_LIMIT:-default}"
log "E8x-0 31B replicas chunk 256 · chat workload 4 per GPU (the load where 1P1D sat at the boundary)"
serve_rep 31_B2_c256 $M31 256 $A_PRIV $B_PRIV && { pt sharegpt 8 0; a=$(attv); python3 -c "import sys; sys.exit(0 if float('${a:-0}'.replace('?','0'))>=0.9 else 1)" && pt sharegpt 12 0; }
log "E8x-1 26B replicas chunk 1024 · 5·6 per GPU"
serve_rep 26_B2_c1024 $M26 1024 $A_PRIV $B_PRIV && { pt random 10 0 $K4; a=$(attv); python3 -c "import sys; sys.exit(0 if float('${a:-0}'.replace('?','0'))>=0.5 else 1)" && pt random 12 0 $K4; }
log "E8x-2 26B replicas chunk 2560 · same MM_LIMIT"
FORCE_MM=1 serve_rep 26_B2_c2560mm $M26 2560 $A_PRIV $B_PRIV && { pt random 2 0 $K4; }
log "E8x-3 26B 1P1D aiohttp · 5·6 per GPU, tuned bundle connection count"
PROXY_KIND=aio UCXSET=TUNED serve_pd 26_1P1D_aio $M26 "$A_PRIV" "$B_PRIV" && {
  SNAP_D=1 pt random 10 0 $K4; a=$(attv); python3 -c "import sys; sys.exit(0 if float('${a:-0}'.replace('?','0'))>=0.5 else 1)" && SNAP_D=1 pt random 12 0 $K4
  SS=1 pt random 0.5 0 $K4; }
log "E8x-4 31B 1P1D aiohttp · chat workload 4 per GPU ×2 (the disaggregation limit with a proxy free of GC pauses)"
PROXY_KIND=aio UCXSET=TUNED serve_pd 31_1P1D_aio $M31 "$A_PRIV" "$B_PRIV" && { SNAP_D=1 pt sharegpt 8 0; SNAP_D=1 pt sharegpt 8 1; }
stop_all
log "E8x DONE"
