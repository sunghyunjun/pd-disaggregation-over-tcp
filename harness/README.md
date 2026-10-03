# harness/

Scripts that ran on the AWS nodes and on the client during measurement. Everything here was executed on a live cluster; nothing in this folder is needed to reproduce the analysis from the published `results/` data (that lives in `analysis/`). The round scripts in `configs/rounds/<round>/` call these files by the path `harness/<name>` from the repository root, so this folder stays flat and the file names do not change.

## Scripts

| Script | Phase | Role |
|---|---|---|
| `preflight_quota.sh` | node setup | Checks spare G-family vCPU quota in the AWS account before a round starts. Argument is the number of vCPUs needed. |
| `env_snapshot.sh` | node setup | Writes the environment block for one run (instance id and type, AZ, AMI, placement group, GPU, vLLM and NIXL versions, iperf3 and ping to the peer) as JSON. Its path is passed to `run_bench.sh` as `ENV_JSON`. |
| `vllm-docker.sh` | node setup | Symlinked onto `PATH` as `vllm`. Runs `vllm ...` inside the running server container with `~/pd` mounted at `/pd`, so benchmark result files land on the host. |
| `hf_prune_blobs.py` | node setup (utility) | Deletes Hugging Face hub blobs no snapshot references, to recover disk after a partial download. |
| `serve.sh` | serving | Starts (or restarts) the vLLM server container on one GPU node with the chunk size, prefix caching and KV connector role given by environment variables, then waits for readiness. Used by every round. |
| `serve_pair.sh` | serving | Foreground wrapper used as the `--serve-cmd` of `vllm bench sweep serve`. Starts `serve.sh` over ssh on one node (`MODE=solo`) or on a prefill and a decode node (`MODE=pd`), then execs the matching proxy. |
| `kvinfo.sh` | serving (utility) | Prints KV cache memory, KV token capacity and KB per token from the running server's log. |
| `reset_caches.sh` | serving | POSTs the prefix, multimodal and encoder cache reset endpoints on each server. Called between measurement points (friction #11). Requires `VLLM_SERVER_DEV_MODE=1`, which `serve.sh` sets. |
| `rr_proxy.py` | proxy | Minimal round-robin OpenAI-compatible proxy in front of the replicas configuration (B1 and B2 baselines). `--conn-limit` caps upstream connections; 100 through E8, 0 from E9. |
| `pd_proxy.py` | proxy | aiohttp proxy for the 1P1D (prefill–decode disaggregation) configuration. Same request flow as vLLM's test proxy. Round E8 onward. |
| `toy_proxy_instr.py` | proxy | Copy of vLLM's test proxy (`tests/v1/kv_connector/nixl_integration/toy_proxy_server.py`, v0.30.0) with `proxy_trace.py` instrumentation added. Identical behavior when `PROXY_TRACE` is unset. Rounds E5 to E7 used the unmodified original. |
| `proxy_trace.py` | proxy (library) | Instrumentation imported by `pd_proxy.py` and `toy_proxy_instr.py`. Records upstream stream gaps, event-loop lag and slow GC passes as one JSON object per line. Enabled only when `PROXY_TRACE=<path>` is set. Read by `analysis/stall_match.py`. |
| `dump_proxy.py` | proxy (debug) | Forwards to one upstream and logs the first N request bodies and every non-200 response. Used once to debug timed-trace 400s. |
| `run_bench.sh` | benchmark | One measurement point. Runs `vllm bench serve` against `BASE_URL`, starts side collectors (sar, nvidia-smi dmon, Prometheus scrape), resets caches first when `RESET_URLS` is set, and writes `results/<run_id>/{bench.json,result.json,bench.log,...}`. Read by `analysis/aggregate.py` and `analysis/analyze.py`. |
| `sweep_ladder.sh` | benchmark | Runs one rate ladder with `vllm bench sweep serve` using `serve_pair.sh` and `reset_caches.sh`. Alternative to looping `run_bench.sh`. |
| `sweep_to_runs.py` | benchmark | Converts `vllm bench sweep serve` output into the `results/<run_id>/{result,bench}.json` layout that `analysis/aggregate.py` expects. |
| `greedy_check.py` | benchmark (correctness gate) | Sends fixed prompts with greedy decoding, records the outputs, and compares two records. Used to confirm that a changed transfer path still moves the whole KV. |
| `convert_azure.py` | benchmark (data prep) | Converts the Azure LLM inference traces (Splitwise) to the Mooncake jsonl format that `vllm bench serve --dataset-name timed_trace` replays. |
| `node_collect.sh` | collection | 1-second collector on a GPU node: filtered `/metrics` as TSV, `sar -n DEV`, `nvidia-smi dmon`. `start`, `stop`, `verify`. Read by `analysis/parse_prom.py`. |
| `ss_sample.sh` | collection | Samples `ss -tinH dst PEER_IP` at a fixed interval to count TCP connections between the prefill and decode nodes and the bytes each carries (round E8). Read by `analysis/ss_parse.py`. |

## Flow of one measurement round

1. **Bring up the nodes.** `infra/up.sh PROFILE GPU_COUNT [--client] [--pg]` creates the GPU nodes, optionally a client node and a cluster placement group. Run `harness/preflight_quota.sh N` first if another round may still be using G-family instances.
2. **Prepare each GPU node.** Clone the repository to `~/pd`, link `harness/vllm-docker.sh` onto `PATH` as `vllm`, and capture `harness/env_snapshot.sh results/env_<node>.json PEER_IP`.
3. **Start serving.** On each GPU node, `CHUNK=... PREFIX=on|off CONNECTOR=none|producer|consumer harness/serve.sh MODEL`. Replicas use `CONNECTOR=none` on every node. 1P1D uses `producer` on the prefill node and `consumer` on the decode node.
4. **Start a proxy on the client.** For replicas: `harness/rr_proxy.py --port 8000 --upstreams http://A:8100 http://B:8100`. For 1P1D: `harness/pd_proxy.py` (E8 onward), `harness/toy_proxy_instr.py` (E8 with tracing), or vLLM's test proxy (E5 to E7).
5. **Start collectors.** `harness/node_collect.sh start` on each GPU node. `harness/ss_sample.sh start PEER_IP OUT` on the prefill node when connection-level TCP data is wanted.
6. **Measure.** For each point of the rate ladder, `harness/run_bench.sh STAGE CONFIG NETWORK WORKLOAD RATE [bench args]` with `BASE_URL` pointing at the proxy and `RESET_URLS` listing the servers. Or run the whole ladder with `harness/sweep_ladder.sh` and convert with `harness/sweep_to_runs.py`. When the transfer path changes, run `harness/greedy_check.py` before and after and compare.
7. **Stop collectors and tear down.** `harness/node_collect.sh stop`, `harness/ss_sample.sh stop`, then `infra/down.sh`.

The result of every point is a folder `results/<round>/<run_id>/` holding `bench.json` (vLLM's per-request output), `result.json` (the same plus a `meta` block with stage, config, network, workload, rate, chunk, prefix caching and the environment snapshot), `bench.log`, and the per-point side collector files `sar.txt`, `dmon.txt`, `prom.txt`. The node-level collector files `collect_<host>_<tag>_{prom.tsv,sar.txt,dmon.txt}` sit beside them. Everything downstream is in `analysis/`.

The round scripts in `configs/rounds/<round>/` encode exactly which of these steps each round ran, with which models, chunk sizes and request rates. They are the authoritative record; this page is the map.

## Environment variables accepted by `serve.sh`

Read from `harness/serve.sh`. The first argument is the model id; any further arguments are appended to the vLLM command line.

| Variable | Default | Effect |
|---|---|---|
| `CHUNK` | `2048` | `--max-num-batched-tokens`, the chunked prefill size. |
| `PORT` | `8000` | `--port`. Rounds used 8100 for the prefill or single node and 8200 for the decode node. |
| `MAXLEN` | `32768` | `--max-model-len`. |
| `GPU_UTIL` | `0.90` | `--gpu-memory-utilization`. |
| `PREFIX` | `on` | `off` adds `--no-enable-prefix-caching`. |
| `CONNECTOR` | `none` | `producer` or `consumer` enables the KV connector with `kv_role` `kv_producer` or `kv_consumer`, sets the NIXL side channel to `OWN_IP:5600`, and sets `UCX_TLS=tcp,cuda_copy,cuda_ipc` and `UCX_NET_DEVICES=all`. |
| `OWN_IP` | first address from `hostname -I` | Host advertised for the NIXL side channel. |
| `IMAGE` | `vllm/vllm-openai:v0.30.0` | Docker image. |
| `UCX_EXTRA` | empty | Space-separated `K=V` pairs passed into the container as environment variables (UCX transfer-path tuning). |
| `ENV_EXTRA` | empty | Space-separated `K=V` pairs passed into the container as environment variables (anything else). |
| `EXTRA_MOUNTS` | empty | Space-separated `host:container[:ro]` bind mounts added to the container. |
| `MM_LIMIT` | `{"image":0}` | Value for `--limit-mm-per-prompt`. Used in E8 to confirm startup with small chunks. |
| `KV_CONNECTOR_NAME` | `NixlConnector` | `kv_connector` in `--kv-transfer-config`. |
| `KV_ENGINE_ID` | unset | `engine_id` in `--kv-transfer-config` when set. |
| `KV_BUFFER_DEVICE` | unset | `kv_buffer_device` in `--kv-transfer-config` when set. |
| `NIXL_THREADS` | unset | `kv_connector_extra_config.num_threads` in `--kv-transfer-config` when set. |

Fixed settings: the container is named `vllm`, runs with `--gpus all --ipc=host --network host`, mounts `~/pd` at `/pd` and the Hugging Face and vLLM caches, and always passes `--max-num-seqs 256 --seed 0`. `VLLM_SERVER_DEV_MODE=1` is set so `reset_caches.sh` works, and `VLLM_SSM_CONV_STATE_LAYOUT=DS` is always set. The Hugging Face token is read from `~/.hf_token`. The script waits up to 15 minutes for "Application startup complete"; on container exit it saves the log to `results/serve_fail_<ts>.log` and returns 1.

## Why the folder is flat

Every round script and runbook under `configs/rounds/` refers to these files as `harness/<name>` relative to the repository root (cloned to `~/pd` on the nodes). Moving or renaming a file here would silently break the record of what each round executed, so the layout is kept as it was during measurement. Post-hoc analysis scripts were moved to `analysis/` and paper tooling to `paper/tools/` after the last round; comments in this folder point to the new locations.
