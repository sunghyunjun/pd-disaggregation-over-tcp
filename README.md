# Chunk First: When Prefill–Decode Disaggregation Pays Off over TCP

Measurements and a calibrated model: chunked prefill vs. prefill–decode (P/D) disaggregation over TCP on single-GPU cloud instances, with stock vLLM (v0.30.0, NIXL/UCX) and Gemma 4 26B and 31B on AWS g6e, g7, and g7e 2xlarge.

Technical report: [doi:10.5281/zenodo.23085600](https://doi.org/10.5281/zenodo.23085600) · [PDF](paper/en/main.pdf) · [LaTeX](paper/en/) · Code and data: [doi:10.5281/zenodo.23085749](https://doi.org/10.5281/zenodo.23085749)

## TL;DR

- **Tune the chunk first.** A replica stalls when another request's prefill shares its scheduler step, and the chunk size bounds that stall: for 26B with 4K inputs the median longest gap fell from 48 ms at a 2,560-token chunk to 21 ms at 512.
- **At 4K inputs and in chat, disaggregation over TCP served more under no latency target we could rank** against replicas with a tuned chunk. It won (about 3× for 26B) only against replicas held at 2,560 tokens, which is where vLLM 0.30.0 keeps Gemma 4 when video input is enabled.
- **Disaggregation's extra time to first token was mostly the KV transfer.** Raising UCX's TCP segment size from 8 KB to 256 KB made the transfer 3.4× faster at low load; after that, the cloud's per-flow cap and NIXL's four-way split set the rate.
- **Where chunking runs out is a matter of input length.** A step-time model calibrated on the runs predicts that, at low load and a 50 ms gap limit, inputs of roughly 14K–37K tokens (lower edge 11K–34K within the model's uncertainty) need so many chunks that 1P1D over TCP meets TTFT limits of a second or more that no chunk meets, provided the KV cache is small (hybrid attention). This is a prediction, not a measurement.

![Strict-SLO attainment against load: tuned-chunk replicas vs 1P1D](paper/figures_v4/png/fig5_head_to_head.png)

![Model prediction: lowest TTFT limit each side can meet by input length](paper/figures_v4/png/fig7_boundary.png)

## A procedure for small-GPU fleets over TCP (Section 7.1 of the report)

1. Measure the replicas' **longest gap per request**, not system percentiles, at the load you plan to serve.
2. Use the **largest chunk whose longest step fits the gap limit**; check that the stack allows it (Gemma 4 in vLLM 0.30.0 needs every modality disabled to go below 2,496 tokens).
3. Check the TTFT that chunk gives. If it meets the limit, stop.
4. Reduce prefill work before moving it: prefix-aware routing, then KV-cache loading where prompts repeat.
5. Disaggregate over TCP only where no admissible chunk meets both limits and the transfer fits (Eq. 2 of the report: KV volume ÷ (m × per-flow cap) + residual).
6. Fix the serving path: raise UCX's TCP segment size, keep nodes in a cluster placement group, use proxies that neither cap connections nor pause for garbage collection.

## Pitfalls we hit (Appendix B)

- System-wide inter-token p99 looked fine while 48% of requests stalled; judge per request.
- Gemma 4's multimodal budget check kept the chunk at 2,496 tokens or more until every modality was disabled.
- vLLM's test proxy for NIXL paused all streams during its gen-2 garbage collection (25–40 ms).
- aiohttp's default connection limit (100) throttled the replicas by one load step.

## Repository layout

```
harness/    measurement harness and analysis: aggregate.py, safe_runs.py, slo_sensitivity.py,
            decisive_ci.py, boundary_model.py, make_figures_v4.py, proxies (rr_proxy.py, pd_proxy.py)
configs/    vllm serve flag sets, per-round run scripts and runbooks
infra/      Terraform for GPU nodes, client node, placement group (set ALLOWED_SSH_CIDR before infra/up.sh)
results/    all_runs.csv (455 runs), safe_runs.csv (audit labels), per_request.json.gz (per-request timings)
            raw per-run folders are in the release assets and on Zenodo, one tar.gz per measurement round
paper/      en/ LaTeX source and PDF, ko/ Korean rendering, figures_v4/, reviews/ (four rounds of mock review)
RESULTS.md  lab notebook (Korean), including the predictions committed before the last round
PROTOCOL.md pre-registered protocol v1.7 (committed before the first run)
```

## Reproduce the report's numbers and figures

With the raw per-run folders unpacked into `results/<round>/` (release assets), or from the committed summaries alone for everything except `aggregate.py`:

```
python3 harness/aggregate.py results/ -o results/all_runs.csv                 # every run, report SLOs by default
python3 harness/safe_runs.py results/all_runs.csv -o results/safe_runs.csv   # audit: safe / caution / excluded
uv run --with numpy python3 harness/boundary_model.py --json paper/figures_v4/boundary.json   # Section 6 model, Table 3
uv run --with matplotlib python3 harness/make_figures_v4.py                   # figures -> paper/figures_v4 (after boundary_model.py)
python3 harness/decisive_ci.py --tex                                           # Appendix F
python3 harness/chunk31_buckets.py                                             # Section 4.2, 31B prompt-length buckets
cd paper/en && tectonic main.tex                                               # PDF
```

`results/per_request.json.gz` is rebuilt automatically when it no longer matches `safe_runs.csv` (`--rebuild` forces it). The analysis scripts regenerate the committed CSVs and `figures.json` byte for byte.

## How this was done

One person, about $270 of cloud time, 455 runs over nine measurement rounds. The protocol was committed before the first run and the predictions for the last round before that round (Appendix D and E). Four rounds of AI-assisted mock peer review are in `paper/reviews/`; the first two prompted the two follow-up rounds, and the fourth reviewed the model in Section 6. An AI coding assistant (Claude) wrote the harness and analysis scripts, operated the infrastructure, ran the mock reviews, and drafted text and figures; the author designed the study, paid for and directed the runs, and checked the reported numbers against the raw data.

Provenance of this public repository: the history is that of the private working repository with the AWS account ID and local paths replaced and the raw per-run folders removed (`git filter-repo`); `commit-map.txt` maps old to new hashes. A bundle of the original repository is kept by the author; its SHA-256 is in Appendix G of the report.

## License

Code: Apache-2.0. Text, figures, and data: CC BY 4.0. See `LICENSE`.
