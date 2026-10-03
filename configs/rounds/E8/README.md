*English translation of `README.ko.md`; the Korean file is the original. Commands below use the flat `configs/` layout of the time: `configs/setup_E8.sh`, `configs/step0_E8.sh`, and `configs/run_E8.sh` now live in `configs/rounds/E8/` (see `configs/README.md`).*

# Round E8 run order (review response B1, B2, B3)

Background: meta-reviewer recommendation in `paper/reviews/2026-09-30_v0/`. User approval 2026-09-30 (B1+B2+B3 as a bundle, B4 excluded). Run outside working hours (weekdays 10:00 to 19:00 KST).
Estimate: about 5 hours, two g7e.2xlarge (cluster placement group) + c6i.2xlarge, about $37~40.

1. Check credentials: `AWS_PROFILE=default aws sts get-caller-identity`, check which instances are running (do not touch instances of other projects).
2. Infrastructure (same way as E7)
   - Client: `CLIENT_TYPE=c6i.2xlarge bash infra/up.sh g7e_2x 0 --client --hours 8`
   - GPU: `bash infra/up.sh g7e_2x 2 --pg --hours 8 --ws e8` (even if it ends with a DescribeInstanceAttribute permission error, the instances are created. Read the IPs with the AWS CLI)
3. Preparation: `C=<client public> NODES="<two GPU public>" bash configs/setup_E8.sh` (model set: 26B NVFP4, 31B NVFP4, 26B FP8)
4. Step 0 (on the client): `A_PRIV=.. B_PRIV=.. bash configs/step0_E8.sh` → check which MM_LIMIT and extra arguments let 26B 1024/1536/2048 and 31B 256/512 start
   - If 26B rejects all of them: leave CHUNKS26 empty and drop the phase 1 sweep from PHASES, but keep the 2560 control (the stack constraint is itself a result)
   - If 31B rejects all of them: drop the chunk arm of step 5 and measure only the 1P1D connection count
5. Main measurement (on the client, setsid): `A_PRIV=.. B_PRIV=.. CHUNKS26=".." CHUNK31=.. [CHUNK31B=..] MM_LIMIT='..' SERVE_EXTRA='..' bash configs/run_E8.sh > results/run_E8.log 2>&1`
6. Monitoring: phases, attainment, and errors in run_E8.log. Limit of 25 minutes per point.
7. Collection: from the client, `results/*_E8_*`, `rr_proxy_E8_*`, `proxy_E8_*`, `proxy_trace_E8_*`, `xfer_E8/`, `metrics_E8/`, `client_cpu_E8_*`, `step0_E8_*`, `run_E8.log` → `results/E8/`. From the GPU nodes, `collect_*`, `ss_E8_*` → `results/E8/collect/<host>/`, `results/E8/ss/`.
8. Teardown: `bash infra/down.sh --ws e8`, then `bash infra/down.sh --ws default` (caution: after up.sh --ws e8 the current workspace is e8, so down.sh with no argument does not remove the client). Confirm 0 instances (excluding other projects).
   - Step 2 also goes in order (client first, GPU after). They share one terraform folder, so running them at the same time tangles the workspaces.
9. Record: E8 section in RESULTS.md, friction, cost. Update memory.
