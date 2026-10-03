*English translation of `sess_Aprime.md`; the Korean file is the original.*

# Round A′ · Large-model startup check (g7e.2xlarge ×1, 96 GB) · 1h · about $4

Purpose: confirm that the models planned for round C (g7e ×2) actually start, and measure KV bytes/tok, the number of concurrent 32K requests, and the single decode step. Also whether they start with the NixlConnector flags (the first signal of hybrid and sliding-window layer support).
Required: HF token (Gemma 4 terms accepted), `export HF_TOKEN=...`

## 0. Local
```bash
AWS_PROFILE=default infra/up.sh g7e_2x 1 --hours 2      # AZ us-east-1b
rsync -az harness configs ubuntu@<ip>:~/pd/
```
## 1. Shared functions (on the node)
```bash
mkdir -p ~/.local/bin && ln -sf ~/pd/harness/vllm-docker.sh ~/.local/bin/vllm && export PATH=~/.local/bin:$PATH
serve() { docker rm -f vllm 2>/dev/null; docker run -d --name vllm --gpus all --ipc=host --network host -v ~/pd:/pd -v ~/.cache/huggingface:/root/.cache/huggingface \
  -e HF_TOKEN=$HF_TOKEN vllm/vllm-openai:v0.30.0 "$@" --port 8000 --max-model-len 32768 --gpu-memory-utilization 0.90 --seed 0 \
  --limit-mm-per-prompt '{"image":0}' ; docker logs -f vllm 2>&1 | grep -m1 -i -E "startup complete|error" ; }
kvinfo() { docker logs vllm 2>&1 | grep -i -E "KV cache|Maximum concurrency|GPU KV" | tail -3; }
step() { cd ~/pd && MODEL=$1 BASE_URL=http://127.0.0.1:8000 RESULTS_DIR=/pd/results harness/run_bench.sh Ap B1 N0 random inf --max-concurrency 1 --num-prompts 8 --random-input-len 1024 --random-output-len 256; python3 harness/analyze.py results/*_Ap_B1_N0_random_rinf/bench.json | tail -1 | cut -f9,10; }
```
## 2. Per model (8~10 minutes each, including download)
| Order | Model | Command | Record |
|---|---|---|---|
| 1 | Gemma 4 31B BF16 | `serve google/gemma-4-31B-it` | kvinfo, `step google/gemma-4-31B-it` (tbt_p50 = single decode step) |
| 2 | Gemma 4 31B NVFP4 | `serve nvidia/Gemma-4-31B-IT-NVFP4` (`--quantization modelopt` if needed) | same |
| 3 | Gemma 4 26B-A4B BF16 | `serve google/gemma-4-26B-A4B-it` | same |
| 4 | Qwen3.6-35B-A3B BF16 | `serve Qwen/Qwen3.6-35B-A3B` | same. Whether the hybrid model starts |
| 5 | Connector startup check | Restart 1 and 4 with `--kv-transfer-config '{"kv_connector":"NixlConnector","kv_role":"kv_producer"}' -e VLLM_NIXL_SIDE_CHANNEL_HOST=<private ip> -e UCX_TLS=tcp` | Only whether startup completes without errors |
If the download is slow (31B is 62 GB), do 2, 3, and 4 first and 1 if time remains.
## 3. Shutdown
rsync results → `infra/down.sh` → confirm 0 running instances.
## Record: model table in RESULTS.md (model and precision / weights GB / KV bytes/tok / concurrent 32K / single decode step ms / connector startup O or X)
