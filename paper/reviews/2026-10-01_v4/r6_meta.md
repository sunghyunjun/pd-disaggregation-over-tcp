# 종합 심사 (4차, 원고 v4)

대상: "Chunk First: When Prefill–Decode Disaggregation Pays Off over TCP" (paper/en/main.tex v4, 커밋 d0f4c12)
근거: 4차 리뷰 5건(R1 3.5, R2 3.5, R3 4.0, R4 3.5[수치 4.0, 패키징 2.5], R5 4.0)과 그 스크립트, 종합 심사자의 직접 계산. 저장소는 읽기만 했다.
스크립트(`reviews_v4/r6/`, 저장소 루트에서 `uv run --with numpy python3`): `m0_runs.py`, `m0b_fp8runs.py`(런별 간격·TTFT·ITL), `m1_cross.py`(연속 교차, 민감도, 한 점 빼기, 9점 적합), `m2_more.py`(청크별 단계 비용, GPU당 용량, g7 재적합). 출력은 `m1_out.txt`·`m2_out.txt`, 초록은 `abstract_v5.txt`에 있다.
표기: **[확인]**은 종합 심사자가 다시 계산한 값이고, **[R1]** 등은 리뷰어 값이다. "교차"는 L을 64토큰 간격으로 훑어 1P1D TTFT가 복제본 TTFT 아래로 내려간 뒤 다시 올라오지 않는 첫 길이다. 따로 적지 않으면 26B FP8, g7e 기준이다.

## 1. 판정

**주요 수정(major revision).** 범위는 6절과, 그 수치를 옮겨 쓴 초록·서론·7절·결론으로 한정한다. 새 측정은 필요 없다. 4–5절은 3차 판정대로 공개할 수 있다. **v4의 재구성("Chunk First", RQ1–3)은 유지한다.**

- 초록의 새 주장 "beyond roughly 20K tokens, only disaggregation meets both limits"는 지금 형태로는 틀렸다. 이유는 네 가지다.
  1. 숫자가 TTFT 격자에서 나왔다.
  2. TTFT 한도와 저부하라는 조건이 빠졌다.
  3. 1P1D 디코드 노드 간격을 원고 자신의 측정과 달리 7 ms로 고정했다.
  4. 불확실성은 두 배 폭인데 점처럼 썼다.
- 고쳐도 핵심 메시지는 산다. 다만 더 좁고 약하게 말해야 한다((e)).
- 다음 원고에서는 R2와 R4가 수치만 재확인하면 된다. 부제는 "a Calibrated Model"로 바꾼다(R5). 제목은 유지한다.

## 2. 쟁점별 판정

**(a) 경계의 정의는 곡선 교차로 통일한다.**
- m = 1에서 교차는 50 ms 19.0K(처음 닿는 점 18.5K, TTFT 1.34 s)와 30 ms 8.8K(8.5K, 0.65 s)다 [확인; R1·R2·R4와 같다].
- 본문의 21K·11K·19K·25K·6K/4K는 모두 격자 값이다.

**(b) 지도의 기본 m은 1.5로 하고, 1–1.8을 띠로 보인다.**
- 지도는 저부하를 가정하고, 표 3도 m = 1.5로 검증했다. 이 체크포인트의 4K 저부하 m은 1.46–1.61이었다 [R3].
- 26B 전송은 약 16K부터 네 조각으로 나뉜다 [확인, 원고의 디스크립터 구조로 계산]. 네 조각 전송의 저부하 m은 1.8이다 [R3, 31B 4K].
- m = 1은 부하 아래 값이다.
- 교차는 다음과 같다 [확인].
  - m = 1.5: 50 ms 14.1K(0.84 s), 30 ms 6.3K
  - m = 1.8: 12.5K, 5.8K

**(c) 1P1D 디코드 노드 간격은 L에 비례하는 직선으로 둔다. 필수다.**
- 요청별 최장 간격 p90 [확인]:
  - 4K(GPU당 0.25): 14.4 ms
  - 16K(GPU당 0.125): 27.8 ms(7%가 30 ms 초과)
  - 16K(GPU당 0.25): 33.5 ms(48%가 30 ms 초과)
- ITL 중앙값은 7.75에서 7.98 ms로 거의 그대로다. 길어진 것은 드문 긴 단계다.
- g7 NVFP4의 p90은 4K 18.7, 16K 29.5, 32K 43.3 ms다. 4K와 16K로 그은 직선은 32K에서 43.2 ms를 예측한다 [확인]. 직선 가정이 표본 밖에서 맞았다는 뜻이다.
- FP8 직선은 30 ms에 18.4K, 50 ms에 36.7K에서 닿는다.
- 따라서 1P1D만 가능한 범위(m = 1.5)는 30 ms에서 6.3–18.4K, 50 ms에서 14.1–36.7K다. 64K 문장과 30 ms 전역 KV 예외는 이로써 없어진다.

**(d) 불확실성** [모두 확인]

| 변동 | 50 ms | 30 ms |
|---|---|---|
| 기준 m 1.5 / m 1.8 / m 1 | 14.1K / 12.5K / 19.0K | 6.3K / 5.8K / 8.8K |
| 한 점 빼기, m 1.5 (m 1) | 11.1–22.9K (14.0–32.5K) | 4.2–11.3K (5.3–16.5K) |
| FP8 간격 9점 합동 적합, 공분산 95%, m 1.5 | 13.8K (11.1–17.0K) | 5.9K (4.4–8.1K) |
| 16K 표본 밖 오차 보정 / b×0.9, m 1.5 | 10.8K / 14.8K | 5.1K / 6.5K |
| 512토큰 이하 단계 비용 12 ms, m 1.5 (m 1) | 14.1K (26.9K) | 10.4K (13.8K) |

- 단계당 비용을 TTFT 차이로 구하면 2,560→1,024에서 18.5–19.0 ms, 1,024→512에서 11.3–12.0 ms다 [확인]. CUDA graph 캡처 상한 512 [R1]와 맞는다.
- 50 ms·m 1.5에서 교차가 쓰는 청크(약 650)는 보정한 청크 범위 안에 있다. 그래서 이 가정에 둔감하다.
- 결론: 50 ms 교차는 약 11–33K, 30 ms는 4–17K다. 부트스트랩 폭(18.6–19.1K)은 작으므로 [R2], 불확실성은 모델 식별에서 온다.

**(e) 핵심 메시지는 살아남는다. 다만 조건이 넷이다.**
- 기제는 측정과 맞는다. 4K TTFT는 157 → 194 → 239 ms로 단계 수와 함께 늘었다.
- 이득은 50 ms에서 작다 [확인, m 1.5]: 16K 8%, 20K 16%, 32K 28%(2.54 대 3.53 s).
- 두 한도를 함께 지키는 최장 입력(50 ms):
  - TTFT 1 s: 복제본 15.6K, 1P1D 16.2K
  - 3 s: 29.6K 대 36.5K
- 엄격 SLO(1 s, 50 ms)에서는 사실상 그런 구간이 없다. m 1에서는 없고, m 1.5에서는 차이가 오차 안이다. (1 s, 30 ms)에서는 11.5–16.2K다.
- 조건 넷: TTFT 한도 약 1 s 이상, 저부하, 작은 KV, 디코드 노드 간격의 한계.

**(f) 저부하·용량.**
- GPU당 프리필 용량(모델):
  - 50 ms에서는 모든 L에서 복제본이 1P1D 이상이다(16K 0.95 대 0.79, 32K 0.29 대 0.25). R1·R2가 옳다.
  - 30 ms에서는 8K부터 1P1D가 높다(16K 0.79 대 0.59) [확인]. 그러나 디코드 간격이 부하와 함께 커진다.
- 16K를 넘는 1P1D 측정은 하나뿐이다. g7 32K, GPU당 0.125에서 TTFT 9.3 s였고 복제본은 3.5 s였다. 이때 P 노드는 약 86% 가동이었다 [확인; 가동률은 산술 추정].
- 그러므로 6절은 지연 실현 가능성에 대한 절이고, 굿풋은 주장하지 않는다.

**(g) 나머지.**
- 220 KiB는 "슬라이딩 층이 모든 토큰을 보관할 때"의 크기이고, 전역 형상으로 계산하면 120 KiB다 [R3]. (c)를 넣으면 220 KiB에서는 두 패널 모두 창이 없다. 120 KiB의 50 ms 교차는 48K다 [확인].
- ×0.05는 191 Gbps다. 95 Gbps로 바꾸면 교차는 5.4K/2.8K다 [확인].
- g7 재적합 결과는 32K 간격 +7.1%, 32K TTFT −1.1%, 16K TTFT −7.4%다. b×0.85는 16K 보정점을 136.0 ms로 깨뜨리고(실측 150.2), b×0.9는 140.7 ms다. "seven"은 여섯이다 [확인].

## 3. A. 반드시 고칠 것

**A1. 교차와 수치를 바꾼다(L287–291).** L287 끝에 다음 문장을 더한다: "We call the shortest input beyond which the orange curve stays below the blue one the crossover length." 289–291행은 다음으로 바꾼다.
> \item At 4K the model is close to our measurements: the largest chunk for a 50~ms gap is about 1,600 tokens (TTFT 0.17~s; measured 1,024 tokens, 0.19~s) and for 30~ms about 560 (0.25~s; measured 512, 0.24~s); 1P1D needs 0.33~s at $m = 1.5$ (measured 0.36~s).
> \item At a 50~ms gap limit the crossover length is about 14K tokens, where both sides need about 0.85~s. Beyond it the admissible chunk shrinks (336 tokens at 32K) and 1P1D over TCP meets TTFT limits that replicas cannot (1.33 against 1.58~s at 20K, 2.5 against 3.5~s at 32K), until about 37K, where the decode node's own longest gap reaches 50~ms.
> \item At 30~ms the crossover length is about 6K (1.01 against 1.75~s at 16K), and 1P1D's advantage ends near 18K; beyond about 36K no chunk of 128 tokens or more fits.
> \item Under our strict SLO (1~s, 50~ms) the model predicts essentially no such region: replicas meet 1~s up to about 15.5K tokens and 1P1D up to about 16K. For a 3~s limit, the longest input is about 30K for replicas and 36K for 1P1D.

**A2. 디코드 노드 간격을 L247 뒤에 넣는다.** 코드도 함께 고친다(A11).
> On the 1P1D side the gap limit applies to the decode node, whose longest gap grew with input length while its median inter-token latency did not (p90 14.4~ms at 4K and 27.8~ms at 16K; median 7.8 and 8.0~ms). We model it as the line through these two points; on g7 the same construction for 26B NVFP4 predicted the 32K value (43.2 against 43.3~ms). We did not identify the cause.

**A3. m의 근거를 적는다(L247 끝).**
> We use $m = 1.5$, the low-load rate we measured for this checkpoint and the value checked in Table~\ref{tab:model}; Figure~\ref{fig:boundary} also shows $m = 1$, the rate at the loads that decided our verdicts, and $m = 1.8$, the low-load rate of transfers split four ways, as 26B transfers are above about 16K tokens.

**A4. 간격 한도와 불확실성을 고친다(L298 수정, L299 교체).**
> \textbf{Gap limit.} A tighter limit moves the crossover to shorter inputs (about 6K at 30~ms against 14K at 50~ms), but the decode node's gap ends 1P1D's advantage sooner (18K against 37K).

> \textbf{Model error and transfer rate.} The fit has four points for three parameters, and the crossover depends mostly on the per-step cost $d + e$ (16~ms). At 50~ms and $m = 1.5$, refitting without each point in turn moves it from 11K to 23K tokens; a joint fit to all nine gap points we measured for this checkpoint gives 14K (95\% range 11K--17K); correcting for the out-of-sample errors at 16K gives 11K; scaling $b$ by 0.9, which removes most of the 32K gap overestimate on g7, gives 15K. With $m = 1$ every value moves later, up to 33K. TTFT differences between chunks imply a per-step cost of 18--19~ms above 1,024 tokens but 11--12~ms below, consistent with CUDA graphs for steps of up to 512 tokens; this leaves the 50~ms crossover unchanged but moves the 30~ms one to about 10K. The model therefore places the crossover between roughly 11K and 33K tokens at 50~ms and 4K and 17K at 30~ms, not at a point.

**A5. KV 크기 문단을 교체한다(L296).**
> \textbf{KV size.} With the transfer volume of a KV cache whose sliding-window layers kept every token (220~KiB per token; 6.9~GiB at 32K against 840~MiB) and step times unchanged, 1P1D meets no TTFT limit that replicas miss at either gap limit (dash-dot); with global-layer shapes in every layer (120~KiB per token) the 50~ms crossover moves to about 48K, past the decode node's limit. Global attention would also lengthen the replicas' steps, which we did not model. A small KV cache relative to the link, here from hybrid attention, is what lets disaggregation over TCP take over.

**A6. 빠른 연결 문단을 고친다(L297, L325).**
> \textbf{Link speed.} With a transfer at 95~Gbps, ten times one TCP flow, the crossover moves to about 5.5K tokens at 50~ms and 3K at 30~ms (dotted), at first for TTFT limits of about 0.2~s; we kept the decode node's measured gap, which a faster link might change.

L325는 "a transfer ten times faster than one TCP flow moves the crossover to about 3--5.5K tokens; we did not measure EFA."로 바꾼다.

**A7. 저부하와 지표를 밝힌다(L236 끝에 추가, L300 교체).** L236 끝: "Unlike Section~\ref{sec:h2hsec}, the map asks which side can meet both limits at low load, not how much load each serves per GPU."
> \textbf{Load.} At equal GPU count the 1P1D prefill node does two GPUs' prefill: at a 50~ms gap limit its prefill capacity per GPU is below the replicas' at every length (0.79 against 0.95 requests/s per GPU at 16K, 0.25 against 0.29 at 32K); at 30~ms it is higher, but the decode node's gap grows with load (at 16K, 48\% of requests exceeded 30~ms at 0.25 requests/s per GPU). Our only 1P1D measurement beyond 16K (g7, 32K, 0.125 requests/s per GPU) had a median TTFT of 9.3~s against 3.5~s for replicas, with its prefill node about 85\% busy. At long inputs, low load means rates below those we measured; we modeled no queueing.

**A8. 표 3, g7 점검, 개수를 고친다.**
- 표 3 열 머리는 "longest gap (p90)"으로 바꾼다. g7e 점검 행에는 오차(%)를 붙인다.
- 다음 행을 추가한다: "1P1D decode node, 4K / 16K: longest gap 14.4 / 27.8 — sets line".
- g7 블록은 아래와 같이 바꾼다.
  - 4K 간격 131.2/131.2 (fit), 4K TTFT 278/278 (sets $o$)
  - 16K 간격 254.5/254.5 (fit), 16K TTFT 1,430/1,324 (check, −7.4%)
  - 32K 간격 375.7/402.5 (+7.1%), 32K TTFT 3,507/3,470 (−1.1%)
  - 1P1D 디코드 노드 32K 간격 43.3/43.2. 앞의 둘과 함께 extrapolation check로 표시한다.
- 캡션에 추가: "The 28~ms residual and $m = 1.5$ come from session E4's 4K placement-group run, so that check repeats its configuration. The g7 rows refit a two-parameter version (a per-chunk cost proportional to the chunk size, and $b$) exactly to the 4K and 16K gaps."
- L249와 L343: "seven" → "six measurements on g7e (and four on g7)". L343 끝에는 "…and it locates the crossover only to within a factor of about two"를 붙인다.
- L277은 다음으로 바꾼다.
> Beyond 16K we have only 26B NVFP4 runs on the slower g7 GPU at a 2,560-token chunk (session B). A two-parameter version of the model, solved on the 4K and 16K gaps, predicted the 16K and 32K TTFTs within 8\% and 1\% and overestimated the 32K gap by 7\% (Table~\ref{tab:model}). This tests the attention term to 32K, not the per-step cost that decides the crossover. At 16K the model underestimated the replicas' TTFT on both GPUs; we do not know why.

**A9. 연결 문장을 맞춘다.** 초록(L32), RQ3 답, 결론(L354)은 6절 문안으로 바꾼다.
- L51 RQ3: "Our model predicts that at low load chunking runs out for long inputs, from roughly 15K tokens at a 50~ms gap limit for 26B FP8 (10K--30K within its uncertainty), where disaggregation over TCP can meet TTFT limits of a second or more that no chunk meets, given a small KV cache (RQ3)."
- L57: "locates where" → "estimates, with its uncertainty, where".
- L320: "…only where no admissible chunk meets both limits (in our model, 26B FP8 on g7e at a 50~ms gap: inputs beyond roughly 15K tokens, TTFT limits of a second or more, low load) and the transfer fits".
- L354 "plan on about one flow's rate" 뒤: "under load (long transfers reached 1.5--1.8 flows at low load)".

**A10. 그림 7을 다시 그린다(`fig_boundary`).**
- 패널 제목: "(a) Model, gap limit 50 ms", "(b) Model, gap limit 30 ms". x축 2K–48K, y축에 0.125 눈금을 더한다.
- 계열:
  - 파랑 실선: 복제본
  - 주황 실선: 1P1D m 1.5. 그 둘레에 m 1–1.8 띠를 옅게 칠한다.
  - 주황 점선: 95 Gbps
  - 가는 주황 쇄선과 끝 라벨: 220 KiB. 갈색 긴 대시는 그림 5에서 P 청크 8,192를 뜻하므로 쓰지 않는다.
- 디코드 간격 직선이 한도를 넘는 L부터는 1P1D 곡선을 회색 점선으로 바꾸고 "decode gap > limit"라고 표시한다.
- 음영은 m 1.5 곡선이 복제본 아래이고 그 한도 이하인 구간에만 칠한다(`interpolate=True`). 회색 영역의 라벨은 "Neither replicas nor 1P1D over TCP"로 한다.
- 1 s와 3 s에 가로 기준선을 긋는다.
- 4K 실측값을 속 빈 표식으로 찍는다: (a) 1,024토큰 0.194 s, (b) 512토큰 0.239 s, 1P1D 0.362 s.
- 4K와 16K에 보정 눈금을 두고, 16K에는 가는 실선을, 외삽 구간에는 옅은 빗금을 넣는다.
- 범례의 "(as measured)"는 "(this checkpoint's KV, m = 1.5; band m = 1–1.8)"로 바꾼다.
- 색은 파랑/주황 두 계열만 쓰고 선 모양과 명도로 한 번 더 구분한다.
- 캡션(L283)은 이 구성대로 고쳐 쓰고, 8K 꺾임이 P 노드의 두 번째 단계 때문이라고 적는다.
- `figures.json` 메타에 패널별 교차 L·TTFT, 끝 L, m을 저장한다.

**A11. `boundary_model.py`를 고치고 공개 패키지를 정리한다.**
1. 상수: `MBIT_PER_MIB`(리터럴 네 곳 대체), `M_MAP = 1.5`, `M_BAND = (1.0, 1.8)`, `FAST_GBPS = 95.4`. `GBPS_PER_MIBS`는 지운다.
2. d와 d7은 보정 런의 `itl_p50_ms` 평균으로 계산한다. docstring의 "≥10% overlapped"는 런 네 개의 이름으로 바꾸고, 사용법은 `uv run --with numpy`로 고친다.
3. `dgap_pd(L)`를 추가한다. E2 P1tuned 4K(rate 0.5)와 16K(rate 0.25)의 `longest_gap_ms`를 잇는 직선이다. 세션 B P1의 직선으로 32K를 예측하는 점검도 출력한다.
4. g7 재적합은 반복 안에서 `step7`로 최장 청크를 고르고 `[k/2560, k*(p+k/2)]`로 푼다. 16K TTFT 행을 추가한다.
5. 지도의 `par["d"] <= G`를 `dgap_pd(L) <= G`로 바꾼다.
6. `first_pd_only`와 T 격자는 지운다. 대신 다음 두 함수를 둔다.
   - `crossover(G, m, kv, xfer_gbps, bscale, R, rep_scale, pd_scale, d_small)`: L을 2,048–49,152에서 64 간격으로 훑어, 안정 교차 L, 그 L의 양쪽 TTFT, 끝 L을 낸다.
   - `longest_L(G, T)`: T = 1, 1.5, 2, 3 s에서 가능한 최장 L을 낸다.
7. 민감도: m 1·1.5·1.8, 한 점 빼기 4회, 9점 합동 적합(점 목록, 선형화 공분산, 시드 고정 400회 추출의 2.5·50·97.5%), 16K 오차 보정, b×0.9, 잔여 87 ms, `d_small = 12`(c ≤ 512), 95 Gbps, KV 220·120 KiB. 결과는 출력하고 JSON `crossover`에 저장한다. 곡선과 GPU당 용량(8K–32K)도 함께 저장한다.
8. README를 v4로 갱신한다. 실행 순서와 "four rounds"를 반영하고, 공개 전에 RESULTS.md의 AWS 계정 ID를 지운다(차단 항목).

**A12. 문장을 정확하게 고친다.**
- L98: "FP8 (weight-only)" → "FP8 (weights and activations, with dynamic activation scales)" [R3].
- L231: "rejected chunks below 2,496 tokens, one video item's budget, in both configurations we tested that kept video input enabled; we did not test settings that lower that budget, or whether image or audio input alone forces it."
- L319 KV 적재:
  > If KV caches are reused across nodes, loading a full prompt's cache moves at least $V(L)$ (only the matched prefix on a partial hit) if the store keeps the hybrid layout, which we did not check, and runs at $m \le 1$ over one connection. For 26B NVFP4 at 4K, NIXL's split pull moved 140~MiB in about 84~ms, against a colocated TTFT of about 130~ms of which prefill is only part; longer prompts favor loading.
- L69: "of the same size" → "of at least the same size".
- L176: "1~s budget" → "1~s TTFT limit".

## 4. B. 고치면 좋은 것

- **분량.** R5의 절감안 중 1번(8절과 그림 8을 부록으로 옮기고 두 문장만 남김), 2번 일부(L95·L107·L113·L120), 3번(7.1절 삭제, RQ 답은 각 절 끝으로), 4번(L158 NIXL 산술을 부록 C로)을 받는다. 약 1,050단어가 줄어 A의 추가분을 넣어도 본문은 약 7,500단어가 된다. L58의 "four pitfalls"도 고친다.
- **용어.** "crossover length", "longest gap"(관측), "step time"(모델), "tuned chunk", "largest admissible chunk"로 통일한다. 분리만 가능한 구간에는 "window"를 쓰지 않는다(R5).
- 2,048 이상치는 모델과 맞는다(52.6 ms) [R1]. 긴 입력에서 P 노드가 포화해도 KV 유량은 한 흐름보다 작다(16K 6.9 Gbps) [R3, 확인]. 층별 겹침 전송과 위치 적응 청크는 향후 과제로 적는다.
- L301의 "48 against 63 ms"는 통계 종류를 맞추고, L321의 "idle 70%"는 "SM active 30%"로 바꾼다. 버전 고정, 결정적 그림, draft.md·ko 동기화, 부록 D의 사후 분석 표기도 한다(R4).

## 5. C. 받아들이지 않는 것

- **초록 범위로 R1의 "15–30K", R3의 "15–25K", R5의 "above 1.5 s"를 쓰는 안.** 정의, m, 디코드 간격을 고친 뒤 다시 계산한 값으로 대체한다.
- **R1의 "오차 8% 초과 지점"(22K)을 경계 정의로 쓰는 안.** 정의는 교차 하나로 두고, 오차는 범위로 보고한다.
- **R3의 m = 1.8을 기준으로 쓰는 안.** 31B와 배치 그룹 밖 런에서 온 값이므로 띠의 끝으로만 쓴다.
- **R2의 D = 11.25 ms를 기준으로 쓰는 안.** TTFT 차이는 청크에 따라 11–19 ms로 달라지므로 청크 의존 민감도로 다룬다.
- **R4의 "16K 너머만 b를 줄이는 변형".** b×0.9 민감도로 충분하다.
- **R3의 "EFA 100 Gbps, GDR 없음"을 본문에 넣는 안**은 미검증이다. **R2의 "GPU당 0.03 req/s"**는 특정 T에 대한 어림이고, **R1의 MoE 가중치 읽기 해석**도 미검증이다. 셋 다 넣지 않는다.
- **제목 변경.** 측정과 예측 모두 "when"에 답하므로 그대로 둔다.

## 6. 초록 최종안, RQ3 답, 결론 핵심 문장

**초록**(210단어, `wc -w`, `r6/abstract_v5.txt`. LaTeX 표기는 ×, ~, --로 바꾼다)
> Prefill–decode disaggregation usually relies on RDMA or NVLink, which cheap single-GPU instances lack. For a TCP-linked fleet of such instances, we ask whether disaggregation is worth considering once chunked prefill, which attacks the same decode stalls, is tuned, and if so, where. Serving Gemma 4 26B and 31B with stock vLLM and NIXL/UCX on AWS, we measured both costs: a replica's longest inter-token gap followed the chunk size (26B, 4K inputs: 48 ms at 2,560 tokens, 21 ms at 512), and disaggregation's added time to first token (TTFT) was mostly KV transfer, which a larger UCX segment made 3.4× faster at low load. At 4K inputs and in chat, against tuned chunks, disaggregation served more per GPU under none of the latency targets our measured rates could rank; it won, by about 3× for 26B, only against replicas held at 2,560 tokens, near vLLM v0.30.0's floor for Gemma 4 with video enabled. A step-time model calibrated on our runs predicts that at low load and a 50 ms gap limit, inputs of roughly 15K–35K tokens (lower edge 10K–30K within its uncertainty) need so many chunks that disaggregation over TCP meets TTFT limits of a second or more that no chunk meets, given a small KV cache. Tune the chunk first.

**RQ3 답**(6절 끝)
> Input length, through the step count. A gap limit caps the chunk, the cap shrinks as the prefix grows, and each extra step costs 11--19~ms. For 26B FP8 on g7e at low load, the model predicts that 1P1D over TCP meets TTFT limits that no admissible chunk meets from about 14K tokens at a 50~ms gap limit (11K--33K within its uncertainty) and about 6K at 30~ms (4K--17K), until the decode node's own longest gap reaches the limit, near 37K and 18K. The advantage is modest at 50~ms (2.5 against 3.5~s at 32K), needs TTFT limits of about a second or more, and concerns latency at low load, not goodput per GPU. It needs a small KV cache: with the volume of a cache whose sliding-window layers kept every token, it disappears. These are predictions calibrated at 4K and 16K, not measurements.

**결론 핵심 문장**(L354의 "For long inputs … hybrid attention." 교체)
> For long inputs, a gap limit forces chunks so small that the step count dominates TTFT, and our calibrated model predicts that at low load disaggregation over TCP then meets TTFT limits of a second or more that chunked prefill cannot, from roughly 15K tokens at a 50~ms gap limit (10K--30K within the model's uncertainty) until the decode node's own gap reaches the limit, provided the KV cache is small, as with hybrid attention.

## 7. 리뷰어 간 불일치와 판단

1. **m의 기준.** R1은 1, R3는 1.8을 제안했고, R2와 R4는 근거를 요구했다. 기준은 1.5로 하고 1–1.8은 띠로 보인다(2절 (b)).
2. **교차 값.** R1 18.7K, R2·R4 18.5K, 본문 21K는 정의 차이일 뿐이다. R3의 "m 1.8이면 14K"는 격자 값이고, 연속으로 풀면 12.5K다.
3. **9점 적합 띠.** R2는 16.3–24.3K, 종합 심사자(m 1)는 14.6–21.5K다. 점 구성이 달라서 생긴 차이다. 범위의 끝은 한 점 빼기 결과가 정한다.
4. **"복제본 용량이 모든 L에서 이상"(R1·R2).** 50 ms에서만 맞는다. 굿풋을 주장하지 말라는 결론은 같다.
5. **30 ms 전역 KV(R4·R5).** 디코드 간격 직선을 넣으면 30 ms에서도 창이 없다. 그 이유를 문장으로 밝힌다.
6. **b 배율과 빠른 연결 배율.** b는 R4가 옳으므로 0.9를 쓴다. "×0.1 = ×0.05"(R3)는 격자의 산물이고, 연속으로 풀면 5.4K 대 4.5K다.
7. **세부.** 엄격 SLO 30 ms 띠는 R5가 12–14K(격자), 종합 심사자가 11.5–16.2K(m 1.5)다. R2의 4K p90 14.4 ms는 GPU당 0.125가 아니라 0.25에서 잰 값이다.
8. **점수(3.5–4.0).** 판정은 낮은 점수를 준 쪽의 이유를 따른다. 측정은 공개 수준이고, 6절 수치는 지금 형태로는 공개할 수 없다.
