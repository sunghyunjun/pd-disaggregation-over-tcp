# pd-without-rdma

When does prefill–decode disaggregation over TCP beat colocated replicas with chunked prefill on single-GPU cloud instances without RDMA? Measurements with stock vLLM (v0.30.0, NIXL/UCX over TCP) and Gemma 4 26B and 31B on AWS g6e, g7, and g7e 2xlarge instances.

Status: measurements finished (sessions B–E9, 455 runs); paper draft v3 in `paper/en/`. The protocol in `PROTOCOL.md` was committed before the first session; deviations are listed in the paper's Appendix D. Session E9's predictions were committed before that session (Appendix E).

```
harness/    measurement and analysis scripts (aggregate.py, safe_runs.py, slo_sensitivity.py, decisive_ci.py, make_figures_v3.py, proxies)
configs/    vllm serve flag sets, proxies, per-session run scripts and sheets
infra/      Terraform (GPU nodes, client node, placement group)
data/       traces converted to vLLM timed_trace jsonl  [raw not committed]
results/    one folder per run (result.json, bench.json, time series); all_runs.csv, safe_runs.csv, per_request.json.gz
paper/      en/ (LaTeX), ko/ (Korean draft), figures_v3/, reviews/ (three rounds of AI-assisted mock review)
```

Reproduce the paper's numbers and figures from `results/`:

```
python3 harness/aggregate.py results/ -o results/all_runs.csv         # every run, paper SLOs by default
python3 harness/safe_runs.py results/all_runs.csv -o results/safe_runs.csv   # audit: safe / caution / excluded
uv run --with matplotlib python3 harness/make_figures_v3.py            # figures and figures.json -> paper/figures_v3
python3 harness/decisive_ci.py --tex                                    # Appendix F table
python3 harness/chunk31_buckets.py                                      # Section 4.2, 31B prompt-length buckets
cd paper/en && tectonic main.tex                                        # PDF
```

The per-request cache `results/per_request.json.gz` is rebuilt automatically when it no longer matches `safe_runs.csv` (`--rebuild` forces it).

License: code Apache-2.0, text and figures CC-BY-4.0.
