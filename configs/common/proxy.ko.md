# 프록시

## P1 (vLLM 저장소 toy proxy)
```bash
git clone --depth 1 https://github.com/vllm-project/vllm.git /opt/vllm-src   # 커밋 해시를 env에 기록
python3 /opt/vllm-src/tests/v1/kv_connector/nixl_integration/toy_proxy_server.py \
  --port 8000 --prefiller-hosts $PREFILL_IP --prefiller-ports 8100 --decoder-hosts $DECODE_IP --decoder-ports 8200
```
(옵션명은 커밋에 따라 다를 수 있음. `--help`로 확인. 다중 decoder를 받는지도 여기서 확인 → 열린 질문 5)

## B2 (라운드로빈)
toy proxy가 라운드로빈 모드를 지원하지 않으면 `harness/rr_proxy.py`(aiohttp, 30줄)를 쓴다. 두 구성 모두 같은 클라이언트 노드에서 프록시를 돌린다.

## 프록시 오버헤드 검증 (B2, 단계 B 첫 일)
같은 부하를 (a) 프록시 경유 (b) 인스턴스 직접 으로 두 번 재서 goodput 차이 5% 이내 확인. 결과는 RESULTS.md에.
