*English translation of `sat_A.md`; the Korean file is the original.*

# Saturday round A command sheet (g7.2xlarge ×1, RTX PRO 4500 32GB, 8 vCPU quota), revised 9/24

Goal: start three models and verify KV bytes/tok (Gemma 4 26B-A4B NVFP4, Gemma 4 12B BF16→FP8, Qwen3-8B BF16), single decode step time → SLO ms, B1 ShareGPT sweep (main model 26B-A4B NVFP4, chunks 2048 and 8192), part of synthetic 4K/16K × 512, Azure-conv replay.
Main model: `RedHatAI/gemma-4-26B-A4B-it-NVFP4` (or `nvidia/Gemma-4-26B-A4B-NVFP4`); check the model card for whether `--quantization modelopt` is needed. Anchor: `Qwen/Qwen3-8B`.
Time budget 2h. If boot plus preparation exceeds 15 minutes, baking an AMI becomes the first task next week.

## 0. Local (the day before the round)
```bash
cd <repo>
# ShareGPT (if needed): https://huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered  ShareGPT_V3_unfiltered_cleaned_split.json
infra/up.sh g7_2x 1 --hours 3          # on-demand, auto-terminates after 3h (AZ us-east-1b)
```

## 1. Node preparation (ssh ubuntu@<ip>)
```bash
mkdir -p ~/pd && cd ~/pd && git clone --depth 1 https://github.com/vllm-project/vllm.git vllm-src   # record the commit hash
# copy harness and data (from local): rsync -av harness configs data/traces ubuntu@<ip>:~/pd/
docker run -d --name vllm --gpus all --ipc=host --network host -v ~/.cache/huggingface:/root/.cache/huggingface -v ~/pd:/pd \
  -e HF_TOKEN=$HF_TOKEN vllm/vllm-openai:v0.30.0 \
  RedHatAI/gemma-4-26B-A4B-it-NVFP4 --max-model-len 32768 --gpu-memory-utilization 0.90 --max-num-batched-tokens 2048 \
  --kv-cache-dtype auto --limit-mm-per-prompt '{"image":0}' \
  --max-num-seqs 256 --seed 0 --port 8000
docker logs -f vllm | grep -m1 "Application startup complete"
curl -s localhost:8000/v1/models | head -c 200
bash harness/env_snapshot.sh results/env_A.json              # no peer
export MODEL=RedHatAI/gemma-4-26B-A4B-it-NVFP4 BASE_URL=http://127.0.0.1:8000 RESULTS_DIR=/pd/results ENV_JSON=/pd/results/env_A.json \
       SHAREGPT_JSON=/pd/data/ShareGPT_V3_unfiltered_cleaned_split.json TRACES_DIR=/pd/data/traces
cd ~/pd   # run_bench.sh runs from here. Side collectors (sar/dmon/prom) run on the host and write results to the same folder
# bench serve runs inside the container. When the harness calls `vllm`, the wrapper forwards it via docker exec:
mkdir -p ~/.local/bin && ln -sf ~/pd/harness/vllm-docker.sh ~/.local/bin/vllm && export PATH=~/.local/bin:$PATH
# result paths are container paths /pd/..., so keep RESULTS_DIR=/pd/results and view them on the host as ~/pd/results
```
KV bytes/token check: `docker logs vllm | grep -i "GPU KV cache size\|Maximum concurrency"` → record in RESULTS (26B-A4B expected 80 KB/tok; check whether sliding-window layers are excluded). In the same way, start Gemma 4 12B BF16 (24GB, KV 3GB expected), FP8, and Qwen3-8B BF16 and record only the values (5 minutes each).

## 2. Single decode step time → fix the SLO (5 minutes)
```bash
harness/run_bench.sh A B1 N0 random inf --max-concurrency 1 --num-prompts 20 --random-input-len 1024 --random-output-len 512
python3 harness/analyze.py results/*_A_B1_N0_random_rinf/bench.json      # tbt_p50_ms = single decode step
# SLO: chat tbt = 5×step, doc tbt = 25×step  → export SLO_CHAT_TBT SLO_DOC_TBT (ms), used by analyze.py --slo
```

## 3. ShareGPT sweep, chunk 2048 (≈25 minutes)
```bash
for r in 0.5 1 2 4 6 8; do harness/run_bench.sh A B1 N0 sharegpt $r; done
harness/run_bench.sh A B1 N0 sharegpt inf --num-prompts 300              # maximum throughput reference value
python3 harness/analyze.py results/*_A_B1_N0_sharegpt_*/bench.json --slo chat=ttft:1000,tbt:$SLO_CHAT_TBT --slo doc=ttft:3000,tbt:$SLO_DOC_TBT --csv results/A_sharegpt_c2048.csv
```
If the request rate at which the SLO breaks does not appear below 8, add 12 and 16. If it already breaks at 0.5, add 0.25.

## 4. Restart with chunk 8192 and repeat step 3 (≈25 minutes)
```bash
docker rm -f vllm && (the docker run above with --max-num-batched-tokens 8192) && for r in 0.5 1 2 4 6 8; do CHUNK=8192 harness/run_bench.sh A B1c8k N0 sharegpt $r; done
```

## 5. Part of the synthetic set (≈20 minutes), prefix caching off (restart with `--no-enable-prefix-caching`, chunk 2048)
```bash
for L in 4096 16384; do for r in 0.25 0.5 1; do harness/run_bench.sh A B1 N0 random $r --random-input-len $L --random-output-len 512; done; done
```

## 6. Azure-conv replay (≈10 minutes)
```bash
TRACE_SEC_MULT=0.002 harness/run_bench.sh A B1 N0 azure_conv self --num-prompts 600    # 2x slower, first 600 requests (≈4 minutes)
```
The original trace's 5.5 req/s overloads a single A10G → use a multiplier of 0.002~0.004. Record the effective req/s in RESULTS.

## 7. Cleanup
```bash
rsync -av ubuntu@<ip>:~/pd/results/ ./results/ ; infra/down.sh
```
RESULTS.md §A: single decode step ms, SLO values, sweep table (csv), maximum throughput, KV bytes/tok, friction.
