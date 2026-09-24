#!/bin/bash
export PATH=~/.local/bin:$PATH HF_TOKEN=$(cat ~/.hf_token)
for m in nvidia/Gemma-4-26B-A4B-NVFP4 nvidia/Gemma-4-31B-IT-NVFP4 Qwen/Qwen3.6-35B-A3B-FP8 google/gemma-4-26B-A4B-it Qwen/Qwen3-8B RedHatAI/gemma-4-31B-it-FP8-block google/gemma-4-31B-it; do
  echo "=== $(date -u +%T) start $m"; hf download "$m" --exclude "*.gguf" >/dev/null 2>&1 && echo "=== $(date -u +%T) done $m" || echo "=== FAIL $m"
done
hf download anon8231489123/ShareGPT_Vicuna_unfiltered ShareGPT_V3_unfiltered_cleaned_split.json --repo-type dataset --local-dir ~/pd/data >/dev/null 2>&1 && echo "=== done sharegpt"
df -h / | tail -1
