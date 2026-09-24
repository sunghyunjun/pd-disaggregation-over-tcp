# 세션 A′ · 큰 모델 기동 검증 (g7e.2xlarge ×1, 96 GB) · 1h · 약 $4

목적: 세션 C(g7e ×2)에서 쓸 모델이 실제로 뜨는지, KV bytes/tok·32K 동시 수·단일 스텝을 실측. NixlConnector 플래그로도 뜨는지(hybrid·슬라이딩 층 지원의 첫 신호).
필요: HF 토큰(Gemma 4 약관 동의), `export HF_TOKEN=...`

## 0. 로컬
```bash
AWS_PROFILE=default infra/up.sh g7e_2x 1 --hours 2      # AZ us-east-1b
rsync -az harness configs ubuntu@<ip>:~/pd/
```
## 1. 공통 함수 (노드에서)
```bash
mkdir -p ~/.local/bin && ln -sf ~/pd/harness/vllm-docker.sh ~/.local/bin/vllm && export PATH=~/.local/bin:$PATH
serve() { docker rm -f vllm 2>/dev/null; docker run -d --name vllm --gpus all --ipc=host --network host -v ~/pd:/pd -v ~/.cache/huggingface:/root/.cache/huggingface \
  -e HF_TOKEN=$HF_TOKEN vllm/vllm-openai:v0.30.0 "$@" --port 8000 --max-model-len 32768 --gpu-memory-utilization 0.90 --seed 0 \
  --limit-mm-per-prompt '{"image":0}' ; docker logs -f vllm 2>&1 | grep -m1 -i -E "startup complete|error" ; }
kvinfo() { docker logs vllm 2>&1 | grep -i -E "KV cache|Maximum concurrency|GPU KV" | tail -3; }
step() { cd ~/pd && MODEL=$1 BASE_URL=http://127.0.0.1:8000 RESULTS_DIR=/pd/results harness/run_bench.sh Ap B1 N0 random inf --max-concurrency 1 --num-prompts 8 --random-input-len 1024 --random-output-len 256; python3 harness/analyze.py results/*_Ap_B1_N0_random_rinf/bench.json | tail -1 | cut -f9,10; }
```
## 2. 모델별 (각 8~10분: 다운로드 포함)
| 순서 | 모델 | 명령 | 기록 |
|---|---|---|---|
| 1 | Gemma 4 31B BF16 | `serve google/gemma-4-31B-it` | kvinfo, `step google/gemma-4-31B-it` (tbt_p50 = 단일 스텝) |
| 2 | Gemma 4 31B NVFP4 | `serve nvidia/Gemma-4-31B-IT-NVFP4` (필요 시 `--quantization modelopt`) | 동일 |
| 3 | Gemma 4 26B-A4B BF16 | `serve google/gemma-4-26B-A4B-it` | 동일 |
| 4 | Qwen3.6-35B-A3B BF16 | `serve Qwen/Qwen3.6-35B-A3B` | 동일. hybrid 기동 여부 |
| 5 | 커넥터 기동 확인 | 1·4를 `--kv-transfer-config '{"kv_connector":"NixlConnector","kv_role":"kv_producer"}' -e VLLM_NIXL_SIDE_CHANNEL_HOST=<private ip> -e UCX_TLS=tcp`로 재기동 | 에러 없이 startup complete인지만 |
다운로드가 느리면(31B 62 GB) 2·3·4를 먼저 하고 1은 시간이 남을 때.
## 3. 종료
results rsync → `infra/down.sh` → running 인스턴스 0 확인.
## 기록: RESULTS.md 모델 표 (모델·정밀도 / 가중치 GB / KV bytes/tok / 32K 동시 / 단일 스텝 ms / 커넥터 기동 O·X)
