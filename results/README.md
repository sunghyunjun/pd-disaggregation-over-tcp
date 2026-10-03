# results/

Three files are committed here. The raw per-run folders (`results/<round>/<run_id>/` with `result.json`, `bench.json`, logs, and collector output) are distributed as release assets, one `results-<round>.tar.gz` per measurement round with checksums in `SHA256SUMS.txt`; unpack them into this directory to rerun `analysis/aggregate.py`, `analysis/safe_runs.py`, `analysis/chunk31_buckets.py`, and `analysis/make_figures.py`. Generated text is removed from every run in the public copies; output lengths and all timings are complete. Round codes (B, D, E1 to E9, and the unused A, A′, C1, P) match Table G1 of the report and the `stage` column below.

| File | Made by | Content |
|---|---|---|
| `all_runs.csv` | `analysis/aggregate.py` | one row per run (455 rows): metadata, environment snapshot, the `vllm bench serve` summary, and per-request SLO metrics recomputed by `analysis/analyze.py` |
| `safe_runs.csv` | `analysis/safe_runs.py` | the same rows plus two audit columns, `safety` and `safety_reason`; every figure and table of the report reads this file |
| `per_request.json.gz` | `analysis/slo_sensitivity.py` | per-request arrays of every safe and caution run (327 runs), so that the analyses do not reparse about 2 GB of `bench.json`; rebuilt automatically when it no longer matches `safe_runs.csv` |

## Columns of all_runs.csv and safe_runs.csv

Empty cells mean the value was not recorded for that run. Milliseconds are written as `_ms`; rates are per second over the whole setup (not per GPU) unless stated.

**Run identity (from `result.json` meta)**

| Column | Unit | Meaning |
|---|---|---|
| `run_id` | | `<UTC timestamp>_<stage>_<config>_<network>_<workload>_r<rate>`, also the folder name of the raw run |
| `stage` | | measurement round code (A, Ap, B, C1, D, E1 to E9, P) |
| `config` | | configuration name as used by the round's run script, e.g. `26_B2` (two colocated replicas of 26B), `26_1P1D` (one prefill and one decode node), `26_B2_c1024` (replicas at a 1,024-token chunk), `26_1P1D_aio` (1P1D behind the aiohttp proxy), `31_B2_c256`, `P1tuned`, `p1_tcfix_5gbit`; prefixes `26`, `26F`, `26H`, `31` are 26B NVFP4, 26B FP8, 26B BF16, and 31B NVFP4 |
| `network` | | `N0` for no bandwidth limit; `tc1gbit`, `tc2500mbit` for a sender-side token-bucket limit (round B; round D encodes the limit in `config`) |
| `workload` | | `random` (synthetic prompts of fixed length, see `input_len_median`), `sharegpt` (ShareGPT chat), `azure_conv` (Azure conversation trace) |
| `rate` | requests/s | the arrival rate requested from `vllm bench serve` for the whole setup; `inf` sends everything at once (closed loop, see `max_concurrency`), `self` replays the trace at its own arrival times |
| `model` | | Hugging Face model id |
| `chunk` | tokens | the scheduler's maximum tokens per step on the replicas or the prefill node (`max_num_batched_tokens`); 2,560 unless the round varied it |
| `prefix_caching` | | `on`, `off`, or empty when not recorded; only `off` runs are safe |
| `discarded` | | `True` for a run the operator discarded during the round (one run) |

**Environment snapshot (from the round's `env_snapshot`; recorded in rounds A, A′, B, C1, and P only)**

| Column | Unit | Meaning |
|---|---|---|
| `instance_type` | | EC2 instance type; unreliable, in round B it holds the client's type (`c6i.xlarge`), and the E rounds left it empty, so the report maps instances from `stage` |
| `az` | | availability zone |
| `vllm` | | vLLM version |
| `iperf_p1_gbps`, `iperf_p4_gbps` | Gbit/s | iperf3 throughput between the two GPU nodes with 1 and 4 parallel flows |
| `ping_ms` | ms | average round-trip time between the nodes |

**Load and throughput (from `vllm bench serve` via `bench.json`)**

| Column | Unit | Meaning |
|---|---|---|
| `num_prompts` | | requests sent |
| `request_rate` | requests/s | the rate as `vllm bench serve` recorded it (`inf` for closed loop and self-timed replay) |
| `max_concurrency` | | concurrency cap of the closed-loop runs, empty otherwise |
| `duration_s` | s | wall time of the run |
| `completed`, `failed` | | requests that finished and requests that errored |
| `req_per_s` | requests/s | completed requests per second |
| `out_tok_per_s`, `total_tok_per_s` | tokens/s | output tokens per second, and input plus output tokens per second |
| `input_len_median`, `output_len_median` | tokens | median prompt and output length over the run's requests (1,024 to 32,768 for the synthetic grid; the analysis scripts select synthetic runs by this value, e.g. 4096 or 16384) |

**Latency summary (from `vllm bench serve`, over all requests or all tokens of the run)**

| Column | Unit | Meaning |
|---|---|---|
| `ttft_mean_ms`, `ttft_p50_ms`, `ttft_p90_ms`, `ttft_p99_ms` | ms | time to first token, mean and percentiles over requests |
| `tpot_mean_ms`, `tpot_p99_ms` | ms | time per output token (mean gap within a request), mean and p99 over requests |
| `itl_p50_ms`, `itl_p90_ms`, `itl_p99_ms` | ms | inter-token latency percentiles over every gap of every request (the system-wide percentiles of Section 4.1) |
| `vllm_goodput_req_s` | requests/s | the goodput `vllm bench serve` reports with its own `--goodput` limits; not used by the report, which cannot express the longest-gap condition that way |

**Per-request metrics (recomputed by `analysis/analyze.py` from the per-request arrays in `bench.json`)**

| Column | Unit | Meaning |
|---|---|---|
| `tbt_p50_ms`, `tbt_p90_ms`, `tbt_p99_ms` | ms | inter-token gap percentiles over every gap of every request, recomputed with linear interpolation; the same quantity as `itl_*` |
| `itl_max_over_median_p50` | ratio | for each request the longest gap divided by its median gap; the median of that ratio over requests |
| `stall_req_frac` | fraction | share of requests whose longest gap is more than five times their median gap |
| `attain_chat` | fraction | share of requests that meet the strict SLO: no error, TTFT at most 1,000 ms, longest gap at most 50 ms (a one-token output has no gaps and passes the gap condition) |
| `goodput_chat_req_s` | requests/s | requests meeting the strict SLO per second of run time |
| `goodput_chat_tok_s` | tokens/s | output tokens of requests meeting the strict SLO per second of run time (the report's SLO goodput) |
| `attain_doc`, `goodput_doc_req_s`, `goodput_doc_tok_s` | | the same for the relaxed SLO: TTFT at most 3,000 ms, longest gap at most 250 ms |

The strict and relaxed limits are the defaults of `analysis/aggregate.py` since 2026-10-01 (before that the gap limits were 100 and 400 ms; the committed files use 50 and 250).

**Audit columns (added by `analysis/safe_runs.py`, `safe_runs.csv` only)**

| Column | Meaning |
|---|---|
| `safety` | `안전` (safe), `주의` (caution), or `제외` (excluded); the strings are Korean in the file and are matched literally by every analysis script |
| `safety_reason` | the rule that assigned a caution or excluded label, empty for safe runs |

## Safety labels

The labels are assigned in this order by `classify()` in `analysis/safe_runs.py`; the first matching rule wins. The reason strings are quoted as they appear in the CSV, with a translation.

| Label | Reason string in the CSV | Meaning | Rule |
|---|---|---|---|
| excluded (`제외`) | `폐기 런` | discarded run | `discarded` is `True` |
| excluded (`제외`) | `접두어 캐시 켬 또는 미기록, 같은 시드 반복` | prefix caching on or not recorded, same seed repeated | `stage` is A, Ap, C1, or P (the setup and prefix-cache-contaminated rounds) |
| excluded (`제외`) | `접두어 캐시 켬` | prefix caching on | `prefix_caching` is `on` (ShareGPT and Azure in round B, the D3 ladder, Azure in E2, and others) |
| excluded (`제외`) | `기동 실패 런` | failed start | `ttft_p50_ms` is 0 or missing, i.e. the server never answered |
| caution (`주의`) | `클라이언트 프록시 한계 구간` | client proxy limit range | round E5, ShareGPT, rate 32 requests/s or more: the client-side proxy ran out of CPU |
| caution (`주의`) | `복제본 프록시 연결 상한 100 도달(E9 이전 rr_proxy)` | the replica proxy's connection cap of 100 was reached (rr_proxy before E9) | a replica run (`B2` or `B3` in `config`) before round E9 at a finite rate in which 100 requests were in flight at once, as counted from the client's start and end times; before E9 the replica proxy used aiohttp's default connector, which caps concurrent connections at 100, so later requests waited inside the proxy (Appendix B.1) |
| safe (`안전`) | (empty) | usable for conclusions | everything else: prefix caching off, not discarded, not a failed start, not in a client-limited range |

Counts in the committed file: 313 safe, 14 caution, 128 excluded, 455 in total. Verdicts and the main-text figures use safe runs only; caution runs appear in the appendix figures with hollow or hatched markers.

## per_request.json.gz

A gzip-compressed JSON object keyed by `run_id`, built by `build_cache()` in `analysis/slo_sensitivity.py` from the `bench.json` of every run labelled safe or caution. Each value holds:

| Key | Type | Meaning |
|---|---|---|
| `stage`, `config`, `workload`, `rate`, `network`, `input_len_median`, `safety` | string | copied from `safe_runs.csv` |
| `duration` | float, s | run wall time from `bench.json` |
| `ttft` | list of float, s | time to first token per request, rounded to 10 µs |
| `maxitl` | list of float or null, s | the longest inter-token gap of each request; `null` when the output was a single token (no gaps) |
| `e2e` | list of float, s | end-to-end latency per request |
| `outlen` | list of int, tokens | output length per request |
| `err` | list of 0 or 1 | 1 when the request returned an error |

Lists are aligned by request in the order `vllm bench serve` saved them. `attain(run, T, B)` and `goodput(run, T, B)` in the same module define the SLO test used everywhere: a request passes when `err` is 0, `ttft` is at most T seconds, and `maxitl` is null or at most B milliseconds.

`load_cache()` checks the cache against `safe_runs.csv` on every use. If a run's label changed, or a safe or caution run with a `bench.json` on disk is missing from the cache, the cache is rebuilt from the raw folders; `--rebuild` on `analysis/make_figures.py`, `analysis/decisive_ci.py`, or `analysis/slo_sensitivity.py` forces a rebuild. With no raw folders present, the committed cache is used as is.
