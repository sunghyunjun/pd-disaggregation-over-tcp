# Reviewer 1 (LLM 서빙 시스템) 2차 심사평 — v1

대상: "Chunked Prefill or Disaggregation? Prefill–Decode Serving over TCP on Single-GPU Cloud Instances" (paper/en/main.tex, v1)
근거: v1 원고·그림(figures.json), 세션 E8 원자료(bench.json 47개, prom.txt, proxy_trace, metrics_E8, ss, xfer_E8), RESULTS.md, harness 코드. 모두 읽기만 했다.
재현 스크립트: `reviews_v1/r1_v1_checks.py`(프록시 상한, 디코드 서버 ITL 히스토그램, 소켓 busy·rwnd), `reviews_v1/r1_e8_runs.py`(런별 실패 원인·TTFT·TPOT·동시 요청 수).

## 요약

v1은 1차 심사의 핵심 지적을 실험으로 받았다. 세션 E8에서 복제본의 청크를 스윕했고, 그 결과 헤드라인을 뒤집었다. 26B 4K는 청크 1,024 복제본이 1P1D와 같은 부하를 지키면서 첫 토큰이 더 빨랐다. 31B 대화는 청크 256 복제본이 GPU당 6건을 통과했다. 제목과 틀("choose the chunk first, and disaggregate when no acceptable chunk meets the stall limit")도 이제 데이터와 맞는다. 프록시 GC가 만든 전역 정지를 계측으로 가려낸 것, P–D 연결 수를 소켓으로 센 것도 좋은 작업이다.

남은 문제는 세 갈래다. 첫째, 복제본 쪽에 새 측정 산물이 있다. `harness/rr_proxy.py`가 aiohttp 기본 커넥터(동시 연결 100)를 써서, GPU당 4건 이상에서 복제본의 TTFT 실패가 전부 프록시 대기열에서 나왔다. 복제본의 "failed at 5 (0.78)"는 서버 한계가 아니다. 둘째, 판정 규칙과 측정 범위가 결과를 만든 곳이 있다. 26B 4K의 "4 대 3"은 반복 횟수 비대칭(복제본 1런, 1P1D 3런)에서 나왔다. "분리만 가능"한 영역(26B 30 ms, FP8 30–40 ms)은 측정하지 않은 1,024 미만 청크에 기댄다. 논문 자신의 청크–멈춤 관계로 외삽하면 26B의 30 ms 칸과 FP8의 40 ms 칸은 청크 512에서 뒤집힐 가능성이 크다. 1차의 실패 양상(튜닝하지 않은 노브에 기댄 "분리 우위")이 더 작은 영역에서 반복된다. 셋째, 분리 쪽 해석에 빠진 것이 있다. 디코드 노드 자체의 멈춤(31B 전역 정지는 기존 데이터로 이미 디코드 서버 쪽으로 판명된다), P 노드 청크 2,560 고정, 연결 수 귀속과 E4 스레드 16 실험의 모순이다.

두 산물(프록시 상한, 반복 비대칭)을 고치면 결론의 방향은 v1보다 오히려 복제본 쪽으로 더 기운다. 방향은 견고하고, 고칠 곳은 수치와 "분리만 가능" 문장, 그리고 분리 쪽 튜닝 범위의 공개다.

## 1차 지적 반영 점검

| 항목 | 판정 | 근거(v1 위치·수치) |
|---|---|---|
| R1-1 복제본 청크 미튜닝 | 반영 | E8 스윕(§4.2, Fig 2, Table 2): 26B 1,024–2,048, 31B 256/512, FP8 1,024. 잔여: 1,024에서 멈춤(약점 3), P 청크 미튜닝(약점 5) |
| R1-2 31B 메커니즘·상대 SLO | 대부분 반영 | §4.2 프롬프트 길이 구간별 달성률(<200 토큰 99–100%, 400–800 12%), 청크 256 검증. §3.5에 50 ms 근거와 사전 등록 이탈. 상대 기준 판정표는 없음 |
| R1-3 식 1·"almost entirely"·선형 가정 | 부분 | 61–85%, 아핀 V(L), 저부하 한정, M/D/1 보정, 16K 예시 수정(§3.2, §4.6). 잔여: 아핀식의 정의역(약점 8), hold-out 오차 미보고 |
| R1-4 m 메커니즘 | 부분 | ss로 연결 4+1개 측정(§4.5, Fig 5c). 잔여: "four worker threads" 귀속과 E4 스레드 16 무효 결과의 모순(약점 6) |
| R1-5 관련 연구 누락 | 대부분 반영 | §2에 TaiChi, EcoServe, ThunderServe, HexGen-2, Etalon, Andes, KVDirect 추가. 잔여: TaiChi 서술 부정확(약점 7) |
| R1-6 라우터 비대칭 | 부분 | PD용 aiohttp 프록시 추가, GC 원인 규명(§4.7). 새 비대칭: 복제본 프록시의 연결 상한 100(약점 1) |
| R1-7 비율 규칙 | 반영 | §4.8 "we draw no rule for the prefill-to-decode ratio" |
| R1-8 격자 해상도·pull 범위 | 부분 | 한계 절 "Coarse rate grids". pull-after-prefill 한정은 PR 56874 실패와 EFA 논의로 간접 반영 |
| 사소(정확성 결과, host staging, "Faster GPUs", tc 합산, 단위, §3.1 설정) | 반영 | §4.8 Correctness, §4.5, 부록 캡션, §3.3 |
| 사소(출력 512 고정·랜덤 입력의 한계, Fig 1 마커) | 미반영 | 한계 절에 없음. Fig 1은 여전히 "Replicas / single node" 한 마커 |
| 좌장 A1(26B 4K 조건) | 반영(대체) | 결론 자체를 청크 스윕 결과로 바꿈 |
| 좌장 A2(31B 50 ms 한정·메커니즘) | 반영 | §4.2, Table 2 |
| 좌장 A3(SLO 변경 공개) | 부분 | §3.5, 부록 D. 상대 기준 판정표 없음 |
| 좌장 A4(전역 정지·프록시 비대칭) | 반영, 새 문제 | §3.3, §4.7. 복제본 프록시 상한은 새 문제(약점 1) |
| 좌장 A5(비율 규칙 격하) | 반영 | §4.8 |
| 좌장 A6(식 1) | 부분 | 약점 8 |
| 좌장 A7(m 정의·메커니즘) | 부분 | 약점 6 |
| 좌장 A10(관련 연구) | 대부분 반영 | 약점 7 |
| 좌장 B1(청크 스윕) | 반영 | 1,024 미만 미측정(약점 3) |
| 좌장 B2(전역 정지 원인) | 반영 | 26B는 규명. 31B 이벤트는 "did not trace further"(약점 4) |
| 좌장 B3(연결 수) | 반영 | ss 4+1, 세그먼트 단독 대조 포함 |
| 좌장 B4(31B 저부하 복제본) | 해당 없음 | 청크 256이 GPU당 6건 통과 |

## 강점

- 결정적인 실험을 돌렸고, 결과가 원래 주장과 반대로 나오자 헤드라인을 바꿨다. 두 기준선(청크 2,560, 최적 청크)을 나란히 보고한 것은 이 분야 측정 논문에서 드물고 가치가 크다.
- Gemma 4의 멀티모달 예산 검사(2,496은 video 항목의 예산이고, image·audio·video를 모두 끄면 풀린다)를 찾아 적었다. 실무자가 바로 쓸 수 있는 발견이다.
- 전역 정지를 프록시 이벤트 루프 지연, GC, 디코드 서버 ITL 히스토그램 스냅샷으로 갈랐다(§4.7, Fig 7). 같은 시드에서 같은 시각에 재현되는 서버 쪽 사건까지 구분한 방법론이 모범적이다.
- 소켓 수를 직접 셌고(4+1, 바이트 몫 22–27%), UCX 이득을 세그먼트 크기 하나로 귀속하는 절제 실험을 했다.
- 청크 2,560 대조군이 E7과 일치해(0.950 대 0.933–0.958) 날짜 효과를 배제했다.
- 31B의 탈락을 겹친 프롬프트 길이로 설명하고, 그 설명대로 청크 256이 구제한다는 것을 보였다(예측과 검증의 짝).

## 주요 약점

### 1. [필수] 복제본 프록시의 동시 연결 상한(100)이 GPU당 4건 이상에서 복제본 판정을 만들었다

- 위치: §4.3 "1,024-token replicas passed up to 4 requests/s per GPU (0.977, interval 0.950–0.997) and failed at 5 (0.78)", Table 2, Fig 3a, Fig 4 아래 줄, 초록 "3--4 requests/s per GPU against the replicas' 4", §3.3 "Replicas used a small aiohttp round-robin proxy".
- 문제: `harness/rr_proxy.py`는 `aiohttp.ClientSession(timeout=...)`만 만들고 커넥터를 지정하지 않는다. aiohttp 기본 `TCPConnector`는 동시 연결을 100개로 제한한다. 스트리밍 응답은 끝날 때까지 연결을 쥐므로, 진행 중 요청이 100개를 넘으면 나머지는 프록시 안에서 기다린다. 반면 `harness/pd_proxy.py`는 `TCPConnector(limit=0)`(무제한)이고, vLLM 테스트 프록시도 httpx `max_connections=None`이다. E8에서 분리 쪽 프록시만 대칭화하면서 방향이 반대인 새 비대칭이 생겼다.
- 원자료 근거(`r1_v1_checks.py` 1절):
  - 청크 1,024, GPU당 5건: 실패 393건이 전부 TTFT다(간격 실패 0). TTFT p50은 237 ms인데 p90은 72.4 s, p99는 113 s다. 클라이언트 쪽 진행 중 요청은 121개에서 311개로 계속 늘었다. 같은 시간 복제본 서버(prom.txt, 한 노드)의 `num_requests_running`은 약 45–52에 머물렀고, `num_requests_waiting`은 0–3, KV 사용률은 약 10%였다. 서버는 포화하지 않았고 대기열은 프록시에 있었다.
  - TTFT 1 s 초과 실패는 모두 진행 중 요청이 100개 이상일 때 도착한 요청이다. 청크 1,024의 GPU당 4건(33건, 최소 100), 5건(393건, 최소 100), 6건(746건, 최소 100), 청크 1,536의 GPU당 4건(89건, 최소 100), 31B 청크 256의 GPU당 6건(4건, 최소 101)이 그렇다.
  - 따라서 청크 1,024의 GPU당 4건 0.977은 프록시 대기열만으로 깎인 값이다(간격 실패 0). 5건 0.782와 6건 0.640은 복제본의 한계가 아니다. 5건에서도 입장한 요청의 최대 간격은 p50 38.4 ms, p90 39.7 ms였다.
  - 이전 세션도 같은 프록시를 썼다. E2 B2 채팅 GPU당 12건(동시 167, TTFT 실패 83건), E5 26_B2 채팅 r32와 26_B3 r48(주의 런, "client-limited"로 분류)이 같은 원인인지 다시 봐야 한다.
- 중요한 이유: v1의 결론 방향은 오히려 강해진다. 그러나 "Per GPU the two approaches support about the same load", 표 2의 "4 (1,024), \$0.49", 그림 3a의 5–6건 하락, 그림 4 아래 줄에서 느슨한 SLO(1.5–5 s × 50–100 ms)의 "Similar" 칸이 모두 이 상한에 걸려 있다. 논문 §4.7이 경고하는 바로 그 종류("proxy stalls that look like ...")의 산물이 복제본 쪽에 있다는 점도 독자가 가장 먼저 짚을 것이다.
- 조치:
  - `rr_proxy.py`에 `connector=aiohttp.TCPConnector(limit=0)`를 넣는다. 청크 1,024 복제본(26B 4K)을 GPU당 4·5·6건 각 2회, 31B 청크 256을 GPU당 6·8건, 같은 날 1P1D(aiohttp)를 GPU당 4·5건 각 2회 잰다. 두 노드 재기동 포함 약 1–1.5시간, 약 \$10이다.
  - 재측정하지 않으면: 진행 중 요청이 100개를 넘은 복제본 점은 모두 "proxy-limited"로 표시하고 판정에서 뺀다. 복제본 한계는 "≥4 (26B), ≥6 (31B)"로 쓴다. "failed at 5 (0.78)"는 삭제하고, 표 2·그림 3·그림 4를 다시 만든다.
  - 부록 B(Practical pitfalls)에 한 줄 넣는다: "aiohttp's default connector caps concurrent upstream connections at 100; set `limit=0` in any streaming proxy."

### 2. [필수] "분리만 가능"한 영역은 측정하지 않은 청크 아래에만 있다

- 위치: 초록 "Disaggregation remained the only option when the gap limit was tighter than chunking reached (30~ms for 26B, 30--40~ms for its FP8 variant)", §4.4 첫 항목, RQ3 "disaggregation won only at 30~ms (26B NVFP4) and 30--40~ms (26B FP8)", 결론.
- 문제: 이 칸들은 스윕을 1,024에서 멈췄기 때문에 생긴다. 논문 자신의 데이터가 청크를 더 줄이면 멈춤이 더 짧아진다고 예측한다.
  - 같은 멀티모달 설정 안에서 GPU당 1건의 최대 간격 중앙값은 1,536 → 38.8 ms, 1,024 → 27.6 ms다. 프리필 토큰당 약 22 µs에 디코드 몫 약 5 ms를 더한 아핀 관계다. 이 관계로 청크 512는 GPU당 1건에서 약 16–17 ms, GPU당 2건(청크 1,024에서 32.1 ms, 중앙 ITL 10.5 ms)에서 약 21–22 ms로 외삽된다. 설정이 다른 2,560 점까지 이은 완만한 기울기(약 13.5 µs/토큰)를 써도 각각 약 21 ms, 25 ms다(모두 측정값이 아니다).
  - 1P1D가 30 ms에서 통과하는 것은 GPU당 2건까지다(E7 att30 0.919–1.000, E5 0.954). GPU당 3건에서는 0.66–0.77이다. 청크 512 복제본이 GPU당 2건에서 30 ms를 지킬 가능성이 높다.
  - FP8은 청크 1,024의 최대 간격이 43 ms(GPU당 0.5–1건)다. 2,560 → 1,024 기울기(약 12 µs/토큰)나 NVFP4의 기울기(약 22 µs/토큰)로 외삽하면 청크 512는 약 32–37 ms다. 40 ms 칸은 뒤집힐 가능성이 크고, 30 ms 칸은 남을 수 있다.
  - 작은 청크의 비용은 데이터에 거의 보이지 않는다. 같은 부하에서 TPOT 평균은 청크 1,024와 1,536/2,560이 같다(GPU당 2건 12.6 대 12.8 ms, 4건 20.6 대 22.0 ms). TTFT는 29–34 ms 늘었을 뿐이다. 1,024가 바닥이라는 근거가 없다. 31B는 좌장 분석과 §4.2가 "스텝당 프리필 약 200토큰 이하"를 요구하므로 256에서 멈춘 것이 타당하다. 26B는 그렇지 않다.
- 중요한 이유: 1차의 치명 결함과 같은 구조다. 튜닝하지 않은 복제본 노브에 "분리만 가능"을 기댄다. 초록에 발견으로 올라가 있어 영향이 크다.
- 조치:
  - 26B NVFP4 청크 512(가능하면 768)를 GPU당 1–4건, FP8 청크 512를 GPU당 0.5–2건 잰다. 약 1시간이면 되고 약점 1의 재측정과 같은 세션에 붙일 수 있다.
  - 재지 않으면 문장을 바꾼다. "tighter than the shortest stall we measured with chunks of 1,024 tokens or more (30 ms for 26B, 30--40 ms for FP8); our affine fit predicts that a 512-token chunk would bring the 26B replicas' stall to about 16--25 ms, which we did not measure." 초록에서는 이 문장을 빼거나 조건문으로 낮춘다.

### 3. [필수] 26B 4K의 "4 대 3"과 원가 차이는 반복 횟수 비대칭에서 나왔다

- 위치: §3.5 "Supported load is the highest measured rate at which every repeat reaches 0.9 attainment", 표 2 "4 (1,024), \$0.49 | 3, \$0.63", §4.3, 그림 4 가운데 칸(1 s/50 ms의 "Replicas serve more").
- 문제: 판정을 가르는 GPU당 4건에서 청크 1,024 복제본은 1런(시드 8007, 0.977)이고, 1P1D는 aiohttp로 3런(8007: 0.954, 9007: 0.992, 셋째 0.885)과 테스트 프록시로 4런이다. "every repeat" 규칙은 많이 반복한 쪽을 불리하게 만든다. 같은 시드(8007)끼리 비교하면 둘 다 통과한다(0.977 대 0.954). 게다가 복제본의 0.977은 약점 1의 프록시 대기열로 깎인 값이다. 1P1D 0.885 런의 간격 실패(95+18건)는 디코드 서버 쪽 단일 사건(서버 ITL >50 ms 113건)이다. 그림 4의 3/4 = 0.75는 격자 한 칸 차이라서 "Replicas serve more (≤0.8×)" 판정이 해상도 한계에 걸려 있다.
- 조치: 판정점에서 양쪽 반복 수를 같게 하거나(각 3회 이상), 시드 짝 비교를 쓰거나, 평균 달성률과 블록 부트스트랩 구간으로 판정한다. 약점 1을 고치기 전에는 "Both reached 4 requests/s per GPU on the matched seed (0.977 and 0.954); the replicas' upper limit was set by our proxy (Section X)"로 쓴다. 원가는 "equal at 4 requests/s per GPU"로 바꾼다. 초록의 "3--4 requests/s per GPU against the replicas' 4"도 고친다.

### 4. [필수] 디코드 노드의 자체 멈춤을 해석에 넣어야 한다. 31B 전역 정지는 이미 디코드 서버 쪽으로 판명된다

- 위치: §4.7 "For 31B chat, our aiohttp proxy still showed two and four global events per run, which we did not trace further", "Removing the global events raises 1P1D's attainment at 4 requests/s per GPU from 0.77--0.99 to 0.94--0.99", 결론 "Its benefit, protecting decodes from other requests' prefills, is exactly what chunked prefill provides by other means."
- 문제:
  - 31B 이벤트는 기존 데이터로 추적된다. 디코드 서버 ITL 히스토그램의 전후 차이에서 50 ms 초과 토큰 간격이 두 런에 110개와 316개다(`r1_v1_checks.py` 2절). 프록시 계측에는 5 ms 넘는 2세대 GC도, 20 ms 넘는 루프 지연도 없다. 프록시가 상류에서 받은 동시 간격 묶음(15개 스트림 이상이 5 ms 안에 40 ms 넘게 멈춤)은 두 런에 35개이고, 한 번에 18–76개(대개 35개 이상) 스트림이 40–62 ms씩 멈췄다. 클라이언트 간격 실패(110, 139건)는 이것으로 설명된다. 31B 1P1D의 경계 판정(0.903/0.924)은 프록시가 아니라 디코드 서버의 멈춤 때문이다.
  - 따라서 "Removing the global events ... 0.94--0.99"에는 프록시 산물(테스트 프록시 GC)과 실제 서버 멈춤(aiohttp 셋째 런의 113건)이 섞여 있다. 서버 쪽 사건은 빼면 안 된다.
  - 디코드 노드는 부하가 오르면 요청별 최대 간격도 길어진다. 중앙값이 GPU당 0.25건 12.2 ms, 3건 27.6 ms, 4건 34.6 ms다. 같은 GPU 수에서 1P1D는 두 GPU 몫의 디코드 배치를 GPU 하나에 싣는다. 그래서 중앙 ITL이 복제본보다 길다. GPU당 2건 13.6 대 10.5 ms, 3건 15.6 대 13.2 ms, 4건 20.8 대 15.7 ms다. GPU당 4건에서 요청별 최대 간격 중앙값은 1P1D(aiohttp) 33.8–35.5 ms, 청크 1,024 복제본 36.7 ms로 같다. 1P1D가 30 ms에서 GPU당 2건까지만 통과하는 이유가 이것이다.
- 중요한 이유: 논문의 틀은 "분리는 디코드를 프리필에서 보호한다"이다. 그러나 이 스택의 TCP 분리는 디코드 노드에 자체 멈춤이 있고, 같은 GPU 수에서 디코드 배치를 두 배로 만든다. 이것이 분리 이득의 상한을 정하는 서빙 쪽 메커니즘이며, 결론 문장이 이를 빠뜨린다.
- 조치:
  - §4.7의 31B 문장을 "the decode server logged 110 and 316 gaps over 50 ms while the proxy showed no collection or loop lag, so these are decode-side pauses"로 바꾼다. 제거 후 달성률은 프록시 원인 사건만 빼서 다시 계산한다.
  - 헤드투헤드(§4.3)에 중앙 ITL, TPOT, 요청별 최대 간격을 함께 싣고, "at equal GPU count the decode node carries both GPUs' decode batch"를 한 문장 넣는다. 결론 문장도 이에 맞춰 고친다.
  - [권장] 메커니즘 가설을 적고, 가능하면 확인한다. 저자 노트(RESULTS.md 486행)대로 NIXL 전송 발행과 완료 폴링이 엔진 스텝 루프에서 돈다면, 디코드 노드에서는 KV 도착 처리와 전송되지 않은 프롬프트 토큰의 계산이 디코드 스텝에 섞인다. 26B 사건이 같은 시드에서 같은 시각에 반복된 점은 도착 순서(버스트)와 관련이 있음을 시사한다. 디코드 스텝 시간과 그 스텝에서 완료된 전송 수를 짝지은 트레이스 하나면 가려진다.

### 5. [필수] 분리 쪽 튜닝 범위를 공개해야 한다. P 노드 청크는 병목인데 고정됐다

- 위치: §3.3 "Prefill nodes used a 2,560-token chunk", §4.3, 한계 절.
- 문제: v1은 복제본의 청크만 조정했다. 분리 쪽에는 판정 부하에서 결과를 바꿀 수 있는 노브가 남아 있다.
  - P 노드 청크: P는 디코드를 하지 않으므로 큰 청크의 멈춤 비용이 없다. 2,560이면 4K 프롬프트가 두 스텝으로 나뉜다. GPU당 5건에서 1P1D를 무너뜨린 것은 P다. P 서버의 `num_requests_waiting`이 최대 33(running 1–2)까지 쌓였고, TTFT p50은 1.45 s였다. GPU당 4건에서 P의 nvidia-smi SM 활성률은 79–83%, D는 100%였다. P 청크를 4,096–8,192로 키우면 P 처리량이 늘고 TTFT에서 한 스텝이 빠질 수 있다.
  - UCX 묶음: 헤드투헤드의 분리 런은 모두 변수 7개 묶음을 썼다. 그 안의 `UCX_TCP_RCVBUF=8m` 명시 설정은 수신 버퍼 자동 조정을 끄고 `rmem_max`에 잘렸을 가능성이 크다. ss를 보면 변수 7개 묶음에서는 연결별 busy 시간 중 39–44%(31B는 38–45%)가 `rwnd_limited`였고, 세그먼트만 바꾼 설정에서는 0%였다. 저부하 중앙값도 14.16 대 14.97 Gbps로 조금 낮다. 부하가 오르면 평균 전송 시간이 83 ms(GPU당 0.25건)에서 110, 119, 173 ms(3, 4, 5건)로 늘어나므로, 부하 구간에서 이 차이가 더 클 수 있다.
  - 3노드: 2P1D의 붕괴는 테스트 프록시 GC 때문이었고(§4.7), 고친 프록시로는 3노드 분리를 재지 않았다. 4K는 P가 병목이므로 2P1D가 가장 유력한 분리 구성이다.
- 조치: §4.3과 한계 절에 "the disaggregated side kept a 2,560-token prefill chunk, the seven-variable UCX set, and 1P1D only"를 명시한다. [권장] P 청크 8,192와 세그먼트 단독 UCX로 1P1D(aiohttp)를 GPU당 4·5건 각 2회 잰다. 약 40분이다. 이 측정은 분리 쪽을 유리하게 만드는 유일한 남은 실험이라서, 공정성 논증에서 값이 크다.

### 6. [필수] 연결 수 귀속과 "we did not test that"이 저자 자신의 E4 결과와 충돌한다

- 위치: §4.5 "This matches the four worker threads of vLLM's NIXL connector in v0.30.0, each with its own UCX endpoint", "more connections, not other UCX settings, are the remaining lever; we did not test that", §5.3 "$m$ depends on NIXL's thread count", 식 (2) 설명 "$m$ the effective number of parallel connections".
- 문제:
  - RESULTS.md E4-2 (c)에서 NIXL 스레드를 4에서 16으로 올렸는데 실효 대역폭은 13.99 대 13.86 Gbps로 같았다(D1c에서도 차이 없음). 연결이 스레드 수를 따른다면 16스레드는 연결을 늘렸어야 하고, 연결이 남은 지렛대라면 전송률이 올랐어야 한다. 둘 중 하나는 틀렸다. 스레드를 늘리는 실험은 이미 했으므로 "we did not test that"도 부정확하다.
  - 저자 노트의 소스 독해(분할 크기 = max(ceil(N/threads), 1,024 디스크립터))는 26B 4K(디스크립터 약 2,240개)를 불균등한 세 조각(약 46/46/9%)으로 나눈다고 예측한다. ss가 보여 준 "네 연결 22–27% 균등"과 맞지 않는다. 네 연결의 출처(NIXL 스레드, UCX 레인, 장치 채널 등)는 확정되지 않았다.
  - m의 이름도 맞지 않는다. 전송 중 활성 연결은 평균 2.3개(26B), 3.4개(31B)인데 m은 1.5–1.8이다. ss의 커널 busy 시간으로 계산한 연결별 전송률은 7.1–8.9 Gbps로 흐름 상한 9.54 Gbps의 74–93%다(`r1_v1_checks.py` 3절). m은 "활성 연결 수 × 연결별 효율"에 해당하는 실효 배수다.
- 조치: E4의 스레드 16 무효 결과를 본문에 적는다. 귀속 문장은 "four connections whose origin we did not establish; raising NIXL's thread count from 4 to 16 did not change the rate (session E4)"로 낮춘다. "remaining lever"는 "splitting transfers into more pieces (NIXL's split size or worker count, which vLLM does not expose) is untested"로 바꾼다. §5.3의 "$m$ depends on NIXL's thread count"는 삭제한다. m은 "effective parallelism"으로 부르고, 연결별 busy 전송률을 근거로 싣는다.

### 7. [필수] 관련 연구: TaiChi는 이미 청크 크기를 변수로 쓴다

- 위치: §2 "Our results reproduce that boundary on TCP-connected single-GPU nodes and add the chunk size as the variable that moves it."
- 문제: TaiChi 초록은 "Three configurable sliders control the ratio between these instances and their chunk sizes"라고 쓴다. 청크 크기가 경계를 옮긴다는 것은 TaiChi의 설계 전제다. 또 청크 프리필 자체는 SARATHI(Agrawal et al., 2023, arXiv 2308.16369)가 처음 제안했고, Sarathi-Serve(OSDI'24)는 토큰 예산을 둔 stall-free 배칭을 정식화했다. §1과 §2의 "Sarathi-Serve introduced chunked prefill"은 정확하지 않다. DistServe도 청크 프리필 계열 기준선(DeepSpeed-MII의 SplitFuse)과 비교했다. "청크 프리필이냐 분리냐"는 빠른 인터커넥트에서는 이미 다뤄진 질문이다.
- 조치: "TaiChi treats chunk size as one of its sliders; we measure where the boundary falls over cloud TCP with stock vLLM, judged per request, and show that a multimodal budget check can pin the chunk above that boundary"로 바꾼다. 청크 프리필의 출처는 SARATHI로 고친다.

### 8. [필수] 식 (1)은 슬라이딩 윈도우보다 긴 입력에서만 성립한다

- 위치: §3.2 "the transferred KV volume is affine rather than proportional in the input length $L$", 식 (1) "$V(L) \approx 100$ MiB $+ 10$ KiB $\times L$", 절차 3 "KV volume from Eq. (1)".
- 문제: 식 (1)은 L이 0에 가까워도 100 MiB를 예측한다. 실측은 다르다. 26B 대화(입력 약 150–250토큰)의 전송량은 요청당 27.7–30.0 MB다(E5 xfer 로그, 예: `26_1P1D_sharegpt_r16`). 식 (1)은 약 101–103 MiB를 준다. 31B 대화는 평균 107.5 MB였는데(E8 `31_1P1D_aio`), 31B의 식은 없다. 절차 3을 따르는 실무자는 26B 대화의 전송량을 3–4배 과대평가한다.
- 조치: 일반형 $V(L) = b_g L + b_l \min(L, W)$를 쓰고, 모델별 W, $b_g$, $b_l$을 적는다. 식 (1)은 "for $L \ge W$"로 한정한다. 31B 수치도 싣는다. 전송이 작을 때 m < 1이 되는 점(1차 좌장 지적)도 절차 3에 "for transfers of 100 MiB or more"로 반영한다.

### 9. [권장] "default Gemma 4 deployment"와 2,560 고착 시나리오를 다시 확인해야 한다

- 위치: RQ3 "Against replicas stuck at a 2,560-token chunk, as a default Gemma 4 deployment is, disaggregation over TCP served about 3$\times$ more at 50~ms."
- 문제:
  - 2,560은 vLLM의 기본값이 아니라, 이미지만 끈 설정에서 받아들여진 최소값이다. 이전 vLLM v1 릴리스는 70 GiB 이상 GPU의 OpenAI API 서버에 `max_num_batched_tokens` 8,192를 기본으로 줬다. v0.30.0에서도 그렇다면 RTX PRO 6000(96 GB)의 기본 배포는 4K 프롬프트를 한 스텝에 넣어 2,560보다 긴 멈춤을 낸다. v0.30.0 값을 확인해야 한다.
  - 멀티모달을 끌 수 없는 배포에도 대안이 있을 수 있다. vLLM v1 스케줄러는 `--long-prefill-token-threshold`로 요청 하나가 한 스텝에 받는 프리필 토큰을 제한한다. `max_num_batched_tokens`를 2,496 이상으로 둔 채 요청당 조각을 1,024로 묶을 수 있다. 동시 프리필이 여럿이면 예산을 다시 채울 수 있지만, 중간 부하에서는 대부분의 스텝을 묶을 가능성이 있다.
  - 우선순위 스케줄링은 필요 없다고 본다. v1 스케줄러는 이미 실행 중인 디코드를 먼저 배정하고, `--scheduling-policy priority`는 단계가 아니라 요청 사이의 순서를 바꾼다. `--max-num-seqs 256`도 병목이 아니었다(D 노드 동시 약 120–130, 복제본 노드당 50 안팎). 독자가 물을 질문이므로 한 문장씩 적어 두면 좋다.
- 조치: v0.30.0 기본값을 적는다. "default" 대신 "the smallest chunk accepted with images disabled only"라고 쓴다. 청크 2,560(image:0)에 threshold 1,024를 준 복제본을 GPU당 1–2건에서 한 번 재거나, 미검증 대안으로 명시한다.

### 10. [권장] 청크–멈춤 관계의 서술을 데이터에 맞춘다

- 위치: RQ1 "Shrinking the chunk shortened it almost in proportion (26B: 48 to 28~ms from 2,560 to 1,024 tokens)", 초록 "it fell from 48 to 28~ms", 절차 1 "It equals the time of a step carrying one full chunk", §4.5 끝 "at some cost in prefill throughput and TTFT".
- 문제:
  - 청크가 2.5배 줄 때 멈춤은 1.75배 줄었다. 비례가 아니라 아핀(디코드 스텝 + 토큰당 비용)이다. 청크는 디코드 토큰을 포함한 스텝 예산이라서, 스텝당 프리필 토큰은 "청크 − 실행 중 디코드 수"다.
  - 48 → 28은 멀티모달 설정이 다른 두 점을 잇는다. 같은 설정 안의 계열은 2,048 → 1,536 → 1,024에서 52.3 → 38.8 → 27.6 ms다. 초록은 같은 설정 계열로 쓰거나 설정 차이를 밝힌다.
  - 31B 대화처럼 프롬프트가 청크보다 짧으면 멈춤은 겹친 프롬프트 길이가 정한다. 절차 1은 "a step carrying min(chunk, co-scheduled prompt tokens)"가 정확하다.
  - 작은 청크의 처리량 비용은 관찰되지 않았다(약점 2의 TPOT 비교). 복제본 상한도 약점 1 때문에 측정되지 않았다. "at some cost in prefill throughput"은 "at a TTFT cost of about 30 ms; we saw no throughput cost up to 4 requests/s per GPU"로 바꾼다.

### 11. [권장] 긴 입력은 분리가 이길 수 있는 남은 영역인데 두 튜닝 이전 데이터뿐이다

- 위치: §4.8 "Input length (g7, before transfer tuning)", 결론.
- 문제: 작은 청크의 비용이 분명히 드러나는 곳은 16K–32K 입력이다. 청크 1,024면 16K 프롬프트가 16스텝 이상 걸리고, 복제본의 TTFT가 늘어난다. 분리가 우위를 가질 수 있는 영역인데, 현재 16K 데이터는 g7, 전송 튜닝 전, 청크 2,560 복제본이다. 결론("choose the chunk first")은 4K 이하 입력에서만 검증됐다.
- 조치: 결론의 적용 범위를 "inputs up to 4K tokens"로 명시하거나, 16K에서 청크 1,024 복제본 대 튜닝된 1P1D를 GPU당 0.25–0.5건에서 잰다.

## 사소한 지적

- 그림 5c: ss 샘플 간격 0.1 s는 26B 전송 한 건(73–93 ms)보다 길다. "창 안에서 바이트가 움직인 연결 수"는 동시에 바쁜 연결 수와 다르다. 커널의 `busy:` 시간을 쓰면 연결별 전송률(26B 7.1–8.4 Gbps)과 실효 병렬도를 더 정확히 낼 수 있다. 캡션에 샘플 해상도의 한계를 적는다.
- 초록의 31B 문장 "for 31B chat, 4 against at least 6"에서 1P1D의 4도 가장 높은 측정 부하(검열값)다. "at least 4 (borderline, highest measured) against at least 6"이 정확하다. 표 2와 서술을 맞춘다.
- 표 2의 FP8 행은 날짜와 프록시가 다르다(복제본 E8 aiohttp, 1P1D E7 테스트 프록시). 캡션에 적는다.
- §3.3에 D 노드도 청크 2,560이었다는 것을 적는다.
- "Replicas also always delivered the first token sooner"는 중앙값 기준임을 밝힌다. 약점 1 때문에 고부하 복제본의 TTFT 꼬리는 프록시 산물이다.
- 한계 절에 출력 512 고정(요청이 멈춤에 노출되는 시간이 김)과 랜덤 토큰 입력(MoE 전문가 부하가 비현실적일 수 있음)을 추가한다(1차 사소 지적).
- 그림 1은 여전히 복제본과 단일 노드를 같은 마커로 묶는다.
- §3.6의 주의 런 5개("client-side proxy reached its CPU limit")를 약점 1의 연결 상한으로 다시 판정한다.
- 그림 4 캡션에 "a ratio of 0.75 is one step of our rate grid"를 넣어 해상도 한계를 알린다.

## 질문

1. vLLM v0.30.0이 RTX PRO 6000(96 GB)에서 OpenAI API 서버에 주는 `max_num_batched_tokens` 기본값은 무엇인가?
2. `rr_proxy.py`의 연결 상한을 풀면 청크 1,024 복제본은 GPU당 몇 건에서 무너지는가? 그때 원인은 TTFT인가, 간격인가?
3. NIXL 스레드 16에서 P–D 사이 TCP 연결은 몇 개였는가? 네 연결은 스레드, UCX 레인, 장치 채널 중 어디서 오는가?
4. v0.30.0에서 Gemma 4 하이브리드 KV의 블록 크기는 얼마이고, 디코드 노드가 전송받지 않고 직접 계산하는 프롬프트 토큰은 요청당 몇 개인가?
5. 디코드 노드의 스텝 시간 급증(31B에서 41–62 ms)은 전송 완료나 새 요청 입장과 같은 스텝에서 일어나는가?
6. P 노드 청크를 8,192로 키우면 1P1D의 GPU당 한계가 5건으로 오르는가?
7. `--long-prefill-token-threshold`는 Gemma 4에서 멀티모달을 켠 채 동작하는가?

## 점수

- 점수: 3 (weak accept 경계, 실무자용 프리프린트 기준). 1차 2점에서 올린다. 결정적 실험을 돌리고 결론을 정직하게 바꾼 점을 높이 산다.
- 필수 1–3(프록시 상한, "분리만 가능" 영역, 반복 비대칭)을 고치면 4로 오른다. 셋 다 약 1–1.5시간짜리 세션 하나(청크 1,024 고부하 재측정, 청크 512, P 청크 8,192)로 함께 해결되며, 측정하지 않더라도 문장과 표의 수정으로 공개 가능한 수준이 된다.
- 확신도: 4.
