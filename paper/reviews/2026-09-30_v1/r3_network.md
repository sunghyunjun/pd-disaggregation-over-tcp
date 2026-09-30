# Reviewer 3 (네트워크·클라우드) 2차 심사평

대상: "Chunked Prefill or Disaggregation? Prefill–Decode Serving over TCP on Single-GPU Cloud Instances" (paper/en/main.tex, draft v1, 2026-09-30)
판정 요지: **3.5/5, 확신도 4/5.** 1차 지적 10건 가운데 3건은 반영, 4건은 대부분 반영, 3건은 부분 반영됐다. 그러나 새로 추가된 소켓 표본(E8)을 직접 다시 분석해 보니, v1이 여기서 끌어낸 전송 메커니즘 서술 세 가지가 그 데이터와 맞지 않는다. 하나는 초록에 있다. 새 실험은 필요 없다. 필수 5건은 모두 원고와 기존 데이터만으로 고칠 수 있다.

---

## 요약

v1의 네트워크 쪽 주장은 다섯 가지다.
1. UCX 기본 TCP 세그먼트(8 KB)가 전송을 3.4배 늦췄고, 송수신 세그먼트 두 변수만으로 이득 전부가 설명된다 (E8 절제: 기본 4.45, 세그먼트만 14.97, 7변수 14.16 Gbps).
2. NIXL이 전송 하나를 TCP 연결 네 개에 나눠 실어서 흐름당 상한 9.54 Gbps의 1.5–1.8배를 냈다 (ss 표본: 연결 4개가 22–27%씩, 다섯째가 1–3%).
3. 남은 여지는 연결 수이지 다른 UCX 설정이 아니다 (미시험).
4. 식 (1) V(L) ≈ 100 MiB + 10 KiB·L과 식 (2)로 분리의 첫 토큰 비용을 저부하에서 추정할 수 있다. 대기열이 있으면 M/D/1로 보정한다.
5. 크레딧은 제약이 아니었고, EFA는 8xlarge에 있지만 가격이 1.6–2배라서 26B 4K에서는 값을 못 할 것이다.

1·4·5는 대체로 뒷받침된다. 2·3은 저자들이 공개한 ss 원자료와 NIXL v1.4.1 소스(직접 확인)로 다시 보면 틀렸거나 과하다. 핵심은 세 가지다.
- 26B 전송은 네 연결이 아니라 **2~3조각(64/64/12 MiB)** 으로 나뉜다. NIXL은 1,024 디스크립터 미만의 전송을 아예 나누지 않는다.
- 다섯째 연결은 부수 채널이 아니다. **나뉘지 않은 전송 전체가 지나는 경로**다.
- 연결 네 개가 동시에 움직일 때 합계가 **약 19–21 Gbps에서 멈춘다.** 연결당으로는 4.5 Gbps다. 한 연결이 혼자 움직이면 정확히 9.5 Gbps가 나온다. 즉 31B에서는 흐름당 상한보다 먼저 걸리는 공유 상한이 있다. 이 공유 상한 때문에 "연결 수가 남은 지렛대"라는 결론은 데이터에 맞지 않는다.

---

## 1차 지적 반영 점검

| # | 1차 지적 | 판정 | v1의 근거 / 남은 문제 |
|---|---|---|---|
| 1 | m의 메커니즘 미검증 ("slightly", 소켓 수 미측정) | **부분** | E8에서 P·D 양쪽 `ss -tin`을 떴고 연결 수(4+1)를 보고했다. "slightly"도 사라졌다. 그러나 전송별 조각 규칙(1,024 디스크립터 하한), 다섯째 연결의 역할, 공유 상한은 빠졌다. "more connections, not other UCX settings, are the remaining lever"는 그대로 남았다 (→ 필수 1·2). |
| 2 | 전송량은 아핀, 16K 예시 오류, m의 크기 의존 | **대부분** | 식 (1) V(L) ≈ 100 MiB + 10 KiB·L 추가. 16K 예시를 "about 520 MiB take roughly 0.3–0.7 s on top of a prefill of about 0.8 s"로 바로잡았다. "matched the prediction exactly"도 삭제했다. 남은 문제는 두 가지다. 식 (1)의 적용 범위(L ≥ 슬라이딩 윈도우)를 밝히지 않았다. m이 전송 크기에 따라 1 아래로 떨어진다는 사실도 여전히 없다 (→ 필수 3). |
| 3 | 대기열 항 부재, 31B 적중은 오차 상쇄, 잔차 범위 | **대부분** | "The relation omits queueing … adding an M/D/1 waiting time explains the difference (about 2.2 s). Eq. (2) is therefore a low-load estimate." 선후 관계에 대해서도 "The repository history cannot prove that order"라고 정직하게 적었다. 남은 문제: 계산 내역(S, λ, ρ)과 평균/중앙값 구분이 없다. 체크리스트에 이용률 조건이 없다. 잔차 범위는 노트의 −26~+87 ms 대신 28–87 ms만 보고한다 (→ 권장 6). |
| 4 | MiB 단위, 실효 전송률 정의, 그림 값 하드코딩 | **반영(표기 오류 1건)** | "they are mebibytes, and we convert them to Gbps as MiB×8×1.048576/s". 전송률은 `make_figures_v1.py`의 `xfer_stats()`가 원 로그에서 계산하고, 나도 같은 값(4.45/14.97/14.16/17.28)을 재현했다. 다만 식이 그대로면 Mbit/s가 나온다 (사소 1). m을 "effective number of parallel connections"라고 부르는 것은 틀린 이름이다 (→ 필수 3). 그림 6(TTFT 분해)의 84/283/165 ms는 여전히 노트 인용값이다. |
| 5 | UCX 변수 전체 공개, TX_SEG 단독 절제, 환경 보고 | **대부분** | 부록 C에 7개 변수와 UCX_TLS·NET_DEVICES를 실었다. E8에서 세그먼트 단독 절제도 했다. 그러나 환경 보고(MTU 9001, RTT, 커널, 혼잡 제어, **NIXL·UCX 버전**)가 여전히 없다. 버퍼 문장은 "may have been capped by net.core.wmem_max"에 머문다. ss 표본에서 실제로 잘렸음을 확인할 수 있다 (→ 필수 4·5). |
| 6 | 크레딧 검증 방법 오류 | **반영** | "g7e.2xlarge has a fixed 50 Gbps, and on g6e.2xlarge (5 Gbps baseline, 20 Gbps burst) our 15-minute test load averaged about 1.2 Gbps, computed from the request rate and volume, below the baseline." 계산을 확인했다(0.5 req/s × 280 MiB = 1.17 Gbps). 전후 단일 흐름 iperf 문장도 삭제됐다. |
| 7 | EFA/ENA Express 전제, 대안 | **대부분** | 서론이 "the 2xlarge sizes … have one GPU, no EFA, and no ENA Express; the 8xlarge sizes … add EFA at roughly 1.6–2× the hourly price"로 바뀌었다. §5.3에서 GDR 부재와 제3자 가격 출처를 밝히고 "We did not measure EFA"라고 적었다. 남은 문제는 두 가지다. 8xlarge는 전송 경로(libfabric)와 CPU(32 vCPU)를 함께 바꾼다. MPTCP·ENI 추가·UCCL 같은 TCP 쪽 대안은 한 문장도 없다 (→ 권장 8). |
| 8 | tc는 합계 상한 | **반영** | 그림 A1 캡션과 본문 모두 "the sender's aggregate bandwidth"로 바뀌었다. |
| 9 | 호스트 스테이징 해석 | **부분** | "75×"를 빼고 "slowed TTFT 4.7× at 0.125 requests/s per GPU on g7 and had no stable load at 0.5"로 바꿨다. 측정 조건(GPU 메모리 0.70, 호스트 32 GiB)과 링크 전송률(7.3–9.4 Gbps)은 여전히 없다. |
| 10 | 일반화 범위 | **부분** | §5.3에 "The per-flow cap is an AWS policy, and m depends on NIXL's thread count; on other clouds, measure one flow and several flows with iperf first"를 넣었다. 그러나 "m depends on NIXL's thread count"는 저자 자신의 D1c(스레드 16, 차이 없음)와 모순된다. m을 정하는 것은 1,024 디스크립터 하한이다 (→ 필수 3). 초록에는 범위 표시가 없다. |

1차 사소 지적: "eight flows" 표현 ✓, 그림 2 캡션(해당 그림 교체) ✓. 4.97 = 5 × 8949/9001 확인, 네 쌍 모두 4.97이었다는 명시, RTT 보고, 같은 부피인데 디스크립터 수가 달라지는 문제는 미반영이다. 마지막 항목은 이제 m을 정하는 변수가 되었다 (필수 1).

---

## 강점

- **소켓 수준 증거를 공개했다.** 전송 중 P·D 양쪽에서 `ss -tinH`를 떠서 원문 그대로 공개했고, 파서도 있다. 그래서 나는 연결별 누적 바이트, busy·rwnd_limited 시간, rcv_ssthresh, RTT, MSS까지 다시 계산할 수 있었다. 아래 비판도 대부분 이 공개 덕분에 가능했다. TCP 전송 논문으로서 드문 수준의 투명성이다.
- **절제 설계가 깔끔하다.** 같은 노드, 같은 시드, 같은 부하(GPU당 0.25)에서 기본, 세그먼트만, 7변수를 한 번씩 쟀다. 기본 대비 세그먼트의 3.4배는 효과가 커서 한 번씩만 쟀어도 방향이 흔들리지 않는다.
- **1차 지적 중 틀린 논증을 제대로 걷어 냈다.** 크레딧 논증은 산술로 바꿨고, tc는 합계 상한으로 정정했다. EFA 전제에는 가격 출처를 밝혔고, 예측의 선후는 입증할 수 없다고 인정했다.
- 전송률 그림이 원 로그에서 스크립트로 계산된다(`make_figures_v1.py:160–169`). 1차의 재현성 문제가 해소됐다.
- 세그먼트 크기 권고(체크리스트 4번 "send and receive together")는 실무에 바로 쓸 수 있다. 수신 세그먼트가 작으면 엔진이 뜨지 않는다는 마찰 기록도 쓸모 있다.

---

## 주요 약점

### [필수 1] "NIXL spread each transfer over four TCP connections"는 26B 전송에 대해 틀렸고, 다섯째 연결을 잘못 설명한다

문제 문장은 셋이다.
- 초록: "NIXL spread each transfer over four TCP connections, which lifted it 1.5–1.8× above the 9.5 Gbps per-flow cap"
- §4.5: "Socket samples showed four TCP connections …, each carrying 22–27% of the bytes, plus a fifth carrying 1–3% … This matches the four worker threads of vLLM's NIXL connector in v0.30.0, each with its own UCX endpoint."
- 그림 5(c) 제목: "Four connections per P–D pair"

22–27%는 런 전체 누적 몫이다. 전송 하나를 들여다보면 그림이 다르다. 연결별 누적 바이트를 전송 단위(연속 활동 구간)로 묶어 다시 셌다(`r3_ss_pieces.py`, D 쪽 파일).

| 조건 | 단일 전송 수 | 조각 수 분포 (연결 >1 MiB) | 가장 큰 조각 중앙값 | 대표 분할 |
|---|---|---|---|---|
| 26B, UCX 기본 | 61 | 2조각 28, 3조각 33 | 67.9 MiB (48%) | 64/64/12 MiB |
| 26B, 세그먼트만 | 73 | **1조각 3**, 2조각 24, 3조각 46 | 66.3 MiB (47%) | 64/64/12 |
| 26B, 7변수 | 71 | 2조각 31, 3조각 40 | 67.6 MiB (48%) | 64/64/12 |
| 31B, 7변수 | 81 | **1조각 1**, 3조각 12, 4조각 68 | 140.9 MiB (25%) | 140/140/140/140 |

**26B 4K 전송 하나가 네 연결을 쓴 경우는 한 번도 없다.** 그림 5(c)에서 26B의 "4" 막대(0.6%)도 전송 두 개가 겹친 표본으로 보인다. 분할은 NIXL v1.4.1 소스와 정확히 맞는다(`src/plugins/ucx/ucx_backend.cpp`, 태그 v1.4.1, 직접 받아 읽음).
- 675–681행: `if (batch_size < splitBatchSize_) return nixlUcxEngine::prepXfer(...)` (나누지 않음). 나눌 때는 `chunk_size = std::max(batch_size / dedicatedThreads_.size(), splitBatchSize_)`, `splitBatchSize_` 기본값은 1024(645–646행).
- 2,240 디스크립터 × 64 KiB → 1024/1024/192 → 64/64/12 MiB. 31B 4,480 → 1120×4 → 140 MiB×4.
- 776–780행: `num_workers ≤ num_dedicated_workers`이면 `num_dedicated_workers + 1`. 스레드 4개면 워커는 5개(전용 4 + 공유 1)다. **이것이 다섯째 연결이다.**

다섯째 연결은 "1–3%"짜리 부수 채널이 아니다. 나뉘지 않은 전송이 통째로 지나는 공유 워커 경로다. 증거는 네 가지다.
- 측정 시작 시점에 이미 워밍업(ShareGPT 30요청, 평균 25.9 MiB·279 디스크립터, 1,024 미만이라 나뉘지 않음) 바이트 대부분을 싣고 있었다. 26B 기본 558.0 MiB, 세그먼트만 556.6 MiB, 31B 1,941.5 MiB이고, 다른 연결은 각각 31–68 MiB였다.
- 런 중에는 140 MiB나 560 MiB 전송을 **혼자서 통째로** 실었다. 세그먼트만 조건에서 3회, 기본에서 2회, 31B에서 1회다.
- 세그먼트만 조건에서 이런 전송이 든 두 10초 창은 vLLM 로그의 P90이 114–124 ms였다. 140 MiB를 9.54 Gbps 한 흐름으로 보내면 123 ms다. 두 창의 평균 디스크립터도 1,637–1,648로, 다른 창 대부분(1,850–2,240)보다 낮았다.
- 31B의 그 전송은 한 연결로 120 ms 구간마다 137.7–139.5 MiB, 즉 **9.5–9.6 Gbps**로 약 0.55 s 동안 흘렀다. 중앙값 272 ms의 두 배다(`r3_ss_timeline.py`).

같은 140 MiB인데 디스크립터 수가 1,108–2,240으로 흔들린다(E8 로그). 노트(RESULTS.md 485행)의 "블록 병합 없음"과 맞지 않으므로 어딘가에서 연속 블록이 합쳐지는 것으로 보인다. 그 결과 조각 수, 곧 m이 KV 블록 배치에 따라 전송마다 달라진다.

**P와 D 표본의 일치에 대해.** 연결별 바이트가 P·D에서 바이트 단위로 일치한다(RESULTS.md 1225행). 그러나 이것은 같은 TCP 연결의 bytes_acked와 bytes_received를 양 끝에서 읽은 값이라 당연히 같다. 파서가 맞다는 확인이지 메커니즘의 독립 증거는 아니다. 활동 분포도 P와 D가 거의 같다(평균 2.30/2.31, 1.85/1.86, 2.27/2.34, 3.42/3.35). 차이는 표본 위상 때문이다.

**수정.** 초록을 "NIXL split each transfer of at least 1,024 descriptors into up to four pieces on separate TCP connections (two or three for a 140 MiB 26B transfer, four for a 560 MiB 31B transfer)"로 고친다. 본문에 분할 규칙(chunk = max(⌊N/4⌋, 1024) 디스크립터, 1,024 미만은 공유 워커 연결 하나)과 NIXL 버전을 적는다. 다섯째 연결은 "a shared worker that carries every unsplit transfer"로 설명한다. 그림 5(c)는 전송별 조각 수 히스토그램으로 바꾸거나 제목을 고친다.

### [필수 2] "more connections, not other UCX settings, are the remaining lever"는 저자 자신의 31B 데이터와 맞지 않는다

§4.5는 "Because the instance's aggregate bandwidth grows almost linearly with flows (Figure 5a), more connections … are the remaining lever; we did not test that"라고 쓴다. 그런데 31B 전송은 이미 연결 네 개를 쓰고 있다. 그 네 연결의 동작을 보면 병목은 흐름당 상한이 아니다.

**(a) 공유 상한 약 20 Gbps.** 앞뒤 구간도 활동 중인 내부 구간만 골라 P 쪽 합계와 연결당 전송률을 계산했다(`r3_ss_interior.py`).

| 31B 7변수, 활동 연결 수 | 구간 수 | 합계 중앙값 (최대) | 연결당 중앙값 |
|---|---|---|---|
| 1 (공유 워커 단독 전송) | 6 | **9.5 (9.6) Gbps** | 9.5 Gbps = 흐름당 상한 |
| 3 | 24 | 18.2 (22.8) Gbps | 6.6 Gbps |
| 4 | 110 | **19.2 (21.1) Gbps** | **4.5 Gbps** |

- 연결이 셋이든 넷이든 합계는 약 19–21 Gbps에서 멈춘다. 연결이 넷일 때 각 연결은 상한의 절반 이하(4.5 Gbps)로 돈다.
- iperf 4흐름(38.1 Gbps)의 절반이다. 따라서 링크나 흐름당 정책이 아니라 노드 쪽 공유 경로가 병목이다.
- 기본 설정에서도 모양이 같다. 활동 연결이 1·2·3·4개일 때 합계 중앙값이 4.3/4.6/4.6/4.5 Gbps이고, 최대는 전부 5.0 이하다. 8 KB 세그먼트가 늦춘 것도 연결 각각이 아니라 공유 경로다.

**(b) busy 시간으로도 같은 결론.** P 쪽 `busy`(송신 대기열이 비어 있지 않은 시간)를 런 전후로 빼서 계산했다(`r3_ss_busy.py`). 전송 하나에 대한 연결 busy 합을 전송 시간으로 나누면 평균 동시 활동 연결 수가 나온다.
- 기본 1.02, 세그먼트만 1.81, 7변수 1.89, **31B 7변수 1.94.**
- 31B는 네 조각을 한꺼번에 받고도 평균 두 연결 몫만 움직인다. 각 연결은 전송 시간(평균 298 ms)의 약 절반(약 145 ms)만 busy다.

**(c) 소스와의 연결.** NIXL v1.4.1은 원격 쪽에 앞쪽 워커 하나의 주소만 공개한다(`workerAddr = workers_.front()->epAddr()`, 809–810행). ss에서도 다섯 연결이 **전부 P의 같은 포트**(36593, 47647, 52757, 54405)로 끝난다. TCP에는 일방향 읽기가 없으니 pull 방식의 READ라도 P 쪽 소프트웨어가 바이트를 보내야 한다(ss에서도 P가 송신자다). 결국 D 쪽 전용 스레드 네 개가 여는 연결을 P 쪽에서는 워커 하나가 받아 처리한다. 이 워커를 도는 스레드(`nixlUcxSharedThread`, 356–373행)가 GPU→호스트 스테이징과 소켓 복사를 도맡는다면 약 20 Gbps의 공유 상한이 설명된다. 나는 이 설명을 **가설**로 제시한다. CPU 프로파일은 없다.

**(d) 저자 자신의 이전 데이터도 같은 방향이다.**
- D1c: 스레드 16개로 늘려도 626 → 621 ms. 1,024 하한 때문에 조각이 3개로 그대로였다.
- D1f: 블록 32로 디스크립터가 128 KiB × 1,120개가 되면 조각이 1024+96의 2개로 줄고, 7변수 대비 TTFT가 466 → 569 ms로 나빠졌다.

연결 수를 늘리는 유일한 방법은 `split_batch_size`를 낮추는 것이다. 그런데 31B에서는 이미 네 연결이 공유 상한에 막혀 있다.

**수정.** 문장을 "The rate saturated near 20 Gbps whether three or four connections were active (per-connection 4.5 Gbps with four), while a single connection alone reached the 9.5 Gbps cap; a shared per-node limit, plausibly the single prefill-side UCX worker that serves all connections, binds before the per-flow cap. Whether more connections or a faster serving path is the next lever is untested." 정도로 바꾼다. 결론의 "NIXL's parallel connections make [the transfer] far cheaper"도 같은 한정을 받는다.

### [필수 3] m의 정의와 식 (1)·(2)·체크리스트의 적용 범위

**m의 이름.** 식 (2)는 m을 "the effective number of parallel connections (1.5–1.8 in our tuned runs)"로 정의한다. 실제로는 26B가 2~3연결로 1.5, 31B가 4연결로 1.8이다. m은 연결 수가 아니라 **실효 전송률 ÷ C_flow**라는 경험 비율이다. 이름을 "rate multiplier"로 바꾸고 이렇게 정의해야 한다.

**m은 상수가 아니다.** 세 방향으로 움직인다. 모두 E8 로그로 확인했다(`r3_xfer.py`).

| 조건 | 10초 창 중앙값 | m (÷9.54) | 원인 |
|---|---|---|---|
| 26B 4K, GPU당 0.25, 7변수 | 14.16 Gbps | 1.48 | 2~3조각 |
| 같은 조건, 두 번째 7변수 런(toy 프록시, 본문 미보고) | 13.46 Gbps | 1.41 | 같음 |
| 26B 4K, **GPU당 3** (판정 부하) | 10.65–10.92 Gbps | 1.12–1.14 | 겹친 전송이 공유 상한을 나눔 |
| 26B 4K, **GPU당 4** (판정 부하, 6런) | 8.77–9.88 Gbps | 0.92–1.04 | 같음 |
| 26B 4K, GPU당 5 | 6.74 Gbps | 0.71 | 같음 |
| **31B 채팅, GPU당 4** (표 2의 1P1D 점) | 7.68–7.80 Gbps | 0.80–0.82 | 창 평균 디스크립터 621–1,022 → 대부분 나뉘지 않음 |

- 판정이 실제로 갈리는 부하(26B GPU당 3–4, 31B 채팅 GPU당 4)에서 m은 0.8–1.1이다.
- 체크리스트 3번은 "m between 1.5 and 2"를 쓰라고 한다. 채팅 크기(26B는 64 MiB 미만, 31B는 약 128 MiB 미만)와 부하 운전 모두에서 전송 시간을 1.5–2배 과소평가하게 된다.
- 26B 4K에서 GPU당 3–4일 때 KV 부하는 7.0–9.4 Gbps다. 약 20 Gbps 공유 상한 대비 이용률 0.35–0.47이므로, 전송당 전송률이 83 → 110–134 ms로 늘어난 것과 맞는다. 흐름당 상한 × 4(38 Gbps)를 용량으로 잡으면 이 둔화를 설명하기 어렵다.

**식 (1)의 범위.** V(L) ≈ 100 MiB + 10 KiB·L은 4K–32K에 맞춘 식이다. 입력이 슬라이딩 윈도우보다 짧으면 고정 100 MiB 항이 성립하지 않는다. 26B 워밍업 ShareGPT 전송은 평균 25.9 MiB였는데, 식 (1)은 최소 101 MiB를 준다. 체크리스트 3번은 "KV volume from Eq. (1)"을 쓰라고 하므로, 채팅 워크로드에 적용하면 4배 이상 틀린다. 일반형 V(L) = b_g·L + b_l·min(L, W)(좌장 A6 제안)로 쓰거나 "for L at least the sliding window"를 붙인다.

**수정.** m의 정의를 바꾼다. 크기별 값을 표로 보인다(1,024 디스크립터 미만은 m ≤ 1, 26B 4K 약 1.5, 31B 4K 약 1.65–1.8). 판정 부하에서의 m을 보고한다. 체크리스트 3번에 "at low load and for transfers of at least 1,024 descriptors"를 붙이고 식 (1)의 범위를 명시한다.

### [필수 4] 7변수 묶음은 "no better"가 아니라 조금 나쁘다. 원인도 측정돼 있다

§4.5는 "the full set of seven UCX variables gave 14.16 Gbps, no better"라고 쓰고, 부록 C는 "the 8 MB buffers may have been capped by net.core.wmem_max"라고 쓴다. ss 표본을 보면 추측이 아니라 확인이 가능하다.
- **수신 창이 고정됐다.** 7변수 런(26B, 31B)에서 D 쪽 `rcv_ssthresh`가 358,614–371,896 B에 묶여 있다. 세그먼트만 조건에서는 자동 조정으로 3.49–5.47 MB까지 커졌다. `UCX_TCP_RCVBUF=8m`이 SO_RCVBUF를 명시해 자동 조정을 끄고, 기본 `rmem_max`로 잘린 값에 머문 것으로 보인다.
- **송신자가 수신 창에 막혔다.** P 쪽 busy 시간 중 `rwnd_limited` 비율이 7변수 39–44%, 31B 38–45%다. 세그먼트만은 0%, 기본은 0–8%다.
- **연결당 전송률이 낮다.** busy 중 전송률이 7변수 7.25–7.57 Gbps, 세그먼트만 7.78–8.39 Gbps다.
- 10초 창 중앙값은 세그먼트만 14.97, 7변수 14.16과 13.46(두 런)이다. 7변수 쪽이 5–10% 낮다.

실무자는 부록 C를 그대로 복사할 것이다. 그리고 본문의 모든 분리 런(E4–E8)이 이 묶음을 썼으므로, 본문의 전송 항(84, 283 ms)은 세그먼트만 썼을 때보다 약간 길었을 가능성이 있다(분리에 불리한 방향이라 결론은 보수적이다).

**수정.** "no better"를 "5–10% lower in two runs; the fixed 8 MB receive buffer, capped by the kernel limit, disabled autotuning and left the sender receive-window-limited for about 40% of its busy time"로 고친다. 두 번째 7변수 런(13.46)도 보고한다. 체크리스트 4번에 "do not set UCX_TCP_SNDBUF/RCVBUF unless net.core.rmem_max/wmem_max are raised"를 추가한다. 부록 C의 "may have been"은 "were"로 고친다.

### [필수 5] 버전과 네트워크 환경 보고 (1차 필수 5의 잔여)

분할 규칙(1,024 디스크립터, 워커 = 스레드 + 1)은 NIXL 버전에 묶인 동작이다. 그런데 원고에는 vLLM v0.30.0만 있고 **NIXL(노트상 1.4.1)과 UCX 버전이 없다.** 환경 정보는 이미 공개된 ss 표본에 다 들어 있다.
- MTU·MSS: `pmtu:9001 mss:8949`
- 혼잡 제어: 전 연결 `cubic`
- 배치 그룹 안 최소 RTT: 25–33 µs (`minrtt`)
- 부하 중 평활 RTT: p50 0.26–1.08 ms, p90 5.2–5.9 ms

한 문단이면 된다. 커널 버전, `rmem_max`·`wmem_max`, `tcp_slow_start_after_idle`, iperf3 버전과 옵션도 함께 적는다. 4.97 Gbps가 5 Gbps에서 MTU 9001의 TCP/IP 헤더를 뺀 값(5 × 8949/9001 = 4.971)과 맞는다는 점도 한 줄로 넣으면 흐름당 상한 해석이 단단해진다.

### [권장 6] 대기열 문장의 계산과 모형 선택을 보인다

"adding an M/D/1 waiting time explains the difference (about 2.2 s)"를 검산했다.
- S = 140 MiB / 0.995 Gbps = 1.180 s, λ = 0.5 /s, ρ = 0.59.
- 평균 대기 Wq = ρS/[2(1−ρ)] = 0.85 s. 비전송 316 ms와 합치면 **2.35 s**다.
- 실측 2.19 s는 TTFT **중앙값**이다. M/D/1에서 ρ = 0.59이면 41%가 대기 없이 지나가므로 중앙값 예측은 평균보다 낮다.
- tbf는 여러 전송의 바이트를 섞어 보내므로 FIFO보다 프로세서 공유에 가깝다. M/G/1-PS로 계산하면 0.316 + S/(1−ρ) = 3.2 s가 나와 실측을 넘는다.

따라서 "explains"는 강하다. S, λ, ρ와 통계 종류를 적고 "consistent with (2.0–2.35 s depending on the statistic)"로 낮춘다. 2 Gbps(예측 1.03 s, 실측 0.954 s)와 3 Gbps(0.758 s 대 0.744 s)도 같이 보이면 설득력이 커진다. 부하 운전에서의 대기열은 m·C_flow가 아니라 [필수 2]의 공유 상한을 용량으로 써야 할 가능성이 높다.

### [권장 7] "segment size alone accounts for the whole gain"의 범위

26B 140 MiB, GPU당 0.25에서는 뒷받침된다(세그먼트만 14.97, 7변수 14.16/13.46). 그러나 범위를 한정해야 한다.
- 팔마다 한 번씩 쟀다. 팔들의 프록시와 서버 이력도 다르다. 기본과 세그먼트만은 toy 프록시에 새로 띄운 서버였고, 7변수(aio)는 GPU당 3–5 부하를 지난 서버였다.
- 31B(560 MiB)나 판정 부하에서는 재지 않았다. 큰 전송에서 `UCX_RNDV_FRAG_SIZE=cuda:8M`의 효과는 모른다.
- §3.1의 "one of them, the TCP segment size"는 TX와 RX 두 변수다. 초록의 "UCX's default 8 KB TCP segment"도 RX 기본값(64 KB)을 함께 바꾼 결과다.
- g7 배치 그룹 없는 환경의 D1d TTFT 이득(626 → 466 ms)을 세그먼트 크기에 귀속하는 것은 다른 환경으로 외삽한 것이다.

메커니즘 설명도 [필수 2]의 관찰로 바꾸는 편이 정확하다. 8 KB 세그먼트는 연결 각각이 아니라 공유 서비스 경로의 처리량을 약 4.6–5 Gbps로 묶었고(연결 수와 무관), 256 KB는 그 상한을 약 20 Gbps로 올렸다.

### [권장 8] EFA 문단의 두 가지 교란

가격과 GDR 서술은 적절하게 한정돼 있다. 내가 직접 확인한 내용은 다음과 같다.
- AWS EFA 문서: g6e.8xlarge와 g7e.8xlarge는 RDMA read/write Yes, GDR No. g7.8xlarge는 GDR Yes.
- Vantage 온디맨드 가격: g7e 8xlarge $5.268 / 2xlarge $3.363 = 1.57배, g6e $4.529 / $2.242 = 2.02배, g7 $4.086 / $2.520 = 1.62배. "roughly 1.6–2×"가 맞다.

다만 두 가지를 추가해야 한다.
- 같은 AWS 문서에 따르면 NIXL은 **Libfabric(≥1.21.0)** 을 통해 EFA를 쓴다. EFA로 가면 UCX 경로가 아니라 다른 백엔드를 쓰게 된다. g6e·g7e 8xlarge에는 GDR이 없으므로 호스트 스테이징도 남는다. "EFA would shrink the transfer term"은 추정이라고 밝힌다.
- 8xlarge는 vCPU가 32개로 2xlarge의 4배다. [필수 2]의 공유 상한이 CPU나 진행 스레드에 묶인 것이라면 8xlarge에서는 TCP만으로도 빨라질 수 있다. EFA의 이득을 따지려면 8xlarge TCP 대조가 필요하다는 점을 한 줄 적는다.

MPTCP(AWS 문서가 단일 흐름 대역폭 대안으로 제시), ENI 추가(g7e.2xlarge 최대 4개), UCCL·Mooncake TE 같은 TCP 쪽 대안도 향후 과제로 한 문장 넣는다.

### [권장 9] 그림 5(c)의 지표와 표본 간격

캡션은 "Share of transfer time … from socket samples every 0.1 s"라고 쓴다.
- 실제 표본 간격은 중앙값 **120.5 ms**다(`sleep 0.1`에 ss 실행 시간이 더해진다).
- 26B 전송(73–93 ms)은 표본 간격보다 짧다. 그래서 막대는 "전송 시간 중 비율"이 아니라 "120 ms 창 안에서 64 KiB 넘게 움직인 연결 수"다. 12 MiB 조각은 약 10 ms 만에 끝나서 창 하나에만 걸리므로 "2개" 막대가 부풀려진다.

전송별 조각 수와 분할(64/64/12)을 보이는 그림이 더 정확하고 해석도 쉽다. 31B는 활동 연결 수별 합계 전송률(1개 9.5, 4개 19.2 Gbps) 패널을 추가하면 [필수 2]를 한눈에 보여 준다.

### [권장 10] 나뉘지 않은 전송이 TTFT 꼬리를 만든다

전송이 통째로 한 연결로 가면 시간이 두 배 가까이 된다. 26B는 123 ms 대 78 ms, 31B는 약 0.55 s 대 0.27 s다. 4K에서는 런당 0–3회로 드물다. 그러나 31B 4K처럼 TTFT 예산에 여유가 없는 구성에서는 이런 한 건이 요청별 판정을 바꿀 수 있다. 한 문장으로 적는다.

### [권장 11] 호스트 스테이징 (1차 9번의 잔여)

측정 조건(g7, GPU 메모리 0.70, 호스트 32 GiB)과 링크 전송률이 7.3–9.4 Gbps로 오히려 올랐다는 사실을 한 줄 덧붙인다. 비용이 링크에서 vLLM의 복사로 옮겨 갔다는 해석이 그래야 가능하다.

---

## 사소한 지적

1. §3.2의 "MiB×8×1.048576/s"를 그대로 계산하면 Mbit/s가 나온다. "/ms"로 쓰거나 10⁻³을 곱한다. 값(4.45/14.97/14.16/17.28)은 맞다.
2. 1.5–1.8배는 10초 창 중앙값 기준이다. 전송 수로 가중한 평균은 14.01/14.62/15.77 Gbps(m = 1.47/1.53/1.65)다. 어느 통계인지 밝힌다.
3. 그림 5 윗제목 "(0.5 and 0.25 requests/s)"는 합계이고 캡션은 GPU당(0.25, 0.125)이다. 하나로 맞춘다.
4. 표 1의 g7.2xlarge 가격이 "--"다. Vantage 기준 $2.520(us-east-1, 온디맨드 Linux, 직접 확인)이다.
5. 크레딧 문장에 g7.2xlarge(기준 40 / 버스트 60 Gbps, 세션 B·D)도 넣는다. 부하보다 훨씬 커서 결론은 같다.
6. 잔차 범위는 노트의 "−26~+87 ms"(RESULTS.md 1009행)인데 본문은 28–87 ms다. 음수 점이 어디서 나왔는지 밝히거나 범위를 맞춘다.
7. 푸시 문장 "468–533 MB per request against 560"은 MiB다. 단위를 통일한다.
8. "each carrying 22–27%"는 기본 조건 한 연결이 21.5%다. "about a quarter each over a run"이 정확하다.
9. "Within the zone, one TCP flow reached at most 4.97 Gbps"에 네 인스턴스 쌍(g5·g6e·g7·g7e) 모두에서 같았다는 사실을 적는다.
10. "four worker threads …, each with its own UCX endpoint"는 D 쪽(요청자)만의 이야기다. P 쪽에는 워커 하나만 있다([필수 2]).
11. 본문의 "0.82 to 0.99"(D1a → D1d, 합계 1 req/s)는 safe_runs.csv에서 0.822 → 0.989로 확인했다. 본문에 출처 런을 적어 두면 좋다.

---

## 저자에게 묻는 질문

1. 전송별 디스크립터 수와 조각 수를 로그로 남길 수 있는가? 1,024 미만 전송이 공유 워커 연결(다섯째)로 가는지 직접 확인해 달라.
2. 140 MiB 전송의 디스크립터가 1,108–2,240으로 달라지는 이유는 무엇인가? 병합은 vLLM에서 일어나는가, NIXL에서 일어나는가?
3. vLLM이 NIXL 진행 스레드(`enable_prog_thread`)를 켜는가? 31B 전송 중 P 노드의 스레드별 CPU 사용률(`top -H`, `perf`)에서 한 스레드가 100%에 붙는가?
4. `split_batch_size`를 `kv_connector_extra_config`로 넘길 수 있는가? 26B 4K에서 256으로 낮추고 스레드를 8로 올린 한 점이면 "연결 수 대 공유 상한"을 가를 수 있다.
5. 31B 4K와 판정 부하(26B GPU당 3–4)에서 세그먼트만 조건을 쟀는가? `RNDV_FRAG_SIZE`는 큰 전송에서 효과가 있는가?
6. `net.core.rmem_max`/`wmem_max`, 커널 버전, `tcp_slow_start_after_idle`, iperf3 버전과 옵션은 무엇이었나? 특히 iperf3가 3.16 이전(단일 스레드) 판이었다면, 한 프로세스가 38 Gbps를 낸 셈이므로 공유 상한의 원인 후보가 좁혀진다.
7. 1 Gbps 대기열 검산은 평균과 중앙값 중 어느 것을 비교했나? FIFO 대신 프로세서 공유를 쓰면 어떻게 되는가?
8. 31B 채팅(표 2)의 1P1D 전송은 대부분 나뉘지 않은 한 연결 전송(m ≈ 0.8)으로 보인다. 이 점에서 식 (2)의 추정값은 실측과 얼마나 맞는가?

---

## 점수·확신도

- **점수 3.5/5** (네트워크·클라우드 절 기준). 1차의 크레딧, tc, EFA 전제, 단위, 아핀 전송량 문제는 거의 해결됐다. 원자료 공개 수준도 높아졌다. 그러나 새로 추가한 메커니즘 서술 세 가지가 공개 데이터와 맞지 않는다. 초록의 "each transfer over four TCP connections", "remaining lever는 연결 수", "m = 연결 수 1.5–1.8을 체크리스트에 그대로 쓰라"가 그것이다. 필수 1–5는 모두 문장·그림·부록 수정과 기존 데이터 재분석으로 끝난다. 반영되면 4/5로 올린다. 논문의 중심 결론(청크 크기와 분리의 관계)은 이 절의 수정에 영향을 받지 않는다.
- **확신도 4/5.** ss 원자료와 vLLM 전송 로그는 직접 재분석했고, NIXL v1.4.1 소스의 해당 행도 직접 읽었다. 공유 상한의 원인(P 쪽 단일 워커·진행 스레드, 스테이징, CPU)은 소스와 데이터로 뒷받침되지만 프로파일이 없으므로 가설로 남긴다. UCX TCP의 원격 읽기 구현 세부는 소스를 확인하지 않았다.

---

## 확인한 문서와 도구

**웹 자료 (2026-09-30)**
- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/efa.html — **직접 확인(WebFetch).** 지원 인스턴스 표(g6e.8xlarge·g7e.8xlarge GDR No, g7.8xlarge GDR Yes, 모두 RDMA read/write Yes), "NIXL integrates with Libfabric 1.21.0 and later", "EFA … at no additional cost".
- https://instances.vantage.sh/aws/ec2/{g7e.8xlarge, g6e.8xlarge, g7.8xlarge, g7.2xlarge, g7e.2xlarge} — **직접 확인(WebFetch).** $5.268 / $4.529 / $4.086 / $2.520 / $3.363. AWS 가격표 API와는 대조하지 않았고, g7e·g7 8xlarge 페이지는 추출문에 지역 표기가 불분명했다.
- https://raw.githubusercontent.com/ai-dynamo/nixl/v1.4.1/src/plugins/ucx/ucx_backend.cpp — **직접 받아 읽음(curl).** 645–646, 675–683, 721, 754–757, 776–780, 809–810, 356–373행. 사본은 스크래치 `nixl_v141/ucx_backend.cpp`에 있다. 같은 파일의 main 판은 WebFetch 요약으로만 봤고 근거로 쓰지 않았다.
- NIXL libfabric/EFA 관련 WebSearch — 검색 요약만 봤고 근거로 쓰지 않았다.
- AWS ac.html, ena-express.html, ec2-instance-network-bandwidth.html — 1차 심사 때 직접 확인했고, 이번에는 다시 받지 않았다(저자 측 r0 노트와 일치).
- UCX 소스 — 확인하지 않았다.

**재분석 스크립트 (읽기 전용, 스크래치 `reviews_v1/`)**
- `r3_ss_bursts.py`: 전송 단위 묶음, 분할 패턴, 다섯째 연결, TCP 상태
- `r3_ss_pieces.py`: 단일 전송의 조각 수
- `r3_ss_busy.py`: P 쪽 busy 중 전송률, rwnd_limited 비율
- `r3_ss_interior.py`: 내부 구간 합계와 연결당 전송률
- `r3_ss_timeline.py`: 31B 전송별 구간 시계열
- `r3_xfer.py`: vLLM 전송 로그 → Gbps, m, 판정 부하 값

**검토한 저장소 자료**
- paper/en/main.tex, paper/figures_v1/v1_transfer.pdf, figures.json
- harness/make_figures_v1.py, ss_sample.sh, ss_parse.py, serve.sh, pd_proxy.py, toy_proxy_instr.py
- configs/lib_E8.sh, run_E8.sh, run_E8x.sh, run_D1.sh, run_D2.sh
- results/E8/ss/*.txt (8개), results/E8/xfer_E8/*.log (17개), results/safe_runs.csv
- RESULTS.md (세션 D, E4, E5, E8 절)
