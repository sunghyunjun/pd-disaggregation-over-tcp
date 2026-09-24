# 세션 P · 2노드 배관 (g5.xlarge ×2, 8 vCPU 쿼타) · 1h · 약 $2

목적: P1(prefill→decode, NixlConnector over TCP)이 노드 간에 끝까지 도는지, 하네스 전체 경로(run_bench.sh → result.json)가 동작하는지, B2 라운드로빈 경로가 동작하는지. **숫자는 참고만**(GPU 작고 네트워크 burst 타입).
모델: `Qwen/Qwen3-1.7B`(BF16 3.4 GB, 토큰 불필요). 이미지: `vllm/vllm-openai:v0.30.0`(kv_connectors 요구사항에 nixl==1.4.1 포함 — 1단계에서 확인).

## 0. 로컬 (시작 5분 전)
```bash
cd <repo>
AWS_PROFILE=default infra/up.sh g5_xl 2 --hours 2
# 출력의 gpu_public_ips / gpu_private_ips 를 적어 둔다
export A_PUB=<gpu0 public> B_PUB=<gpu1 public> A_PRIV=<gpu0 private> B_PRIV=<gpu1 private>
for h in $A_PUB $B_PUB; do rsync -az harness configs ubuntu@$h:~/pd/; done
```
user-data가 docker pull(약 10 GB)과 iperf3 서버를 띄운다. `ssh ubuntu@$A_PUB 'tail -2 /var/log/user-data.log; docker images | grep vllm'`로 완료 확인(부팅 후 5~8분).

## 1. 두 노드 공통 확인 (각 3분)
```bash
ssh ubuntu@$A_PUB
nvidia-smi -L
docker run --rm --entrypoint python3 vllm/vllm-openai:v0.30.0 -c "import vllm, nixl; print(vllm.__version__, 'nixl ok')"
iperf3 -c $B_PRIV -P 1 -t 10 | tail -3      # 단일 흐름 (A→B). B에서는 -c $A_PRIV
iperf3 -c $B_PRIV -P 4 -t 10 | tail -3      # 4흐름
ping -c 5 $B_PRIV | tail -1
bash ~/pd/harness/env_snapshot.sh ~/pd/results/env_P_A.json $B_PRIV
```
기록: nixl import 성공 여부, iperf 단일/4흐름 Gbps, RTT. (예상: 단일 2.5~5, 4흐름 5~10, RTT 0.1~0.3 ms)

**nixl import가 실패하면** (공식 이미지가 `INSTALL_KV_CONNECTORS=true`로 빌드되지 않은 경우): 컨테이너 기동 후 설치.
```bash
# 2단계의 docker run 뒤에, startup 전이라도:
docker exec vllm pip install "nixl==1.4.1"        # UCX 포함 휠. 실패하면 마찰 로그 1호
docker restart vllm
```
또는 미리 파생 이미지: `echo 'FROM vllm/vllm-openai:v0.30.0\nRUN pip install nixl==1.4.1' | docker build -t vllm-nixl -` 후 이미지명을 vllm-nixl로.

## 2. P1 기동 (노드 A = prefill, 노드 B = decode) (10분)
노드 A:
```bash
docker run -d --name vllm --gpus all --ipc=host --network host -v ~/pd:/pd -v ~/.cache/huggingface:/root/.cache/huggingface \
  -e VLLM_NIXL_SIDE_CHANNEL_HOST=$A_PRIV -e VLLM_NIXL_SIDE_CHANNEL_PORT=5600 -e UCX_TLS=tcp -e UCX_NET_DEVICES=all \
  vllm/vllm-openai:v0.30.0 Qwen/Qwen3-1.7B --port 8100 --max-model-len 8192 --gpu-memory-utilization 0.85 --seed 0 \
  --kv-transfer-config '{"kv_connector":"NixlConnector","kv_role":"kv_producer"}'
docker logs -f vllm 2>&1 | grep -m1 -i "startup complete"
```
노드 B: 같은 명령에서 `HOST=$B_PRIV`, `--port 8200`, `"kv_role":"kv_consumer"`.

프록시(이번만 노드 A에서; vLLM 저장소의 toy proxy):
```bash
git clone --depth 1 --branch v0.30.0 https://github.com/vllm-project/vllm.git ~/pd/vllm-src
pip3 install --user fastapi uvicorn httpx 2>/dev/null
python3 ~/pd/vllm-src/tests/v1/kv_connector/nixl_integration/toy_proxy_server.py --host 0.0.0.0 --port 8000 \
  --prefiller-hosts $A_PRIV --prefiller-ports 8100 --decoder-hosts $B_PRIV --decoder-ports 8200 &
```
## 3. 요청 1개 왕복 (5분) ← 이 세션의 관문
```bash
curl -s localhost:8000/v1/completions -H 'Content-Type: application/json' \
  -d '{"model":"Qwen/Qwen3-1.7B","prompt":"The capital of France is","max_tokens":32}' | head -c 400
docker logs vllm 2>&1 | grep -i -E "nixl|transfer|kv_transfer" | tail -5     # A와 B 모두
```
통과: 완성 텍스트가 돌아오고, B 로그에 원격 KV 읽기(READ/transfer) 흔적. 실패 시 로그 전체 저장(`docker logs vllm > ~/pd/results/P_fail_A.log`) 후 종료 → 평일에 분석.

## 4. 하네스 전체 경로 (10분)
노드 A에서:
```bash
mkdir -p ~/.local/bin && ln -sf ~/pd/harness/vllm-docker.sh ~/.local/bin/vllm && export PATH=~/.local/bin:$PATH
export MODEL=Qwen/Qwen3-1.7B BASE_URL=http://127.0.0.1:8000 RESULTS_DIR=/pd/results ENV_JSON=/pd/results/env_P_A.json
cd ~/pd && harness/run_bench.sh P P1 N0 random 1 --random-input-len 1024 --random-output-len 128 --num-prompts 60
python3 harness/analyze.py results/*_P_P1_*/bench.json
```
통과: result.json 생성, analyze 표 출력, prom.txt/sar.txt/dmon.txt가 비어 있지 않음. bench serve가 컨테이너 안에서 프록시(호스트 8000)에 닿는지가 포인트(--network host라 됨).

## 5. B2 경로 (10분)
두 노드 컨테이너를 `--kv-transfer-config` 없이 각각 `--port 8100`으로 재기동(`docker rm -f vllm` 후). 노드 A에서:
```bash
python3 ~/pd/harness/rr_proxy.py --port 8000 --upstreams http://$A_PRIV:8100 http://$B_PRIV:8100 &
harness/run_bench.sh P B2 N0 random 1 --random-input-len 1024 --random-output-len 128 --num-prompts 60
```
## 6. 종료
```bash
rsync -az ubuntu@$A_PUB:~/pd/results/ ./results/ ; rsync -az ubuntu@$B_PUB:~/pd/results/ ./results/
AWS_PROFILE=default infra/down.sh
AWS_PROFILE=default aws ec2 describe-instances --filters Name=instance-state-name,Values=running --query 'Reservations[].Instances[].InstanceId' --output text   # 비어 있어야 함
```
## 기록할 것 (PLAN §6 마찰 로그 · RESULTS.md §P)
- nixl import 여부, toy proxy 옵션 실제 동작, 요청 왕복 성공 여부, B 로그의 전송 흔적
- iperf 단일/4흐름, RTT, 1K 프롬프트 KV 전송 시간(로그에 찍히면)
- 막힌 지점과 에러 원문
