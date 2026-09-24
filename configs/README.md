# configs

vllm serve 플래그와 프록시 명령. 모든 구성에서 공통: `--max-model-len 32768 --gpu-memory-utilization 0.90 --max-num-batched-tokens ${CHUNK:-2048} --seed 0 --disable-log-requests`.

| 파일 | 구성 |
|---|---|
| `b1.env` | 단일 인스턴스, chunked prefill (B1). B2의 각 복제본도 동일 |
| `p1_prefill.env` | P1 prefill: `--kv-transfer-config '{"kv_connector":"NixlConnector","kv_role":"kv_producer"}'` + `VLLM_NIXL_SIDE_CHANNEL_HOST=<own ip> PORT=5600 UCX_TLS=tcp UCX_NET_DEVICES=all` |
| `p1_decode.env` | P1 decode: `kv_role=kv_consumer`, 같은 env |
| `proxy.md` | toy_proxy_server.py 실행(P1) / 라운드로빈(B2) 명령. B2에서 프록시 유무 5% 검증 절차 |
| `tc.md` | `tc qdisc add dev ens5 root tbf rate 5gbit burst 64mb latency 50ms` 등 대역폭 등화·스윕 명령과 해제 |
