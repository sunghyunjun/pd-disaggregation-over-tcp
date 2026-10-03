# RESULTS.md: reader's guide (English)

`RESULTS.md` is the lab notebook of this study, written in Korean during the measurement rounds. It is kept as written: it is the record that the pre-registered predictions were committed before the last round (private commit 8775497, public commit b220463), and the technical report's Appendix D and E point to it. This file explains its structure and translates the one part a reader is most likely to need, the predictions for the last round. Numbers in the report come from the scripts in `harness/`, not from this notebook.

## Structure

One section per measurement round, in the order the rounds were run. Round codes match the data folders in the release assets (`results-<round>.tar.gz`) and Table G1 of the report.

| Section (round) | Date (UTC) | Content |
|---|---|---|
| P | 2026-09-24 | two-node plumbing on g5.xlarge: iperf, NIXL startup, first end-to-end request |
| A′ | 2026-09-24 | large-model startup check on one g7e.2xlarge |
| A | 2026-09-24 | single g7.2xlarge, chunk and workload sweep (prefix cache on; excluded from the report) |
| C1 | 2026-09-25 | single g7e.2xlarge, quantization and KV capacity (prefix cache on; excluded) |
| B | 2026-09-25 | two g7.2xlarge plus a client: input-length grid, first disaggregation results |
| (re-analysis) | 2026-09-26 | KV transfer throughput reinterpreted from round B logs (no new runs) |
| D | 2026-09-26 | two g7: transfer tuning (UCX variables) and a bandwidth-limit sweep |
| (method notes) | 2026-09-27 | limits of the method, data licenses |
| E1 | 2026-09-26 | cross-GPU, L40S against RTX PRO 6000 at FP8, KV matching |
| E2 | 2026-09-26 | g7e pair, disaggregation against replicas, 16K inputs |
| (harness fixes) | 2026-09-27 | fixes made before the next rounds |
| E3 | 2026-09-27 | g6e (L40S) pair, network credits |
| E4 | 2026-09-27 | cluster placement group, per-flow cap on g7e |
| E5 | 2026-09-27 | two and three g7e nodes, 26B and 31B NVFP4 scaling, transfer estimates |
| E6 | 2026-09-27 | layer-wise push (vLLM PR 56874) trial, output correctness gate |
| (infra) | 2026-09-28 | AWS teardown, standing cost 0 |
| (audit) | 2026-09-28 | run audit and the safe / caution / excluded labels |
| E7 | 2026-09-28 | repeats, real trace, 26B 4K limit, same-round quantization, KV matching |
| E8 | 2026-09-29/30 | response to the first mock review: replica chunk sweep, global-pause cause, P–D connection count |
| E9 predictions | 2026-09-30 13:30 UTC | predictions written and committed before the round (translated below) |
| E9 results | 2026-09-30 | 19 runs, predictions checked |

## Predictions for the last round (E9), translated

Committed at 13:29 UTC on 30 September 2026, 46 minutes before the round started. The run scripts (`configs/run_E9.sh`, `configs/lib_E9.sh`) were committed with them and did not change afterwards. The verdict rule is the strict per-request SLO used since E5 (TTFT at most 1 s, longest gap at most 50 ms, one-token outputs pass the gap criterion); 30 ms verdicts are recomputed from per-request data.

1. 26B NVFP4 replicas, 512-token chunk: median longest gap 15–25 ms at 1–2 requests/s per GPU; median TTFT 40–80 ms above the 1,024-token chunk (161 ms); passes the 30 ms limit at 2 requests/s per GPU or more, which overturns the "only disaggregation at 30 ms" cells for 26B; supported load at 50 ms is 3–4 per GPU (not above 1,024 tokens, since a smaller chunk lowers prefill throughput).
2. 26B, 1,024-token chunk with the proxy cap removed: 4 requests/s per GPU at or above 0.9 in all three repeats; 5 passes (at or above 0.9); 6 fails (gap or TTFT).
3. 26B FP8 replicas, 512-token chunk: median longest gap 25–32 ms; the 40 ms limit passes at 0.5 and 1 per GPU; the 30 ms limit is borderline (0.5 passes, 1 uncertain).
4. 31B: 256-token replicas pass 8 requests/s per GPU in chat; 1P1D with the aiohttp proxy fails at 6; at 4 (seed 10000) it is borderline (0.85–0.95).
5. 1P1D with the aiohttp proxy, 8,192-token prefill chunk and only the UCX segment sizes: TTFT at 4 and 5 per GPU falls (shorter prefill queue), the strict verdict at 5 stays a failure (decode-side gaps), and 4 passes.

Outcome, as scored in Appendix E of the report: predictions 1–3 held as far as tested; in 4 both verdicts held but the seed-10000 run reached 1.000 instead of 0.85–0.95; 5 did not hold (0.874 and 0.976 at 4).

## Notes on reading the notebook

- Verdicts in early sections were made with the rules in force at the time (relative gap limits, no one-token rule); the report's Appendix D lists every deviation from the protocol. Later sections carry dated corrections in parentheses where a number was revised.
- Runs flagged later as caution data (client proxy at its CPU limit, replica proxy at its 100-connection cap) are marked in `results/safe_runs.csv`, not in the notebook.
- The AWS account ID that appeared in one line of the private notebook is replaced by `<AWS_ACCOUNT_ID>` in this public copy; nothing else was changed.
