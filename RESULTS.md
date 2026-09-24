# RESULTS

원자료는 `results/<session>/`. 이 파일은 표와 판정만. 숫자는 result.json에서 스크립트로 뽑는다.

## P · 2노드 배관 (2026-09-24, g5.xlarge ×2, us-east-1b, vLLM v0.30.0, NIXL 1.4.1)

### 네트워크 실측 (iperf3 8s, ping 5회)
| 방향 | 단일 흐름 Gbps | 4흐름 Gbps | RTT ms |
|---|---|---|---|
| A→B | 4.97 | 9.13 / 9.91 (2회) | 0.17 |
| B→A | 4.97 | 9.94 | 0.16 |

판정: **단일 TCP 흐름 5 Gbps 상한이 그대로 관찰됨**(인스턴스 명목 "up to 10", 기준 2.5). 4흐름은 burst 상한 10 근처. 이 값이 §9.5의 전제.

### 배관 체크
| 항목 | 결과 |
|---|---|
| 공식 이미지에 NIXL 포함 | O (nixl 1.4.1, INSTALL_KV_CONNECTORS=true 빌드) |
| 호스트에 toy proxy 의존성(fastapi·httpx·uvicorn) | X → `pip3 install --user` 필요 (user-data에 추가) |
| P1 producer/consumer 기동 | 1차 실패: `UCX_TLS=tcp`만 주면 `ucx_utils.cpp:582 VRAM memory is detected as host by UCX` → `nixl_agent registerMem failed`. **`UCX_TLS=tcp,cuda_copy,cuda_ipc`로 해결됨** (로그 `results/P/P_fail_*_ucx_tcp_only.log`). 양쪽 startup complete, NixlPullConnector, KV cache 128,512 tokens(1.7B, 0.85) |
| 요청 1개 왕복 | **O**. toy proxy(A:8000) → prefill A:8100 → decode B:8200. 5토큰 프롬프트, 32토큰 생성, 왕복 0.64 s. B 로그: `NIXL compatibility check passed`, `Transfer plan: tp_ratio=1, num_kv_heads=8`, `KV Transfer metrics: Num successful transfers=1, Avg xfer time (ms)=37.951, Avg post time (ms)=0.693` |
| run_bench.sh 전체 경로 | **O** (호스트/컨테이너 경로 분리 `RESULTS_DIR_IN_CONTAINER` 추가 후). result.json + prom/sar/dmon 수집 확인 |
| B2 라운드로빈 경로 | **O** (`harness/rr_proxy.py`, aiohttp). toy proxy는 P1 전용 |
| analyze.py | 버그 수정: vLLM은 성공 요청의 errors를 `""`로 저장 → `not e`로 판정 |

### 참고 측정 (숫자는 배관 검증용. Qwen3-1.7B, 입력 1024·출력 128, 1 req/s, 60요청, N0, 클라이언트=노드 A)
| 구성 | TTFT p50/p90 ms | TBT p50/p99 ms | 멈춤 요청 비율 | 출력 tok/s | 채팅형 달성률 | 문서형 달성률 |
|---|---|---|---|---|---|---|
| P1 (A prefill → B decode, TCP) | 434 / 1113 | 9.5 / 48.2 | 0.45 | 124 | 0.65 | 1.0 |
| B2 (복제본 2, 라운드로빈) | 54 / 87 | 8.8 / 10.6 | 0.13 | 125 | 1.0 | 1.0 |

KV 전송(디코드 로그, 1024토큰 = 112 MB/요청 = 112 KB/tok · Qwen3-1.7B 28층×8헤드×128×2×2B):
| 10s 창 | 전송 수 | 평균 xfer ms | P90 xfer ms | MB/s |
|---|---|---|---|---|
| 1 | 11 | 336 | 502 | 334 |
| 2 | 13 | 454 | 698 | 246 |
| 3 | 8 | 718 | 1051 | 156 |

관찰(가설 아님, 배관용 1점): 1 req/s·1K 입력에서도 전송 처리량이 156~334 MB/s(1.2~2.7 Gbps)로 단일 흐름 상한 5 Gbps에 못 미치고, 부하가 쌓이면 xfer 시간이 늘어난다(대기열). P1의 TTFT p50이 B2의 8배. 이 규모에서는 PD가 명백히 손해. 본 측정에서 요청당 고정 비용(핸드셰이크)과 대역폭 비례 성분을 분리해야 함 → E7 F7의 절편.

### 세션 P 결론
- 배관 5항목 모두 통과. 세션 B(g7 ×2)는 승인 당일 시작 가능.
- 마찰 1건(UCX_TLS). 문서 PR 후보.
- 소요: 인스턴스 2대 × 약 25분. 비용 약 $1.


## A′ · g7e.2xlarge ×1 큰 모델 기동 검증 (2026-09-24, RTX PRO 6000 96 GB, driver 580.126, vLLM v0.30.0)

| 모델 · 정밀도 | 기동 | 가중치 로드 | KV 캐시 토큰 | 32K 동시 | 단일 스텝 ms (1K in / 256 out, conc 1) | TTFT p50 ms (1K) | 비고 |
|---|---|---|---|---|---|---|---|
| Gemma 4 31B NVFP4 (nvidia) | O (`/root/.cache/vllm` 마운트 필요, 마찰 #2). **NixlConnector producer로도 기동 O** (Registering KV_Caches, LBHNC) | 96.7 s, 디스크 32.7 GB | 209,266 | 6.39 | **25.1** (p99 25.5) | 109 | Available KV cache memory 50.43 GiB → **258.8 KB/tok (vLLM 계정 기준)**; config 계산값 320은 슬라이딩층 계정 방식 차이로 재검토. 채팅형 TBT SLO = 125 ms, 문서형 = 630 ms |
