*English version; `README.ko.md` is the Korean version of this file.*

# configs

The flag sets and the scripts that drove each measurement round. The scripts are shown as they were executed from the repository root at the time. Paths inside them, such as `configs/lib_E9.sh`, `configs/setup_E8.sh`, or `harness/serve.sh`, refer to the flat layout the repository had during the rounds (every file sat directly under `configs/`), and the host variables (`A_PRIV`, `B_PRIV`, `C_PRIV`, `E_PRIV`, `G_PRIV`) point at nodes that no longer exist. The round scripts are therefore records of what ran, not one-click runners. Their Korean comments and log messages were translated to English afterwards without changing any command, flag, path, number, or line order; Korean that is part of a command (a grep pattern in `run_E3.sh`, a knob label in `run_D_xfer.sh`) was left as is. The one exception to the translation is round E9, whose two scripts are kept byte for byte (see the note at the end).

```
configs/
├── README.md, README.ko.md
├── common/     flag sets and reference sheets shared by the rounds (each .md has a .ko.md Korean original)
└── rounds/     one folder per measurement round: run scripts, and for P, A′, A, E8 the runbook
    ├── P/  Aprime/  A/  B/  C1/  D/
    └── E1/ E2/ E3/ E4/ E5/ E6/ E7/ E8/ E9/
```

## common/

| File | Contents |
|---|---|
| `b1.env` | Single-instance flag set (B1; each replica in B2 is identical). Sets `MODEL` (default `Qwen/Qwen3-8B`), `CHUNK` (default 2048), and `VLLM_FLAGS`: `--dtype bfloat16 --max-model-len 32768 --gpu-memory-utilization 0.90 --max-num-batched-tokens ${CHUNK} --max-num-seqs 256 --seed 0 --disable-log-requests --port ${PORT:-8000}`. Prefix caching stays on for ShareGPT and traces and is turned off for random sweeps (`--no-enable-prefix-caching`). |
| `p1_prefill.env` | Sources `b1.env`, then adds the prefill side of 1P1D: `VLLM_NIXL_SIDE_CHANNEL_HOST=${OWN_IP}` (this node's private IP), `VLLM_NIXL_SIDE_CHANNEL_PORT=5600`, `UCX_TLS=tcp,cuda_copy,cuda_ipc`, `UCX_NET_DEVICES=all`, and `--kv-transfer-config '{"kv_connector":"NixlConnector","kv_role":"kv_producer"}'`. The `UCX_TLS` value comes from round P: with `tcp` alone UCX mistook VRAM for host memory and `registerMem` failed. |
| `p1_decode.env` | Same as `p1_prefill.env` with `kv_role` set to `kv_consumer`. |
| `models.md` | Model candidate matrix: KV KB per token, weight sizes, KV needed for one 32K request, official quantizations, precision support per GPU, what fits where, and the per-instance test matrix. |
| `proxy.md` | Proxy commands: vLLM's test proxy (toy proxy) for 1P1D, `harness/rr_proxy.py` round robin for B2, and the procedure for the 5% proxy-overhead check. |
| `tc.md` | Bandwidth equalization and sweep with `tc qdisc ... tbf` on the sending side, how to verify with iperf3, and how to remove it. |

The later rounds (D onward) do not source these `.env` files directly: the run scripts pass the same flags through `harness/serve.sh` with `CHUNK`, `PREFIX`, `GPU_UTIL`, `CONNECTOR`, `OWN_IP`, and `UCX_EXTRA`.

## rounds/

| Round | Date (UTC) | Instances | Purpose | Scripts in `rounds/<round>/` | Section of RESULTS.md | Release asset |
|---|---|---|---|---|---|---|
| P | 2026-09-24 | g5.xlarge ×2 | Two-node plumbing: iperf, NIXL startup, first end-to-end request | runbook only (`README.md`, `README.ko.md`) | §P | `results-P.tar.gz` |
| A′ (folder `Aprime/`) | 2026-09-24 | g7e.2xlarge ×1 | Large-model startup check | runbook only (`README.md`, `README.ko.md`) | §A′ | `results-Ap.tar.gz` |
| A | 2026-09-24 | g7.2xlarge ×1 | Chunk and workload sweep (prefix cache on; excluded from the report) | `run_A.sh`, runbook | §A | `results-A.tar.gz` |
| C1 | 2026-09-25 | g7e.2xlarge ×1 | Quantization and KV capacity (prefix cache on; excluded from the report) | `run_C1.sh`, `run_C1_tail.sh`, `prefetch_C1.sh` | §C1 | `results-C1.tar.gz` |
| B | 2026-09-25 | g7.2xlarge ×2 + c6i.xlarge client | Input-length grid and the first disaggregation results | `run_B.sh`, `run_B_knee.sh`, `run_B_tail.sh` | §B | `results-B.tar.gz` |
| D | 2026-09-26 | g7.2xlarge ×2 + client | Transfer tuning (UCX variables) and bandwidth-limit sweep | `run_D_xfer.sh`, `run_D1.sh`, `run_D1b.sh`, `run_D2.sh`, `run_D3.sh` | §D | `results-D.tar.gz` |
| E1 | 2026-09-26 | g6e.2xlarge ×1 + g7e.2xlarge ×1 | Cross-GPU L40S vs RTX PRO 6000 at FP8, KV matching | `run_E1.sh`, `run_E1b.sh`, `run_E1c.sh` | §E1 | `results-E1.tar.gz` |
| E2 | 2026-09-26 | g7e.2xlarge ×2 | Disaggregation vs replicas, 16K inputs | `run_E2.sh`, `run_E2b.sh` | §E2 | `results-E2.tar.gz` |
| E3 | 2026-09-27 | g6e.2xlarge ×2 | Network credits | `run_E3.sh` | §E3 | `results-E3.tar.gz` |
| E4 | 2026-09-27 | g7e.2xlarge ×2, cluster placement group | Per-flow cap on g7e | `run_E4.sh`, `run_E4b.sh` | §E4 | `results-E4.tar.gz` |
| E5 | 2026-09-27 | g7e.2xlarge ×2 and ×3, cluster placement group | 26B and 31B NVFP4 scaling | `run_E5.sh`, `run_E5b.sh` | §E5 | `results-E5.tar.gz` |
| E6 | 2026-09-27 | g7e.2xlarge ×2, cluster placement group | Layer-wise push (vLLM PR 56874) trial and output-correctness gate | `run_E6.sh`, `run_E6b.sh`, `run_E6c.sh` | §E6 | `results-E6.tar.gz` |
| E7 | 2026-09-28 | g7e.2xlarge ×2 and ×3, cluster placement group | Repeats, real trace, 26B 4K limit, same-round quantization, KV matching | `lib_E7.sh`, `run_E7a.sh`, `run_E7b.sh`, `run_E7c.sh` | §E7 | `results-E7.tar.gz` |
| E8 | 2026-09-29/30 | g7e.2xlarge ×2, cluster placement group + c6i.2xlarge client | Replica chunk sweep, global-pause cause, P–D connection count | `lib_E8.sh`, `setup_E8.sh`, `step0_E8.sh`, `run_E8.sh`, `run_E8x.sh`, runbook | §E8 | `results-E8.tar.gz` |
| E9 | 2026-09-30 | g7e.2xlarge ×2, cluster placement group + c6i.2xlarge client | Predictions committed before the round (13:30 UTC), 19 runs | `lib_E9.sh`, `run_E9.sh` | §E9 (predictions, then results) | `results-E9.tar.gz` |

Notes on the table:

- The data of rounds P, A′, A, and C1 are published but excluded from the report: P was plumbing only, A and C1 ran with the prefix cache on, and A′ was a startup check. Same-seed repeats in the early rounds are excluded as well; `results/safe_runs.csv` carries the audit labels.
- `lib_*.sh` files are sourced by the `run_*.sh` of the same round and are not run on their own. `setup_E8.sh` ran on the local machine; every other script ran on the client node.
- `rounds/D/run_D_xfer.sh` calls `harness/xfer_probe.py`, a standalone NIXL transfer probe that was never committed and was not preserved. The round D bandwidth-sweep runs in the release assets and in RESULTS.md §D come from the vLLM-based scripts (`run_D1.sh`, `run_D1b.sh`, `run_D2.sh`, `run_D3.sh`) and do not depend on it.
- Release assets are named after the data folder in `results/`, so round A′ is `results-Ap.tar.gz` while its scripts folder is `rounds/Aprime/`.
- The runbooks (`README.md` per round) are the English translation and `README.ko.md` the Korean original. Commands quoted in them, such as `bash configs/setup_E8.sh`, use the flat layout of the time for the same reason as the scripts.

## The E9 scripts

`rounds/E9/run_E9.sh` and `rounds/E9/lib_E9.sh` are byte-identical to the pre-registered commit (public hash `b220463`), which recorded the predictions for the last round before any of its runs started. Their comments are still in Korean for that reason. The scripts of every other round had their comments and log messages translated afterwards; `git log` on each file shows the translation commit separately from the measurement-time commits.
