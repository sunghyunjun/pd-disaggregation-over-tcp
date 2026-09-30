# 좌장 메타리뷰 (2차, 원고 v1)

대상: "Chunked Prefill or Disaggregation? Prefill–Decode Serving over TCP on Single-GPU Cloud Instances" (paper/en/main.tex, draft v1, 2026-09-30)
근거: 2차 리뷰 5건(r1_systems 3/5, r2_methods 4/5, r3_network 3.5/5, r4_repro 3.5/5, r5_writing 4/5), 1차 기록(paper/reviews/2026-09-30_v0/), 좌장 직접 확인. 저장소는 읽기만 했다.
좌장 확인 스크립트(이 폴더의 `r6/`, 읽기 전용):
- `r6_proxycap.py`: 감사 통과 복제본 런 전체에서 클라이언트 쪽 진행 중 요청 수와, 진행 중 100개 이상일 때 도착한 요청의 실패 수
- `r6_keypoints.py`: 결정적 맞대결 점의 시드, 새·옛 1토큰 규칙 달성률, TTFT p50/p99, 요청별 최대 간격과 ITL 중앙값, 진행 중 100개 미만으로 도착한 요청만의 달성률
- `r6_xfer.py`: vLLM 전송 로그의 10초 창 전송률과 m(= 전송률 ÷ 9.54 Gbps), 부하별
- 그 밖에 인라인으로 확인했다: 디코드 서버 ITL 히스토그램 전후 차분, 1P1D의 간격 실패 비율, NIXL v1.4.1 소스 해당 행(R3 사본), R2의 E7 사건 분류(`r2/a6_e7events.py`), R3의 31B 소켓 내부 구간 분석(`r3_ss_interior.py`)

기준: 학회 투고가 아니라 실무자가 인용할 독립 프리프린트(Zenodo). 저자와 합의한 틀은 "청크 프리필과 분리는 함께 따져야 하고, TCP 분리가 틀린 선택은 아니다"이다. "반드시 고칠 것"은 틀렸거나, 오해를 부르거나, 공개하지 않았거나, 전문 독자가 논문을 기각할 근거로 쓸 만한 것으로 한정한다.

---

## 1. 판정

**중폭 수정(major revision). 원고 수정과 기존 데이터 재분석만으로 공개할 수 있다.** 새 측정(E9)은 필수가 아니다. 다만 26B 청크 512 한 항목은 결론의 모양을 바꿀 수 있어서, 약 $15–18짜리 짧은 세션을 권한다(3절).

v1의 방향은 "청크를 조정한 복제본 앞에서 TCP 분리는 엄격 SLO에서 더 많이 처리하지 못했다"이다. 이 방향은 v1보다 오히려 단단해졌다. 이번 심사에서 드러난 두 측정 산물(복제본 프록시의 연결 상한, 반복 수 비대칭)이 모두 복제본에 불리하게 작용했기 때문이다. 고칠 것은 방향이 아니라 경계값과 기제 서술이다.
- v1 초록의 핵심 주장 여덟 개 중 다섯 개는 문구를 바꿔야 한다: 26B "3–4 against 4", 31B "4 against at least 6", "always delivered the first token sooner", "the only option", "four TCP connections … 1.5–1.8×".
- 본문에서 데이터와 맞지 않는 서술이 다섯 곳이다: 복제본 "failed at 5 (0.78)", 2P1D 붕괴의 프록시 귀속, 31B에서 aiohttp 프록시가 한계를 올렸다는 암시, "more connections … are the remaining lever", "four connections per transfer".

저자 틀("TCP 분리는 틀리지 않았다")에 대한 좌장 의견: v1은 이 틀을 30–40 ms 칸에 기대고 있는데, 그 칸이 가장 약하다((c) 참조). 더 튼튼한 근거는 이미 데이터에 있다. vLLM v0.30.0에서 Gemma 4는 video 입력을 켜 두는 한 청크를 2,496 아래로 내릴 수 없다. 그 조건에서 분리는 50 ms 한도로 약 3배를 처리했다. 멀티모달 입력을 끌 수 없는 배포는 실제로 흔하다. 이 시나리오를 분리가 이기는 대표 사례로 세우기를 권한다.

### 1.1 쟁점별 판정

**(a) 26B 4K의 "4 대 3": 유지되지 않는다. "GPU당 약 4로 동률, 복제본 쪽은 프록시가 정한 하한"으로 쓴다.**
- 복제본(청크 1,024)은 GPU당 4를 시드 8007로 한 번만 쟀다(0.977). 1P1D(aiohttp)는 세 시드를 쟀다(8007/9007/10007에서 0.954/0.992/0.885). 같은 시드끼리 비교하면 둘 다 통과한다(0.977 대 0.954, 차이 +0.023 [−0.007, 0.053], R2). "모든 반복 ≥0.9" 규칙은 반복이 많은 쪽을 불리하게 만든다.
- 1P1D를 떨어뜨린 시드 10007의 0.885는 디코드 서버 쪽 단일 사건이다(서버 ITL >50 ms 113건, 좌장 확인).
- 복제본의 0.977도 프록시 대기열에 깎인 값이다((e) 참조). 진행 중 100개 미만일 때 도착한 요청 1,248건만 보면 달성률은 1.000이다.
- 원가 "$0.49 대 $0.63"은 부하가 다른 두 점(4 대 3)을 비교한 것이다. 같은 GPU당 4에서는 $0.49 대 시드별 $0.48–0.54다(R2).

**(b) 31B 대화 "4 대 ≥6": 방향은 유지된다. 1P1D는 "≈4, 경계(측정한 최고 요청률)"로, 복제본은 "≥6"으로 쓴다.**
- 1토큰 규칙은 옳다. 출력이 한 토큰이면 토큰 간격이 없으므로 TTFT로만 판정해야 한다. 규칙은 양쪽에 대칭으로 적용됐다. 복제본 청크 256 GPU당 6은 옛 규칙 0.978에서 새 규칙 0.998이 됐다.
- 그러나 결정적 판정이 이 규칙에 걸려 있다. aiohttp 1P1D 두 런은 옛 규칙으로 0.899/0.878(탈락), 새 규칙으로 0.924/0.903(통과)이다(좌장 재계산). 이 사실은 부록 D에 적어야 한다.
- 표 2 주석이 암시하는 프록시 효과("test proxy 2, aiohttp 4")는 없다. 같은 시드에서 aiohttp가 오히려 낮다(8000: 시험 프록시 0.963(E5)·0.933(E7), aiohttp 0.924 / 9000: 0.958 대 0.903). 시험 프록시가 "2"로 판정된 이유는 시드 10000의 0.885 한 런이다. aiohttp로는 이 시드를 재지 않았다. 두 프록시를 합치면 GPU당 4의 여섯 런 중 다섯 런이 0.9 이상이고, 평균은 0.928이다.
- 1P1D의 탈락 사건은 서버에서 났다. aiohttp 두 런에서 디코드 서버가 50 ms 초과 간격을 110건과 316건 기록했고, 프록시 GC와 루프 지연 기록은 없다(좌장 확인). 게다가 1P1D의 디코드 노드는 두 GPU 몫의 디코드를 한 GPU에 싣는다. GPU당 4에서 중앙 ITL이 33 ms로, GPU당 6의 복제본(31 ms)보다 길다.
- 결론: 옛·새 규칙 어느 쪽으로 봐도 복제본은 6을 통과하고 1P1D는 4 부근이 한계다. 방향은 견고하다. 1P1D를 GPU당 5–6에서 재지 않았으므로 배수는 쓰지 않는다.

**(c) 30–40 ms "분리만 가능" 칸: 위험하다. "우리가 측정한 청크(26B는 1,024 이상) 가운데서"라는 조건을 붙여야 하고, 초록에서는 조건문으로만 남긴다.**
- 같은 멀티모달 설정 안에서 GPU당 1의 요청별 최대 간격 중앙값은 청크 1,024/1,536/2,048에서 27.6/38.8/52.3 ms다.
- 순수 디코드 스텝(같은 부하의 중앙 ITL 8.6 ms)에서 이으면, 청크 512는 GPU당 1에서 약 18 ms 이하다(청크가 커질수록 기울기가 커지는 볼록한 관계라 직선 보간이 위쪽 값이다). 부하 효과(GPU당 1 → 3에서 +6 ms)를 더해도 GPU당 2–3에서 약 22–24 ms다. R2의 직선 외삽(약 15 ms)은 절편(2.5–2.9 ms)이 디코드 스텝보다 작아서 과소 추정이다. 좌장은 15–25 ms 범위로 본다.
- 1P1D는 30 ms에서 GPU당 2까지만 통과하고 3에서는 0.66–0.77이다. 따라서 26B NVFP4의 30 ms 칸은 청크 512에서 "비슷함"이나 "복제본 우세"로 뒤집힐 가능성이 크다.
- FP8은 청크 1,024의 최대 간격이 43 ms다. 청크 512는 약 27–37 ms로 추정된다. 40 ms 칸은 뒤집힐 가능성이 크고, 30 ms 칸은 알 수 없다.
- 이 칸들이 모두 뒤집히면, 측정한 범위에서 조정한 청크를 이긴 분리 사례는 하나도 남지 않는다. 그래서 E9의 가장 중요한 항목이다.

**(d) 전송 서술: 네 가지를 고쳐야 한다. 기제 서술은 R3의 재분석을 받아들인다.** 좌장은 NIXL v1.4.1 소스(R3 사본)와 전송 로그, 소켓 표본으로 확인했다.
- 분할 규칙: `ucx_backend.cpp`에서 디스크립터가 1,024개 미만이면 전송을 나누지 않는다. 1,024개 이상이면 `max(N / 전용 스레드 수, 1024)`개씩 나눈다. 26B 4K 전송(10초 창 평균 디스크립터 약 1,800–2,200)은 **2–3조각**, 31B 4K(약 4,000–4,500)는 **4조각**이다. 채팅 전송(31B 중앙값 약 860)은 **나뉘지 않는다**. "NIXL spread each transfer over four TCP connections"는 26B에 틀렸다.
- 다섯째 연결: 전용 워커 네 개 외의 공유 워커다(`num_workers ≤ 전용 수`이면 `전용 수 + 1`). 나뉘지 않은 전송과 워밍업 전송이 모두 이 연결로 간다. "1–3%의 부수 채널"이 아니다.
- 공유 상한 약 19–21 Gbps: 31B에서 네 연결이 모두 움직인 120 ms 구간 110개의 합계 중앙값은 19.2 Gbps(최대 21.1)이다. 연결 하나만 움직일 때는 9.5 Gbps다(R3 스크립트 재실행). vLLM 로그의 31B 창 최댓값도 19.7 Gbps다. iperf 4흐름(38 Gbps)의 절반이므로 병목은 링크가 아니라 노드 쪽 공유 경로다. 원인(P 쪽 단일 워커, 스테이징 복사, CPU)은 검증되지 않았다.
- "more connections … are the remaining lever": 31B에서는 이미 네 연결이 공유 상한에 막혀 있으므로 데이터와 맞지 않는다. 철회한다. 26B는 2–3조각(약 14–15 Gbps)이라 조각을 늘리면 약 20 Gbps까지는 오를 여지가 있다. 이것도 검증되지 않았다.
- m: "병렬 연결 수"가 아니라 **전송률 배수**(실효 전송률 ÷ 흐름당 상한)다. 부하에 따라 움직인다(좌장 확인). 저부하·분할 전송에서 26B는 1.41–1.57, 31B는 1.81이다. 판정 부하인 26B GPU당 3에서는 1.12–1.14, GPU당 4에서는 0.92–1.04, GPU당 5에서는 0.71이다. 31B 대화 GPU당 4에서는 0.81–0.82다. 체크리스트의 "m between 1.5 and 2"는 부하나 작은 전송에서 전송 시간을 1.5–2배 과소평가한다.
- 7변수 묶음은 "no better"가 아니라 5–10% 낮았다(14.16·13.46 대 14.97 Gbps). R1과 R3가 독립적으로 원인을 같게 짚었다. `UCX_TCP_RCVBUF=8m`이 자동 조정을 끄고 수신 창을 약 360 KB에 묶어, 송신자가 busy 시간의 약 40%를 수신 창에 막혔다.

**(e) 복제본 프록시의 100 연결 상한: 복제본 한계를 하한으로 바꾼다. 방향은 복제본 쪽으로 더 기운다.**
- 사실: `rr_proxy.py`는 aiohttp 기본 커넥터(동시 연결 100, 두 노드 합계)를 썼다. `pd_proxy.py`는 `limit=0`, 시험 프록시는 httpx 무제한이다. 1P1D 런은 GPU당 4에서 진행 중 115–125개까지 올라갔고 막히지 않았다.
- 26B 4K에서 요청 수명은 약 10–11 s다. 리틀의 법칙에 따르면 상한은 GPU당 약 4.5–5에서 걸린다. 좌장 확인 결과(`r6_proxycap.py`, `r6_keypoints.py`)는 다음과 같다.

| 복제본 런 | 달성률 | 도착 시 진행 중 ≥100 | TTFT 실패 (그중 ≥100일 때 도착) | 간격 실패 | ≥100 아래로 도착한 요청의 달성률 |
|---|---|---|---|---|---|
| 26B 청크 1,024, GPU당 3 | 1.000 | 0% (최대 92) | 0 | 0 | 1.000 |
| 26B 청크 1,024, GPU당 4 | 0.977 | 13% | 33 (33) | 0 | 1.000 (TTFT p99 434 ms, 최대 536 ms) |
| 26B 청크 1,024, GPU당 5 | 0.782 | 94% | 393 (393) | 0 / 1,800 | 1.000 (100건) |
| 26B 청크 1,024, GPU당 6 | 0.640 | 95% | 746 (746) | 32 / 2,160 | 1.000 (100건) |
| 26B 청크 1,536, GPU당 4 | 0.719 | 31% | 89 (89) | 322 | 간격만으로도 탈락 |
| 31B 청크 256, GPU당 6 | 0.998 | 3% | 4 (4) | 0 | 1.000 |

- 따라서 26B 4K 복제본의 "failed at 5 (0.78)"와 그림 3(a)의 GPU당 5–6 하락은 서버 한계가 아니다. 복제본 한계는 "≥4"다. GPU당 5에서 입장한 요청은 간격 한도를 모두 지켰다(0/1,800). 같은 부하에서 1P1D는 요청의 54%가 50 ms 넘는 간격을 겪었다(40 ms 초과는 97%). 상한을 풀면 26B 4K의 엄격 SLO 비교가 "동률"에서 "복제본 우세(5 대 4)"로 바뀔 가능성이 높다. 측정값은 아니다.
- 복제본의 TTFT 꼬리(GPU당 4에서 p99 2,056 ms)도 전부 프록시 대기열이다. 대기열 없이 들어간 요청은 p99 434 ms, 최대 536 ms였다. 1P1D는 p99 970–1,254 ms다.
- 영향받지 않는 것: 청크 2,560 복제본의 모든 판정(26B 4K GPU당 1–2에서 진행 중 최대 80 미만), 즉 "약 3배" 주장. GPU당 3 이하의 모든 4K 판정. 31B 복제본 ≥6(상한에 걸린 실패 4건).
- 과거 세션: E2 대화 GPU당 12(0.981, 상한 실패 83건)와 E5 26_B2 대화 GPU당 16(주의 런, 0.975)은 상한에 걸렸지만 통과했다. E5 26_B3 대화 GPU당 16(주의 런, 0.768)의 실패는 전부 상한 때문이다(진행 중 최대 1,680). §3.6의 주의 런 사유("client-side proxy reached its CPU limit")는 복제본 주의 런 두 개에 대해서는 연결 상한으로 바꿔야 한다.

**(f) 프록시 GC 귀속: 범위를 "26B 1P1D, 세션 E8"로 좁힌다.**
- 성립하는 것: 시험 프록시에서 26B GPU당 4 세 런의 정지 5건 중 4건이 25–40 ms 2세대 GC와 겹친다. 계측이 세 층(프록시, 클라이언트 몰림, 서버 히스토그램 0건)에서 일치한다(R2 재확인).
- 성립하지 않는 것:
  - aiohttp 26B 시드 10007의 사건과 31B 대화의 사건은 모두 서버 쪽이다. 디코드 서버의 50 ms 초과가 113, 110, 316건이고, 토큰 몰림이 없으며, 프록시 GC와 루프 지연도 없다.
  - E7 2P1D(GPU당 3, 0.769)의 정지 5건 중 GC형 몰림 신호가 있는 것은 1건뿐이다(R2 분류 좌장 재실행). E7에는 프록시 계측도 없다. GC형 1건만 빼면 0.834로 여전히 탈락한다. "it explains the collapse of our three-node 2P1D"는 철회한다. 1차에서 철회한 "decode node could not hold"의 반대 방향 과잉 주장이다.
  - "Removing the global events … 0.94–0.99"는 프록시 사건과 서버 사건을 섞었다. 서버 사건은 분리 구성의 실제 비용이므로 빼면 안 된다. GC형만 빼면 시험 프록시 런은 0.77–0.98에서 0.88–0.99가 되고, aiohttp 런은 그대로다.
  - "failed in a way replicas did not"는 같은 정의(5 ms 안에 15요청 이상이 50 ms 넘게 멈춤)로는 틀렸다. 청크 1,536 복제본에도 이런 사건이 있다. 차이는 모양이다. 복제본의 사건은 청크 스텝 하나 길이(50 ms를 조금 넘음)이고 몰림이 없으며, 한 복제본의 요청만 멈춘다.
- 31B 대화에서 "test proxy made earlier limits conservative"는 성립하지 않는다. 같은 시드에서 시험 프록시가 더 높았다.

### 1.2 v1 주장별 상태

| v1 주장 | 상태 | 조치 |
|---|---|---|
| 시스템 퍼센타일이 요청별 멈춤을 가린다(202런 중 28) | 유지 | 202에 주의 런 2개 포함 표기 |
| 청크 크기가 복제본 멈춤을 정한다 | 유지, 문구 수정 | "bounds", 같은 설정 안에서 선형, 대화는 min(청크, 겹친 프롬프트) |
| 청크 2,560 복제본 대비 약 3배(26B 4K, 50 ms) | 유지 | 프록시 상한과 무관. "default deployment" 대신 video 제약으로 설명 |
| 26B 4K 튜닝 청크 대비 "4 대 3", $0.49 대 $0.63 | 수정 | 동률(약 4), 복제본은 하한, 같은 부하 원가 |
| 복제본 "failed at 5 (0.78)" | 철회 | 프록시 상한 |
| 31B 대화 "4 against at least 6", 프록시별 2 대 4 | 수정 | ≈4 경계, 프록시 효과 없음, 1토큰 규칙 공개 |
| 복제본이 첫 토큰을 항상 먼저 | 수정 | 중앙값 기준. 꼬리는 프록시 산물 |
| 30 ms(26B), 30–40 ms(FP8)는 분리만 | 위험 | 측정 청크 조건. E9 1순위 |
| 첫 토큰 추가분의 61–85%가 전송(저부하) | 유지 | 31B 평균 정의(283 대 전송 가중 298 ms) |
| UCX 세그먼트로 3.4배 | 유지, 문구 | 송·수신 두 변수. 7변수 묶음은 5–10% 낮음 |
| 전송마다 연결 네 개, 1.5–1.8× | 수정 | 26B 2–3조각, 31B 4조각, 1,024 디스크립터 미만은 나누지 않음 |
| 다섯째 연결 1–3% | 수정 | 공유 워커, 나뉘지 않은 전송이 지나는 경로 |
| 남은 지렛대는 연결 수 | 철회 | 31B에서 약 20 Gbps 공유 상한 |
| m = 병렬 연결 수(1.5–1.8), 체크리스트 1.5–2 | 수정 | 전송률 배수, 부하와 크기에 따라 0.7–1.8 |
| 식 (1) V(L) ≈ 100 MiB + 10 KiB·L | 범위 한정 | L ≥ 슬라이딩 윈도우, 대화 전송량 별도 |
| M/D/1이 1 Gbps 차이를 "explains" | 문구 | "consistent with", S·λ·ρ 명시 |
| 프록시 GC가 전역 정지를 설명 | 범위 축소 | 26B E8만 |
| 2P1D 붕괴는 프록시 탓 | 철회 | GC형 1/5, 계측 없음 |
| 31B 정지 "did not trace further" | 수정 | 서버 쪽(110·316건) |
| 결론 "exactly what chunked prefill provides" | 수정 | 청크 크기만큼, 측정 범위 안에서 |

---

## 2. A. 반드시 고칠 것 (원고·재분석만으로 가능)

중복을 합쳤다. 괄호는 출처 리뷰어다.

**A1. 26B 4K 맞대결을 동률로 고친다** (R1-3, R2-1, R4 #83, R5)
- 대상: 표 2, §4.3, §4.4 둘째 항목, RQ3, 초록.
- 표 2의 26B 행은 복제본 "≥4 (1,024; proxy-limited)", 1P1D "3; borderline at 4"로 쓴다. 원가는 같은 부하로 비교한다: "at 4 requests/s per GPU, \$0.49 against \$0.48–0.54 over three seeds".
- §4.3 문안: "At 4 requests/s per GPU both passed on the matched seed (0.977 and 0.954). 1P1D fell below 0.9 on one of three seeds (0.885, a decode-server pause; Section 4.7), and we measured the replicas on that load with one seed only. We therefore treat the two as equal at about 4 requests/s per GPU; the replicas' limit is a lower bound set by our proxy (Section 3.3)."
- 짝지은 시드 차이(+0.023 [−0.007, 0.053])를 한 줄 싣는다.

**A2. 복제본 프록시의 연결 상한을 공개하고, 상한 때문에 생긴 탈락을 판정에서 뺀다** (R1-1, 좌장 확인)
- §3.3 문안: "Our replica proxy used aiohttp's default connection pool, which allows at most 100 concurrent upstream connections; the disaggregated proxies had no limit. With 4K inputs this cap binds near 4.5–5 requests/s per GPU. At 4–6 requests/s per GPU every replica request that missed the TTFT limit had arrived while 100 requests were in flight, and every request that arrived below the cap met the SLO."
- §4.3의 "failed at 5 (0.78)"를 삭제한다. 그림 3(a)의 GPU당 5·6 점은 속 빈 마커로 바꾸고 "proxy-limited"라고 적는다.
- 그림 4를 다시 계산한다. 규칙은 이렇다. 상한 아래에서 통과한 점은 그대로 둔다(상한은 달성률을 낮추기만 한다). 상한 때문에 탈락한 점은 측정하지 않은 것으로 보고, 복제본을 그 아래 요청률에서 절단(censored)으로 처리한다. 대상은 26B 청크 1,024의 GPU당 5·6이다. 청크 1,536의 GPU당 4는 간격 한도를 넘는 칸에서만 유지한다. 아래 줄 26B NVFP4의 느슨한 SLO 칸("Similar")이 바뀔 수 있다.
- §3.6의 주의 런 사유를 고친다. 복제본 주의 런 두 개(E5 26_B2·26_B3, GPU당 16)는 연결 상한이 원인이다. 분리 주의 런 세 개는 httpx 무제한이므로 기존 사유를 유지하되 확인한다.
- 부록 B에 한 줄을 넣는다: "aiohttp's default connector caps concurrent connections at 100; set `limit=0` in any streaming proxy."
- 복제본의 TTFT 꼬리를 말하는 모든 곳(초록 "always", §4.3)에 "median"을 붙이고, 고부하 꼬리는 이 상한의 산물이라고 적는다.

**A3. 31B 대화 판정을 "≈4 경계 대 ≥6"으로 고치고 1토큰 규칙 변경을 공개한다** (R2-2, R4 P1, R5)
- 표 2: 1P1D "≈4 (borderline; highest rate measured)", 복제본 "≥6 (256)".
- 표 2 주석의 "With vLLM's test proxy, 1P1D supported 2" 문장은 프록시 효과로 읽힌다. 다음으로 바꾼다: "With either proxy 1P1D was at the threshold at 4 (five of six runs ≥0.9); the test-proxy verdict of 2 comes from one seed (0.885) that we did not repeat with our proxy."
- 부록 D에 추가한다(R4 문안): "Counting single-token outputs as meeting the gap criterion was adopted after session E8, following review; it moved the two 31B chat 1P1D runs at 4 requests/s per GPU from 0.899 and 0.878 to 0.924 and 0.903, raised the 256-token replicas at 6 from 0.978 to 0.998, and changed no other verdict."
- §4.3의 "passed 4 only narrowly"에 서버 쪽 정지(A5)와 디코드 노드 부하(A6)를 연결한다.

**A4. "분리만 가능" 칸에 측정 범위 조건을 붙인다** (R1-2, R2-5, R5)
- 대상: 초록, §4.4 첫 항목, RQ3, 결론, 그림 4 캡션, 한계 절.
- 문안: "Among the chunks we measured (1,024 tokens or more for 26B), only disaggregation met a 30 ms limit for 26B NVFP4 and 30–40 ms for 26B FP8. vLLM accepts smaller chunks once every modality is disabled; from our sweep we expect a 512-token chunk to bring the 26B replicas' longest gap to roughly 15–25 ms, which we did not measure."
- §4.4 끝의 "at some cost in prefill throughput and TTFT"는 근거가 없다. "at a TTFT cost of about 30 ms per halving; we saw no throughput cost of the 1,024-token chunk up to 4 requests/s per GPU"로 바꾼다.
- 26B FP8의 30–40 ms 칸은 복제본(E8)과 1P1D(E7, 시험 프록시)가 다른 날이다. 캡션에 적는다.

**A5. 전역 정지를 GC형과 서버형으로 나누고 귀속 범위를 좁힌다** (R1-4, R2-3, R4 #125·#133·#134, R5)
- 부록에 런별 표를 싣는다. 열은 달성률, 정지 수, GC 일치, 몰림 신호, 서버 >50 ms, GC형만 뺀 값, 전부 뺀 값이다(R2 약점 3의 표를 그대로 쓰면 된다).
- §4.7 문안:
  - "With vLLM's test proxy, four of the five global pauses in three 26B runs at 4 requests/s per GPU coincided with a 25–40 ms garbage collection in the proxy, and streams resumed with a burst of tokens. Our aiohttp proxy showed no such pause."
  - "The remaining pauses were server-side: one in the 26B runs (113 gaps over 50 ms in the decode server's histogram, at the same time in both runs with that seed) and all of those in 31B chat (110 and 316 gaps). The proxy logged no collection or loop lag during them and the streams resumed without a burst."
  - "Removing only the proxy pauses raises the test-proxy runs from 0.77–0.98 to 0.88–0.99; the aiohttp runs are unchanged."
- 2P1D 문장은 다음으로 바꾼다: "Our three-node 2P1D configuration failed at 3 requests/s per GPU through five global pauses (0.77; 0.996 without them). Only one of them had the proxy-collection signature, and that session had no proxy trace, so we cannot attribute the collapse." §4.8 "Their failures near the limit were dominated by the proxy stalls above"는 삭제한다.
- "then received a burst of tokens"는 GC형에만 붙인다. 사건 규모는 "15–115 in-flight requests (typically 40–110) for 50–80 ms"로 쓴다(R4).
- "failed in a way replicas did not"는 모양의 차이로 바꾼다: "replica pauses last one chunk step, just over 50 ms, and stop only the requests of one replica".
- 서버형의 원인은 가설로 한 줄 적는다(디코드 노드 엔진 코어의 GC 또는 NIXL 완료 처리. 같은 시드에서 같은 시각에 재현됨).

**A6. 디코드 노드 쪽 기제를 맞대결과 결론에 넣는다** (R1-4, 좌장 확인)
- §4.3에 한 문단을 넣는다. 같은 GPU 수에서 1P1D의 디코드 노드는 두 GPU 몫의 디코드를 싣는다. 그래서 중앙 ITL이 복제본보다 길다(GPU당 3에서 15.5 대 13.2 ms, 4에서 20.8 대 15.7 ms). GPU당 4에서 요청별 최대 간격 중앙값은 1P1D 33.8–35.5 ms, 청크 1,024 복제본 36.7 ms로 비슷하다. GPU당 5에서 1P1D는 프리필 대기열(TTFT p50 1.45 s)과 함께 간격에서도 무너졌다(요청의 54%가 50 ms 초과).
- 결론의 "Its benefit … is exactly what chunked prefill provides by other means"는 다음으로 바꾼다: "Chunked prefill protects decodes from other requests' prefills to a degree set by the chunk size, and at equal GPU count disaggregation pays for its isolation with a decode node that carries the batch of two GPUs."

**A7. 전송 기제 서술을 소켓 데이터와 NIXL 소스에 맞춘다** (R3 필수 1·2·4, R1-6, R4 #106, R5)
- 초록: "four TCP connections … 1.5–1.8×"를 뺀다(6절 재작성안).
- §4.5 둘째 문단 문안: "NIXL (v1.4.1) splits a transfer of at least 1,024 descriptors into up to four pieces, one per dedicated worker thread, and sends smaller transfers whole over a shared worker's connection. A 26B transfer at 4K (about 1,800–2,200 descriptors of 64 KiB) therefore travelled as two or three pieces and a 31B transfer as four, over four TCP connections plus the shared one. With all four busy, the 31B transfer's aggregate rate stayed near 19–21 Gbps, half of what four iperf flows reached, while one connection alone reached the 9.5 Gbps per-flow cap. A shared per-node limit, not the per-flow cap, therefore bounded the larger transfer; we did not identify it. Raising NIXL's thread count from 4 to 16 did not change the rate in session E4, as the 1,024-descriptor floor predicts."
- 삭제: "This matches the four worker threads … each with its own UCX endpoint", "which is why its rate is higher", "more connections, not other UCX settings, are the remaining lever".
- §5.3의 "m depends on NIXL's thread count"는 삭제하고, "how NIXL splits a transfer is version-specific"으로 바꾼다.
- 그림 5(c): 제목을 "Connections that moved data within a 0.12 s sample"로 바꾸고, 표본 간격(중앙값 120.5 ms)이 26B 전송(73–93 ms)보다 길다고 캡션에 적는다. 전송별 조각 수 히스토그램으로 바꾸면 더 좋다.
- P·D 양쪽 표본의 바이트 일치는 같은 연결의 양 끝을 읽은 값이라 독립 증거가 아니다. 증거로 쓰지 않는다.
- 7변수 묶음: "no better"를 고친다. 문안: "the full set gave 14.16 and 13.46 Gbps in two runs, 5–10% below the segment sizes alone; its fixed 8 MB receive buffer disabled autotuning, the receive window stayed near 360 KB, and the sender was receive-window-limited for about 40% of its busy time." 부록 C의 "may have been capped"를 이 관찰로 바꾼다. 체크리스트 4에 "do not set UCX_TCP_SNDBUF/RCVBUF unless the kernel limits are raised"를 추가한다.
- 환경 한 문단(R3 필수 5): NIXL 1.4.1, UCX 버전(기록이 있으면), MTU 9001·MSS 8949, cubic, 배치 그룹 최소 RTT 25–33 µs. 4.97 Gbps = 5 × 8949/9001은 한 줄로 넣는다.

**A8. m, 식 (1)·(2), 체크리스트 3의 적용 범위를 적는다** (R1-8, R3 필수 3·권장 6, R4 P2·#115, R5)
- m을 "rate multiplier: effective transfer rate divided by the per-flow cap"으로 다시 정의한다. 표를 하나 싣는다. 저부하·분할 전송에서 26B 1.41–1.57, 31B 1.81이다. 26B GPU당 3에서 1.12–1.14, 4에서 0.92–1.04다. 31B 대화(나뉘지 않은 전송)는 0.81–0.82다.
- 식 (1)은 "for L at least the sliding window"로 한정하거나 일반형 V(L) = b_g·L + b_l·min(L, W)로 쓴다. 대화 전송량을 따로 적는다(26B 약 26–30 MiB, 31B 약 107–110 MiB).
- 체크리스트 3 문안: "… with Eq. (2) at low load: take the KV volume from vLLM's transfer log (Eq. (1) holds for 26B inputs longer than the sliding window), measure one iperf flow, and use m ≈ 1.5 only for transfers of at least 1,024 descriptors; use m ≈ 1 for smaller transfers or near the load you plan to serve."
- 1 Gbps 대기열 문장: "explains"를 "is consistent with"로 바꾸고 S = 1.17 s, λ = 0.5 /s, ρ = 0.59, 평균 대기 0.83–0.85 s를 적는다. 비교 대상이 중앙값(2.19 s)이라는 점도 적는다.
- 31B 전송 283 ms는 "10 s 창 평균의 평균"이다. 전송 가중 평균은 298 ms다. 정의를 캡션에 적고 하나로 맞춘다. 잔차 범위도 그에 맞춘다(R4).

**A9. 청크–멈춤 관계의 서술을 데이터에 맞춘다** (R1-10, R2-6, R4 #146·#59, R5)
- RQ1과 §4.2 문안: "Within one engine setting the replicas' longest gap grew roughly linearly with the chunk (27.6, 38.8, and 52.3 ms at 1,024, 1,536, and 2,048 tokens for 26B at 1 request/s per GPU) and by a further 5–9 ms from 1 to 4 requests/s per GPU. The 2,560-token control, which needed a different multimodal setting, sat below that line (48.4 ms); we cannot separate the setting from the chunk for that point."
- "almost in proportion"과 "It equals the time of a step carrying one full chunk"는 고친다. 체크리스트 1 문안: "With long inputs it is the time of a step that carries a full chunk; with short prompts, the time of the step that carries the longest co-scheduled prompt."
- 31B 구간에 200–400토큰 구간(풀링 약 0.43)을 넣고, "above 800 tokens, none did"는 "almost none (1 of 323)"으로 쓴다.

**A10. 문제 설정, 제약 서술, 관련 연구의 문구를 고친다** (R1-7·9, R2 사소, R5)
- RQ3의 "as a default Gemma 4 deployment is"는 근거가 없다. 다음으로 바꾼다: "Against replicas at a 2,560-token chunk, close to the 2,496-token minimum that vLLM v0.30.0 imposes on Gemma 4 while video input is enabled, disaggregation over TCP served about 3× more at 50 ms."
- 멀티모달 검사 서술을 시험한 조합에 맞춘다. 저자 노트는 image:0, image:0+audio:0, 셋 다 0만 시험했다. 2,496은 video 항목의 예산이다. "passes only when images, audio, and video are all disabled"는 시험하지 않은 조합까지 말한다. 문안: "vLLM rejects chunks below 2,496 tokens, the budget of one video item, unless video input is disabled; we ran smaller chunks with every modality disabled and did not test other combinations."
- §2: TaiChi는 청크 크기를 조절 노브(slider)로 이미 쓴다. "add the chunk size as the variable that moves it"를 "measure how far the chunk size moves it over cloud TCP with stock vLLM"으로 낮춘다. 청크 프리필의 출처는 SARATHI(Agrawal et al., 2023, arXiv:2308.16369)로 쓰고, Sarathi-Serve는 stall-free 배칭으로 인용한다. TaiChi 초록 문구는 저자가 원문으로 확인한다.
- 결론의 "which can be estimated before deployment"는 "roughly estimated at low load"로 쓴다.

**A11. 통계 보고를 약속한 만큼 한다** (R2-4·8, R4 P3·#44, R5)
- 결정적 점의 구간 표를 부록에 싣는다(R2 약점 4의 표). 반복한 점은 반복 계층 부트스트랩, 한 런짜리 점은 "within-run only"로 표시한다. 복제본 GPU당 4의 [0.950, 0.997]은 프록시 상한이 걸린 런의 런 내 구간이라고 적는다.
- borderline을 수치로 정의한다: "any repeat within 0.85–0.95, or a repeat-level interval that contains 0.9". 이 정의로 청크 2,560 복제본 GPU당 1(다섯 런의 하한 0.867–0.919)도 borderline으로 표시한다.
- 짝지은 시드 설계를 §3.6에 적는다. 시드는 요청률과 반복 번호로 정해지므로 구성과 세션이 달라도 같은 도착 순서와 프롬프트를 공유한다. 그래서 "five runs"가 시드 세 개일 수 있다.
- 주 판정 규칙("모든 반복 ≥0.9")은 유지한다. 반복 평균 규칙으로 다시 그린 그림 4를 부록에 민감도로 싣는다. 두 규칙에서 판정이 다른 칸은 본문에 "within one grid step"으로 쓴다(D3 참조).
- 그림 4 캡션: 빗금 정의를 코드에 맞춘다("a side still passed at its highest measured rate and the ratio cannot be resolved"). 비율의 방향을 적는다. "a ratio of 0.75 is one step of our rate grid"를 넣는다.
- 부트스트랩, 겹친 프롬프트 구간, 정지 분류, 프록시 상한 점검 코드를 harness로 옮긴다.

**A12. 사실과 다른 서술을 정정한다** (R4 ❌ 4건·⚠️, R5, R2 사소)
- §3.6: "Median TTFT varied by at most 5.1%"는 E8에서 최대 10%다(477–526 ms). "±0.09"는 ±0.10이다(시험 프록시 1P1D 0.77–0.98). "well above 0.9 … at most 0.03"에는 "within a session"을 붙인다. 워밍업은 "raised attainment by at most 0.019 and lowered it by at most 0.029, flipping no verdict"로 쓴다.
- 표 1 캡션 "All main-text results come from g7e"는 틀렸다. R4 문안으로 바꾼다.
- §3.1 "All servers used … 0.90"은 예외가 있다: KV 맞춤 0.42, 호스트 스테이징 0.70, E1c 16,384 문맥.
- 그림 1의 202런에는 주의 런 2개가 들어 있다(분리 7런 중 2런). 캡션이나 필터를 고친다.
- 방법 절에 적는다: ShareGPT 요청에 채팅 템플릿을 적용하지 않았고, 출력 길이를 참조 길이로 고정했다. 1토큰 출력은 대화 런의 1.0–5.6%다.
- 단위: "MiB×8×1.048576/s"는 Mbit/s를 준다. "468–533 MB"는 MiB로 쓴다.
- 그림 속 전체 요청률(그림 5 부제, A1, A2, A7 행 라벨, A8 x축, A9 제목)을 GPU당으로 바꾸거나 "total"을 붙인다(R4, R5).
- 그림 A7 제목 "Repeats only disagree near the 0.9 threshold"는 1차에서 필수였는데 남아 있다. "Disagreement flips a verdict only near 0.9"로 고친다.

**A13. 분리 쪽 고정 노브와 적용 범위를 공개한다** (R1-5·11)
- §4.3과 한계 절 문안: "The disaggregated side kept a 2,560-token chunk on both nodes, the seven-variable UCX set, and one prefill node. At 5 requests/s per GPU its prefill node queued (up to 33 waiting requests) and its decode node exceeded the gap limit for 54% of requests, so a larger prefill chunk alone would not have met the strict SLO there."
- 결론의 적용 범위를 적는다: "4K-token inputs and chat". 16K 이상에서는 작은 청크가 TTFT를 늘리므로, 분리가 이길 수 있는 남은 영역이다. 우리 16K 데이터는 전송 조정 전이고 청크 2,560이다.

**A14. 글과 그림의 필수 수정** (R5 필수 2·5, R4)
- 초록은 200단어 안으로 줄인다(6절).
- 부록 그림 9개가 본문에서 참조되지 않는다. 대응 문장에 `\ref`를 단다. 그림 A9(GPU별)는 GPU, 정밀도, 튜닝, 배치 그룹이 함께 바뀐 비교다. 빼거나, 교란을 캡션에 적고 본문에 연결한다. 부록 B는 기여 3에서 참조한다.
- `\texttt{--limit-mm-per-prompt}`가 PDF에서 en dash 하나로 찍힌다. `-{}-`로 쓴다. 독자가 복사하는 명령행 인자다.
- 기여 목록의 "the reference proxy"는 "vLLM's test proxy for NIXL"로 쓴다. SLO는 첫 사용에서 풀어 쓴다.

**A15. 공개 차단 항목(원고 밖, 공개 전 필수)** (R4 4절)
- 457 MB 파일과 추적 7.1 GB: GitHub 푸시가 막힌다. 원자료는 Zenodo로 옮기고, result.json의 중복 bench를 뺀다.
- RESULTS.md 1068행의 AWS 계정 ID(HEAD와 이력 한 커밋): 이력을 다시 쓰는 대신, 정리한 스냅샷으로 새 공개 저장소를 만드는 편이 안전하다. 결정은 저자가 한다.
- README는 아직 "pre-measurement"다. 재현 명령 네 줄(R4)을 넣는다. aggregate.py의 기본 SLO(tbt 100/400)를 논문 값으로 바꾼다.
- 심사 폴더 스크립트의 로컬 절대 경로를 정리한다(논문이 모의 심사를 공개한다고 쓰므로).

---

## 3. B. 새 측정이 필요한 것: E9 설계

전제: 측정 전에 `rr_proxy.py`에 `connector=aiohttp.TCPConnector(limit=0)`를 넣는다. 그렇지 않으면 E9의 모든 복제본 점(청크 512의 GPU당 4 포함)이 같은 상한에 걸린다. 예측값을 RESULTS.md에 적어 세션 전에 커밋한다. 청크 512의 최대 간격은 GPU당 1–2에서 15–25 ms, 청크 1,024 복제본은 GPU당 5에서 통과, 31B 1P1D는 GPU당 6에서 탈락으로 예측한다. 이렇게 하면 1차에서 입증하지 못한 "예측의 선후"를 이번에는 커밋 이력으로 보일 수 있다.

| 순위 | 항목 | 요청률(GPU당)과 반복 | 런 | 재기동 | 결정하는 것 |
|---|---|---|---|---|---|
| **1** | 26B NVFP4 복제본 청크 512(모든 모달리티 0) | 1, 2, 3, 4 각 1회 + 결정점 1회 반복 | 5 | 1 | 30 ms 칸(1P1D는 GPU당 2), 청크 512의 50 ms 한계와 TTFT 비용 |
| **2** | 26B 청크 1,024, 프록시 상한 해제 | 4 × 3(시드 8007/9007/10007), 5 × 2, 6 × 1 | 6 | 1 | 표 2와 그림 3(a)의 복제본 한계(하한 → 값), 반복 수 대칭 |
| 3 | 26B FP8 복제본 청크 512 | 0.5, 1 | 2 | 1 | FP8 30–40 ms 칸 |
| 4 | 31B: 복제본 청크 256(상한 해제) 8, 1P1D aiohttp 6과 4(시드 10000) | 각 1회 | 3 | 2 | 31B의 두 경계값, 반복 대칭 |
| 5 | 1P1D, P 청크 8,192 + 세그먼트 두 변수만 | 4 × 2, 5 × 1 | 3 | 1 | 분리 쪽 공정성(TTFT 쪽만 바뀔 것으로 예상) |
| 선택 | 청크 768(GPU당 2·3). 모든 모달리티 0에서 청크 3,072/4,096 기동 확인 + 1런(멀티모달 교란 분리). 디코드 노드 파이썬 GC 콜백(sitecustomize로 주입). 31B 4K 1런에서 P 노드 스레드별 CPU(`pidstat -t`)와 10 ms 간격 ss | – | 2–4 | 1–2 | 서버형 정지 가설, 공유 상한 가설 |

시간과 비용(g7e.2xlarge × 2 = 시간당 $6.73, c6i.2xlarge $0.34). 한 런은 드레인까지 약 4분, 재기동은 약 8분이다. 배치 그룹 용량 대기는 E8에서 17–35분이었다.
- **E9-최소(1–3순위)**: 13런, 재기동 3회. 준비와 정리를 넣어 약 2–2.5시간, **약 $15–18**.
- **E9-전체(1–5순위)**: 약 19–22런, 재기동 6–7회. 약 3.5–4시간, **약 $25–30**.
- 순서: 1순위를 먼저 돈다. 용량 대기나 사고로 세션이 짧아져도 결정적 항목은 남는다.

**가장 중요한 항목은 1순위(26B 청크 512)다.** 결론의 모양을 바꿀 수 있는 항목은 이것 하나다. 청크 512가 30 ms를 GPU당 2 이상에서 지키면, 측정한 범위에서 조정한 청크를 이긴 분리 사례는 FP8 30 ms 하나만 남거나 하나도 남지 않는다. 그러면 "분리가 이기는 곳"의 근거는 멀티모달 제약(2,496) 시나리오와 측정하지 않은 영역(16K 이상, 30 ms 미만)으로 옮겨 간다. 2순위는 수치를 바로잡는 데 가장 중요하지만 방향은 이미 정해져 있고, 측정하지 않아도 정직한 대체 문안이 있다.

결과별 문안:
- 청크 512가 30 ms를 GPU당 2 이상에서 통과하면: 초록의 "Only disaggregation met 30–40 ms limits…" 문장을 "Against the best chunk we measured, disaggregation met no gap limit the replicas could not (26B NVFP4); …"로 바꾸고, 분리의 가치를 멀티모달 제약과 긴 입력으로 설명한다.
- 청크 512가 30 ms를 지키지 못하면: "the shortest stall a chunk reached (512 tokens: X ms)"로 조건을 바꾸고 30 ms 칸을 유지한다.
- 청크 1,024가 상한 해제 후 GPU당 5를 통과하면: 표 2를 "5 대 ≈4"로, 초록을 "served less"로 바꾼다. 통과하지 못하면 "동률"을 유지한다.

측정하지 않을 때의 대체 문안:
- 1순위: A4 문안.
- 2순위: A2와 A1 문안. 표 2는 "≥4 (proxy-limited)"로 쓰고, 한계 절에 "the replicas' limits at 4 or more requests/s per GPU are lower bounds set by our proxy"를 넣는다.
- 3순위: FP8 칸에 A4 조건을 붙인다.
- 4순위: "1P1D was at the threshold at 4, the highest rate we measured for it".
- 5순위: A13 문안.

---

## 4. C. 고치면 좋은 것

- RQ 번호를 서술 순서에 맞추고, §4.7을 §4.3 바로 뒤로 옮긴다(R5-6). 도입부에 결과 두세 문장을 넣는다(R5-7).
- 용어 통일: longest gap(그림의 "max gap"), gap limit(stall limit·budget 혼용), global pause(요청별 stall과 구분), Replicas (2)(그림 A6의 "Rep ×2")(R5-8).
- 표 2에 "median TTFT at supported load" 열을 넣고, 경계 점에 † 표시를 한다. g7 가격($2.520)을 넣거나 "not used for costs"라고 적는다(R3, R5).
- 그림: 그림 3(b)의 가려진 청크 1,024 선(dodge), 그림 5(b)의 x 라벨 겹침, 그림 7의 GC 선과 스파이크 겹침, 캡션에 "107 s 사건이 같은 시드 두 런에 같은 시각", 부록 그림의 5pt대 글자, A4·A5·A9 범례 겹침(R5).
- 그림 6(TTFT 분해)의 값을 스크립트 상수에서 로그 계산으로 바꾼다. `xfer_stats`의 `glob`을 `sorted`로 바꾼다. uv.lock, 도커 digest, 런 매니페스트, CSV `instance_type` 열을 채운다(R4).
- 나뉘지 않은 전송은 시간이 두 배 가까이 걸린다(26B 123 대 78 ms, 31B 약 0.55 대 0.27 s). TTFT 꼬리 요인으로 한 줄 적는다(R3 권장 10).
- EFA 문단: NIXL은 EFA를 libfabric 백엔드로 쓴다. 8xlarge는 vCPU도 네 배다. 공유 상한이 CPU에 묶인 것이라면 8xlarge TCP만으로도 빨라질 수 있다. EFA 이득을 가르려면 8xlarge TCP 대조가 필요하다고 한 줄 적는다. MPTCP, ENI 추가, UCCL은 향후 과제로 한 문장 넣는다(R3 권장 8).
- 호스트 스테이징의 조건(g7, GPU 메모리 0.70)과 링크 전송률을 한 줄 넣는다(R3 권장 11).
- `--long-prefill-token-threshold`: v0.30.0에 있는지 `--help`로 확인한 뒤, 멀티모달을 켠 채 요청당 프리필 조각을 줄이는 미검증 대안으로 한 줄 적을 수 있다(R1-9).
- 참고문헌 형식, Acknowledgments를 Funding으로(R5-10). 비용 원장(세션별 표)을 부록에 싣는다(R4 #164).
- per_request 캐시의 10 µs 반올림(판정 영향 없음)(R2 사소).

---

## 5. D. 반박하거나 받아들이지 않는 것

**D1. R2-7 "청크를 줄이면 프리필 효율이 떨어져 복제본의 TTFT 꼬리가 무거워진다"**: 기제가 틀렸다. 청크 1,024 GPU당 4의 p99 2,056 ms는 전부 프록시 대기열이다. 진행 중 100개 미만일 때 도착한 요청은 p99 434 ms, 최대 536 ms였다(좌장 확인). 받아들이는 것은 "median"이라는 한정어뿐이다.

**D2. R1-6 "E4의 스레드 16 무효 결과가 연결 귀속과 모순된다"**: 추론을 받아들이지 않는다. 1,024 디스크립터 하한 때문에 스레드를 16개로 늘려도 26B 전송은 2–3조각 그대로다(R3, 소스 확인). E4는 연결 기제와 모순되지 않고, 오히려 그 기제가 예측하는 결과다. 다만 R1이 요구한 조치(스레드 귀속 삭제, "remaining lever" 철회, §5.3 삭제)는 R3의 근거로 받아들인다(A7).

**D3. R2-5의 판정 규칙 변경(주 규칙을 반복 평균으로, 절단 판정에 여유 조건)**: 주 규칙으로는 받아들이지 않는다. 결과를 본 뒤 특정 칸을 뒤집는 규칙 변경은 이 논문이 1차에서 받은 비판(SLO 사후 변경)과 같은 비판을 부른다. 대신 반복 평균 규칙의 지도를 부록 민감도로 싣고, 판정이 갈리는 칸을 본문에 적는다(A11). 31B 50 ms 칸은 규칙을 바꾸지 않고 본문에 "replicas passed 6; 1P1D was borderline at 4, its highest measured rate"로 쓴다. 표 2의 26B 행은 규칙과 상관없이 동률로 고친다(A1). 규칙이 아니라 반복 수가 판정을 만든 경우이기 때문이다.

**D4. R1-5 "P 청크 8,192가 분리에 유리한 유일한 남은 실험이고 공정성 논증에서 값이 크다"**: 비중을 낮춘다. GPU당 5에서 1P1D는 디코드 노드 쪽 간격에서도 무너졌다(요청의 54%가 50 ms 초과, 좌장 확인). P 청크를 키우면 TTFT 쪽만 나아지므로 엄격 SLO 판정은 바뀌지 않을 가능성이 높다. 공개(A13)는 필수이고 측정은 E9 5순위로 둔다.

**D5. 청크 512의 외삽값을 수치로 싣자는 제안(R1 약 16–25 ms, R2 약 15 ms)**: 수치를 발견처럼 싣지 않는다. R2의 직선 절편은 디코드 스텝보다 작아 과소 추정이다. 본문에는 "roughly 15–25 ms, not measured" 수준으로만 쓴다(A4).

**D6. R3의 "P 쪽 단일 UCX 워커가 약 20 Gbps 공유 상한의 원인"**: 가설로만 둔다. 소스(원격에 앞쪽 워커 주소 하나만 공개)와 같은 포트 관찰은 정황이다. CPU 프로파일이 없다. 논문에는 "a shared per-node limit we did not identify"로 쓴다. R3의 "m을 정하는 것은 1,024 디스크립터 하한"도 절반만 맞다. m은 공유 상한과 부하에도 달려 있다(1.1절 (d)).

**D7. R1-9 "vLLM v1은 70 GiB 이상 GPU에 기본 8,192를 준다"**: v0.30.0에서 확인되지 않은 주장이다. 논문에 기본값을 쓰지 않는다. "default deployment"라는 말만 없애면 된다(A10). `--long-prefill-token-threshold` 실험은 요구하지 않는다(C).

**D8. R1-11 16K에서 청크 1,024 복제본과 조정한 1P1D 재측정**: 이번 판의 범위 밖이다. 적용 범위를 명시하는 것(A13)으로 충분하다.

**D9. R3 권장 8의 EFA, MPTCP, ENI, UCCL 실험**: 범위 밖이다. 한 문장의 향후 과제와 EFA 교란 한 줄로 처리한다(C).

**D10. R5-6 RQ 번호 재배치**: 필수가 아니다(C). 전방 참조 두 곳만 정리해도 읽힌다.

**D11. R4 패키징 항목을 논문 심사 점수에 섞는 것**: 원고 밖의 공개 조건으로 따로 다룬다(A15). 공개 전 필수라는 판단은 같다.

**D12. R1의 점수 3(weak accept 경계)**: 좌장은 "방향은 견고하고 경계값과 기제 서술을 고치면 된다"는 R1 자신의 요약에 동의한다. 필수 항목 가운데 결론의 방향을 흔드는 것은 없다. 판정은 중폭 수정이다.

---

## 6. 초록 재작성안 (E9 없이 유지되는 내용만, 198단어)

> Prefill–decode disaggregation usually relies on RDMA or NVLink, which cheap single-GPU cloud instances lack. We ask when TCP disaggregation beats chunked-prefill replicas. On AWS 2xlarge instances we served Gemma 4 26B (mixture of experts) and 31B (dense) with stock vLLM, disaggregated with NIXL/UCX over TCP, and judged each request by time to first token (TTFT) and longest inter-token gap. A replica stalls whenever another request's prefill shares its scheduler step, so its chunk size bounds that gap: for 26B with 4K-token inputs, the median fell from 48 ms at a 2,560-token chunk to 28 ms at 1,024. Under a 1 s TTFT and 50 ms gap limit, disaggregation served about 3× more requests per GPU than replicas at 2,560 tokens, near the minimum vLLM allows Gemma 4 with video input enabled. Against smaller chunks it served no more (26B, 4K: about 4 requests/s per GPU each; 31B chat: 4, at the threshold, against at least 6), with a later median first token. Only disaggregation met 30–40 ms limits, but we measured no 26B chunk below 1,024 tokens. Its first-token cost was mostly the KV transfer, which a larger UCX TCP segment made 3.4× faster. Tune the chunk first.

주:
- "about 3×"는 26B 4K의 격자 값(3 대 1)이다. 본문에는 격자 경계(1.5–4배)를 함께 적는다. FP8과 31B 대화에서는 청크 2,560 복제본이 한 점도 통과하지 못했다.
- "about 4 … each"는 보수적 표현이다. 복제본 쪽은 프록시 상한이 정한 하한이다. 본문과 표 2에 그렇게 적는다.
- 48 → 28 ms는 멀티모달 설정이 다른 두 점이다. 본문(A9)에 밝힌다. 초록에서는 청크를 1,024로 내리려면 모든 모달리티를 꺼야 했다는 사실이 이 차이를 함께 설명한다.
- 전송 연결 수와 1.5–1.8배는 초록에서 뺐다. 이 논문에서 가장 불안정한 서술이고(1.1절 (d)), 실무자에게 필요한 것은 세그먼트 크기 한 줄이다.
- E9를 하면 6·7번째 문장을 3절의 결과별 문안으로 바꾼다.
- "Tune the chunk first"는 R5의 권고다. 제목 질문에 답하는 문장이 초록에 하나는 있어야 한다.

---

## 7. 리뷰어 간 불일치와 좌장 판단

- **복제본 TTFT 꼬리의 원인(R2: 청크 축소로 프리필 효율 저하, R1: 프록시 대기열)**: 좌장이 요청을 도착 시 진행 중 수로 나눠 확인했다. R1이 맞다(D1).
- **E4 스레드 16 결과(R1: 연결 귀속과 모순, R3: 분할 하한으로 설명됨)**: R3가 맞다. 조치는 두 리뷰어가 같다(D2).
- **연결 수(v1: 전송마다 넷, R1: 출처 미확정, R3: 26B 2–3조각, 31B 4조각, R4: 소스 인용 없음)**: 좌장이 NIXL v1.4.1 해당 행과 전송 로그의 디스크립터 수로 확인했다. R3의 규칙을 버전 한정으로 받아들인다.
- **m(R4: 범위를 1.4–1.8로, R3: 정의 변경, 부하·크기 의존)**: 둘 다 받아들인다. R4의 범위는 저부하 값이고, R3의 정의와 부하별 표가 체크리스트를 바로잡는다.
- **31B 1P1D(v1: aiohttp로 4, R2: 프록시 효과 없음, R4: 1토큰 규칙이 뒤집음)**: 둘 다 맞고 서로 보완한다. 좌장이 여섯 런을 두 규칙으로 다시 계산했다. 결론은 "두 프록시 모두 약 4에서 경계"이고, 1토큰 규칙은 옳지만 공개해야 한다.
- **2P1D(R4: "likely"로 약화, R2: 철회)**: R2를 따른다. GC형 신호가 1/5이고 계측이 없으므로 "likely"도 근거가 없다.
- **판정 규칙(R2: 평균 규칙과 여유 조건으로 변경, R1·R5: 표기로 해결)**: 주 규칙은 유지하고 민감도를 공개한다. 표 2의 26B 행만 동률로 고친다(D3).
- **"분리만 가능" 칸(R1: 청크 512에서 뒤집힐 가능성 큼, 측정 요구 / R2: 조건 문구 / R4: 표기대로면 ✅)**: 셋 다 사실관계는 맞다. 판정은 조건 문구가 필수이고 측정이 권장이다. 외삽값은 싣지 않는다(D5). E9 1순위로 둔다.
- **P 청크(R1: 결정적 공정성 실험, 좌장: 디코드 쪽 간격이 먼저 막힘)**: 공개는 필수이고, 측정은 5순위다(D4).
- **7변수 묶음(R1·R3 모두 rwnd 제한 약 40%)**: 두 리뷰어가 독립적으로 같은 결론에 이르렀다. 받아들인다(A7).
- **점수(R1 3, R3 3.5, R4 3.5, R2·R5 4)**: 낮은 점수들은 서로 다른 절(서빙 기제, 네트워크 기제, 패키징)에서 나왔고 결론의 방향을 겨누지 않는다. 좌장 판정은 중폭 수정이다. 공개 판단에 걸리는 것은 A1–A8(주장 수정)과 A15(공개 차단)다.
- **1차 좌장과 이번 판단의 관계**: 1차 좌장은 2P1D 해석 철회(A4)와 m 가설 표기(D11)를 요구했다. v1은 2P1D를 반대 방향으로 다시 과잉 귀속했고, m을 가설이 아니라 기제로 썼다. 이번 A5와 A7은 1차 요구를 다시 적용한 것이다.
