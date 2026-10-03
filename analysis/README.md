# analysis/

Post-hoc analysis of the measurement rounds. Every script runs from the repository root. The scripts that read the raw per-run folders need the release assets (`results-<round>.tar.gz`, checksums in `SHA256SUMS.txt`) unpacked into `results/<round>/`; the others run from the committed `results/safe_runs.csv` and `results/per_request.json.gz` alone. Column meanings and the safety labels are described in `results/README.md`.

## Scripts

| Script | Reads | Writes | Supports |
|---|---|---|---|
| `aggregate.py` | every `results/**/result.json` and the `bench.json` next to it (raw per-run folders) | `results/all_runs.csv`, one row per run | the run counts of Section 3.6 and Table G1; the input of every other script |
| `analyze.py` | one or more `bench.json` files (library used by `aggregate.py`, also a CLI) | TSV to stdout, optional CSV | Section 3.5: per-request SLO attainment and goodput recomputed from per-request TTFT and inter-token gaps, since `vllm bench serve --goodput` cannot express a longest-gap condition |
| `safe_runs.py` | `results/all_runs.csv`, plus `results/*/*/bench.json` to count requests in flight (raw per-run folders) | `results/safe_runs.csv` (`all_runs.csv` plus `safety` and `safety_reason`) | Section 3.6 data selection; the proxy connection cap of Appendix B.1 |
| `slo_sensitivity.py` | `results/safe_runs.csv`, `results/*/*/bench.json` when the cache must be rebuilt | maintains `results/per_request.json.gz`; run directly, it also writes exploratory `fig15` to `fig17` and `sensitivity.json` into `-o` | Section 5.2 (the who-wins grid is computed here and drawn by `make_figures.py`); `load_cache()` is the shared reader of the per-request cache |
| `boundary_model.py` | `results/safe_runs.csv`, `results/per_request.json.gz` | `paper/figures/boundary.json`, calibration and crossover numbers to stdout | Section 6 and Table 3: the step-time model, its calibration, the crossover and its sensitivity |
| `make_figures.py` | `results/safe_runs.csv`, `results/per_request.json.gz`, `paper/figures/boundary.json`; raw folders for the E8 transfer logs (`results/E8/xfer_E8/*.log`), socket samples (`results/E8/ss/*.txt`), and the two proxy-trace runs (`results/E8/proxy_trace_E8_*.jsonl` and their `bench.json`) | `paper/figures/<name>.pdf` and `.svg`, `paper/figures/figures.json` (the numbers behind each figure) | Figures 1 to 7, the Appendix A figures, and the proxy GC figure of Appendix B.1 |
| `fig_common.py` | library for `make_figures.py` | the shared style, CSV loading, and the per-run-summary figures (`fig01` to `fig14`) | Figure 1 and Appendix A |
| `fig_results.py` | library for `make_figures.py` | `v1_chunk_stall`, `v1_ttft`, `v1_who_wins`, `v1_proxy_gc`, plus the earlier form of `v1_head_to_head` and `v1_transfer` | Sections 4.2, 4.4, 5.2, Appendix B.1 |
| `fig_headtohead.py` | library for `make_figures.py` | `v1_head_to_head` and `v1_transfer` in the form the report uses | Sections 4.3 and 5.1 |
| `decisive_ci.py` | `results/safe_runs.csv`, `results/per_request.json.gz` | table to stdout; `--tex` prints LaTeX rows | Appendix F: attainment at the decisive points with hierarchical-bootstrap intervals |
| `chunk31_buckets.py` | `results/safe_runs.csv`, the `bench.json` of the five 31B chat replica runs at 2 requests/s (raw per-run folders) | text to stdout | Section 4.2: share of 31B requests within 50 ms by the length of the longest prompt that arrived on the same replica while they decoded |
| `e8_summary.py` | `results/<round>/*_<round>_*/bench.json` (raw per-run folders) | markdown table to stdout (`summary_E8.md` and `summary_E9.md` in the release assets were made with it) | the E8 and E9 sections of `RESULTS.md`; global stall counts of Appendix B.1. The archived copies carry a Korean header row; the numbers are identical and only the header language differs. |
| `stall_match.py` | a proxy trace (`proxy_trace_*.jsonl`) and run folders (raw) | text to stdout | Appendix B.1: client-side global stalls matched to proxy GC and event-loop pauses |
| `ss_parse.py` | one `ss_sample.sh` output file (`results/E8/ss/*.txt`, raw) | text to stdout | Section 4.3: number of TCP connections that carried the KV transfer and their shares |
| `parse_prom.py` | `collect_*_prom.tsv` from the node collector and the round's `result.json` files (raw) | table to stdout | per-run vLLM metric windows (running, waiting, KV use, preemptions, prefix-cache hit rate) used in the lab notebook and in the prefix-cache audit |
| `coverage_tables.py` | `results/all_runs.csv` | HTML heatmap tables to stdout | an overview of how the runs cover models, instances, configurations, workloads, lengths, rates, and bandwidth settings; not part of the report |
| `table.py` | `analyze.py` TSV on stdin | markdown table to stdout | ad hoc inspection |

## Reproduction order

```
python3 analysis/aggregate.py results/ -o results/all_runs.csv                       # 1  needs raw per-run folders
python3 analysis/safe_runs.py results/all_runs.csv -o results/safe_runs.csv         # 2  needs raw per-run folders
uv run --with numpy python3 analysis/boundary_model.py --json paper/figures/boundary.json   # 3  committed CSV and cache only
uv run --with matplotlib python3 analysis/make_figures.py                           # 4  needs results/E8 transfer logs, socket samples, proxy traces
python3 analysis/decisive_ci.py --tex                                               # 5  committed CSV and cache only
python3 analysis/chunk31_buckets.py                                                 # 6  needs raw per-run folders
```

Steps 1, 2, 4, and 6 read the raw per-run folders from the release assets: `aggregate.py` and `safe_runs.py` read every round, `chunk31_buckets.py` reads five E5/E7/E8 runs, and `make_figures.py` reads the E8 transfer logs, socket samples, and proxy traces (its other inputs are the committed files). Steps 3 and 5 run from `results/safe_runs.csv` and `results/per_request.json.gz` alone. Step 4 must follow step 3 because the boundary figure reads `paper/figures/boundary.json`.

`results/per_request.json.gz` caches the per-request arrays of every safe and caution run. `slo_sensitivity.load_cache()` compares it with `safe_runs.csv` on every load and rebuilds it automatically when the set of runs or their labels no longer match (that rebuild needs the raw `bench.json` files); `--rebuild` on `make_figures.py`, `decisive_ci.py`, or `slo_sensitivity.py` forces it. With the committed inputs, steps 1 to 5 reproduce `all_runs.csv`, `safe_runs.csv`, `boundary.json`, and `figures.json` byte for byte.

The SLO labels in the column names are fixed: `chat` is the strict SLO (TTFT at most 1 s, longest gap per request at most 50 ms) and `doc` is the relaxed SLO (3 s, 250 ms). `aggregate.py --slo name=ttft:MS,tbt:MS` recomputes the attainment and goodput columns for other limits.

Dependencies: Python 3 standard library for everything except `boundary_model.py` (numpy) and `make_figures.py` and `slo_sensitivity.py` (matplotlib, numpy through `boundary_model.py`); the `uv run --with` lines above install them in a temporary environment.
