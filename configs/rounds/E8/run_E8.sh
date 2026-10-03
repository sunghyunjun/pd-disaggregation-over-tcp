#!/usr/bin/env bash
# Round E8 · two g7e.2xlarge (cluster placement group) + c6i.2xlarge client. Response to the mock review of the English manuscript v0 (paper/reviews/2026-09-30_v0).
#   1  B1 26B NVFP4 replica chunk sweep (4K input): same-day 2560 control + each of CHUNKS26 at 1~4 req/s per GPU, repeats near the limit
#   2  B2(i)+B3 1P1D, instrumented toy proxy, tuned UCX bundle: total 8 req/s ×3, 6, 0.5 (ss sampling)
#   3  B2(ii) 1P1D, aiohttp proxy (pd_proxy.py): total 8 req/s ×3, 6
#   4  B3 UCX ablation: segments only at 256k (0.5 with ss, 1), UCX defaults (0.5 with ss)
#   5  B1 31B NVFP4 replicas, chat workload: 2560 control, CHUNK31 (and CHUNK31B) / B3 31B 1P1D 4K 0.25 with ss
#   6  optional: 26B FP8 replicas at chunk C26F, 4K total 1·2 req/s
# Environment: A_PRIV B_PRIV (required), CHUNKS26 (default "1024 1536 2048"), CHUNK31 (default 256), CHUNK31B (skipped when empty), C26F (default 1024),
#          PHASES (default "1 2 3 4 5 6"), MM_LIMIT (per the step 0 result)
: "${A_PRIV:?}" "${B_PRIV:?}"; ALL="$A_PRIV $B_PRIV"
source configs/lib_E8.sh
CHUNKS26=${CHUNKS26:-"1024 1536 2048"}; CHUNK31=${CHUNK31:-256}; CHUNK31B=${CHUNK31B:-}; C26F=${C26F:-1024}; PHASES=${PHASES:-"1 2 3 4 5 6"}
has(){ case " $PHASES " in *" $1 "*) return 0;; esac; return 1; }
log "E8 start PHASES=[$PHASES] CHUNKS26=[$CHUNKS26] CHUNK31=$CHUNK31 CHUNK31B=$CHUNK31B C26F=$C26F MM_LIMIT=${MM_LIMIT:-default}"
collectors_start e8
echo "    single flow $(rsh $A_PRIV "iperf3 -c $B_PRIV -P 1 -t 5 -J 2>/dev/null | jq -r '.end.sum_sent.bits_per_second/1e9'") Gbps"

if has 1; then
  log "E8-1 26B NVFP4 two replicas · chunk sweep (4K input, total rate 2/4/6/8 = 1~4 per GPU)"
  serve_rep 26_B2_c2560 $M26 2560 $A_PRIV $B_PRIV && { pt random 2 0 $K4; pt random 4 0 $K4; }
  for C in $CHUNKS26; do
    serve_rep 26_B2_c$C $M26 $C $A_PRIV $B_PRIV || { log "  chunk $C failed to start, skipped"; continue; }
    pt random 2 0 $K4; pt random 4 0 $K4; pt random 6 0 $K4; a6=$(attv)
    # If 3 req/s per GPU attains less than half, 4 would only build a queue, so skip it
    if python3 -c "import sys; sys.exit(0 if float('${a6:-0}'.replace('?','0'))>=0.5 else 1)"; then pt random 8 0 $K4; else log "  chunk $C: ${a6} at total 6, skipping 8"; fi
    pt random 4 1 $K4; pt random 6 1 $K4
  done
fi

if has 2; then
  log "E8-2 26B NVFP4 1P1D · instrumented toy proxy · tuned UCX bundle (B2 i, B3)"
  PROXY_KIND=toyi UCXSET=TUNED serve_pd 26_1P1D_toyi $M26 "$A_PRIV" "$B_PRIV" && {
    SNAP_D=1 pt random 8 0 $K4; SNAP_D=1 pt random 8 1 $K4; SNAP_D=1 pt random 8 2 $K4; SNAP_D=1 pt random 6 0 $K4
    SS=1 pt random 0.5 0 $K4; }
fi

if has 3; then
  log "E8-3 26B NVFP4 1P1D · aiohttp proxy (B2 ii)"
  PROXY_KIND=aio UCXSET=TUNED serve_pd 26_1P1D_aio $M26 "$A_PRIV" "$B_PRIV" && {
    SNAP_D=1 pt random 8 0 $K4; SNAP_D=1 pt random 8 1 $K4; SNAP_D=1 pt random 8 2 $K4; SNAP_D=1 pt random 6 0 $K4; }
fi

if has 4; then
  log "E8-4 26B NVFP4 1P1D · UCX ablation (B3)"
  PROXY_KIND=toyi UCXSET=SEG serve_pd 26_1P1D_seg $M26 "$A_PRIV" "$B_PRIV" && { SS=1 pt random 0.5 0 $K4; pt random 1 0 $K4; }
  PROXY_KIND=toyi UCXSET=DEFAULT serve_pd 26_1P1D_def $M26 "$A_PRIV" "$B_PRIV" && { SS=1 pt random 0.5 0 $K4; }
fi

if has 5; then
  log "E8-5 31B NVFP4 two replicas · chat-workload chunk (B1), 1P1D 4K connection count (B3)"
  serve_rep 31_B2_c2560 $M31 2560 $A_PRIV $B_PRIV && { pt sharegpt 2 0; }
  serve_rep 31_B2_c$CHUNK31 $M31 $CHUNK31 $A_PRIV $B_PRIV && { pt sharegpt 2 0; pt sharegpt 2 1; pt sharegpt 4 0; }
  [ -n "$CHUNK31B" ] && serve_rep 31_B2_c$CHUNK31B $M31 $CHUNK31B $A_PRIV $B_PRIV && { pt sharegpt 2 0; }
  PROXY_KIND=toyi UCXSET=TUNED serve_pd 31_1P1D_ss $M31 "$A_PRIV" "$B_PRIV" && { SS=1 pt random 0.25 0 $K4; }
fi

if has 6; then
  log "E8-6 26B FP8 two replicas · chunk $C26F (optional)"
  serve_rep 26F_B2_c$C26F $M26F $C26F $A_PRIV $B_PRIV && { pt random 1 0 $K4; pt random 2 0 $K4; }
fi

stop_all; collectors_stop
log "E8 DONE"
