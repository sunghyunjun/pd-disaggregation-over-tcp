# 좌장 메타리뷰 (Reviewer 6, 프로그램 위원장)

대상: "When Does Prefill–Decode Disaggregation Pay Off Without RDMA?" (paper/en/main.tex, 2026-09-30 초안)
근거: 리뷰 5건(r1~r5, R4는 전문 r4_repro.md와 요약 r4_repro_msg.md), 저자 측 확인 노트(r0), 좌장 직접 확인(아래 스크립트 3개, 모두 읽기 전용).
기준: 학회 투고가 아니라 실무자가 인용할 독립 프리프린트(Zenodo DOI). "반드시 고칠 것"은 틀렸거나, 오해를 부르거나, 공개하지 않았거나, 전문 독자가 논문을 기각할 근거로 쓸 만한 것으로 한정한다.

좌장 확인 스크립트(리뷰 폴더):
- `r6_check.py`: 26B 4K 복제본의 요청별 최대 간격 분포와 임계별 달성률
- `r6_check31.py`: 31B 채팅 복제본의 탈락 원인(같은 복제본에 겹친 프롬프트 길이)
- `r6_sim31.py`: 위 관계로 31B 복제본의 저부하 달성률을 외삽

---

## 1. 판정

**공개 전 대폭 수정.** 수정 대부분은 원고와 기존 데이터 재분석으로 끝난다. 다만 26B 4K 헤드라인은 복제본 기준선의 튜닝하지 않은 노브 하나에 걸려 있어서, 약 $25~40짜리 세션 한 번(B1)을 공개 전에 돌리기를 강하게 권한다. 돌리지 않고 공개한다면 초록에 그 조건을 명시해야 한다.

헤드라인 주장별 판정은 다음과 같다.

**(a) 26B 4K에서 GPU당 지원 부하 1.5–4배, 비용 약 3배: 새 데이터 전까지 위험. 조건을 명시해야만 유지된다.**
좌장이 원자료로 확인했다(`r6_check.py`). 복제본 둘을 GPU당 1 req/s로 돌린 네 런 모두에서 요청별 최대 간격의 p10/p50/p90은 48.0–48.2 / 48.3–48.4 / 48.9–49.1 ms다. 임계 45 ms에서는 달성률이 0.006–0.011이고 50 ms에서는 0.933–0.958이다. GPU당 2 req/s에서 탈락한 것도 중앙값 49.4–50.8 ms 때문이다. 즉 복제본의 판정은 "2,560토큰 청크가 섞인 스텝(약 48 ms)이 50 ms보다 1.6 ms 짧다"는 사실 하나로 정해진다. 실험 노트도 이 점을 미결로 남겼다(RESULTS.md 123행 "긴 입력에서의 청크 효과는 미측정(다음)"). 2,560이라는 값도 성능 때문에 고른 것이 아니다. 2048이 Gemma 4의 멀티모달 예산 검사에 걸려 거부됐기 때문이다(77행, 마찰 #4). 디코드 스텝 6.5 ms와 혼합 스텝 48.4 ms로 선형 추정하면 청크 1024는 약 23 ms, 1536은 약 32 ms다(좌장 추정). 그 경우 복제본이 GPU당 2~3 req/s에서도 50 ms를 지킬 가능성이 높고, 이득은 1~1.5배까지 줄 수 있다. FP8/BF16에서 "분리가 사실상 유일한 선택"이라는 주장도 같은 조건에 묶인다.

**(b) 31B 채팅은 분리만 SLO 충족: 표현을 고치면 유지된다.**
이 주장은 절대 50 ms 기준(31B 디코드 스텝 25 ms의 2배)에서만 성립한다. 100 ms 이상에서는 양쪽 모두 통과하고, 사전 등록한 상대 기준(5×스텝 = 125 ms)에서는 차이가 없다. 메커니즘은 좌장이 기존 데이터로 확인했다(`r6_check31.py`, 31B 복제본 둘 × GPU당 1 req/s, 네 런 합산). 한 요청이 디코드하는 동안 같은 복제본에 들어온 프롬프트 중 가장 긴 것이 200토큰 미만이면 50 ms 이내 비율이 0.99–1.00이다. 200–400토큰이면 0.39–0.50, 400–600토큰이면 0.23, 600토큰 이상이면 0.00–0.03이다(ShareGPT 입력 중앙값 140, 평균 247, p90 690). 따라서 원고의 "even short prefills push gaps over 50 ms"는 틀렸고, 원인은 "수백 토큰짜리 프롬프트"다. 이 관계로 외삽하면 복제본 달성률은 GPU당 0.5 req/s에서 약 0.59, 0.25 req/s에서 약 0.72다(`r6_sim31.py`, 모형 추정이며 측정값이 아니다. 1 req/s에서 모형 0.46, 실측 0.43–0.49로 맞는다). 측정 범위 아래로 내려가도 복제본이 0.9에 닿을 가능성은 낮다. 청크를 줄여도 약 200토큰 이하가 아니면 구제되지 않는다. 이 주장은 청크 비판에 26B 4K보다 강하다.

**(c) TTFT 오버헤드 ≈ KV 전송, 식 1의 예측력: 표현을 고치면 유지된다.**
"almost entirely"는 틀렸다. 저부하에서 전송이 차지하는 비중은 61%(26B NVFP4, 84/137 ms), 76%(31B, 283/370), 85%(26B FP8, 165/193, 날짜가 다른 두 측정의 조합)다. 식 1에는 문제가 세 가지 있다. 전송량이 입력 길이에 선형이 아니라 아핀이다. 대기열 항이 없다. §4.3의 16K 예시는 틀렸다. "측정 전에 예측했다"는 두 점뿐이고(+14%, +3–5%), 저장소 이력만으로는 선후를 입증할 수 없다(예측 수치가 처음 나오는 커밋이 E5 결과 커밋 39acfbe다). 잔차 50–90 ms는 RDMA에서도 남는 바닥값이라, Discussion의 RDMA 외삽도 이를 반영해야 한다.

**문제 설정 "단일 GPU 노드에는 RDMA가 없다": 일반 명제로는 틀렸다. 가장 싼 크기에 한정하면 참이다.**
EFA는 단일 GPU인 g6e.8xlarge, g7.8xlarge, g7e.8xlarge에 있다(저자 측이 AWS 문서로 확인). 다만 g6e와 g7e에는 GPUDirect RDMA가 없다. 2xlarge에는 EFA도 ENA Express도 없다. 시간당 가격은 g7e.8xlarge 약 $5.27(2xlarge $3.363의 1.57배), g6e.8xlarge 약 $4.53(2xlarge $2.242의 2.0배)이다. 이 가격은 Vantage 집계(instances.vantage.sh, 2026-09-30 조회)이고 AWS 가격표와는 대조하지 않았다. 질문을 "가장 싼 단일 GPU 크기에서 TCP로 분리하면 충분한가, 아니면 1.6~2배를 내고 EFA 크기를 사야 하는가"로 다시 세우면, 논문의 실무 가치는 오히려 선명해진다.

**그 밖에 흔들리는 주장.** 비율 규칙(기여 4, RQ4, 체크리스트 4)이 가장 약하다. 2P1D @9의 탈락은 디코드 노드 한계가 아니라 전역 정지 5건 때문이다(0.769 → 사건 제외 0.996, 중앙 ITL 23.8 ms). 채팅의 "디코드를 늘려라"는 주의 런과 `--max-num-seqs 256` 설정 상한에 기대고 있다. 기여 목록에서 관찰로 격하해야 한다.

---

## 2. A. 반드시 고칠 것: 기존 데이터와 원고 수정만으로 가능

**A1. 26B 4K 헤드라인에 청크 조건과 임계 여유를 명시한다** (R1-1, R2-1, R5-5)
- 초록, §4.5, §4.7, RQ1, 결론에 모두 조건을 붙인다. 문안: "against replicas whose chunked-prefill size was fixed at 2,560 tokens (the smallest value vLLM accepted for Gemma 4 with its multimodal budget check), which puts their mixed prefill–decode step at about 48 ms, just under the 50 ms limit. We did not tune the replicas' chunk size; smaller chunks may close much of this gap."
- §3.1에 2,560의 출처(2048 거부)와 `--max-num-seqs 256`을 적는다.
- 1.5–4배의 유도를 한 문장으로 쓴다. "replicas' limit lies between 1 and 2 req/s/GPU and 1P1D's between 3 and 4, so the ratio lies in 1.5–4; linear interpolation of mean attainment gives 2.8–3.3×"(R2 계산).
- 복제본 GPU당 1 req/s는 논문 자신의 정의(0.85–0.95)로 borderline이다(네 런 중 세 런이 0.933–0.944, R2 블록 부트스트랩 하한 0.86–0.92). 이렇게 표시한다.
- 26B 4K 복제본의 요청별 최대 간격 히스토그램(48 ms 봉우리)을 그림 하나로 넣기를 권한다. 이 그림 하나가 청크 조건을 가장 정직하게 보여 준다.
- FP8/BF16 문단(§4.4)의 "disaggregation is effectively the only option"은 "the only configuration that met the SLO with a 2,560-token chunk"로 바꾼다.
- 스크립트 작업: 작다. `r6_check.py`를 harness로 옮기면 된다.

**A2. 31B 채팅 주장을 50 ms 조건으로 한정하고, 메커니즘을 데이터로 바꾼다** (R1-2, R2-2, R5 과장 목록)
- §4.5 소제목을 "31B, chat: only disaggregation meets a 50 ms gap limit"으로 바꾼다.
- "The dense model's decode step is long enough that even short prefills push gaps over 50 ms"를 좌장 분석(1절 (b)의 구간별 달성률)으로 교체한다. 문안: "A replica request missed the limit when a prompt of a few hundred tokens was prefilled on the same replica while it was decoding: with the longest co-scheduled prompt under 200 tokens, 99% of requests kept every gap under 50 ms; above 600 tokens, almost none did."
- "no supported load"는 "none at the measured rates (≥1 req/s per GPU)"로 바꾼다. 모형 외삽(0.5 → 약 0.59, 0.25 → 약 0.72)은 모형 추정이라고 밝히고 부록에 싣는다.
- 출력 길이별 달성률(R2: 6–50토큰 0.89–0.91, 400토큰 초과 0.00–0.04)을 한 줄로 적는다.
- 결과가 프롬프트 길이 꼬리에 좌우되므로 ShareGPT 입력 분포(관측 최대 1,018토큰. 샘플러 상한인지 저자가 확인)를 방법 절에 적는다.
- 1P1D GPU당 2 req/s(0.982)는 단일 런임을 표시한다.
- 스크립트 작업: 중간. `r6_check31.py`와 `r6_sim31.py`를 정리하면 된다.

**A3. SLO 기준 변경과 사전 등록 이탈을 공개한다** (R1-2, R2-2a·4·7, R4 재현성, r0-3)
- 절대 50 ms를 주 기준으로 유지하는 데는 좌장도 동의한다(D1 참조). 다만 방법 절에 다음 한 문단을 넣는다. "The pre-registered protocol set the gap limit at 5× each model's decode step (Sarathi-Serve's strict rule). We switched to a common absolute limit because a relative rule makes faster models stricter in absolute terms (38 ms for 26B BF16) and distorts cross-model comparison; 50 ms is 5× the 26B decode step on the slowest GPU we used (10 ms on g7)."
- 상대 기준 판정표를 부록에 싣는다. 민감도 격자에서 바로 뽑을 수 있다. 26B g7e는 5×6.5 = 32.5 ms, 31B는 125 ms다.
- "사전 등록 대비 이탈" 부록을 만든다. PROTOCOL.md가 함께 공개되므로 독자가 스스로 대조하게 된다. 항목은 다음과 같다: 청크 2048 → 2560, 같은 프록시 → 비대칭 프록시(A4), 동등 띠 0.9–1.1 → "similar" 0.8–1.25, 부트스트랩 CI 약속 → 미보고(A12에서 추가), 클라이언트 c6i.2xlarge 고정 → E5는 c6i.xlarge, 워밍업은 E7에만, H100·g5 기준점 없음.
- 50 ms의 정당화 한두 문장을 §3.5에 추가한다(R5-14).
- 스크립트 작업: 작다(민감도 결과에서 표 추출).

**A4. 분리 구성의 전역 정지와 프록시 비대칭을 공개하고, 2P1D 해석을 철회한다** (R2-3, R1-6, r0-2)
- §3.1에 적는다. 복제본은 `harness/rr_proxy.py`(aiohttp), 분리는 vLLM 테스트 코드 `toy_proxy_server.py`를 썼다. 사전 등록은 같은 프록시였고, 프록시 오버헤드는 ShareGPT 1 req/s에서만 검증했다.
- R2 표(1P1D 4K @8, 1P2D @9, 2P1D @9, 31B 1P1D 채팅 @8의 사건 수와 사건 제외 달성률)를 부록에 싣는다. 본문에는 다음처럼 쓴다. "Disaggregated runs near their limits showed one to five global pauses of 55–80 ms that hit 40–110 requests at once and were followed by bursts of sub-2 ms gaps, which points to the delivery path (API server, proxy, or client) rather than GPU compute. Replica runs showed none. Without these events 1P1D would pass at 4 req/s per GPU; if they are proxy artifacts, our disaggregated limits are conservative."
- §4.5의 "2P1D dropped to 0.77 at 9 requests/s because its single decode node could not hold the gap limit"를 삭제한다(사건 제외 0.996, 중앙 ITL 23.8 ms).
- 스크립트 작업: 작다. `r2_global.py`를 harness로 옮기면 된다.

**A5. 비율 규칙을 기여에서 관찰로 격하한다** (R1-7, R4 ❌3, R5-8)
- 기여 4를 삭제하거나 "an observation on three-node ratios"로 바꾼다. 이 원리는 DistServe와 Splitwise의 배치 원리라고 밝힌다.
- 26B 4K의 "1:1이 균형"은 A4 때문에 근거가 없다. "three-node configurations did not beat 1P1D per GPU at the measured rates"로 줄인다.
- 채팅의 "256 동시 시퀀스, 대기 868, KV 43%"는 공개 데이터에 없고(E5 수집 시계열 덮어써짐, 해당 prom.txt는 프리필 노드 값), 주의 런에서 나왔으며, 설정 상한이다. 삭제하거나 "live metrics, not retained; the limit is `--max-num-seqs 256`, not decode compute"라는 각주로 바꾼다. "Chat needs more decode capacity"도 삭제한다.
- 31B 4K "more prefill"의 근거(0.75 req/s의 굿풋 290/177/8)는 어느 구성도 안정적으로 통과하지 못한 점이다. "suggestive"로 낮춘다.
- 체크리스트 4는 "size the side that saturates first; measure it"으로 줄인다.
- 스크립트 작업: 없음.

**A6. 식 1을 고치고 과장을 걷어 낸다** (R1-3, R3-2·3, R4 ❌1, R5 과장 목록)
- 전송량을 아핀으로 쓴다. 26B NVFP4 실측 140/260/412.5 MiB는 V(L) ≈ 100 MiB + 10 KiB·L에 맞는다. 토큰당 바이트는 4K 35 KiB → 16K 16 KiB → 32K 13 KiB로 준다(슬라이딩 윈도우 층). 일반형은 V(L) = L·b_global + min(L, W)·b_local이다.
- "almost entirely"는 "61–85% at low load"로 바꾼다. 초록, 기여 2("equals"), 결론("is the KV transfer time and can be computed in advance")을 모두 고친다.
- 잔차 전체 범위(노트 기준 −26~+87 ms)를 보고한다. 잔차는 프록시 홉, 스케줄링, 첫 디코드 스텝이며 RDMA에서도 남는 바닥값이라고 §5.2에 적는다.
- 대기열 항을 넣거나, 식 1이 저부하 근사라고 명시한다. R2와 R3가 각각 계산한 M/D/1 보정(ρ = λ·S, W_q = ρS/[2(1−ρ)])이 tc 점을 설명한다. 1 Gbps에서 대기열 없는 예측은 1.45–1.50 s, 대기열 포함 예측은 2.16–2.35 s이고 실측은 2.19 s다. 체크리스트 2에 링크 이용률 조건을 넣는다.
- "The transfer volume matched the prediction exactly"는 검증에서 뺀다. 바이트 회계상 당연하고, 26B의 140 MiB는 세션 B에서 이미 쟀다.
- "predicted before we measured"의 근거를 댄다. 예측이 적힌 기록(노트 시각, 세션 로그)을 인용하거나, 그런 기록이 없으면 "computed from the model with m fitted on the two-node runs"로 낮춘다. 오차(+14%, +3–5%)를 본문에 적는다.
- §4.3 16K 예시를 바꾼다. "For 26B FP8 at 16K, prefill alone takes about 0.8 s and the ≈0.5 GiB transfer adds about 0.5–0.6 s (measured PD–replica TTFT difference 465–506 ms), so the 1 s budget cannot be met."
- 전송 크기가 작으면 m < 1이다(25 MB 전송에서 0.37–0.54). 채팅 규모에서는 흐름 상한이 아니라 고정 비용이 지배한다고 적는다.
- 스크립트 작업: 중간. 전송 로그 파서와 항별 예측표가 필요하다.

**A7. m의 단위, 정의, 메커니즘, 튜닝 내용을 정리한다** (R1-4, R3-1·4·5, R4 ❌6·⚠️)
- vLLM의 "MB"는 MiB다(2,240 × 64 KiB = 140 MiB). Gbps 환산을 바로잡으면 m은 1.32/1.46/1.68 → 1.38/1.53/1.76이 된다. 본문의 "1.3–1.7"은 "1.4–1.8"이 된다.
- 6.55 Gbps는 0.5와 1 req/s의 평균이다. 캡션 정의(0.5 req/s)대로면 6.91이다. 13.96은 회색 점 넷(기준 설정 포함)의 평균이다. 정의를 하나로 정하고, `make_figures.py:185`의 상수를 공개 로그에서 계산하는 코드로 바꾼다.
- 메커니즘은 가설로 낮춘다. 문안: "The rate exceeds the single-flow limit, consistent with NIXL splitting a 26B 4K request into three descriptor chunks (1,024/1,024/192) handled by up to three connections (our reading of the v0.30.0 source; we did not count sockets)." "slightly"는 삭제한다.
- 간접 증거 하나는 이미 데이터에 있다. 흐름당 상한이 4.97 Gbps인 경로에 tc로 **합계** 5 Gbps 제한을 걸자 TTFT p50이 471 → 587 ms(+25%)로 늘었다. 흐름 하나만 쓰였다면 거의 영향이 없었어야 한다. 이 점을 본문에 넣는다. 다만 소켓 수의 증명은 아니다.
- "The remaining headroom lies in the number of connections, not in settings"(§4.2, 체크리스트 3)는 "not in the settings we tried; more parallel connections are the likely lever (untested)"로 바꾼다.
- 튜닝 공개. D1d는 UCX 변수 일곱 개(TX/RX_SEG 256k, MAX_IOV 16, MAX_POLL −1, SNDBUF/RCVBUF 8m, RNDV_FRAG host:4M,cuda:8M)에 UCX_TLS와 NET_DEVICES까지 함께 바꿨다. §3.1과 §4.2는 "raising the segment size together with related buffer settings (Appendix) doubled the rate"로 고치고 전체 목록을 부록에 싣는다.
- 호스트 버퍼 모드의 링크 전송률(기본 UCX 7.3–9.4 Gbps)을 적는다. 이는 8 KB 효과가 GPU 스테이징 경로에 한정됐을 가능성을 보여 준다.
- 환경을 보고한다: MTU 9001, RTT(측정분), 커널, 혼잡 제어, NIXL·UCX 버전, sysctl을 바꾸지 않았다는 사실(SNDBUF 8m이 wmem_max에서 잘렸을 수 있음).
- 스크립트 작업: 중간(전송 로그 파서, A6과 공용).

**A8. 네트워크 문단의 틀린 논증을 고친다** (R3-6·8, R4 ❌2, R1 minor, R5)
- 크레딧. 결론은 맞지만 증거가 틀렸다. 단일 흐름(≤4.97)은 기준 대역폭 5 Gbps 아래라서 크레딧 소진을 잡아내지 못한다. 문안: "On g6e.2xlarge (5 Gbps baseline, 20 Gbps burst) our 15-minute load averaged about 1.1–1.2 Gbps (0.5 req/s × 280 MiB, computed, not measured), below the baseline, so the burst allowance could not drain. g7e.2xlarge has a fixed 50 Gbps and no burst model." 전후 iperf 문장은 삭제하거나 "not a test of credit depletion"이라고 밝힌다.
- "18% of the cap"은 "of the baseline bandwidth"로 바꾼다. 0.91은 230 MB를 가정한 계산값이다.
- tc: "Artificially limiting bandwidth shows that this cap sets TTFT"는 "Limiting the sender's aggregate bandwidth shows that link bandwidth sets TTFT"로 바꾼다. tbf는 합계 제한이다. 5 Gbps 점도 본문에 넣는다(A7).
- "Two things did not help or hurt"는 "Host staging hurt; network credits did not matter at our load"로 바꾼다. 호스트 스테이징의 "75× at 1 request/s"는 불안정 대기열의 값이라 측정 길이에 좌우된다. "no stable rate at 1 req/s; 4.7× TTFT at 0.25 req/s (g7, GPU memory utilization 0.70, 30 GiB host memory)"로 조건을 붙이고 구현상의 병리일 수 있다고 적는다.
- 스크립트 작업: 없음.

**A9. 문제 설정(EFA)과 적용 범위를 바로잡는다** (R3-7·10, r0-1)
- 초록과 §1: "Rented cloud GPUs often have neither"를 "The cheapest single-GPU cloud instances, such as the 2xlarge sizes of AWS g6e, g7, and g7e, have neither"로 바꾼다.
- §5.2(또는 §6)에 추가: "EFA is available on the 8xlarge sizes of the same families (without GPUDirect RDMA on g6e and g7e) at about 1.6–2× the hourly price; ENA Express is not available on 2xlarge sizes. Where the TTFT budget does not bind (26B, 4K), RDMA would mainly remove the 84 ms transfer term, which is unlikely to recover a 1.6× price premium; where it binds (31B 4K, 16K inputs) it may." 마지막 문장은 추론이라고 표시한다.
- 가격은 AWS 공식 가격표로 확인한 뒤 적는다.
- 한계 절에 적는다: 흐름당 상한은 AWS 정책이고, m은 NIXL/UCX 버전의 분할 규칙에 묶여 있다. 다른 클라우드에서는 `iperf3 -P 1`과 `-P N`을 먼저 재라.
- 스크립트 작업: 없음.

**A10. 관련 연구와 참고문헌** (R1-5, R5-7)
- 추가할 문헌과 논점은 다음과 같다. 좌장이 arXiv 초록 여섯 건의 존재와 인용 문장을 확인했다. Andes는 확인하지 않았다.
  - TaiChi(2508.01989): "aggregation is optimal for tight TTFT and relaxed TPOT, while disaggregation excels for strict TPOT and relaxed TTFT"이고, 청크 크기가 slider다. RQ3의 결론과 같은 경계이므로 "이 경계를 TCP와 요청별 최대 간격에서 정량화했다"로 위치를 잡는다.
  - EcoServe(2504.18154): 커머디티 인터커넥트 클러스터에서 "the FuDG strategy highly relies on high-performance interconnects, making them less cost-effective." 이 논문의 결론과 정면으로 대비되므로 반드시 논의한다. OSDI'26 게재 여부는 arXiv 페이지에 없으므로 저자가 확인한다.
  - ThunderServe(MLSys'25)와 HexGen-2(ICLR'25): 이기종 GPU와 클라우드 네트워크 조건에서 단계 분리를 다룬다. ThunderServe의 "4비트 KV 전송 양자화"는 초록에 없으므로 본문을 확인한 뒤 인용한다.
  - Etalon(2407.07000, fluidity-index)과 Andes(QoE): 기여 1을 "요청별 관점의 적용"으로 재서술한다.
  - KVDirect(2501.14743): pull 방식 KV 전송의 근거.
- §2의 "Where this work sits"와 "We did not find a study of the same setting"을 위 문헌을 반영해 다시 쓴다.
- 참고문헌에서 arXiv @misc 6건이 eprint 없이 "…, 2026."으로만 찍혀 찾을 수 없다. 이것은 인용 가능한 문서로서 결함이므로 A에 둔다. 연도 중복([8]), {McAllister}, 제목 대소문자 보호도 함께 고친다.
- 스크립트 작업: 없음.

**A11. 초록의 모순, 단위, SLO 이름** (R5-1·2·3)
- "For chat-length inputs it brought no gain"은 31B 채팅 문장과 모순된다. "for the MoE 26B model"로 한정한다.
- "When a service must keep every gap under 50–75 ms, disaggregation wins"는 26B FP8 채팅(g7e, 모든 SLO에서 복제본 우세 0.3–0.7)과 어긋난다. "for 4K inputs or the dense model"을 붙인다.
- 요청률은 전부 GPU당으로 통일하거나 모든 수치에 total과 per GPU를 붙인다. §4.5의 31B 문단, 표 2, 그림 5·A5가 대상이다.
- "chat SLO"는 "strict SLO (1 s / 50 ms)", "document SLO"는 "relaxed SLO (3 s / 250 ms)"로 바꾼다. 4K 입력에 "chat goodput"이 붙는 혼동이 사라진다.
- 스크립트 작업: 그림 라벨 재생성.

**A12. 데이터 선별과 통계 서술** (R2-4·7·minor, R4 ❌4·⚠️, R5-6)
- §3.6 "Only points with attainment between 0.85 and 0.95 varied by up to ±0.09"는 틀렸다(26B 복제본 GPU당 2 req/s: 0.478–0.644, 전날 0.367). R4 문안으로 바꾼다. 그림 A5 제목도 "Disagreement flips the verdict only near 0.9"로 고친다.
- 산식을 명시한다: 389 − 128 − 5(주의) = 256. 폐기 규칙을 열거한다. "All measurements"는 "All reported measurements"로 고친다. 그림 1의 166런에는 주의 런 2개가 들어 있고, "18 replica" 중 1런은 단일 노드다. 이것도 적는다.
- "each run lasts 180 s"를 "max(100, 180·r) requests"로 바꾼다. 0.25 req/s 런은 약 400 s다.
- 출력 1토큰 요청(ShareGPT의 2.4–3.0%)을 실패로 세는 버그를 고친다. R2 확인으로는 1 s/50 ms 판정이 바뀌는 런은 없다.
- 판정을 좌우하는 점(각 구성의 통과 한계와 첫 탈락 점)에 요청 시간 블록 부트스트랩 95% CI를 보고한다. R2 스크립트가 있다. 단일 런 점(1P1D @6, 1P2D @9, 31B 1P1D @4, 2P1D 채팅 @24 0.904)을 표시한다.
- 코드와 서술을 맞춘다. `capacity()`는 통과한 요청률 중 굿풋 최대값을 쓴다. 표 3은 반복 평균을, 그림 8은 최소값을 쓴다. 둘 중 하나로 통일하고 방법 절에 적는다.
- 26B 채팅 비용은 "both ≤ $0.63, not separable"로 쓴다.
- E5와 E7의 클라이언트 사양 차이를 적는다. 그림 6·7의 막대가 두 날을 섞는다는 점도 캡션에 적는다.
- 워밍업이 없던 세션의 첫 1~3요청을 잘라 낸 결과(R4: +0.019 이내)를 한 줄 적는다.
- 스크립트 작업: 중간(R2 스크립트 정리, analyze.py 수정, 그림 재생성).

**A13. 틀리거나 근거가 다른 개별 수치** (R4 ❌·⚠️, R1 minor, R5)
- §4.7 "$3.15" → $3.14(g6e $2.242/h). 표 1 캡션에 g6e 요금을 추가한다.
- 프런티어 수치: "50–65 ms" → 48–64, "70–90 vs 35–48" → 75–89 vs 33–48.
- §4.4 "16 req/s chat no gain at any precision": BF16은 "neither passed"다.
- 267 ms(§4.3)와 269 ms(§4.4)는 다른 런이다. 351 ms와 165 ms도 서로 다른 런이다. 158 ms는 단일 노드가 아니라 E2 복제본 값이다. 각각 밝힌다.
- 초록과 RQ3의 "at 100 ms or more the difference mostly disappears"는 "shrinks to ≤2× or cannot be resolved within the measured rates; 31B 4K at a TTFT limit ≥1.5 s and g7 4K remain disaggregation-only"로 바꾼다.
- §4.4 소제목 "Faster GPUs narrow the gap"은 데이터와 맞지 않는다. 복제본은 세 GPU 모두에서 0.02–0.14로 무너졌고, 0.97로 오른 것은 NVFP4로 바꾼 효과다. "Replicas collapse at 4K on every GPU; only lighter NVFP4 weights let them hold"로 바꾼다.
- 푸시 전송량(468–533 MB, pull은 560 MB)의 차이를 한 줄로 적는다. 290 tok/s는 E5 1회 값(반복 282–344)이다. TTFT 변동 5.1% 사례가 있다. 그림 A5의 "all 1.00"에는 0.999와 0.998이 섞여 있다.
- 비용 합계($220, 기록 합 약 $181, 저자 노트 $217)를 하나로 정하고 출처를 적는다.

**A14. 정확성 검사 결과를 적는다** (R1 minor, R5-4, R4 ❓)
- §4.8은 무엇을 비교했는지만 쓰고 결과가 없다. 게이트 정의(커밋 ffe5c99: 짧은 프롬프트는 바이트 일치, 긴 프롬프트는 참조 내용어의 40% 이상 공유)와 결과 수(노트의 재기동 후 일치 수, E6 게이트 JSON에 남아 있음)를 적는다. 긴 프롬프트에서 완전 일치를 기대하지 않는 이유(배치 비결정성)도 한 구절 넣는다.

**A15. 재현 패키지** (R4)
- 공개 원자료로 재현되지 않는 수치를 없앤다. 그림 3·4의 `make_figures.py` 상수를 로그 파서로 바꾼다. 잘린 E2 전송 로그는 잘렸다고 표시한다.
- GitHub에 푸시할 수 없는 파일이 있다. `results/E5/rr_proxy_E5_26_B3.log`는 436 MB이고, 50 MB가 넘는 `result.json`/`bench.json` 쌍이 있다. 원자료는 Zenodo로 옮기고 `result.json` 중복을 없앤다.
- README는 측정 전 상태(H100, writeup/)다. 명령 네 개와 SLO 인자를 README에 적는다.
- 버전을 기록한다: vLLM 이미지 태그와 digest, NIXL·UCX 버전, HF revision. CSV의 `instance_type` 열도 고친다.

**A16. 공개 전 정보 정리** (R4)
- RESULTS.md 1068행의 S3 버킷 이름에 AWS 계정 ID가 들어 있다(좌장 확인). 이 값은 git 이력에도 있으므로, HEAD만 고치면 부족하다. 새 이력으로 공개하거나 이력을 정리한다.
- `.session_*.env`, `env_*.json`의 인스턴스 ID, IP, AMI, `variables.tf`의 개인 프로필명과 `0.0.0.0/0` SSH CIDR도 정리한다. 모두 비용 없는 작업이다.

---

## 3. B. 반드시 고칠 것: 새 측정이 필요하거나, 측정하지 않으면 한계로 명시해야 하는 것

가격 가정: g7e.2xlarge $3.363/h × 2대, 클라이언트 c6i.2xlarge 약 $0.34/h. 비교 가능성을 위해 E5·E7과 같은 AZ, 같은 클러스터 배치 그룹, 같은 시드와 워밍업을 쓴다.

**B1. 복제본 청크 크기 스윕: 가장 중요한 실험이다**
- 이유: 헤드라인 (a)를 뒤집을 수 있는 유일한 실험이다. 나머지는 분리 쪽을 불리하게 만든 요인(B2)이거나 서술만 바꾼다(B3, B4). 청크 크기는 Sarathi-Serve 이래 공동 배치의 표준 노브이므로, 전문 독자가 가장 먼저 물을 질문이다.
- 0단계 기동 확인(10분): 26B NVFP4를 `--max-num-batched-tokens 1024 --limit-mm-per-prompt '{"image":0}'`로 띄운다. Gemma 4에 다른 모달리티가 있으면 그것도 0으로 둔다. 기동하지 않으면 그 사실 자체가 결과다. "stock vLLM v0.30.0에서 Gemma 4 복제본은 2,560 아래로 내릴 수 없다"를 방법 절에 적고, 이득은 이 스택의 제약으로 해석한다.
- 본 측정: 26B NVFP4, 4K 입력/512 출력, 복제본 둘. 청크는 {1024, 1536, 2048} 세 값에 2560을 같은 날 대조군으로 더한다. 요청률은 GPU당 {1, 2, 3, 4}(합계 2, 4, 6, 8)다. 한계 부근 두 점은 2회 반복한다. 같은 날 1P1D 대조로 GPU당 3과 4를 2회씩 잰다.
- 선택 팔(각 +20~30분): 26B FP8 복제본을 청크 1024로 GPU당 0.5와 1에서 잰다(FP8/BF16 주장 검증). 31B 채팅 복제본을 청크 256으로 GPU당 1에서 잰다(31B 주장이 청크에 강건한지 확인).
- 판정 규칙을 미리 적어 둔다. 이득 = 1P1D 지원 부하 ÷ (청크별 복제본 지원 부하의 최댓값), 기준은 1 s/50 ms다. 40 ms와 75 ms도 요청별 원자료로 함께 보고한다.
- 규모: 약 26~30런 × 4~5분에 재기동 5회와 준비·정리를 더해 약 3~3.5시간이다. 2 × $3.363 × 3.5 ≈ $24, 클라이언트 포함 약 $25다. 선택 팔을 넣으면 약 $30~35다.
- 측정하지 않을 경우의 문안(초록과 §4.5에 모두): "The replicas used a fixed 2,560-token prefill chunk, the smallest our vLLM version accepted for Gemma 4, which puts their mixed step at about 48 ms, 1.6 ms under the 50 ms limit. We did not measure smaller chunks, which would shorten the stall and may remove most of the gain; the 1.5–4× figure should be read as the gain over this baseline." 이 경우 26B 4K를 초록의 첫 번째 결과로 두지 말고, 31B 채팅과 전송 분석을 앞에 둔다.

**B2. 전역 정지의 원인과 프록시 대칭**
- 이유: 분리 구성의 한계 판정(1P1D 4K가 GPU당 3인지 4인지, 31B 1P1D 채팅이 2인지 4인지)과 3노드 해석을 정한다. 방향은 분리를 불리하게 만드는 쪽이므로 헤드라인을 뒤집지는 않는다.
- 최소 설계: 1P1D 26B 4K를 합계 8 req/s로 3회 돈다. 조건은 둘이다. (i) 현재 toy proxy에 이벤트 루프 지연 로깅(1 ms 주기)을 붙인다. (ii) `rr_proxy.py`에 P→D 경로를 넣은 aiohttp 프록시로 복제본과 같은 코드 경로를 쓴다. 두 조건 모두 D 노드의 엔진 스텝 시간을 기록하고, 클라이언트 수신 시각과 대조한다. (ii)에서 정지가 사라지면 프록시 산물로 확정하고 1P1D 한계를 GPU당 4로 고친다.
- 규모: 약 1~1.5시간, 약 $7~10(B1 세션에 붙일 때). 프록시 개발은 로컬 작업이다.
- 측정하지 않을 경우: A4 문안 그대로 쓰고, 분리 구성의 한계는 보수적이라고 명시한다. 3노드 비율 해석은 하지 않는다.

**B3. m의 연결 수(소켓 수) 확인**
- 이유: §4.2와 체크리스트 3의 메커니즘 주장("여유는 연결 수에 있다")을 검증한다.
- 최소 설계: 1P1D 26B NVFP4 4K와 31B NVFP4 4K를 각각 0.5 req/s로 5분씩 돈다. 이때 P와 D에서 `ss -tin`을 50~100 ms마다 떠서 P–D 사이 ESTAB 5-tuple 수와 소켓별 `bytes_acked` 증분을 센다. 한 점을 더해 UCX TX/RX_SEG만 256k로 바꾼 단독 대조(R3-5)를 잰다.
- 규모: 31B 적재를 포함해 약 30~45분, 약 $4~5.
- 측정하지 않을 경우: A7 문안(가설, 소스 독해, 간접 증거인 tbf 5 Gbps 점)으로 충분하다.

**B4. 31B 채팅 복제본의 GPU당 1 req/s 미만**
- 우선순위가 낮다. 좌장 모형이 0.5에서 약 0.59, 0.25에서 약 0.72를 예측하므로 "none at ≥1 req/s per GPU"와 모형 외삽만으로 주장이 선다.
- 최소 설계: 복제본 둘, GPU당 0.25와 0.5 req/s, 각 3회. 요청 수 max(100, 180r) 규칙상 런당 약 3~7분이다.
- 규모: 31B 적재를 포함해 약 45분, 약 $5(B3과 같은 세션이면 적재 비용을 공유한다).
- 측정하지 않을 경우: A2 문안을 쓰고 모형 외삽을 부록에 둔다.

**권하지 않는 측정.** 3노드 재측정(2P1D의 `--max-num-seqs` 상향 등), 8xlarge+EFA 기준선, 한계점 조밀 격자와 긴 런은 이번 프리프린트에서 요구하지 않는다. 비율 규칙은 A5처럼 격하하고, EFA는 A9처럼 논의로 처리한다.

**한 세션으로 묶으면:** 기동 확인 → B1 → B3 → B2 → B4 순으로 약 5~5.5시간, 클라이언트를 포함해 약 $37~45다. E7($90)의 절반 이하이고, 가장 비싼 불확실성(헤드라인 (a))을 해소한다. 저자 승인이 필요하다.

---

## 4. C. 고치면 좋은 것

- **그림 가독성:** 인쇄 크기 글자가 그림 8 약 4.4pt, 그림 9 약 5pt, A7 셀 약 3.9pt, A5 행 라벨 약 5pt다(R5). 6~7pt 이상으로 키운다. 그림 8은 패널을 줄이고, 결론형 제목을 달고, "best config of each kind"를 캡션에 적고, 쓰이지 않는 "Similar" 범주를 없앤다. 그림 9 캡션에는 결론 한 문장("Top: replicas reach the first token sooner. Bottom: disaggregation keeps gaps shorter.")을 넣는다. 그림 1은 단일 노드와 복제본의 마커를 나눈다. 그림 A6은 파랑/주황으로 나눈다. 그림 속 제목 형식을 통일한다.
- **구조:** RQ 번호를 서술 순서에 맞춘다. §5.1은 한 줄 답으로 줄이고 체크리스트를 산출물로 남긴다. 도입부 끝에 "Key findings"를 넣는다. §4.8의 잡탕을 흩어 놓는다(트레이스는 §4.5, 푸시와 PR #56874는 §4.2). 부록 B를 본문에서 참조한다.
- **용어 통일:** replicas/aggregated/colocation, maximum gap/max ITL, TTFT budget/limit, per-flow cap/single-flow limit, supported load 계열을 하나씩으로 정한다. 약어(SLO, SM, EFA, UCCL, UCX, NIXL)는 첫 사용에서 풀어 쓴다. "pull-based connector"는 §3.1에서 정의한다.
- **보조 지표와 한계:** 토큰당 멈춤률이나 Etalon식 지표를 보조로 싣는다. 출력 512 고정은 요청이 멈춤에 노출되는 시간을 늘린다. 랜덤 토큰 입력은 MoE 전문가 부하를 비현실적으로 만들 수 있다. 둘 다 한계 절에 적는다.
- **공정성 주석:** P 노드 청크 확대와 D 노드 `--max-num-seqs` 조정도 분리 쪽 튜닝 여지라고 한 줄 적는다(R1-1). 대칭성을 보여 준다.
- **선택 재분석:** 기존 분리 점 전체에 대한 식 1의 hold-out 오차를 이용률 대비로 그린다(R1-3). 전송 로그가 남은 점만으로 한다.
- **자잘한 형식:** 제목 줄바꿈("RDMA?"가 홀로 남음), 부제에 "Single-GPU Cloud Instances"를 넣는 안, URL 줄 간격(`xurl`), Acknowledgments를 Funding으로, 표 C1(`\ref`, "26B, 31B FP8" 중의성, "plumbing runs"), CITATION.cff와 LICENSE 경로, `.gitignore` 패턴, uv.lock.
- **문장:** R5의 문장 교정표(약 60건)는 대부분 그대로 받아도 좋다. 번역투 예시로 "Two things did not help or hurt", "has a cost at all"이 있다.

---

## 5. D. 반박하거나 받아들이지 않을 것

**D1. "절대 50 ms가 dense 모델에서 분리에 유리하게 편향된다. 상대 기준(5×스텝)을 써야 한다"** (R1-2, R2-2a): 주 기준으로는 받아들이지 않는다. SLO는 사용자가 체감하는 요구이고, 하드웨어의 스텝 시간에 따라 느슨해지면 안 된다. 느린 모델에 125 ms를 허용하는 상대 기준은 "이 모델이 느리니 사용자도 더 참아라"는 뜻이 된다. 저자의 결정(노트 150행)은 타당하다. 받아들일 것은 공개와 병기(A3)뿐이고, 주장의 조건문(A2)으로 충분하다.

**D2. 31B 메커니즘을 밝히려면 스텝 단위 트레이스와 CUDA graph 모드 조사가 필요하다** (R1-2): 받아들이지 않는다. R1은 "100토큰 안팎의 프리필"을 전제로 연산량만으로는 스텝이 두 배가 될 수 없다고 봤다. 그러나 실제 ShareGPT 입력은 평균 247, p90 690토큰이다. 겹친 프롬프트 길이로 탈락이 거의 완전히 갈린다(1절 (b)). 연산량으로 설명되므로 런타임 효과를 가정할 필요가 없다.

**D3. 31B 복제본을 GPU당 1 req/s 미만에서 측정해야 한다** (R2-2b): 필수가 아니다. 서술을 "≥1 req/s per GPU"로 한정하고 모형 외삽을 붙이면 충분하다(B4는 선택).

**D4. 2P1D를 `--max-num-seqs` 상향으로 재측정하고, 비율을 정량 예측해 검증하라** (R1-7): 이번 판에서는 받아들이지 않는다. 3노드 측정은 비싸고, 주장을 격하하면(A5) 필요가 없다.

**D5. 한계점 조밀 격자, 긴 런, 0.9 교차점의 로지스틱 적합** (R2-4 일부): 조밀 격자와 긴 런은 요구하지 않는다. 주장을 격자 구간으로 쓰면 된다. 로지스틱 적합은 2배 간격 격자와 1~4회 반복으로는 잘 식별되지 않는다. 보간값(2.8–3.3배)을 민감도로만 보고하는 편이 정직하다. 블록 부트스트랩 CI는 받아들인다(A12).

**D6. 서버 타임스탬프로 TTFT를 분해하라** (R1-3 일부): 새 런이 필요하므로 요구하지 않는다. 저부하 범위 명시, 대기열 항, 잔차 전체 범위 보고(A6)로 대신한다.

**D7. TX_SEG 단독 절제 실험, 호스트 스테이징 nsys 프로파일** (R3-5·9): 필수가 아니다. 두 배 향상을 변수 묶음에 귀속하고(A7), 호스트 스테이징은 조건을 붙인 부정적 결과 한 줄로 줄이면(A8) 논문의 주장과 무관해진다. TX_SEG 단독 대조는 B3에 싼 값으로 붙일 수 있다.

**D8. ENI 추가 레일, MPTCP, NCCL/Mooncake TE/UCCL 실험과 8xlarge+EFA 기준선** (R3-7 실험 부분): 범위 밖이다. 논의와 향후 과제로 처리한다(A9). 다만 EFA 전제의 서술 수정은 필수다.

**D9. §2 "All of them assume a fast interconnect"가 ThunderServe·HexGen-2와 충돌한다** (R1-5 일부): 그 문장은 바로 앞에 나열한 DistServe 계열을 가리키므로 문자 그대로는 맞다. 충돌하는 곳은 "Where this work sits"와 "We did not find a study of the same setting"이고, 여기를 고치면 된다(A10). Etalon이 "퍼센타일이 멈춤을 가린다"를 이미 보였다는 주장은 초록 수준에서는 "conventional metrics fail to fully capture…"까지만 확인된다. 관련 관점으로 인용하되 과장하지 않는다.

**D10. 크레딧 결론은 근거가 없다** (R3-6): 결론은 유지된다. 평균 부하(약 1.1–1.2 Gbps)가 기준 대역폭 5 Gbps보다 낮아서 버킷이 줄어들 수 없다는 산술로 성립한다. g7e.2xlarge에는 버스트 모델 자체가 없다. 증거 문장만 바꾸면 된다(A8).

**D11. "연결이 늘수록 연결당 효율이 떨어지니 공유 병목(CPU, cuda_copy)이 있다"** (R3-1): 저자의 설명만큼이나 검증되지 않은 추론이다. 이상적 배수(2.2/1.9/4배 이상)는 조각 하나가 소켓 하나에서 완전히 병렬로 돈다고 가정한다. 그런데 노트의 소스 독해(스레드 쌍당 엔드포인트 하나, `dev_num_paths=1`)는 그 가정을 보장하지 않는다. 두 설명 모두 가설로 표기한다. 판정은 B3의 소켓 수로 한다.

**D12. 점수 2/5(weak reject)** (R1): 워크숍 기준으로는 이해할 수 있다. 실무자용 프리프린트로서는 A를 반영하고 (a)에 조건을 달면 공개할 만하다. R1의 핵심 지적(청크)은 받아들이되, 그 비판이 논문 전체가 아니라 주장 하나에 해당한다는 점을 구분한다.

---

## 6. 초록 재작성안 (새 실험 없이 유지되는 내용만, 200단어)

> Prefill–decode (PD) disaggregation is usually deployed over RDMA or NVLink. The cheapest single-GPU AWS instances (2xlarge sizes) offer neither, so the KV cache must cross TCP. We measured stock vLLM v0.30.0 with NIXL/UCX over TCP on one to three such nodes serving Gemma 4 26B (mixture-of-experts) and 31B (dense), judging each request by its time to first token (TTFT) and its longest gap between output tokens. With default UCX settings the transfer software, not the network, was the bottleneck; after tuning, the transfer rate tracked the cloud's single-flow limit. At low load, KV transfer made up 61–85% of the TTFT that disaggregation added. The outcome hinged on the gap limit. At 50 ms, for 26B with 4K-token inputs, disaggregation served about 3× (grid bounds 1.5–4×) more requests per GPU than replicas whose untuned 2,560-token prefill chunk put their gaps at about 48 ms. For 31B chat, prompts of a few hundred tokens pushed replica gaps past 50 ms at every measured load, while disaggregation met the limit at 2 requests/s per GPU. With limits of 100 ms or more, or for 26B chat, we found no clear gain, and replicas always reached the first token sooner. We release per-request data.

주: B1을 측정하면 26B 4K 문장은 결과에 맞춰 바꾼다. 이득이 유지되면 "even against replicas tuned for chunk size"를 붙이고, 줄어들면 수치를 바꾼다. 체크리스트는 초록에서 빼고 본문 산출물로만 둔다. 체크리스트 1이 복제본의 실측 최대 간격을 요구하므로 "decides in advance"는 과장이다(R5).

---

## 7. 리뷰어 간 불일치와 좌장 판단

- **심각도(R1 2/5 대 나머지 3/5):** R1은 청크 문제를 "잠재적 치명"으로 봤고, R2는 같은 문제를 "2 ms 여유"로 정량화했다. 좌장은 둘이 같은 사실을 가리킨다고 확인했다(48.4 ms 봉우리). 이것은 주장 (a)에 치명적일 수 있지만 논문 전체에 치명적이지는 않다. 판정은 "대폭 수정 + B1 강력 권고"다.
- **상대 대 절대 SLO(R1·R2 대 저자 노트):** 절대 기준을 주 기준으로 유지하고, 공개하고, 병기한다(D1).
- **31B 메커니즘(R1: 런타임 효과 의심, R2: 출력 길이 의존):** 좌장 분석이 둘을 한 번에 설명한다. 탈락은 같은 복제본에 겹친 수백 토큰 프롬프트 때문이고, 출력이 길수록 그런 프롬프트와 겹칠 확률이 커진다.
- **m 메커니즘(R1: 소켓을 세라, R3: 공유 병목, 저자 노트: NIXL 3조각 분할):** 방향(흐름이 여러 개)에는 tbf 5 Gbps 점이라는 간접 증거가 있다. 개수와 효율은 미검증이다. 가설로 표기하고, 판정은 B3에 맡긴다.
- **전역 정지(R2 발견)와 프록시 비대칭(R1 지적):** 같은 문제의 양면이다. 둘 다 분리 쪽에 불리하므로 헤드라인 방향은 보수적이다. 다만 2P1D 해석과 비율 규칙은 무너진다(A4, A5).
- **크레딧(R3: 방법 틀림, 저자: 결론 맞음):** 둘 다 맞다. 증거만 바꾼다(D10).
- **관련 연구(R1: §2 문장이 틀림):** 문장 자체는 범위가 한정돼 맞고, 틀린 것은 위치 설정 문단이다(D9).
- **R4의 재현성 판정(CSV 경로 5점, CSV 밖 수치 감점):** 좌장도 동의한다. 논문 수치 중 공개 스크립트로 재현되지 않는 것(그림 3·4, m, 전송률)이 모두 네트워크 절에 몰려 있다. 이는 A6·A7의 서술 문제와 같은 뿌리이므로 전송 로그 파서 하나로 함께 해결한다.
