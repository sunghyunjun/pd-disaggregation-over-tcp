# 토요일 A 세션 명령어 시트 (g7.2xlarge ×1, RTX PRO 4500 32GB, 8 vCPU 쿼타) — 9/24 개정

목표: 모델 3종 기동·KV bytes/tok 검증(Gemma 4 26B-A4B NVFP4, Gemma 4 12B BF16→FP8, Qwen3-8B BF16), 단일 스텝 시간 → SLO ms, B1 ShareGPT 스윕(주 모델 26B-A4B NVFP4, 청크 2048·8192), 합성 4K/16K × 512 일부, Azure-conv 재생.
주 모델: `RedHatAI/gemma-4-26B-A4B-it-NVFP4` (또는 `nvidia/Gemma-4-26B-A4B-NVFP4`) `--quantization modelopt` 여부는 카드 확인. 앵커: `Qwen/Qwen3-8B`.
시간 예산 2h. 부팅+준비 15분을 넘기면 AMI 굽기를 다음 주 첫 과제로.

## 0. 로컬 (세션 전날)
```bash
cd <repo>
# ShareGPT (필요 시): https://huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered  ShareGPT_V3_unfiltered_cleaned_split.json
infra/up.sh g7_2x 1 --hours 3          # 온디맨드, 3h 자동 종료 (AZ us-east-1b)
```

## 1. 노드 준비 (ssh ubuntu@<ip>)
```bash
mkdir -p ~/pd && cd ~/pd && git clone --depth 1 https://github.com/vllm-project/vllm.git vllm-src   # 커밋 해시 기록
# 하네스·데이터 복사 (로컬에서): rsync -av harness configs data/traces ubuntu@<ip>:~/pd/
docker run -d --name vllm --gpus all --ipc=host --network host -v ~/.cache/huggingface:/root/.cache/huggingface -v ~/pd:/pd \
  -e HF_TOKEN=$HF_TOKEN vllm/vllm-openai:v0.30.0 \
  RedHatAI/gemma-4-26B-A4B-it-NVFP4 --max-model-len 32768 --gpu-memory-utilization 0.90 --max-num-batched-tokens 2048 \
  --kv-cache-dtype auto --limit-mm-per-prompt '{"image":0}' \
  --max-num-seqs 256 --seed 0 --port 8000
docker logs -f vllm | grep -m1 "Application startup complete"
curl -s localhost:8000/v1/models | head -c 200
bash harness/env_snapshot.sh results/env_A.json              # peer 없음
export MODEL=RedHatAI/gemma-4-26B-A4B-it-NVFP4 BASE_URL=http://127.0.0.1:8000 RESULTS_DIR=/pd/results ENV_JSON=/pd/results/env_A.json \
       SHAREGPT_JSON=/pd/data/ShareGPT_V3_unfiltered_cleaned_split.json TRACES_DIR=/pd/data/traces
cd ~/pd   # run_bench.sh는 여기서. 사이드 수집기(sar/dmon/prom)는 호스트에서 돌고 결과는 같은 폴더
# bench serve는 컨테이너 안에서 실행. 하네스가 `vllm`을 부르면 래퍼가 docker exec로 넘김:
mkdir -p ~/.local/bin && ln -sf ~/pd/harness/vllm-docker.sh ~/.local/bin/vllm && export PATH=~/.local/bin:$PATH
# 결과 경로는 컨테이너 기준 /pd/... 이므로 RESULTS_DIR=/pd/results 로 두고 호스트에서는 ~/pd/results 로 본다
```
KV bytes/token 확인: `docker logs vllm | grep -i "GPU KV cache size\|Maximum concurrency"` → RESULTS에 기록(26B-A4B 80 KB/tok 예상, 슬라이딩 층 제외 여부 확인). 같은 방식으로 Gemma 4 12B BF16(24GB, KV 3GB 예상)·FP8, Qwen3-8B BF16도 기동해 값만 기록(각 5분).

## 2. 단일 스텝 시간 → SLO 확정 (5분)
```bash
harness/run_bench.sh A B1 N0 random inf --max-concurrency 1 --num-prompts 20 --random-input-len 1024 --random-output-len 512
python3 analysis/analyze.py results/*_A_B1_N0_random_rinf/bench.json      # tbt_p50_ms = 단일 스텝
# SLO: chat tbt = 5×step, doc tbt = 25×step  → export SLO_CHAT_TBT SLO_DOC_TBT (ms), analyze.py --slo 에 사용
```

## 3. ShareGPT 스윕, 청크 2048 (≈25분)
```bash
for r in 0.5 1 2 4 6 8; do harness/run_bench.sh A B1 N0 sharegpt $r; done
harness/run_bench.sh A B1 N0 sharegpt inf --num-prompts 300              # 최대 처리량 참고값
python3 analysis/analyze.py results/*_A_B1_N0_sharegpt_*/bench.json --slo chat=ttft:1000,tbt:$SLO_CHAT_TBT --slo doc=ttft:3000,tbt:$SLO_DOC_TBT --csv results/A_sharegpt_c2048.csv
```
SLO가 깨지는 요청률이 8 밑에서 안 보이면 12, 16 추가. 0.5에서 이미 깨지면 0.25 추가.

## 4. 청크 8192로 재기동 후 3 반복 (≈25분)
```bash
docker rm -f vllm && (위 docker run에서 --max-num-batched-tokens 8192) && for r in 0.5 1 2 4 6 8; do CHUNK=8192 harness/run_bench.sh A B1c8k N0 sharegpt $r; done
```

## 5. 합성 일부 (≈20분) — prefix caching 끔 (`--no-enable-prefix-caching`로 재기동, 청크 2048)
```bash
for L in 4096 16384; do for r in 0.25 0.5 1; do harness/run_bench.sh A B1 N0 random $r --random-input-len $L --random-output-len 512; done; done
```

## 6. Azure-conv 재생 (≈10분)
```bash
TRACE_SEC_MULT=0.002 harness/run_bench.sh A B1 N0 azure_conv self --num-prompts 600    # 2배 느리게, 첫 600요청(≈4분)
```
원 트레이스 5.5 req/s는 A10G 1대에 과부하 → 배율 0.002~0.004로. 실효 req/s를 RESULTS에.

## 7. 정리
```bash
rsync -av ubuntu@<ip>:~/pd/results/ ./results/ ; infra/down.sh
```
RESULTS.md §A: 단일 스텝 ms, SLO 값, 스윕 표(csv), 최대 처리량, KV bytes/tok, 마찰.
