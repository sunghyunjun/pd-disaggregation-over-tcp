# pd-without-rdma

Does prefill/decode disaggregation pay off on readily available cloud GPUs (AWS g5/g6/g7) without RDMA?
Break-even measurements against colocated serving at equal GPU count and per dollar, with an H100 NVLink reference.

Status: pre-measurement. Protocol fixed before any run (see `PROTOCOL.md`). Results land in `results/` as raw JSON.

```
harness/    run_bench.sh (one measurement point), analyze.py (TBT-based goodput), convert_azure.py, env_snapshot.sh, rr_proxy.py
configs/    vllm serve flag sets (B1/B2/P1), proxy, tc bandwidth shaping, per-session command sheets
infra/      Terraform (on-demand GPU nodes, client node, placement group), ENA Express toggle
data/       traces (Azure LLM inference, Mooncake FAST'25) converted to vLLM timed_trace jsonl  [raw not committed]
results/    one folder per run: result.json (meta+env+bench), sar/dmon/prom time series
```

Quick start (stage A, single node): `infra/up.sh g5_2x 1` then follow `configs/sat_A.md`.

Write-up: markdown in `writeup/` (canonical) mirrored to the blog; archived on Zenodo with a DOI at release.
License: code Apache-2.0, text and figures CC-BY-4.0.
