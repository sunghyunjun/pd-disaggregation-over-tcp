# 종합 심사 (3차, 원고 v2)

대상: "Chunked Prefill or Disaggregation? Prefill–Decode Serving over TCP on Single-GPU Cloud Instances" (paper/en/main.tex, draft v2, 2026-10-01, 25쪽)
근거: 3차 리뷰 5건(r1_systems 4/5, r2_methods 4/5, r3_network 4/5, r4_repro 3.5/5[수치 4.5, 패키징 1.5], r5_writing 4/5)과 그 스크립트, 1·2차 기록(paper/reviews/2026-09-30_v0/, _v1/), 종합 심사자 직접 확인. 저장소는 읽기만 했다.
종합 심사자 확인 스크립트(이 폴더의 `r6/`, 읽기 전용):
- `m1_spot.py`: 결정점의 런별 달성률, TTFT 중앙값, TPOT, ITL 중앙값(26B NVFP4, 26B FP8, 31B 대화)
- `m2_cells.py`: 그림 4 아래 줄의 칸별 양쪽 최선 구성, 요청률, 절단 여부, 굿풋 비율
- `m3_relaxed.py`: 26B 완화 칸(TTFT 3·5 s × 간격 100–300 ms)에서 1P1D 계열과 복제본의 요청률별 달성률
- `abstract_v3.txt`: 5절 초록 최종안(200단어, `wc -w` 기준)
- 인라인으로 확인한 것: `configs/run_E9.sh`·`lib_E9.sh`·`results/E9/run_E9.log`의 UCX 설정, `results/E8/ss/*.txt`의 wscale, `make_figures_v2.py`의 `ss_active()`(그림 5c 지표), 예측 문단과 실행 스크립트의 8775497 이후 불변(`git diff`), 계정 ID가 든 파일·커밋(값은 적지 않는다), 리뷰 뒤 생긴 커밋 dd15bd7(E9 포함 요청별 캐시), 그림 A9 값
표기: **[확인]**은 종합 심사자가 원자료로 다시 계산한 값이다. **[R1]** 등은 해당 리뷰어가 보고했고 종합 심사자가 다시 계산하지 않은 값이다. 둘 이상의 리뷰어가 따로 계산해 일치한 값은 [R1·R3]처럼 적는다.

기준: 실무자가 인용할 독립 프리프린트(Zenodo DOI, 이후 arXiv 가능). "반드시 고칠 것"은 틀렸거나, 오해를 부르거나, 공개하지 않았거나, 재현을 막는 것으로 한정한다. 저자는 다음 단계로 영어를 교정하고 공개한다. 추가 AWS 측정은 결론을 바꿀 수 있을 때만 권한다.

---

## 1. 판정

**소폭 수정(minor revision). 새 측정은 필요 없다. 2절 A 항목을 반영하면 저자의 영어 교정을 거쳐 공개할 수 있다.**

- 결론의 방향은 선다. 청크를 조정한 복제본 앞에서 TCP 분리가 더 많이 처리한 SLO는 없었다. 분리는 복제본의 청크가 2,560에 묶였을 때만 이겼다. 다섯 리뷰어 모두 이 방향을 받아들였다. 판정 규칙을 반복 평균 규칙으로 바꾸거나 동률 띠를 격자 한 칸(0.75–1.33)으로 넓혀도 분리 우세 칸은 생기지 않는다(R1·R2 따로 재계산).
- E9는 사전 커밋한 계획대로 19런을 재실행 없이 모두 실었다. 수치 158개 대조에서 E9 수치는 전부 원자료와 맞았고, 파이프라인은 CSV와 figures.json을 바이트 단위로 다시 만든다(R4).
- 남은 문제는 세 종류다.
  1. 범위: 헤드라인 문장이 순위를 매기지 못한 칸, 26B에만 해당하는 3배, 1P1D가 통과하지 못한 부하의 TTFT까지 덮는다.
  2. 공개 누락과 기제 서술 오류: P 청크 8,192 런의 UCX 설정, 31B 대화 전송의 분할, 7변수 묶음의 기제, "structural" 문장, 그림 5(c).
  3. 사전 등록 채점과 증거 보존, 공개 패키징.
- 모두 원고·그림 수정, 기존 데이터 재집계, 파일 정리로 끝난다. 어느 것도 결론의 방향을 바꾸지 않는다. 몇몇 정정(1P1D의 경계 표기, P 8,192 런의 느린 전송)은 오히려 분리 쪽에 유리했던 조건을 드러내므로 결론을 보수적으로 만든다.

### 1.1 쟁점별 판정

**(a) "no SLO cell favors disaggregation"의 범위: 선다. 단, "순위를 매길 수 있었던 SLO"로 한정한다.**
- 그림 4 아래 줄 192칸 [확인, figures.json·`m2_cells.py`]: 복제본 우세 76, 복제본만 충족 23, 둘 다 불충족 8, 판정 불가 85, 분리 우세·분리만 충족 0. 판정 불가는 26B NVFP4 9칸, 26B FP8 48칸, 31B 대화 28칸이다(R1·R2와 일치).
- **종합 심사자의 새 확인: 26B 판정 불가 9칸 가운데 8칸은 실제로는 동률이다.**
  - 대상은 TTFT 3·5 s × 간격 100–300 ms 칸이다. 분리 쪽 최선은 E8 aiohttp 1P1D의 GPU당 5 단일 런이다(TTFT 3 s·간격 100 ms에서 0.926). 이 구성을 GPU당 5까지만 쟀기 때문에 "절단"으로 분류됐다.
  - 그런데 같은 서빙 구성(1P1D, P 청크 2,560)은 GPU당 6에서 시험 프록시로 TTFT 중앙값 14.6 s, 이 칸들의 달성률 0.046–0.100으로 무너졌다 [확인, `m3_relaxed.py`]. 프리필 대기열의 발산이므로 프록시 종류와 무관하다.
  - 청크 1,024 복제본도 GPU당 5 통과, 6 실패다. 격자 위에서는 둘 다 5이고, 굿풋 비율 0.91–0.98은 동률 띠(0.8–1.25) 안이다.
  - `slo_sensitivity.GROUPS`가 같은 구성을 프록시·세션별로 나눴기 때문에 절단으로 보였다. R1은 이 칸들에서 "분리가 같거나 더 많이 처리할 가능성이 배제되지 않는다"고 했지만, GPU당 6의 실패로 "분리 우세"(비율 ≥1.25, 약 GPU당 6.25 이상 필요)는 사실상 배제된다.
- 따라서 정확한 요약은 이렇다. 192칸 중 99칸은 복제본이 더 많이 처리했거나 혼자 충족했다. 8칸은 둘 다 불충족, 8칸은 동률이다. 77칸(FP8 48, 31B 28, 26B 1)은 측정한 요청률 안에서 순위를 매길 수 없다. 분리가 더 많이 처리한 칸은 없다.
- 26B의 "복제본 우세" 47칸 중 12칸은 비율이 0.7955–0.7967이다(GPU당 5 대 4, 격자 한 칸) [확인]. 방향은 튼튼하지만 크기는 격자 한 칸이다.
- 판정: "no SLO we could rank favored disaggregation"은 선다. "replicas served more / at least as much in every SLO we tested"는 쓰지 않는다(A1).

**(b) "3×"의 범위: 26B NVFP4 4K에만 해당한다(3 대 1 req/s/GPU).** FP8과 31B 대화에서는 청크 2,560 복제본이 어떤 측정 부하도 지키지 못했으므로 배수가 정의되지 않는다(분리만 충족). 도입부의 "near 2,500 tokens"는 "at 2,560 tokens"다(A2).

**(c) TTFT 비교 범위: 방향은 맞고 괄호 수치가 틀렸다.**
- 양쪽이 모두 통과한 부하만 모으면 복제본 78–247 ms, 1P1D 255–384 ms다. R2와 R4가 따로 계산해 일치했고, 종합 심사자가 26B(청크 512–1,536, GPU당 1–3), FP8(194–247 대 362–384), 31B(78–93 대 255–308, 시험 프록시가 탈락한 GPU당 4는 aiohttp 값만)의 개별 값을 대조했다 [확인].
- 원고의 359(청크 512)와 477–526(1P1D)은 1P1D가 통과하지 못한 26B GPU당 4의 값이다.
- RQ3·결론의 "always … the first token later"에는 "median"을 붙인다(A13-1).

**(d) P 청크 8,192 런의 UCX 설정: 공개 누락이며 필수로 고친다.**
- `configs/run_E9.sh` 25행 `UCXSET=SEG`, `lib_E9.sh` 19행(TX/RX 세그먼트 256k만), `run_E9.log`의 "ucx=SEG pchunk=8192" [확인]. 예측 커밋에는 "P 청크 8,192 + UCX 세그먼트만"이 적혀 있고 원고에만 없다. §3.1과 부록 C는 이 런까지 7변수를 썼다고 읽힌다.
- 이 런은 P 청크와 UCX 묶음을 함께 바꿨다. 같은 시드에서 전송은 오히려 느렸다(GPU당 4 평균 165–190 대 119–140 ms, m 0.65–0.81) [R1·R3·R4]. 따라서 TTFT 감소는 프리필 쪽 몫이다.
- GPU당 5에서는 P가 따라가는 대신 KV 전송이 쌓였다(평균 약 0.92 s, E8 P 2,560에서 0.18 s) [R1·R3]. 이때 제공된 KV 트래픽은 11.7 Gbps였다(10 req/s × 140 MiB, 산술).
- 판정은 바뀌지 않는다. 그러나 "부하에서는 전송이 대기열이 된다"는 RQ2의 답에 들어가야 한다(A3).

**(e) 31B 1P1D 경계 표기: 비대칭이며 필수로 고친다.**
- GPU당 4의 값은 aiohttp 세 런 0.924, 0.903, 1.000이고, 시험 프록시 네 런에는 0.885가 있다 [확인].
- E8 두 런은 E8 뒤 채택한 1토큰 규칙 전에는 0.899, 0.878이었다. 곧 이 "통과"는 프록시 선택과 사후 규칙 두 가지에 기댄다. 둘 다 분리에 유리한 쪽이다.
- 26B처럼 "borderline"으로 표기하고, 수치 정의("a repeat between 0.85 and 0.95")를 §3.6에 둔다. 표 2의 1P1D 열이 aiohttp 값임을 적는다(A4).

**(f) 청크 512의 TTFT·처리량 비용과 절차 문구: 필수로 고친다.**
- 청크 512의 TTFT 중앙값 [확인]:
  - GPU당 1–3: 205–235 ms. 청크 2,048–2,560보다 약 70–80 ms 늦다.
  - GPU당 4: 359 ms. 청크 1,024는 200 ms다. p99는 1.13 s 대 0.39–0.46 s다.
  - GPU당 4의 실패 1.5%는 전부 TTFT다 [R1].
- 청크 512는 GPU당 5를 재지 않았다. 절차 2의 "cost at most about 80 ms of median TTFT and no supported load"는 GPU당 3까지만 맞고, 512의 지원 부하에 대해서는 검증되지 않았다. 저자 자신의 예측 1도 "청크가 작아 프리필 처리량이 줄어 1,024보다 높지는 않음"이었다.
- 절차는 "스택이 허락하는 가장 작은 청크"가 아니라 "간격 한도에 맞는 가장 큰 청크"를 권해야 한다(A5).
- R1이 추정한 청크 512의 처리 한계(약 4.5 req/s/GPU)는 선형 맞춤의 추정이다. 본문 수치로 쓰지 않는다(C3).

**(g) 디코드 노드의 "structural" 주장: 26B에서는 근거가 틀렸다. 필수로 고친다.**
- 원고의 중앙 ITL(15.5 대 13.2, 20.8 대 15.9 ms)은 재현된다 [확인]. 그러나 복제본 ITL은 이봉 분포다. 디코드만 싣는 짧은 스텝이 많고 청크를 실은 긴 스텝이 드물어 중앙값만 낮다.
- 판정에 닿는 지표는 반대 방향을 가리킨다 [확인]:
  - 평균 ITL(TPOT): GPU당 3에서 1P1D 15.7 대 복제본 16.7 ms, 4에서 20.5–20.9 대 20.7–20.9 ms로 같다.
  - 요청별 최대 간격 중앙값: 1P1D가 더 짧다. GPU당 3에서 27.6 대 33.8 ms, 4에서 33.8–35.5 대 36.4–37.2 ms다.
- 26B 1P1D가 GPU당 4에서 떨어진 원인은 간격의 전형값이 아니다. TTFT 꼬리(p99 0.97–1.25 s 대 0.39–0.46 s)와 드문 디코드 서버 정지다.
- 구조 비용은 31B 대화에서만 보인다. GPU당 4에서 TPOT가 1P1D 32.3–33.4 대 복제본 30.3 ms다 [확인]. P GPU의 SM 활성률은 32–41%, D는 100%다 [R1, dmon].
- 이 정정은 결론 문장도 더 정확하게 만든다. 분리는 격리 이득을 실제로 냈다(최대 간격이 더 짧다). 그러나 조정한 청크가 이미 한도 안에 들어와 그 이득이 부하로 바뀌지 않았다(A6).
- 이 지표는 R1이 2차에 제안했고 이번에 스스로 정정했다.

**(h) 31B 대화의 NIXL 분할: 원고가 적은 규칙과 스스로 어긋난다. 필수로 고친다.**
- 원고가 쓴 디스크립터 구조(26B 4K 2,240 = 전역 5층 × 128 + 슬라이딩 25층 × 64)를 31B(전역 10층, 슬라이딩 50층)에 적용하면, 약 290토큰부터 1,024 디스크립터를 넘는다 [확인, 산술]. 26B는 약 590토큰부터다.
- 31B 대화 전송의 31–35%(바이트 기준 75–80%)가 나뉜다 [R3]. "which are not split"은 틀렸다. m은 "about 0.8 (0.78–0.85 across sessions)"로 쓴다(A7).

**(i) 7변수 UCX 기제: 원고 두 곳이 서로 다르고, 둘 다 기제를 빗나간다. 필수로 고친다.**
- E8 ss에서 7변수 두 런만 D 쪽 수신 창 배율이 2다. 두 런 모두 wscale 7,2이고, 세그먼트만·기본 런은 7,7이다 [확인]. 광고할 수 있는 창의 상한은 262,140 B다.
- §4.5는 "fixes the socket buffers at 8 MB, which disables autotuning"이라고 쓰고, 부록 C는 "capped by the kernel's maximums"라고 쓴다. 둘을 "8 MB를 요청했으나 커널 한도에 잘렸고(한도 값은 기록 없음), 연결 시점에 수신 창 배율이 2로 정해졌다"로 통일한다. 배율 2는 관측이고, 한도에 잘렸다는 것은 추론이다.
- 31B의 19–21 Gbps "shared per-node limit"도 이 묶음에서만 관측됐다. 조건을 붙인다(A8).

**(j) 그림 5(c): 2차 필수 항목이 그대로 남았다. 필수로 고친다.**
- 코드상 지표는 "연속한 두 소켓 표본(약 0.12 s) 사이에 64 KiB 넘게 움직인 연결 수의 분포이며, 한 연결이라도 움직인 표본만 센다"이다 [확인, `ss_active()`]. 다섯째 공유 연결은 세지 않는다.
- 제목 "Four connections per P–D pair", 캡션 "Share of transfer time … every 0.1 s", 본문 "kept all four busy 64% of the time"은 이 지표와 다르다. TCP busy 기록으로는 31B 전송 중 데이터가 걸려 있던 연결이 평균 1.94개다 [R3].
- 윗제목 "(0.5 and 0.25 requests/s)"는 합계다(A9).

**(k) 사전 등록 채점: "four of five held"는 후하다. 필수로 고친다.**
- 예측 4의 셋째 부분("GPU당 4, 시드 10000은 경계 0.85–0.95")이 1.000으로 빗나갔다 [확인]. RESULTS.md 결과표도 이 칸에 ✅도 ✗도 달지 않았다.
- 정확한 요약: 셋은 시험한 범위에서 맞았다. 넷째는 두 판정이 맞았으나 수치 범위가 빗나갔다. 다섯째는 빗나갔다. 두 빗나감은 방향이 반대다(4에서는 1P1D가 예측보다 잘했고, 5에서는 못했다). 예측 1의 "1,024보다 높지 않다"는 GPU당 5를 재지 않아 시험되지 않았다.
- 예측 문단과 `run_E9.sh`·`lib_E9.sh`·`rr_proxy.py`·`pd_proxy.py`는 8775497 뒤 바뀌지 않았다 [확인]. 커밋은 2026-09-30 13:29 UTC이고, 세션 스크립트는 46분 뒤, 첫 측정은 50분 뒤에 시작했다 [R1·R2].
- 다만 저장소에 원격이 없어 시각은 자체 기록이다. 계정 ID가 든 커밋 e03d4de가 8775497의 조상이라, 이력을 정리하면 해시가 바뀐다 [확인](A10, 6절).

### 1.2 주장별 상태

| 주장 | 상태 |
|---|---|
| 청크가 복제본 정지를 정한다(26B 4K 48 → 21 ms) | 유지 |
| 상한을 푼 청크 1,024 복제본 GPU당 5 통과, 6 붕괴(서버 포화) | 유지 [확인; 서버 지표는 R1] |
| 26B 1P1D GPU당 3 통과, 4 경계, 5 붕괴 | 유지 |
| 31B 대화 복제본 ≥8 대 1P1D 4 | 유지. "4 (borderline, aiohttp proxy)"로 쓴다 |
| 복제본 프록시 상한이 지원 부하를 한 칸 낮췄다 | 유지. 상한이 간격을 줄이기도 했다는 사실을 덧붙이면 통과 런까지 뺀 규칙이 정당해진다(B4) |
| 약 3배 | 26B NVFP4 4K로 한정 |
| 어떤 SLO에서도 분리가 더 많이 처리하지 않았다 | "순위를 매길 수 있었던 SLO에서"로 한정하고 칸 수를 공개 |
| 조정한 복제본이 첫 토큰을 항상 먼저 | "median"을 붙이고 범위를 78–247 대 255–384 ms로 |
| 저부하에서 추가 TTFT의 61–85%가 전송 | 유지. 31B 283 ms의 통계 정의만 밝힌다 |
| UCX 세그먼트로 3.4배 | "at low load"를 붙인다 |
| 세그먼트만이 7변수보다 5–10% 빠르다 | 저부하로 한정. 부하에서 세그먼트만 쓴 유일한 런은 교란돼 있다 |
| 판정 부하에서 m 0.92–1.14 | P 8,192 런(0.65–0.81)과 31B 대화(약 0.8)를 함께 적고 통계를 밝힌다 |
| 31B 대화 전송은 나뉘지 않는다 | 철회 |
| 1P1D의 간격 비용은 구조적이다 | 26B에서는 철회, 31B 대화로 한정 |
| 청크 512–1,024는 TTFT 80 ms 이하·지원 부하 손실 없음 | GPU당 3까지로 한정. 512는 4까지만 측정 |
| E9 예측 넷 적중 | "셋 적중, 하나 부분 적중, 하나 빗나감" |
| 식 (2)로 배포 전에 추정할 수 있다 | "roughly, at low load" |
| 분리의 이득은 청크 프리필도 주는 것이다 | "chunked prefill bounds, rather than removes, …"로 |

---

## 2. A. 반드시 고칠 것

모든 항목은 원고·그림·파일 수정이다. 새 측정은 없다. 영문 문안은 저자가 교정할 초안이다. 수치는 [확인] 또는 둘 이상의 리뷰어가 일치한 값만 문안에 넣었다.

### A1. 헤드라인을 "순위를 매길 수 있었던 SLO"로 한정하고 칸 수를 공개한다 (R1-1, R2-1, R5-3, 1.1(a))
- 초록: 5절 최종안.
- §1 "In short" 문안: "... and no SLO that our measured rates could rank favored disaggregation over TCP against replicas with a tuned chunk. Disaggregation won only against replicas held at 2,560 tokens (about 3× for 26B with 4K inputs)."
- §4.4 끝에 추가:
  > Of the 192 cells in the bottom row, replicas served more or alone met the SLO in 99, neither side met it in 8, and none favored disaggregation. In eight 26B cells (TTFT 3–5 s, gaps of 100 ms or more) both sides passed 5 and failed 6 requests/s per GPU (1P1D's prefill queue diverged at 6, median TTFT 14.6 s), so we count them as ties. The remaining 77 cells, 48 of them 26B FP8, which we measured only up to 1 request/s per GPU, could not be ranked. In 12 of the 26B cells where replicas served more, the margin was one step of our rate grid (5 against 4 requests/s per GPU).
- 민감도 한 문장(부록 D 또는 F): "With a mean-over-repeats rule, or with the equivalence band widened to one rate step (0.75–1.33), no cell favors disaggregation."
- 그림 4 캡션: "Hatched: at least one side still passed at its highest measured rate, so the ratio could not be placed in one category. Ratios are disaggregated ÷ replica SLO goodput." 동률 8칸은 그림에 표시하거나 캡션에 적는다. 코드로 처리하려면 같은 서빙 구성의 프록시 변형을 절단 판정에서만 합친다(B6).
- RQ3·결론의 "served no more in/under any SLO we tested"도 같은 한정어로 고친다.

### A2. "3×"를 26B 4K로 한정한다 (R4 #3, R5-3)
- 초록·§1·RQ3·결론: "about 3× for 26B with 4K inputs (3 against 1 request/s per GPU); for 26B FP8 and 31B chat, 2,560-token replicas met the strict SLO at no measured load".
- 도입부 "held near 2,500 tokens" → "held at 2,560 tokens".

### A3. P 청크 8,192 런의 UCX 설정을 공개하고, 부하에서의 전송 사실을 넣는다 (R1-3, R2-8, R3-1, R4 #22)
- §3.1: "... seven UCX environment variables (Appendix C), except the three E9 runs with an 8,192-token prefill chunk, which set only the two segment sizes."
- 부록 C: "used in sessions E4–E9 except those runs". 그림 3 범례, 부록 D의 예측 5, 표 F1 행 라벨에 "segment sizes only"를 붙인다.
- §4.3 문안:
  > Raising the prefill chunk to 8,192 tokens, in runs that also set only the UCX segment sizes, cut 1P1D's median TTFT at 4 requests/s per GPU from about 500 to 416–451 ms. Its transfers were slower than with the seven-variable set at the same seeds (165–190 against 119–140 ms on average), so the gain came from the prefill side. The verdicts did not change (0.874 and 0.976 at 4, 0.365 at 5). At 5 the prefill node kept up, and KV transfers queued instead (mean 0.92 s against 0.18 s with a 2,560-token prefill chunk) at an offered KV traffic of 11.7 Gbps. Because these runs changed two settings, we do not attribute the slowdown.
- §4.5의 m:
  - "0.92–1.14 for 26B at 3–4 requests/s per GPU (0.65–0.81 in the 8,192-token prefill runs)"로 쓰고, 31B 대화 값은 A7대로 고친다.
  - 한 문장을 더한다: "Under load, the time vLLM reports includes waiting for other transfers, so m there describes the queue rather than the link."
  - m의 정의에 통계(10 s 창 중앙값인지 전송 가중 평균인지)를 적는다. 그림 6 캡션의 31B 283 ms도 같은 통계로 맞춘다. 전송 가중 평균이면 297.6 ms다 [R3·R4].
- 절차 3:
  - "(it fell to about 1 in our runs)" → "(0.65–1.14 at the loads we tested)".
  - 한 줄을 더한다: "Check that the offered KV traffic, request rate × V(L), stays well below m × C_flow measured at that load; our 26B pair queued transfers at 11.7 Gbps offered."
- RQ2 끝: "Queueing adds to it under load; when the prefill node kept up, transfers queued instead."
- 결론: "a KV transfer that can be estimated before deployment" → "a KV transfer that can be roughly estimated at low load".
- 절차 4: "(send and receive together, without pinning socket buffers)" 뒤에 "; we compared the two settings only at low load"를 붙인다.

### A4. 경계 표기를 대칭으로 하고 수치로 정의한다 (R1-7, R2-3, R4 #86·#92, R5-4)
- §3.6: "we call a point borderline if any repeat falls between 0.85 and 0.95".
- 표 2:
  - 1P1D 열 머리를 "1P1D (aiohttp proxy)"로 바꾼다.
  - 31B 칸은 "4 (borderline)" 또는 "4†"로 쓰고, 캡션에 "† borderline (a repeat within 0.85–0.95); with vLLM's test proxy 1P1D failed at 4 (0.885)"를 넣는다.
  - FP8 행에는 약속한 TTFT를 채우거나 비운 이유를 적는다.
  - 31B 복제본 "≥8"은 GPU당 8 한 런이고, GPU당 6 런은 상한 도달로 주의 데이터라는 점을 캡션에 적는다.
- 초록: "for 31B chat, borderline at 4 against at least 8".
- §4.3: "while 1P1D passed 4 narrowly with our aiohttp proxy (0.903, 0.924, and 1.000) but not with the test proxy (0.885–0.963 in four runs), and failed at 6 (0.765)".
- §3.5의 1토큰 규칙 문장 끝: "under the earlier rule, 1P1D's two E8 runs at 4 would have failed (0.899 and 0.878)".

### A5. 청크 크기 절차와 RQ1의 비용 서술을 고친다 (R1-2, R2-6, R5-3)
- RQ1: "... at a median TTFT cost of about 30 ms at 1,024 tokens and 70 ms at 512 (1 request/s per GPU), without losing supported load down to 1,024 tokens; 512 tokens passed up to 4, the highest rate we measured for it." 근거: 청크 1,024는 161 대 132 ms(GPU당 1), 167–168 대 136 ms(2) [확인].
- 절차 1 끝: "Measure it at the load you plan to serve: at a 1,024-token chunk the median longest gap grew from 28 ms at 1 request/s per GPU to 42–43 ms at 5." [확인]
- 절차 2 문안:
  > Use the largest chunk whose longest gap fits the limit, not the smallest the stack allows, and check that the stack allows it (for Gemma 4 in vLLM v0.30.0, disable every modality). A smaller chunk spreads each prefill over more steps, which raises TTFT and lowers the prefill rate a replica sustains. In our 26B runs, 1,024 tokens added about 30 ms of median TTFT and passed 5 requests/s per GPU; 512 tokens added 70–80 ms up to 3 and reached 359 against 200 ms at 4, and we did not test it above 4. For 31B chat, 256 tokens left median TTFT unchanged.
- (선택) 절차 3에 R1의 두 조건을 식으로 넣는다. 꽉 찬 스텝 시간 t(c)가 간격 한도 이하이고, ⌈L/(c − B)⌉·t(c)와 대기의 합이 TTFT 한도 이하여야 한다(B는 실행 중 디코드 수). 두 조건을 함께 만족하는 c가 없는 곳이 분리를 검토할 영역이다. 16K 이상 입력이 왜 남은 영역인지도 이 식이 설명한다.

### A6. "structural" 문장과 결론의 이득 문장을 고친다 (R1-4, R5-3, 1.1(g))
- §4.3 문안(수치 [확인], SM 활성률은 [R1]):
  > At equal GPU count, 1P1D's decode node carries the decodes of both GPUs. For 26B with 4K inputs this did not lengthen the gaps that decide the SLO: at 3 and 4 requests/s per GPU its mean inter-token latency (15.7 and 20.5–20.9 ms) matched that of 1,024-token replicas (16.7 and 20.7–20.9 ms), and its median longest gap was shorter (27.6 against 33.8 ms at 3), because no prefill entered its decode steps. It failed at 4 on the TTFT tail (p99 0.97–1.25 s against 0.39–0.46 s) and on rare decode-server pauses (Section 4.7). For 31B chat the fixed 1:1 split was unbalanced: short prompts kept the prefill GPU busy only 32–41% of the time, and at 4 requests/s per GPU the decode node's mean inter-token latency was 32–33 ms against 30 ms for 256-token replicas.
- RQ2의 "and the decode node's doubled batch adds to the gaps" → "; for 31B chat, the fixed 1:1 split left the prefill GPU mostly idle while the decode node ran slower steps".
- §5.3의 "the decode node's doubled batch" → "the fixed split between the phases".
- 결론 문안:
  > Its benefit is real: with no prefill in its decode steps, 1P1D's longest gaps were shorter than those of 1,024-token replicas. But chunked prefill bounds, rather than removes, the prefill work in each step, and with a well-chosen chunk that bound met every gap limit we could rank, so isolation bought no extra load while the transfer and the prefill queue lengthened TTFT.

### A7. NIXL 분할 서술과 31B 대화의 m을 고친다 (R3-2, R3 권장 8, R4 #115)
- 분할 규칙: "splits the list only when it holds at least 1,024 descriptors, in pieces of at least 1,024" → "into pieces of max(N/4, 1,024) descriptors, the last one smaller, so a list of fewer than 1,024 descriptors goes out as one piece".
- "a chat-sized transfer as a single piece" → "a transfer under 1,024 descriptors (26B inputs under about 590 tokens, 31B under about 290) as a single piece on a shared connection".
- "31B chat transfers, which are not split, reached 0.81" → "31B chat transfers, about a third of which (three quarters of the bytes) were split, mostly into one 1,024-descriptor piece and a small remainder, ran at about 0.8 (0.78–0.85 across sessions)".
- "about 1,900–2,240 descriptors"는 저부하 값이라고 적는다. 부하에서는 10 s 창 평균이 1,100–2,240이었다 [R3].

### A8. 7변수 묶음의 기제를 고치고 한 가지로 맞춘다 (R3-3, 1.1(i))
- §4.5 문안:
  > The full set of seven UCX variables gave 13.5–14.2 Gbps, 5–10% lower: it requested 8 MB socket buffers, the kernel capped them (we did not record its limits), and the receiver's TCP window scale was fixed at 2 when the connection opened, capping the window at 256 KiB. The sender was limited by the receive window for about 40% of its busy time.
- 부록 C의 마지막 문장을 같은 내용으로 바꾼다.
- 부록 B 함정: "Setting UCX_TCP_SNDBUF/RCVBUF above the kernel's limits pins a small TCP window scale at connection time; raise net.core.rmem_max and wmem_max first, or leave them unset."
- 공유 상한 문장: "With the seven-variable set, under which the sender was receive-window-limited even with four connections active, 31B transfers aggregated 19–21 Gbps, ... which points to a shared limit that we did not identify."

### A9. 그림 5(c)와 64% 문장을 고친다 (R3-4, R5, 2차 A7 잔여, 1.1(j))
- 제목: "(c) Connections moving data per sample".
- 캡션: "Share of socket samples (about 0.12 s apart, longer than a 26B transfer of 73–93 ms) in which 1–4 of the four worker connections moved more than 64 KiB, among samples in which any moved; the shared fifth connection is not counted."
- 본문: "in 64% of the samples taken during 31B transfers all four connections moved data; by TCP's busy counters about two connections had data outstanding at a time".
- 윗제목 "(0.5 and 0.25 requests/s)" → "(b, c) at 0.25 and 0.125 requests/s per GPU". (a)는 iperf라 부하가 없다.
- (b)는 7변수 두 런 중 aiohttp 런(14.16)임을 캡션에 적는다. "bars are medians"는 "black lines are medians"로 쓰고, x 라벨 겹침을 푼다.
- (c)의 파랑(26B)과 주황(31B)은 논문 전체의 색 의미(파랑 = 복제본, 주황 = 분리)와 충돌한다. 두 계열 모두 분리 전송이므로 주황 두 명도에 빗금을 더해 구분한다(녹색약 독자를 위해 명도와 무늬로 이중 부호화).

### A10. 사전 등록 서술과 채점을 고친다 (R1-6, R2-2, R4 #153·P1, R5-7, 1.1(k))
- 부록 D 마지막 항목 문안:
  > Session E9's predictions (five items) were committed to our then-private repository at 13:29 UTC on 30 September 2026, together with the run scripts, which did not change afterwards; the session started 46 minutes later. The timestamps are recorded by git on our machine and are not externally anchored. Three predictions held as far as we tested them. In the fourth, both verdicts held (31B replicas passed 8 requests/s per GPU and 1P1D failed at 6), but the seed-10000 1P1D run at 4 reached 1.000 rather than the predicted 0.85–0.95. The fifth (1P1D with an 8,192-token prefill chunk passing 4) did not hold (0.874 and 0.976). The two misses went in opposite directions. The prediction that 512-token replicas would not exceed 1,024-token ones was not tested above 4 requests/s per GPU.
- 예측, 측정값, 적중 여부를 담은 작은 표를 별도 부록 항목으로 둔다(R2 표: 하위 예측 16개 중 12 적중, 2 빗나감, 1 일부 미시험, 1 반증 불가). 지금처럼 "Deviations" 목록 끝에 두면 이탈 사항처럼 읽힌다(R5).
- 해시는 6절대로 공개 저장소의 새 해시를 쓰고, "(8775497 in our private repository)"를 괄호로 둔다.
- §4.6 "so the repository cannot prove their order" → "so the repository does not record their order".
- 부록 D 제목의 "pre-registered protocol"에 각주를 단다: "Protocol v1.7, committed to our local repository on 24 September 2026 before the first session; not externally timestamped."
- RESULTS.md(공개 전, 결과 절만 고치고 예측 문단은 건드리지 않는다):
  - 예측 4의 시드 10000 칸에 ✗를 단다.
  - FP8 행의 "30 ms는 0.5·1 모두 1.000"과 해석 절의 "FP8은 GPU당 1건까지 30 ms 1.000"을 "0.5에서 1.000, 1에서 0.958"로 고친다 [확인].
  - E8 절의 "청크 1,024 복제본 지원 부하 GPU당 4건", "청크 256이면 GPU당 6건"에 해당 런이 지금은 주의 데이터라는 주석을 단다.

### A11. 그림 3이 판정과 어긋나게 읽히지 않게 한다 (R5-1)
- 판정 규칙(모든 반복 ≥0.9)으로 통과하지 못한 점은 속 빈 마커로 그리고, 캡션에 "hollow: some repeat below 0.9"를 넣는다. 해당 점은 26B 1P1D aiohttp GPU당 4(평균 0.944), P 8,192 GPU당 4(0.925), 31B 시험 프록시 GPU당 4(0.935)다. 선을 반복 최솟값으로 잇는 방법도 있다.
- x = 4에서 계열을 조금씩 어긋나게 둬 최소–최대 막대가 보이게 한다. (b) FP8은 세 계열이 1.0에 겹치므로 "all three at 1.00"을 패널에 적는다.
- 캡션에 선 모양(dotted 2,560 / solid 1,024 / dash-dot 512 또는 256)과 "8,192-token prefill runs: UCX segment sizes only"를 넣는다.
- 시험 프록시 선이 4에서 6으로 바로 잇는 구간(5 미측정)을 캡션에 적는다.

### A12. 옛 결론의 흔적을 지운다 (R5-2, R5-3, R5-8)
- 그림 A9: 제목을 조건만 담게 바꾼다(예: "4K input, 0.5 requests/s per GPU, 2,560-token replicas").
- §4.8 문안: "Against 2,560-token replicas, 1P1D reached 0.83–1.00 and the replicas 0.02–0.97 across GPUs (Appendix Figure A9); only g7e passed for either, and we did not test smaller chunks on g6e or g7." [확인, figures.json fig06]
- §4.4 제목 "Where each approach wins"는 아래 줄에 분리가 이기는 칸이 없으므로 주장형으로 바꾼다(예: "No SLO we could rank favors disaggregation against a tuned chunk").
- 부록 그림 A2·A3·A9 범례의 "Replicas (2)"를 "Replicas (2), chunk 2,560"으로 바꾼다.
- 결론·RQ3의 세 문장은 A3(추정), A6(이득), A13-1(median)대로 고친다.

### A13. 수치·사실 정정 묶음 (R1, R2, R3, R4, R5; 모두 원고 한두 줄)
1. §4.3 TTFT: "At every load where both passed, tuned replicas had a lower median TTFT (78–247 ms against 255–384 ms for 1P1D); at 4 requests/s per GPU for 26B, where 1P1D was borderline, 200–359 against 416–526 ms." RQ3·결론의 "always … later" → "its median TTFT was always higher".
2. §3.2: "chat requests of a few hundred tokens moved 28–30 MB" → "chat requests (median input about 100 tokens, mean about 230) moved 25–26 MiB on average, as Eq. (1) predicts from their input lengths" [R3·R4].
3. §3.3·한계: "Eleven replica runs before E9 reached the cap; two were already caution data at the client's limit, and we mark the other nine as caution." §3.6의 주의 사유: "(two of them replica runs that also reached the connection cap)" [R2·R4].
4. §3.6 워밍업: "raised attainment by at most 0.019, lowered it by at most 0.029, and flipped no verdict" [R2·R4].
5. §3.6: "Points well above 0.9 varied by at most 0.03 within a session".
6. 한계: "Decisive points have one to four runs".
7. 그림 1 캡션: "7 disaggregated runs (2 of them caution)".
8. 그림 2 캡션: 2,560 점의 합산은 (a)(c)만이고 (b) FP8은 E7 한 런이다. "The 512-token points come from E9"를 넣는다.
9. §4.2의 31B 구간은 캡션의 런 집합과 맞춘다. 5런이면 42%, 12%, 800토큰 초과 1 of 323이고, E5·E7 4런이면 43%다 [R4]. "none" → "almost none (1 of 323)". 스크립트는 A16-4.
10. §4.7 전역 정지:
    - 규모: "zero to five times per run, 15–115 in-flight requests (typically 35–110) paused together for 50–80 ms" [R4].
    - "then received a burst of tokens"는 GC형 사건에만 붙인다.
    - 같은 시드 서버형 사건은 "most likely a server-side pause"로 쓴다. 31B에서는 같은 시드 10000이 시험 프록시 0.885, aiohttp 1.000이므로 "tied to the request sequence"로 일반화하지 않는다.
11. §4.7 GC 문단에 판정 영향을 한 문장 넣거나, 절 제목을 "proxies that distort the measurement"로 바꾼다. 기여 3은 다음처럼 고친다: "four pitfalls that changed our conclusions" → "that can change a verdict", "the reference proxy" → "vLLM's test proxy for NIXL", "pauses all streams" → "paused all streams in our runs".
12. §3.3·부록 B: "the check passes only when images, audio, and video are all disabled" → "it accepts smaller chunks with every modality disabled; with only images disabled it rejects them, and we did not test other combinations". RQ3의 "with video input enabled"도 "with audio and video input enabled"로 고친다.
13. §3.1: "a 32,768-token context (16,384 for the 31B FP8 cross-GPU runs of E1)".
14. §3.4: ShareGPT 출력 중앙값을 "24–177"로 쓰거나 예외를 적는다. ShareGPT에 채팅 템플릿을 적용하지 않았고 출력 길이를 참조 길이로 고정했다는 사실을 한 줄 넣는다(R2의 세 번째 요청).
15. 표 1: g7의 "Used for"에 "bandwidth limit, cross-GPU comparison"을 더한다. g7 가격 "--"는 값을 채우거나 이유를 적는다.
16. 부록 표:
    - 번호: 부록 E의 표는 E1, 부록 F의 표는 F1이다. `\thesection`으로 번호를 붙인다.
    - 표 F1 캡션: "Attainment with TTFT ≤1 s and the listed gap limit".
    - 행 라벨: "1P1D test proxy (E7, E8)"로 고치고, 시드 8007이 두 번 들어 있음을 적는다. "26B 4K"는 "26B NVFP4, 4K"로 쓴다.
    - 결정점을 추가한다. 30 ms의 청크 512 GPU당 3과 1P1D GPU당 3, 그리고 3배의 근거인 청크 2,560 GPU당 1·2와 1P1D GPU당 3이다.
17. 그림 A3의 BF16 대화 복제본(0.389)은 주의 런으로 표시한다. 그림 A4(b)의 "client-limited"는 "caution run (client or proxy limit)"으로 고친다.
18. §4.8 트레이스 "(4 and 5.9 requests/s in total)" → "(4–5.9 requests/s in total)".

### A14. 맞대결 양쪽의 멀티모달 설정 차이를 공개한다 (R2-8)
- 한계 절: "Tuned-chunk replicas ran with every modality disabled, while the disaggregated servers kept only images disabled; KV capacity did not bind at the decisive loads, and we did not measure the effect on step time."

### A15. 구간 표(현 표 F1)에 해석 정보를 넣는다 (R2-4)
- 캡션: "Intervals are for the attainment pooled across repeats; the verdict uses the minimum over repeats. Rows with one run have within-run intervals only, and 1.000–1.000 means no failure was observed, not certainty. With two to four repeats the intervals are descriptive."
- 26B aiohttp 행 값의 순서가 시드 순서라면 캡션에 적는다.

### A16. 공개 전 재현성과 패키징 (R2-5, R4 4·5절)
1. **E9 포함 캐시**: 리뷰가 끝난 뒤 커밋 dd15bd7로 커밋됐다(327런) [확인]. 남은 일은 다음과 같다.
   - 새 복제본에서 `decisive_ci.py`(14행)와 `make_figures_v2.py`가 도는지 한 번 확인한다.
   - 조용한 불일치를 막는다. `load_cache()`가 캐시의 런 ID·safety 집합을 safe_runs.csv와 비교해 다르면 다시 만들게 하고, 두 스크립트에 `--rebuild`를 넣는다.
2. `aggregate.py`의 기본 SLO를 논문 값으로 바꾼다(chat ttft 1000, tbt 50; doc 3000, 250). 지금은 인자를 빼면 다른 CSV가 나온다.
3. README: "pre-measurement" 문구를 바꾸고, R4 5절의 재현 명령 여섯 줄을 넣는다.
4. 31B 프롬프트 구간 스크립트(R4 `chk_31b.py`)를 harness로 옮기고 런 집합을 적는다.
5. 원자료(457 MB 파일 등, 추적 7.9 GB)는 Zenodo로 옮긴다. 공개 저장소는 6절의 방식으로 계정 ID를 뺀다. 공개 전에 모든 이력에서 그 문자열이 사라졌는지 `git log --all -S`로 확인한다. 현재 이 문자열은 RESULTS.md 1068행 한 곳이고, 커밋 e03d4de가 들여왔으며, 커밋 메시지에는 없다 [확인].
6. 원고 자리표시자 3개(연락처, 초고 날짜, GitHub·Zenodo)를 채운다. 3차 기록까지 공개한다면 "two mock reviews"를 "three rounds of AI-assisted mock review, two of which prompted E8 and E9"처럼 고친다.
7. RESULTS.md 정정(A10).

---

## 3. B. 고치면 좋은 것 (간단히)

- **B1. 짝 차이 구간.** 26B GPU당 4에서 같은 시드 짝 차이(복제본 − 1P1D aiohttp)는 +0.056 [0.009, 0.128]이다. 같은 날 짝(P 8,192 변형)은 +0.075 [0.013, 0.173]이다 [R2]. 날짜 교란을 닫는 한 줄이다.
- **B2. 복제본 결정점의 간격 여유.** 청크 1,024 GPU당 5의 최장 간격은 46.3·47.1 ms(45 ms 초과 5.2–7.4%)이고, 31B 청크 256 GPU당 8은 48.1 ms(6.3%)다 [확인]. 2,560의 "1.6 ms"를 스스로 짚은 기준을 새 결정점에도 적용한다. 판정이 뒤집힐 위험은 낮다.
- **B3. 사건률 서술.** 복제본에서 서버 정지가 없었던 런 5개와 1P1D에서 있었던 런 2/5는 통계적으로 가를 수 없다(피셔 p = 0.44, R2). §4.7의 "that 1,024-token replicas did not"을 "we saw none in the five replica runs at 4–5 requests/s per GPU"로 낮춘다.
- **B4. 상한은 간격도 줄였다.** 청크 1,024 GPU당 5에서 ITL 중앙값은 상한이 있을 때 17.3 ms, 풀었을 때 30.3–31.8 ms였다 [확인, safe_runs.csv itl_p50_ms]. 통과한 상한 런까지 뺀 규칙을 이 사실로 정당화한다.
- **B5. 분리 쪽 GC 런은 판정에 남겼다는 비대칭.** 결정 칸에서 aiohttp 변형이 같은 판정을 준다는 사실과 함께 §3.6에 한 줄 적는다.
- **B6. 최선 선택의 그룹 분할.** 같은 구성을 세션·프록시별로 나누면 반복이 적은 쪽이 판정을 가져간다(분리에 유리). 칸별 최선 구성·요청률·반복 수 표를 부록에 싣거나, 절단 판정만이라도 같은 서빙 구성을 합친다. 이렇게 하면 A1의 동률 8칸이 코드로 나온다.
- **B7. 식 (1)의 계수를 설정에서 유도.** 26B는 b_w = 25층 × 8헤드 × 256 × 2 × 1 B = 100 KiB, b_g = 10 KiB이고, 31B는 400·40 KiB다. 로그된 입력 길이로 대화 전송량을 0.1 MiB 안에서 재현한다 [R3]. K = V 구조의 해석은 넣지 않는다(C7).
- **B8. 환경 문단.** MTU 9001/MSS 8949, cubic, 배치 그룹 최소 RTT 27–31 µs, 클라이언트 커널 6.8.0-1064-aws를 적는다. GPU 노드 커널·rmem_max·UCX 버전은 "not recorded"로 적는다 [R3].
- **B9. 작은 전송의 m.** 25 MiB 26B 대화 전송은 m 0.55–0.60이었다(합계 16 req/s) [R3]. 식 (2)를 대화 크기에 쓰려면 고정 항 t₀나 크기별 m이 필요하다고 한 줄 적는다.
- **B10. 1 Gbps 대기열 검산.** S ≈ 1.17 s, λ = 0.5/s(합계), ρ ≈ 0.59를 적는다. M/D/1 평균 대기를 더하면 약 2.33 s이고, 측정 2.19 s는 중앙값이다 [확인, 산술]. "about 2.2 s"가 어떤 통계인지 밝힌다.
- **B11. NIXL 스레드 16.** 초기 시험에서 차이가 없었다(626 → 621 ms)는 사실을 분할 규칙의 독립 증거로 한 문장 넣는다 [R3].
- **B12. 관련 연구.** vLLM 문서의 "disaggregated prefill does not improve throughput"와 청크 조정 대비 꼬리 ITL 동기를 인용하고, 이 논문이 그 주장을 클라우드 TCP에서 시험했다고 적는다. TaiChi의 결론(엄격한 TPOT에서는 분리)과 방향이 다른 이유의 후보를 한 문장 적는다. 후보는 평균 TPOT 대 요청별 최대 간격, 인터커넥트, 모델과 규모다. TaiChi 서술("combines aggregated and disaggregated instances")을 원문(P-heavy·D-heavy 인스턴스와 슬라이더)에 맞춘다 [R1].
- **B13. EFA 문단.** GDR이 없는 것은 g6e·g7e의 8xlarge이고(g7.8xlarge는 있음), 8xlarge의 NIC 대역은 g6e 25, g7e·g7 100 Gbps다 [R3, 2026-10-01 AWS 문서]. 저자가 공개 전에 다시 확인한다.
- **B14. 디코드 서버 API 프로세스 가설(선택).** 26B P 8,192 GPU당 5에서 50 ms 넘는 간격을 프록시는 4,496건, 엔진 히스토그램은 348건 기록했다 [R1]. 넣는다면 "points at the decode server's front end, which we did not test" 수준으로만 쓴다(C5).
- **B15. 표현.**
  - §4.4의 "80–300 ms transfer" 전방 참조에 절 번호를 단다.
  - §4.3 둘째 문단(256단어)을 셋으로 나눈다.
  - 용어를 통일한다: longest gap, limit, global pause, tuned chunk, vLLM's test proxy, SLO 첫 풀이.
  - 그림: A7 행 라벨(4.4 pt)을 키운다. 그림 3의 갈색 dash-dot을 다른 선 모양으로 바꾼다(녹색약). 그림 4 굵은 칸에 비율을 적는다. 그림 A1 비등간격 축을 고친다.
  - 표 2를 부하·원가·TTFT 세 소열로 나눈다.
  - 참고문헌 [2]·[16]·[26], 접근일을 정리한다.
  - Acknowledgments를 "Funding"으로 바꾼다.
  - 도입부에 "AI-assisted"를 넣는다.
  - 2,560 기준선의 틀을 "untuned"가 아니라 "the smaller chunks that disabling every modality allows"로 통일한다.
- **B16. 패키징(권장).**
  - 런 매니페스트: E4–E9 행에 `ucx_set`, `proxy`, `prefill_chunk`, `instance_type` 열을 채운다. 있었다면 이번 UCX 누락이 CSV에서 보였을 것이다.
  - 버전 고정: uv.lock 또는 requirements, 도커 digest, HF revision.
  - 저장소 정리: .gitignore, 세션 env, 테라폼 기본값(개인 프로필, 0.0.0.0/0), CITATION·LICENSE 갱신.
  - 심사 폴더의 절대 경로 15개를 정리한다.
  - 코드: glob을 정렬하고, 캐시 값의 10 µs 반올림을 뺀다.
- **B17. 한계 절.** 출력 512 고정, 무작위 토큰 입력(MoE 라우팅), 디코드 256 상한이 묶이지 않았다는 사실(진행 중 최대 106–213)을 적는다 [R1].
- **B18. 사전 등록의 가치.** 예측 대부분은 2차 메타리뷰의 외삽을 옮긴 저위험 예측이었다. 가치는 적중률보다 실행 목록과 판정 규칙을 미리 고정하고 19런을 모두 보고한 데 있다고 한 문장 적는다 [R2].

---

## 4. C. 반박하거나 받아들이지 않는 것

1. **R1 "빗나간 두 하위 예측은 모두 분리에 유리한 방향이다".** 틀렸다. 예측 5(P 8,192가 4 통과)의 빗나감은 1P1D가 예측보다 못한 것이라 분리에 불리하다. R2의 "one in each direction"이 맞다. R1의 영문 문안 자체는 방향을 적지 않아 쓸 수 있다.
2. **R1 "26B 완화 칸에서 P 청크 8,192 1P1D가 GPU당 5를 통과했고, 분리가 같거나 더 많이 처리할 가능성이 배제되지 않는다".** 둘 다 부정확하다. 이 칸들의 분리 쪽 최선은 E8 aiohttp(P 2,560) 런이다. P 8,192 런은 TTFT 3 s·간격 100 ms에서 0.831로 탈락이다 [확인]. 같은 1P1D가 GPU당 6에서 무너졌으므로 "분리 우세"는 사실상 배제되고, 이 칸들은 동률이다(1.1(a)).
3. **R1의 청크 512 처리 한계 "약 4.5 req/s/GPU".** 선형 맞춤 추정이다. 본문에 수치로 싣지 않는다. 절차에는 측정값(GPU당 4의 TTFT 359 대 200 ms)과 "4보다 높게는 재지 않았다"만 쓴다.
4. **새 측정 요청.** R1은 세그먼트만 대 7변수(P 2,560, GPU당 4·5)와 D API 서버 증설을, R2는 31B 1P1D GPU당 5와 청크 512 GPU당 5를 요청했다. 어느 것도 판정이나 헤드라인을 바꾸지 않는다. 교란과 미시험 사실을 원고에 적으면 된다. 저자가 다른 이유로 세션을 연다면 우선순위는 다음과 같다.
   1. 청크 512 GPU당 5: 절차 2의 처리량 주장을 직접 시험한다.
   2. 31B 1P1D GPU당 5: 비율 "≥8 대 4"의 괄호를 좁힌다.
   3. P 2,560에서 세그먼트만 대 7변수: 절차 4를 부하에서 시험한다.
5. **R1의 API 프로세스 해석을 본문 결론으로 싣는 것.** 받아들이지 않는다. v0.30.0의 ITL 히스토그램이 엔진 코어 시각으로 계산되는지 확인되지 않았고(R1 스스로 main 브랜치만 확인), 대기 사유 라벨도 순서를 가정했다. 싣는다면 B14 수준의 가설로만 쓴다. §3.1 기본값 목록에 "one API server process"를 넣는 것은 v0.30.0 기본값을 확인한 뒤에만 한다.
6. **R2의 짝 차이 구간을 필수로 둔 것.** 권장(B1)으로 내린다. 판정 규칙은 반복 최솟값이고, 구간 표의 해석 정보(A15)가 필수 부분이다.
7. **R3의 "b_g가 10 KiB이므로 vLLM이 attention_k_eq_v에서도 K와 V를 따로 저장한다".** 계수는 맞지만 저장 방식의 해석은 추론이다. 싣지 않는다. "documented 10 Gbps"를 MSS로 환산해 바꾸자는 제안도 받아들이지 않는다. 원고는 이미 측정값 9.54 Gbps를 C_flow로 쓴다.
8. **R2의 동률 띠를 격자 한 칸으로 넓힌 그림.** 그림의 띠(0.8–1.25)는 사전 프로토콜에서 한 번 바꾼 값이다. 지금 다시 바꾸면 사후 변경이다. 민감도 결과를 한 문장으로 적는 데서 그친다(A1).
9. **R3의 m을 전송 가중 평균으로 바꾸자는 요구.** 통계를 밝히고 식 (2)와 그림 6에서 같은 통계를 쓰면 충분하다. 어느 통계를 쓸지는 저자가 고른다.
10. **R5의 결과 절 재배치(선택 A: §4.5–4.6을 §4.3 앞으로).** 영어 교정 직전의 큰 구조 변경은 상호 참조 오류 위험이 크다. 전방 참조에 절 번호를 다는 것으로 충분하다(B15).
11. **R5 "그림 4의 (0.75 s, 40 ms) 빗금 칸은 오류처럼 보인다", "범례의 Similar를 빼라".** 앞의 칸은 규칙대로다. 복제본 청크 512가 GPU당 4에서 절단됐고, 비율 0.807이 "비슷함"과 "복제본 우세" 사이에서 갈리지 않는다 [확인]. 캡션 수정(A1)으로 충분하다. A1의 동률 칸을 그림에 넣으면 "Similar"가 쓰이므로 범례는 남긴다.
12. **R4의 패키징 점수(1.5).** 지적은 모두 맞다. 다만 저자가 새 공개 저장소를 따로 만들기로 했으므로, 원고 개정의 차단 항목이 아니라 DOI 공개의 차단 항목으로 둔다(A16).

---

## 5. 초록 최종안 (200단어, `wc -w` 기준; `r6/abstract_v3.txt`)

> Prefill–decode disaggregation usually needs RDMA or NVLink, which cheap single-GPU instances lack; we ask when, over TCP, it beats colocated replicas with chunked prefill. On AWS 2xlarge instances we served Gemma 4 26B (mixture of experts) and 31B (dense) with stock vLLM and NIXL/UCX, judging each request by its time to first token (TTFT) and longest inter-token gap. A replica stalls when another request's prefill shares its step, so the chunk size bounds that gap: for 26B with 4K inputs, its median fell from 48 ms at a 2,560-token chunk to 21 ms at 512. Under a 1 s TTFT and 50 ms gap limit, disaggregation served about 3× more requests per GPU than 26B replicas held at 2,560 tokens, near the floor vLLM set for multimodal Gemma 4. Against smaller chunks, no limit pair we could rank favored it, down to 30 ms gaps: for 26B it was borderline at 4 requests/s per GPU while replicas supported 5; for 31B chat, borderline at 4 against at least 8. Its TTFT cost was mostly KV transfer, which a larger UCX segment made 3.4× faster at low load. Tune the chunk first; disaggregate when no workable chunk meets the gap limit.

v2 대비 바꾼 곳과 이유:
- "the median" → "its median": 가리키는 대상이 요청별 최대 간격임을 분명히 했다(R5).
- 3배에 "26B"를 붙였다(A2).
- "never served more under any SLO we tested" → "no limit pair we could rank favored it": 판정 불가 칸을 덮지 않는다(A1).
- 31B 1P1D를 "borderline at 4"로 썼다(A4). "replicas held 5" → "supported 5": "held"의 두 뜻을 피했다(R5).
- 3.4배에 "at low load"를 붙였다(A3, R3).
- 마지막 문장에 조건절을 넣었다(R5). RQ3와 결론이 이미 "청크를 충분히 줄일 수 없을 때는 분리"라고 말하므로 초록도 맞춘다.
- "near the minimum vLLM allows Gemma 4 with video enabled" → "near the floor vLLM set for multimodal Gemma 4": 시험하지 않은 조합(video만 켬)을 주장하지 않는다(A13-12). 저자가 "(with audio and video enabled)"를 원하면 두 단어를 다른 곳에서 줄인다.
- SLO라는 약어는 초록에서 빼고 본문 첫 사용에서 풀어 쓴다.

---

## 6. 사전 등록 증거 보존 방안

### 6.1 사실 관계 [확인]
- 예측 커밋 8775497: author 13:29:43 UTC, committer 13:29:54 UTC(원 커밋을 11초 뒤 amend해 머리글의 시각 표기만 고쳤다, R2 reflog 확인). 커밋에는 RESULTS.md의 예측 절, `run_E9.sh`, `lib_E9.sh`, `rr_proxy.py`가 들어 있다. 이 파일들의 해당 내용은 이후 바뀌지 않았다.
- 저장소에는 원격이 없다. 예측의 시각은 저자 기계의 git이 기록한 값이고, 외부에 고정된 흔적(공개 푸시, 타임스탬프 서비스, 제3자에게 보낸 해시)이 없다. 프로토콜 v1.7(루트 커밋 7e4ce5b, 2026-09-24)도 같다.
- 계정 ID는 RESULTS.md 1068행 한 곳에 있다. 커밋 e03d4de(2026-09-28)가 들여왔고, 8775497은 그 후손이다. 커밋 메시지에는 없다. **8775497 시점의 RESULTS.md에도 이 ID가 들어 있다.**

### 6.2 선택지 평가

핵심 제약: 측정 전에 외부에 고정한 것이 없으므로, **지금 할 수 있는 어떤 조치도 "측정 전"이라는 순서를 제3자에게 암호학적으로 증명하지 못한다.** 지금의 조치로 할 수 있는 것은 두 가지다. (1) 자체 기록을 손실 없이 공개한다. (2) 공개 시점 이후의 변경을 막는다. 선택지는 이 기준으로 평가한다.

| 선택지 | 보존되는 것 | 한계 | 평가 |
|---|---|---|---|
| ① 원 커밋 해시 8775497 + 그 시점 RESULTS.md의 SHA-256만 인용 | 없다 | 해당 파일에 계정 ID가 있어 파일을 공개하지 않으면 누구도 대조할 수 없다. 공개하면 ID가 드러난다. 대조가 되더라도 지금 공개한 해시는 순서를 증명하지 않는다 | 단독으로는 쓰지 않는다. 식별자로만 괄호에 남긴다 |
| ② 예측 원문을 "원래 시각"과 함께 공개 저장소에 싣기 | 문구 | 시각이 자기 주장이다. 함께 커밋된 스크립트와의 관계가 사라진다 | 편의용 사본으로는 좋다(예: `prereg/E9_predictions.md`). 증거로는 ③에 못 미친다 |
| ③ 이력을 보존한 채 계정 ID만 치환한 공개 저장소(`git filter-repo --replace-text`, 원자료는 경로·크기 필터로 제외) | 커밋 순서, 작성·커밋 시각, 메시지, 예측→결과의 차이 전체 | e03d4de 이후 모든 해시가 바뀐다(8775497 → 새 해시). ID가 없는 파일(`run_E9.sh` 등)의 blob 해시는 그대로다 | **권장.** 외부 증거가 원래 없었으므로 새 해시로 잃는 것이 없다. filter-repo의 `commit-map`(옛 → 새)을 함께 싣는다 |
| ④ 새 스냅샷 저장소(커밋 하나) + ③의 이력을 `git bundle`로 Zenodo에 첨부 | ③과 같음(이력은 번들에 있다) | 메인 저장소에서는 시간 순서가 안 보인다 | 메인 저장소를 깨끗하게 두고 싶다면 ③과 동등한 대안이다 |
| ⑤ 원본(ID 포함) 저장소 번들을 비공개·제한 공개로 보관하고 SHA-256을 논문에 인쇄 | 원본과 공개본이 ID 한 줄 말고는 같다는 사실을, 요청한 제3자가 같은 filter-repo 명령으로 해시를 재현해 확인할 수 있다 | 순서는 증명하지 못한다. Zenodo 제한 공개(요청 승인제)나 저자 보관이 필요하다 | ③·④의 보완으로 권장한다. 비용이 작다 |
| ⑥ 지금 GPG 서명 태그나 OpenTimestamps로 공개본 고정 | 공개 시점 이후 이력이 바뀌지 않았다는 증거 | 측정 전 순서와는 무관하다 | 선택. Zenodo DOI 자체가 같은 역할을 대부분 한다 |

### 6.3 권고
1. **공개 저장소는 이력을 보존한 채 ID만 치환해 만든다(③).** 원자료는 같은 filter-repo 실행에서 경로·크기 필터로 빼고 Zenodo로 옮긴다. 메인 저장소를 한 커밋으로 두고 싶다면 ④로 같은 이력을 번들로 첨부한다. 이력을 통째로 합쳐 버리는 스냅샷만 공개하는 것은 권하지 않는다. 예측 커밋이 결과 커밋보다 앞선다는 자체 기록마저 사라진다.
2. filter-repo 전에 원본 저장소의 `git bundle --all`을 만들어 보관한다(⑤). SHA-256을 논문 부록 F에 적는다. 요청이 있으면 제3자가 대조할 수 있다고 쓴다.
3. 치환한 뒤 확인한다.
   - `git log --all -S<ID>`와 `git grep <ID> $(git rev-list --all)`의 결과가 비어야 한다.
   - 예측 절의 문구가 원본과 글자 하나까지 같아야 한다.
   - 새 해시를 `commit-map`에서 찾아 태그를 단다(`e9-predictions`, 서명 태그면 더 좋다).
4. 논문 부록 D에는 A10 문안대로 적는다. 새 해시를 쓰고, 8775497은 괄호 속 식별자로 두며, "not externally anchored"를 분명히 쓴다. "prove"라는 말은 쓰지 않는다.
5. 앞으로의 세션을 위한 권고:
   - 예측은 비밀이 없는 별도 파일(예: `prereg/E10.md`)에 쓴다. 그래야 이후 이력을 정리해도 blob 해시가 살아남는다.
   - 측정 전에 공개 원격에 푸시하거나, 커밋 해시를 OpenTimestamps나 공개 게시로 외부에 고정한다.

---

## 7. 리뷰어 간 불일치와 종합 판단

1. **헤드라인 범위의 표현.**
   - R1은 "in every SLO cell we could decide (107 of 192), replicas with a tuned chunk served more"를, R2는 "served no more in any SLO cell we could decide"를, R5는 "no SLO we tested favored disaggregation"을 제안했다.
   - 판단: R1의 107에는 둘 다 불충족인 8칸이 들어 있다. "served more"는 26B 동률 8칸(1.1(a))과 격자 한 칸 차이 12칸 때문에 과하다. R5의 "tested"는 판정 불가 칸을 덮는다. 불변하는 사실은 "순위를 매길 수 있었던 칸 중 분리가 앞선 칸은 없다"이다. 그래서 초록은 "no limit pair we could rank favored it"로, 본문은 A1의 칸 수로 쓴다.
2. **사전 등록 채점.**
   - 원고는 "넷 적중", R4는 "셋 온전히 적중", R2는 "하위 예측 16개 중 12 적중·2 빗나감·1 일부 미시험·1 반증 불가"로 셌다. R1은 "두 빗나감 모두 분리에 유리"라고 했다.
   - 판단: 항목 수준 요약은 R4, 부록 표는 R2를 따른다. R1의 방향 서술은 틀렸다(C1).
3. **E9 P 8,192 런 GPU당 5의 전송 지연을 어떻게 읽을까.**
   - R1은 "전송 경로가 병목이 됐다(링크 지속 약 11 Gbps, 단일 31B 전송의 19–21 Gbps 미만)"로, R3는 "링크는 여유가 있었다(P NIC 평균 = 제공 부하 11.7 Gbps, 1초 최고 17 Gbps), 시간은 링크 밖에서 쓰였다"로 읽었다.
   - 판단: 정상 상태에서 링크 평균은 정의상 제공 부하와 같다. 따라서 두 관찰 모두 "링크 포화"나 "링크 밖"을 입증하지 못한다. 공통 사실은 "P가 따라가자 전송이 쌓였다(평균 0.92 s)"이다. 게다가 UCX 설정이 함께 바뀌었다. 원고에는 이 사실과 교란만 쓰고 원인은 적지 않는다(A3).
4. **"structural" 문장.**
   - R1은 자신의 2차 제안을 철회하고 26B에서 평균 ITL이 같다고 보였다. R5는 결론 문안 29번에서 오히려 "a decode node that carries twice the decodes"를 강조하자고 했다.
   - 판단: R1이 맞다 [확인]. R5의 해당 구절은 31B 대화에만 쓸 수 있다(A6).
5. **경계의 수치 정의.**
   - R2는 "반복 하나가 0.85–0.95이거나 반복 수준 구간이 0.9를 포함", R5는 "반복 하나가 0.85–0.95"를 제안했다.
   - 판단: R5의 반복 기준 하나만 쓴다. 구간 조건을 더하면 FP8 청크 512의 30 ms(구간 0.900–1.000)처럼 경계 여부가 셋째 자리에서 갈리는 점이 생긴다.
6. **통계 보고의 무게.** R2는 짝 차이와 표 해석 정보를 모두 필수로 두었다. 판단: 해석 정보는 필수(A15), 짝 차이는 권장(B1)이다.
7. **새 측정.**
   - R1·R2는 선택 측정 네 가지를 제안했다. R3·R4·R5는 필요 없다고 봤다.
   - 판단: 필요 없다. 어느 것도 판정을 바꾸지 않는다(C4).
8. **31B 대화의 m.**
   - R3는 창 중앙값 0.79–0.82와 부하 의존(1–2에서 0.94–1.05, 6에서 0.52–0.57)을, R4는 세션별 0.78–0.85를 보고했다.
   - 판단: 본문은 "about 0.8 (0.78–0.85 across sessions)"로 쓴다. 부하 의존은 B9와 함께 한 줄 넣을 수 있다.
9. **31B 1P1D 경계의 근거.**
   - R2는 1토큰 규칙 의존을, R4·R5는 프록시 의존을 강조했다.
   - 판단: 둘 다 사실이고 둘 다 분리에 유리한 쪽이다. 표 2 각주에는 프록시를, §3.5에는 규칙을 적는다(A4).
10. **패키징의 무게.**
    - R4는 패키징을 1.5점으로 보고 필수 항목으로 올렸다. 다른 리뷰어는 원고만 봤다.
    - 판단: 원고 개정과 공개를 나눈다. 과학적 개정은 A1–A15다. A16과 6절은 DOI 공개 전에 끝낸다. 캐시 커밋은 이미 dd15bd7로 해결됐다.
11. **3차 심사 기록의 공개 여부.** 판단: 저자가 정한다. 공개한다면 원고의 "two mock reviews"를 고친다(A16-6).
