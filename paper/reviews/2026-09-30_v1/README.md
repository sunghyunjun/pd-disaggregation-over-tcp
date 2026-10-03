# 영어 원고 v1 모의 심사 2차 (2026-09-30)

## English summary

Round 2, on English draft v1 (private commit cbac960, 22 pages), after measurement round E8 (47 runs) and the change of framing to "tune the chunk and disaggregation together". Same five roles plus a meta-reviewer; each reviewer first checked whether its round-1 points had been addressed. Scores (round 1 to round 2): systems 2 to 3, methods 3 to 4, network 3 to 3.5, reproducibility 3 to 3.5, writing 3 to 4; meta verdict: moderate revision, publishable without new measurements. Two new artifacts were found, both against the replicas: the replica proxy's default aiohttp connector capped concurrent connections at 100 (every TTFT failure of 1,024-token replicas at 4–5 requests/s per GPU arrived while 100 or more requests were in flight), and the 26B "4 against 3" verdict rested on an asymmetric number of repeats. Mechanism corrections: NIXL's split rule, the shared fifth connection, the 19–21 Gbps aggregate for 31B, the UCX seven-variable set being 5–10% slower than the segment sizes alone, and the one-token rule's effect on 31B. The meta-reviewer listed 15 required edits and an optional round E9 (first priority: 26B at a 512-token chunk), which the author ran with predictions committed in advance. Reviews and scripts are in Korean.

대상: `paper/en/main.tex` v1(커밋 cbac960, 22쪽). 1차 심사(`../2026-09-30_v0/`) 뒤 세션 E8(47런)을 더해 "청크 프리필과 분리를 함께 조정한다"로 방향을 바꾼 판.
방식: 1차와 같은 역할의 심사 에이전트 5명 + 좌장 1명. 각 심사자는 자기 1차 지적의 반영 여부를 먼저 대조했다. 저장소는 읽기만 했다.

| 파일 | 역할 | 점수(1차 → 2차) |
|---|---|---|
| r1_systems.md | 서빙 시스템 | 2 → 3 |
| r2_methods.md | 측정·통계 | 3 → 4 |
| r3_network.md | 네트워크·클라우드 | 3 → 3.5 |
| r4_repro.md | 재현성 | 3 → 3.5 (논문 수치 4.5, 패키징 2) |
| r5_writing.md | 글쓰기·그림 | 3 → 4 |
| r6_chair.md | 좌장 | 중폭 수정, 새 측정 없이 공개 가능 |
| scripts/ | 심사자·좌장 분석 스크립트 | r6/r6_proxycap.py, r6/r6_xfer.py는 저자 측이 다시 돌려 확인 |

## 좌장 판정 요지
- 방향("청크를 조정한 복제본 앞에서 TCP 분리는 더 많이 처리하지 못했다")은 v1보다 단단해졌다. 새로 드러난 두 산물이 모두 복제본에 불리했다.
  - 복제본 프록시(`harness/rr_proxy.py`)가 aiohttp 기본 커넥터라 동시 연결 100개 상한. 분리용 `pd_proxy.py`는 무제한. 청크 1,024 복제본의 GPU당 4·5건 TTFT 실패는 전부 진행 중 100개 이상일 때 도착한 요청(33/33, 393/393), 간격 실패 0(저자 측 재확인).
  - 26B 4K "4 대 3"은 반복 수 비대칭(복제본 1런, 1P1D 3런). 같은 시드로는 둘 다 통과 → 동률.
- 경계값과 기제 서술 수정 필요:
  - 30–40 ms "분리만 가능" 칸은 측정하지 않은 1,024 미만 청크에 기댄다.
  - 전송: NIXL은 1,024 디스크립터 미만을 나누지 않는다(26B 4K 2–3조각, 31B 4K 4조각, 대화 크기는 한 연결). 다섯째 연결은 공유 워커. 31B는 연결 넷이 모두 움직여도 합계 19–21 Gbps. "연결 수가 남은 지렛대" 철회. m은 판정 부하에서 0.92–1.14, 31B 대화 0.81(저자 측 재확인).
  - 7변수 UCX 묶음은 세그먼트만 바꾼 것보다 5–10% 낮음(수신 창 고정).
  - 31B 대화 1P1D "4"는 1토큰 규칙 변경이 두 런을 뒤집은 결과 → "≈4, 경계", 규칙 변경 공개.
  - 프록시 GC 귀속은 26B 1P1D E8 한정, 2P1D 귀속 철회, 31B 정지는 서버 쪽.
- 필수 수정 A 15건, 선택 측정 E9(1순위 26B 청크 512), 반박 D 12건, 초록 재작성안(r6/abstract_v2.txt).
