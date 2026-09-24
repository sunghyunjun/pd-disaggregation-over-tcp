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
| P1 producer/consumer 기동 | 1차 실패: `UCX_TLS=tcp`만 주면 `ucx_utils.cpp:582 VRAM memory is detected as host by UCX` → `nixl_agent registerMem failed`. **`UCX_TLS=tcp,cuda_copy,cuda_ipc`로 해결 시도** (로그 `results/P/P_fail_*_ucx_tcp_only.log`) |
| 요청 1개 왕복 | (대기) |
| run_bench.sh 전체 경로 | (대기) |
| B2 라운드로빈 경로 | (대기) |
