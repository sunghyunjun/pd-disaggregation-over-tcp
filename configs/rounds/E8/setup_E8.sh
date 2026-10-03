#!/usr/bin/env bash
# Round E8 preparation (run on the local Mac). Same order as setup_e7.sh: wait for client init -> copy harness, data and token -> download models on each GPU node.
# Usage: C=<client public IP> NODES="<GPU public IP> <GPU public IP>" bash configs/setup_E8.sh
set -u
: "${C:?}" "${NODES:?}"
S="ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15"
cd <repo>
log(){ echo "[$(date -u +%T)] $*"; }
log "waiting for client init"
until $S ubuntu@$C 'test -f /var/log/user-data.log' 2>/dev/null; do sleep 15; done
$S ubuntu@$C '~/venv/bin/python -c "import vllm;print(\"client vllm\",vllm.__version__)"'
$S ubuntu@$C 'mkdir -p ~/pd/results ~/pd/data/traces ~/pd/vllm-src/tests/v1/kv_connector/nixl_integration ~/.cache/huggingface; test -f ~/.ssh/id_ed25519 || ssh-keygen -q -t ed25519 -N "" -f ~/.ssh/id_ed25519; ~/venv/bin/pip install -q fastapi uvicorn httpx >/dev/null 2>&1; echo proxy-deps-ok'
rsync -az harness/ ubuntu@$C:~/pd/harness/ && rsync -az configs/ ubuntu@$C:~/pd/configs/ && rsync -az third_party/ ubuntu@$C:~/pd/third_party/ && rsync -az data/traces/ ubuntu@$C:~/pd/data/traces/
scp -q third_party/toy_proxy_server_v0.30.0.py ubuntu@$C:~/pd/vllm-src/tests/v1/kv_connector/nixl_integration/toy_proxy_server.py
scp -q ~/.config/pd-hf-token ubuntu@$C:~/.cache/huggingface/token && $S ubuntu@$C 'chmod 600 ~/.cache/huggingface/token'
$S ubuntu@$C '~/venv/bin/python -c "
from huggingface_hub import hf_hub_download
p=hf_hub_download(\"anon8231489123/ShareGPT_Vicuna_unfiltered\",\"ShareGPT_V3_unfiltered_cleaned_split.json\",repo_type=\"dataset\",local_dir=\"/home/ubuntu/pd/data\")
import os;print(\"ShareGPT\",os.path.getsize(p))"'
PUB=$($S ubuntu@$C 'cat ~/.ssh/id_ed25519.pub')
log "client ready"
for h in $NODES; do (
  until $S ubuntu@$h 'cloud-init status 2>/dev/null | grep -q done' 2>/dev/null; do sleep 10; done
  $S ubuntu@$h "grep -qF '$PUB' ~/.ssh/authorized_keys || echo '$PUB' >> ~/.ssh/authorized_keys; mkdir -p ~/pd/results"
  rsync -az harness/ ubuntu@$h:~/pd/harness/ && rsync -az third_party/ ubuntu@$h:~/pd/third_party/
  scp -q ~/.config/pd-hf-token ubuntu@$h:~/.hf_token && $S ubuntu@$h 'chmod 600 ~/.hf_token'
  $S ubuntu@$h 'pip install -q --user "huggingface_hub[cli]" hf_transfer >/dev/null 2>&1
    export PATH=$HOME/.local/bin:$PATH HF_HUB_ENABLE_HF_TRANSFER=1 HF_TOKEN=$(cat ~/.hf_token)
    for m in nvidia/Gemma-4-26B-A4B-NVFP4 nvidia/Gemma-4-31B-IT-NVFP4 RedHatAI/gemma-4-26B-A4B-it-FP8-dynamic; do hf download $m >/dev/null 2>~/dl_err.log && echo "  $m ok" || echo "  $m failed"; done
    docker image inspect vllm/vllm-openai:v0.30.0 >/dev/null 2>&1 && echo "  image ok" || echo "  image missing"
    du -sh ~/.cache/huggingface | sed "s/^/  cache /"'
  log "$h node ready"
) & done
wait
log "SETUP DONE"
