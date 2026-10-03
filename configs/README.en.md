*English translation of `README.md`; the Korean file is the original.*

# configs

vllm serve flags and proxy commands. Common to every configuration: `--max-model-len 32768 --gpu-memory-utilization 0.90 --max-num-batched-tokens ${CHUNK:-2048} --seed 0 --disable-log-requests`.

| File | Configuration |
|---|---|
| `b1.env` | Single instance, chunked prefill (B1). Each replica in B2 is identical |
| `p1_prefill.env` | P1 prefill: `--kv-transfer-config '{"kv_connector":"NixlConnector","kv_role":"kv_producer"}'` + `VLLM_NIXL_SIDE_CHANNEL_HOST=<own ip> PORT=5600 UCX_TLS=tcp UCX_NET_DEVICES=all` |
| `p1_decode.env` | P1 decode: `kv_role=kv_consumer`, same env |
| `proxy.md` | Commands to run toy_proxy_server.py (P1) / round robin (B2). Procedure for the 5% check with and without the proxy in B2 |
| `tc.md` | Bandwidth equalization and sweep commands such as `tc qdisc add dev ens5 root tbf rate 5gbit burst 64mb latency 50ms`, and how to remove them |
note: use rsync -R so data/traces keeps its path

## Files

English translations of the Korean documents in this folder:

- `README.en.md`: this file
- `E8_RUNBOOK.en.md`: run order for round E8 (review response)
- `models.en.md`: model candidate matrix and per-instance test matrix
- `proxy.en.md`: proxy commands (vLLM's test proxy for P1, round robin for B2)
- `sat_A.en.md`: Saturday round A command sheet (g7.2xlarge x1)
- `sess_Aprime.en.md`: round A′, large-model startup check (g7e.2xlarge x1)
- `sess_P.en.md`: round P, two-node plumbing (g5.xlarge x2)
- `tc.en.md`: tc bandwidth equalization / sweep
