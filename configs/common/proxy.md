*English translation of `proxy.md`; the Korean file is the original.*

# Proxy

## P1 (vLLM's test proxy from the vLLM repository)
```bash
git clone --depth 1 https://github.com/vllm-project/vllm.git /opt/vllm-src   # record the commit hash in env
python3 /opt/vllm-src/tests/v1/kv_connector/nixl_integration/toy_proxy_server.py \
  --port 8000 --prefiller-hosts $PREFILL_IP --prefiller-ports 8100 --decoder-hosts $DECODE_IP --decoder-ports 8200
```
(Option names may differ by commit. Check with `--help`. Also check here whether it accepts multiple decoders → open question 5)

## B2 (round robin)
If the test proxy does not support a round-robin mode, use `harness/rr_proxy.py` (aiohttp, 30 lines). In both configurations the proxy runs on the same client node.

## Proxy overhead check (B2, first day of stage B)
Measure the same load twice, (a) through the proxy and (b) directly against the instance, and confirm that the goodput difference is within 5%. Results go in RESULTS.md.
