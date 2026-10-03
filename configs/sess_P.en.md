*English translation of `sess_P.md`; the Korean file is the original.*

# Round P · Two-node plumbing (g5.xlarge ×2, 8 vCPU quota) · 1h · about $2

> **Completed 2026-09-24.** Results in RESULTS.md §P. What changed from the sheet below: `UCX_TLS=tcp,cuda_copy,cuda_ipc`, proxy dependencies are installed by user-data, `RESULTS_DIR` (host) and `RESULTS_DIR_IN_CONTAINER=/pd/results` are separated, the proxy is started with `setsid nohup ... < /dev/null & disown`.

Purpose: confirm that P1 (prefill→decode, NixlConnector over TCP) runs end to end across nodes, that the full harness path (run_bench.sh → result.json) works, and that the B2 round-robin path works. **Numbers are for reference only** (small GPU, burst-type network).
Model: `Qwen/Qwen3-1.7B` (BF16 3.4 GB, no token needed). Image: `vllm/vllm-openai:v0.30.0` (the kv_connectors requirements include nixl==1.4.1; confirm in step 1).

## 0. Local (5 minutes before start)
```bash
cd <repo>
AWS_PROFILE=default infra/up.sh g5_xl 2 --hours 2
# write down gpu_public_ips / gpu_private_ips from the output
export A_PUB=<gpu0 public> B_PUB=<gpu1 public> A_PRIV=<gpu0 private> B_PRIV=<gpu1 private>
for h in $A_PUB $B_PUB; do rsync -az harness configs ubuntu@$h:~/pd/; done
```
user-data runs docker pull (about 10 GB) and starts an iperf3 server. Confirm completion with `ssh ubuntu@$A_PUB 'tail -2 /var/log/user-data.log; docker images | grep vllm'` (5~8 minutes after boot).

## 1. Checks common to both nodes (3 minutes each)
```bash
ssh ubuntu@$A_PUB
nvidia-smi -L
docker run --rm --entrypoint python3 vllm/vllm-openai:v0.30.0 -c "import vllm, nixl; print(vllm.__version__, 'nixl ok')"
iperf3 -c $B_PRIV -P 1 -t 10 | tail -3      # single flow (A→B). On B, use -c $A_PRIV
iperf3 -c $B_PRIV -P 4 -t 10 | tail -3      # 4 flows
ping -c 5 $B_PRIV | tail -1
bash ~/pd/harness/env_snapshot.sh ~/pd/results/env_P_A.json $B_PRIV
```
Record: whether nixl import succeeds, iperf single-flow / 4-flow Gbps, RTT. (Expected: single 2.5~5, 4 flows 5~10, RTT 0.1~0.3 ms)

**If nixl import fails** (the official image was not built with `INSTALL_KV_CONNECTORS=true`): install after starting the container.
```bash
# after the docker run in step 2, even before startup:
docker exec vllm pip install "nixl==1.4.1"        # wheel includes UCX. If it fails, friction log entry 1
docker restart vllm
```
Or build a derived image in advance: `echo 'FROM vllm/vllm-openai:v0.30.0\nRUN pip install nixl==1.4.1' | docker build -t vllm-nixl -` and then use vllm-nixl as the image name.

## 2. Start P1 (node A = prefill, node B = decode) (10 minutes)
Node A:
```bash
docker run -d --name vllm --gpus all --ipc=host --network host -v ~/pd:/pd -v ~/.cache/huggingface:/root/.cache/huggingface \
  -e VLLM_NIXL_SIDE_CHANNEL_HOST=$A_PRIV -e VLLM_NIXL_SIDE_CHANNEL_PORT=5600 -e UCX_TLS=tcp -e UCX_NET_DEVICES=all \
  vllm/vllm-openai:v0.30.0 Qwen/Qwen3-1.7B --port 8100 --max-model-len 8192 --gpu-memory-utilization 0.85 --seed 0 \
  --kv-transfer-config '{"kv_connector":"NixlConnector","kv_role":"kv_producer"}'
docker logs -f vllm 2>&1 | grep -m1 -i "startup complete"
```
Node B: same command with `HOST=$B_PRIV`, `--port 8200`, `"kv_role":"kv_consumer"`.

Proxy (this time on node A; vLLM's test proxy from the vLLM repository):
```bash
git clone --depth 1 --branch v0.30.0 https://github.com/vllm-project/vllm.git ~/pd/vllm-src
pip3 install --user fastapi uvicorn httpx 2>/dev/null
python3 ~/pd/vllm-src/tests/v1/kv_connector/nixl_integration/toy_proxy_server.py --host 0.0.0.0 --port 8000 \
  --prefiller-hosts $A_PRIV --prefiller-ports 8100 --decoder-hosts $B_PRIV --decoder-ports 8200 &
```
## 3. One request round trip (5 minutes) ← the gate of this round
```bash
curl -s localhost:8000/v1/completions -H 'Content-Type: application/json' \
  -d '{"model":"Qwen/Qwen3-1.7B","prompt":"The capital of France is","max_tokens":32}' | head -c 400
docker logs vllm 2>&1 | grep -i -E "nixl|transfer|kv_transfer" | tail -5     # on both A and B
```
Pass: completion text comes back, and B's log shows a remote KV read (READ/transfer). On failure, save the full log (`docker logs vllm > ~/pd/results/P_fail_A.log`) and shut down → analyze on a weekday.

## 4. Full harness path (10 minutes)
On node A:
```bash
mkdir -p ~/.local/bin && ln -sf ~/pd/harness/vllm-docker.sh ~/.local/bin/vllm && export PATH=~/.local/bin:$PATH
export MODEL=Qwen/Qwen3-1.7B BASE_URL=http://127.0.0.1:8000 RESULTS_DIR=/pd/results ENV_JSON=/pd/results/env_P_A.json
cd ~/pd && harness/run_bench.sh P P1 N0 random 1 --random-input-len 1024 --random-output-len 128 --num-prompts 60
python3 harness/analyze.py results/*_P_P1_*/bench.json
```
Pass: result.json is created, the analyze table prints, and prom.txt/sar.txt/dmon.txt are not empty. The point is whether bench serve inside the container reaches the proxy (host port 8000); it does because of --network host.

## 5. B2 path (10 minutes)
Restart both node containers without `--kv-transfer-config`, each on `--port 8100` (after `docker rm -f vllm`). On node A:
```bash
python3 ~/pd/harness/rr_proxy.py --port 8000 --upstreams http://$A_PRIV:8100 http://$B_PRIV:8100 &
harness/run_bench.sh P B2 N0 random 1 --random-input-len 1024 --random-output-len 128 --num-prompts 60
```
## 6. Shutdown
```bash
rsync -az ubuntu@$A_PUB:~/pd/results/ ./results/ ; rsync -az ubuntu@$B_PUB:~/pd/results/ ./results/
AWS_PROFILE=default infra/down.sh
AWS_PROFILE=default aws ec2 describe-instances --filters Name=instance-state-name,Values=running --query 'Reservations[].Instances[].InstanceId' --output text   # must be empty
```
## What to record (PLAN §6 friction log · RESULTS.md §P)
- Whether nixl imports, whether the test proxy options actually work, whether the request round trip succeeds, transfer traces in B's log
- iperf single-flow / 4-flow, RTT, KV transfer time for a 1K prompt (if it appears in the log)
- Where it got stuck and the verbatim error text
