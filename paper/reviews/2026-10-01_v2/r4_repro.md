# Reviewer 4 (3차) — 재현성·아티팩트 평가 (pd-without-rdma, paper/en/main.tex v2)

대상은 `paper/en/main.tex` v2(커밋 298be40, 25쪽)와 `main.pdf`다. main.pdf의 본문은 tex와 일치했다(pdftotext로 핵심 문구 대조).
저장소는 읽기만 했다. 감사 전후로 `git status`가 같다. `results/per_request.json.gz`의 미커밋 수정(10/1 01:03)은 저자 쪽 것이고, 이번 감사가 만든 변경이 아니다.

재생성 산출물은 모두 `reviews_v2/r4/` 아래에 있다.
- `work/`: harness 사본과 세션 폴더 심볼릭 링크. 캐시(`work/results/per_request.json.gz`)는 여기에 새로 만들었다.
- `work/all_runs.csv`, `work/safe_runs.csv`
- `figs_v2/`: `make_figures_v2.py -o` 출력
- `decisive_ci.txt`, `decisive_ci_tex.txt`: 부록 F 재계산
- `summary_E9_regen.md`: `e8_summary.py results/E9 E9` 출력
- `work_headcache/`, `decisive_ci_headcache.txt`: 커밋된 캐시로 돌린 대조 실험
- `chk_*.py`: 이번 감사의 대조 스크립트 8개(표 2, 상한, 31B 구간, 반복 변동, TTFT 범위, SLO 지도, 기타)
- `committed/`: HEAD의 CSV·figures.json·캐시·summary_E9.md 사본, 예측 문단 비교본

## 0. 요약

- **원장.** 수치 주장 158개를 대조했다(전체 원장은 7절). 범위는 초록, 1~5절, 표 1·2·F1·G1, 그림 캡션, 부록이다.
  - 결과: ✅ 126, ⚠️ 26, ❌ 4, ❓ 2다.
  - ✅ 126에는 외부 인용 세 건(EFA 가격, AWS 규격, 8xlarge vCPU)의 ✅(외부)가 들어 있다. 모델 파라미터 수는 ❓(외부)다.
- **E9 수치는 모두 원자료와 맞는다.** 대조한 수치는 다음과 같다.
  - 청크 512의 21.4 ms, TTFT 205 ms, FP8 26.8 ms
  - 상한을 푼 청크 1,024: GPU당 4에서 1.000 ×3, 5에서 0.999/1.000, 6에서 0.19
  - 청크 512: GPU당 1~4 통과, 4에서 0.985
  - P 청크 8,192: 0.874/0.976, 0.365, TTFT 416–451 ms
  - 31B: 청크 256이 GPU당 8에서 1.000(117 ms, $0.67), 1P1D가 4에서 1.000, 6에서 0.765
  - 30 ms 판정점: 청크 512는 GPU당 3 통과(4에서 0.839), 1P1D는 2 통과(3에서 0.66–0.77), FP8 청크 512는 0.958
  - 부록 F 14행
- **표 2 비용 일곱 개가 모두 맞는다.** $2.00/$0.38/$0.63/$1.87/$1.89/$0.67/$1.67다(2.003/0.381/0.631/1.872·1.873/1.885/0.668/1.674). TTFT 132/259–278/366/117/304 ms도 맞는다. 다만 1P1D 열은 aiohttp 프록시 런만으로 계산했다(⚠️ #90).
- **개수가 모두 맞는다.** 455/313/14/128/122/5/1/9와 그림 1의 215/212/3/28/21/7이다.
  - 분리 7개 중 2개가 주의 런이다(⚠️ #57).
  - 상한에 닿은 E9 이전 복제본 런은 실제로 11개다. 2개는 이미 클라이언트 한계로 주의였다(⚠️ #35).
- **파이프라인이 그대로 재생성된다.** 스크래치에서 아래 순서로 돌렸다.
  1. `aggregate.py --slo …`
  2. `safe_runs.py`
  3. `make_figures_v2.py -o` (캐시를 새로 만듦)
  4. `decisive_ci.py --tex`
  5. `e8_summary.py results/E9 E9`

  결과는 다음과 같다.
  - all_runs.csv, safe_runs.csv, figures_v2/figures.json이 커밋본과 **바이트 단위로 같다**.
  - SVG 17개는 난수 ID와 날짜를 빼면 모두 같다.
  - 부록 F 표와 summary_E9.md도 그대로 나온다.
- **새로 찾은 문제**
  - **❌ 네 건**
    - #22: P 청크 8,192 런이 UCX 세그먼트 두 변수만 썼는데 밝히지 않았다.
    - #28: 대화 전송량 "28–30 MB"가 실제로는 25–26 MiB다.
    - #87: "둘 다 통과한 부하" TTFT 범위 "79–359 대 260–526 ms"가 실제로는 78–247 대 255–384 ms다.
    - #153: E9 예측이 "넷 적중"이라고 했지만, 온전히 맞은 것은 셋이다.
  - **[필수] 새 재현 함정이 있다.** 커밋된 `results/per_request.json.gz`는 v1 시점 캐시다(308런, E9 없음, 새 주의 런 9개가 '안전'). 깨끗한 클론에서는 다음 일이 생긴다.
    - `decisive_ci.py`가 14행 중 6행만 **말없이** 출력한다.
    - `make_figures_v2.py`는 `ValueError: cannot convert float NaN to integer`로 죽는다.
  - **[필수] 사전 등록 해시가 바뀐다.** 계정 ID 이력 정리가 사전 등록 해시 8775497을 바꾼다. 계정 ID가 든 커밋 e03d4de가 8775497의 조상이기 때문이다.
- **2차 지적 반영.**
  - ❌ 네 건 중 세 건은 해결됐다. 나머지 하나(E1b/E1c 16,384 문맥)는 ⚠️로 남았다.
  - 필수 P1(1토큰 규칙 공개)과 P2(m 범위)는 해결됐다. P3(판정 스크립트의 harness 이전)은 부트스트랩만 해결됐다.
  - 권장 항목 중 9건이 그대로 남았다: 약 3배, 283 ms·상수, 워밍업, 0.03, 빗금 캡션, 전역 정지 규모, "none", FP8 캡션, 출력 24토큰. 그림 1의 주의 런 표기는 일부만 반영됐다.
  - 패키징 필수 항목(457 MB 파일, 계정 ID, README, 기본 SLO 함정, 버전 고정)은 **하나도 바뀌지 않았다**.

## 1. ❌ 항목과 수정 문구

1. **[필수] #22 (#82와 연결) 3.1절 "Unless stated otherwise, disaggregated runs used seven UCX environment variables", 부록 C "The tuned set used in sessions E4–E9"**
   - E9의 P 청크 8,192 세 런은 UCX 두 변수만 썼다(TX/RX 세그먼트 256k).
     - 근거 1: `configs/run_E9.sh` 5단계의 `UCXSET=SEG`
     - 근거 2: `results/E9/run_E9.log`의 "proxy=aio ucx=SEG pchunk=8192"
   - 비교 대상인 E8 aiohttp 1P1D는 7변수 묶음이다. 따라서 4.3절 "Raising the prefill chunk to 8,192 tokens cut 1P1D's median TTFT … from about 500 to 416–451 ms"는 두 변수를 함께 바꾼 결과다.
   - 이 런들의 전송은 오히려 느렸다. GPU당 4에서 전송 평균은 165–190 ms, m은 0.68/0.81이다. P 2,560 aiohttp 런은 119–140 ms, m 0.92–1.04였다. TTFT가 준 원인은 전송이 아니라 프리필 대기열로 보인다.
   - 수정 문구
     - 3.1절: "… seven UCX environment variables …, except the three E9 runs with an 8,192-token prefill chunk, which set only the two segment sizes"
     - 4.3절: "Raising the prefill chunk to 8,192 tokens (with only the two segment-size UCX variables) cut …"
     - 부록 C: "used in sessions E4–E9 except the 8,192-token prefill-chunk runs"
     - 그림 3 범례: "1P1D, aiohttp, prefill chunk 8,192, segment-only UCX"
2. **[필수] #28 3.2절 "chat requests of a few hundred tokens moved 28–30 MB, as the formula predicts"**
   - 26B NVFP4 대화 1P1D 런의 vLLM 로그를 봤다(E5·E7, 7개 파일).
     - 10초 창 중앙값: 24.4–27.0 MiB
     - 전송 가중 평균: 25.1–26.0 MiB
   - 같은 런의 요청별 입력 길이(중앙값 93–112, 평균 226–235 토큰)로 식 (1)을 계산하면 평균 24.2–25.2 MiB다.
   - 식은 맞고 수치만 틀렸다. 28–30은 창 최댓값 근처다.
   - 수정 문구: "chat requests (median input about 100 tokens, mean about 230) moved 25–26 MiB on average, close to the 24–25 MiB that Eq. (1) gives for their input lengths."
3. **[필수] #87 4.3절 "At every load where both passed, tuned replicas reached the first token sooner (medians of 79–359 ms …, against 260–526 ms for 1P1D)"**
   - 359(청크 512)와 526(aiohttp)은 26B GPU당 4의 값이다. 이 부하에서 1P1D는 통과하지 못했다(0.885, 0.767 포함).
   - 둘 다 통과한 부하만 모으면 복제본은 78–247 ms, 1P1D는 255–384 ms다(런별 TTFT 중앙값, `chk_ttft_range.py`).
     - 복제본 최소: 31B 청크 256 GPU당 1, 78 ms
     - 복제본 최대: FP8 청크 512 GPU당 1, 247 ms
     - 1P1D 최소: 31B 시험 프록시 GPU당 2, 255 ms
     - 1P1D 최대: FP8 GPU당 1, 384 ms
   - 방향(복제본이 항상 빠름)은 모든 부하에서 맞다.
   - 수정 문구: "At every load where both passed, tuned replicas reached the first token sooner (median TTFT 78–247 ms against 255–384 ms for 1P1D); at 4 requests/s per GPU for 26B, where 1P1D was borderline, 200–359 against 416–527 ms."
4. **[필수] #153 부록 D "four of five held, and the fifth … did not"**
   - 커밋 8775497의 예측 4는 세 부분이다: 31B 청크 256 GPU당 8 통과, 1P1D GPU당 6 실패, **GPU당 4(시드 10000)는 경계(0.85~0.95)**.
   - 셋째가 빗나갔다. 측정값은 1.000이다(E9 `31_1P1D_aio sharegpt r8` n2). RESULTS.md 결과표도 이 칸에 ✅를 달지 않았다.
   - 예측 1의 "50 ms 지원 부하 GPU당 3~4"는 GPU당 5를 재지 않았으므로 확인되지 않았다(≥4).
   - 예측 문단은 커밋 뒤로 바뀌지 않았다(빈 줄 하나만 다름). run_E9.sh, lib_E9.sh, rr_proxy.py도 커밋 뒤 그대로다.
   - 수정 문구: "Session E9's predictions were committed before the session (commit 8775497). Three held in full. In the fourth, the verdicts held (31B replicas passed 8 requests/s per GPU and 1P1D failed at 6), but the seed-10000 1P1D run at 4 reached 1.000 rather than the predicted 0.85–0.95. The fifth (1P1D with an 8,192-token prefill chunk passing 4 requests/s per GPU) did not hold (0.874 and 0.976). The 512-token replicas' supported load (predicted 3–4) was not tested above 4."

## 2. ⚠️ 항목

### [필수]

- **P1. 사전 등록 해시와 이력 정리 (#154, #12)**
  - 계정 ID를 이력에서 지우는 일은 2차부터 필수 항목이다. 계정 ID가 든 커밋 e03d4de는 8775497의 조상이다. 따라서 filter-repo 같은 이력 재작성은 논문이 인용한 해시를 바꾼다.
  - 방법은 둘이다.
    - (a) 이력을 다시 쓰고 부록 D의 해시를 새 값으로 고친다. `e9-predictions` 태그를 단다.
    - (b) 공개 저장소를 새 이력으로 만든다. 이때는 원 커밋을 Zenodo 아카이브에 번들(`git bundle`)로 싣고 해시를 대조할 수 있게 한다.
  - 문구도 고친다[권장]. 저장소에 원격이 없어서(`git remote -v` 빈 값) 커밋 시각은 자기 기록이다.
    - 부록 D: "committed to our local repository at 13:30 UTC, 50 minutes before the first E9 run (the repository was not public at the time)"
    - 4.6절 "so the repository cannot prove their order"는 "so the repository does not record their order"로 누그러뜨린다. 로컬 커밋도 순서를 증명하지는 못한다.
- **P2. 31B 프롬프트 길이 구간 스크립트 (#67, #69; 2차 P3의 잔여)**
  - `harness/decisive_ci.py`로 부트스트랩 구간은 재현된다(부록 F 14행 일치).
  - 4.2절의 구간 수치는 여전히 harness에 스크립트가 없다.
  - 런 선택에 따라 값도 다르다. 캡션대로 E5·E7·E8의 2,560 런 5개를 쓰면 200–400토큰 구간이 0.415(142건)다. E5·E7 4런만 쓰면 0.434로, 논문의 43%와 맞는다(1차 심사 스크립트 `r6_check31.py`가 `31_B2`만 골랐다).
  - `reviews_v2/r4/chk_31b.py`를 `harness/coscheduled_prompt.py`로 옮기고 런 집합을 적는다.
- **P3. 커밋된 캐시와 재생성 함정.** 5절 1번에서 다룬다.

### [권장]

- **#3, #13, #141: "about 3× more requests per GPU than replicas held at 2,560 tokens"(초록, 1절, RQ3)**
  - 배수는 26B 4K에서만 정의된다(3 대 1). FP8과 31B는 2,560 복제본이 어떤 부하도 지키지 못했다.
  - 2차 권장이 그대로 남았다.
  - 문안: "for 26B with 4K inputs about 3× (3 against 1 request/s per GPU), and for 26B FP8 and 31B chat only disaggregation met the limit"
- **#20: 표 1의 g7 "Used for"**
  - g7은 대역폭 제한(그림 A1)과 GPU 비교(그림 A9, g7 막대는 세션 B)에도 쓰였다.
  - "input-length comparison, first transfer tuning, bandwidth limit, cross-GPU comparison"으로 고친다.
- **#23: 3.1절 "a 32,768-token context"**
  - E1b/E1c의 31B FP8 런(`l40s_31b_fp8_len16k`, `pro6000_31b_fp8_len16k_*`)은 max-model-len 16,384다.
  - "(16,384 for the 31B FP8 cross-GPU runs)"를 더한다. 2차 ❌ #21의 잔여다.
- **#35, #147, #48: "Nine replica runs before E9 reached the cap"**
  - `safe_runs.max_inflight`로 E9 이전 복제본 런을 모두 세면 상한 도달은 **11런**이다.
  - 나머지 2런은 E5 대화 GPU당 16의 `26_B2 r32`(최대 진행 중 140)와 `26_B3 r48`(1,680)이다. 이미 '클라이언트 한계'로 주의 처리돼 있다.
  - 좌장(e)도 이 둘의 사유를 연결 상한으로 바꾸라고 했다.
  - 문안: "Eleven replica runs before E9 reached the cap; two were already caution data at the client's limit, and we mark the other nine as caution"
  - 3.6절: "5 in which the client-side proxy reached its CPU limit (two of them replica runs that also reached the connection cap)"
- **#39: ShareGPT 출력 중앙값 "59–177"**
  - 감사 런 89개 중 E1 31B FP8 KV 맞춤 @12가 24토큰이다. "24–177"로 고치거나 예외를 적는다. 2차 권장이 그대로 남았다.
- **#50: 워밍업 "changed attainment by at most 0.019"**
  - E7 이전 감사 런 165개를 봤다. 첫 다섯 요청을 빼면 최대 +0.019, 최대 −0.029(B P1 tc1gbit)다. 판정이 뒤집힌 런은 없다.
  - 문안: "raised attainment by at most 0.019, lowered it by at most 0.029, and flipped no verdict"
- **#52: "Points well above 0.9 varied by at most 0.03"**
  - 세션 안 반복만 보면 최대 0.026이다.
  - 그림 3은 GPU당 3의 E7 시험 프록시(1.000)와 E8 계측 사본(0.956)을 반복으로 묶는다. 차이는 0.044다.
  - "within a session"을 붙인다.
- **#57: 그림 1 캡션**
  - 음영 안 분리 7런 중 2런이 주의 런이다. E5 1P1D 대화 GPU당 16(0.868)과 1P2D GPU당 16(0.772)이고, 둘 다 클라이언트 한계다.
  - "7 disaggregated runs (2 of them caution)"으로 쓴다.
- **#67: "43% with 200–400"** → 캡션의 런 집합(5런)이면 "42%"다. 또는 "E5 and E7"로 집합을 좁힌다(P2).
- **#69: "none above 800"** → 5런 합산 1/323(0.3%)이다. "almost none"으로 쓴다.
- **#72: 그림 2 캡션 "The 2,560-token points pool the repeats of sessions E5, E7, and E8"**
  - (b) FP8은 E7 한 런이다. "(a) and (c)"로 한정한다.
- **#82: P 청크 8,192 귀속** → ❌ 1번에서 고친다.
- **#86, #92: 31B 대화 1P1D "passed 4"와 표 2의 "4"**
  - aiohttp 세 런(0.903, 0.924, 1.000)은 통과한다.
  - 같은 부하의 시험 프록시 네 런에 0.885가 있다. 시험 프록시로는 규칙상 탈락이다.
  - 표 2의 26B 행은 "(borderline at 4)"라고 적었다. 31B 행도 같은 기준으로 "4 (borderline)"로 쓴다.
  - 본문: "passed 4 with our aiohttp proxy (…) and was borderline with the test proxy (0.885–0.963)"
- **#90: 표 2 1P1D 열**
  - $0.63과 366 ms는 GPU당 3의 aiohttp 한 런 값이다.
  - "minimum over repeats"를 GPU당 3의 세 런(E7 시험 프록시 1.000, E8 계측 사본 0.956, E8 aiohttp 1.000)에 모두 적용하면 $0.66, 366–374 ms다. 31B의 $1.67과 304 ms도 aiohttp 세 런 값이다.
  - 열 머리를 "1P1D (aiohttp proxy)"로 적는다.
- **#102: 그림 4 캡션 "Hatched: both sides still passed at their highest measured rate"**
  - `classify()`는 한쪽만 censored여도 비율이 구간을 못 벗어나면 빗금이다.
  - 한쪽만 censored인 빗금 칸 수는 다음과 같다. 26B NVFP4 위 행 27칸·아래 행 9칸, 31B 위 행 7칸이다(`chk_who.py`).
  - 2차 #96 권장이 그대로 남았다.
  - 문안: "Hatched: a side still passed at its highest measured rate, so the ratio cannot be resolved"
- **#115: "31B chat transfers … reached 0.81"**
  - E8 두 런(0.82/0.81)만의 값이다.
  - 같은 부하의 다른 런: E9 0.78, E7 0.78–0.82, E5 0.85다.
  - "were at 0.78–0.85"로 쓴다.
- **#121: 그림 5와 4.6절의 31B 전송 283 ms**
  - 283 ms는 10초 창 평균들의 단순 평균이다(E5 `31_1P1D_random_r0.25`: 283.1). 전송 수로 가중하면 297.6 ms다.
  - 가중 평균을 쓰면 전송 몫은 80%, 잔차는 72 ms다.
  - `fig_ttft`의 값은 여전히 상수다(FP8 행 165 ms는 1차에서 168–170 ms로 재계산됐다).
  - 캡션에 정의를 적고, 계산 코드로 바꾼다. 2차 #115·#123이 그대로 남았다.
- **#125: 4.7절 "one to five times per run, 40–110 in-flight requests paused together for 55–80 ms"**
  - 한계 근처(26B GPU당 3–4, 31B 대화 GPU당 4) 분리 런의 전역 정지를 셌다.
    - 횟수: 런당 0–5회
    - 크기: 16–113요청(대개 35–110)
    - 이벤트별 중앙 간격: 50–79 ms
  - 문안: "zero to five times per run, 15–115 in-flight requests (typically 35–110) paused together for 50–80 ms"
  - 2차 권장이 그대로 남았다.
- **#146: 한계 절 "Decisive points have one to three runs"** → 표 F1에 4런 점이 네 개 있다. "one to four"로 고친다.
- **#150: 그림 A3**
  - ShareGPT BF16 복제본 막대(0.389)는 상한에 닿은 주의 런이다(E7 `26H_B2 sharegpt r16`).
  - 실패 대부분은 간격 때문이다(2,880요청 중 1,744). 상한 아래에서 도착한 요청만 보면 0.41이라 결론은 같다.
  - 캡션에 "the BF16 chat replica point reached the proxy cap"을 적거나 빈 표식으로 그린다.
- **#156: 표 F1 행 라벨 "26B 4K, 1P1D test proxy (E5–E8)" (GPU당 4)** → 실제 출처는 E7 1런과 E8 3런이다. "(E7, E8)"로 고친다.
- **RESULTS.md E9 절(논문 밖)**
  - 결과표 FP8 행과 '해석'의 "30 ms … 0.5·1 모두 1.000", "FP8은 GPU당 1건까지 30 ms 1.000"은 틀렸다. GPU당 1은 30 ms에서 0.958이다(논문과 표 F1은 맞다).
  - 예측 4의 시드 10000 칸에 ✗를 단다.
  - E8 절의 "청크 1024 복제본의 지원 부하 GPU당 4건", "청크 256이면 GPU당 6건"에는 해당 런이 지금 주의 데이터라는 주석을 붙인다.

## 3. ❓ 항목

- **#25: Gemma 4 파라미터 수(3.8B/25.2B, 30.7B).** 모델 카드 수치라 저장소 밖이다. 참고문헌 `gemma4`가 모델 카드인지 확인한다.
- **#148: 감사의 글 "about $270"**
  - RESULTS.md의 세션별 추정을 더하면 $267다(E9 절 "누적 약 $267").
  - P·A′·E1·E2는 비용 기록이 없고, 결제 원장도 없다. 2차 ❓가 그대로 남았다.
- **런 매니페스트.** CSV의 `instance_type`과 `vllm` 열은 세션 B에만 채워져 있다. 제외되지 않은 D~E9 303개 행은 모두 비었다. 인스턴스와 설정(UCX 묶음, P 청크, 프록시, util, max-model-len)은 RESULTS.md 서술과 configs로만 확인된다. ❌ 1번의 UCX 혼입도 매니페스트가 있었다면 CSV에서 보였을 것이다.

## 4. 재현성

### 4.1 재생성 결과

| 단계 | 명령(스크래치 `work/`에서) | 결과 |
|---|---|---|
| 집계 | `python3 harness/aggregate.py results/ -o all_runs.csv --slo chat=ttft:1000,tbt:50 --slo doc=ttft:3000,tbt:250` (100 s) | 455런, 커밋본과 **바이트 동일** |
| 분류 | `python3 harness/safe_runs.py all_runs.csv -o safe_runs.csv` | 안전 313, 주의 14, 제외 128. **바이트 동일** |
| 캐시·그림 | `uv run --with matplotlib python3 harness/make_figures_v2.py --csv safe_runs.csv -o ../figs_v2` (matplotlib 3.11.2) | 캐시 327런을 새로 만듦. 저자 작업 트리의 미커밋 캐시와 **내용 동일**. figures.json **바이트 동일**. SVG 17개가 난수 ID·날짜를 빼면 모두 동일 |
| 부록 F | `python3 harness/decisive_ci.py --tex` | 14행의 런 수, 런별 달성률, 95% 구간이 표 F1과 **모두 일치** |
| E9 요약 | `python3 harness/e8_summary.py results/E9 E9` | `results/E9/summary_E9.md`와 **동일** |
| 전송·소켓 | vLLM 전송 로그 파서(`r6_xfer.py`와 같은 정의), `stall_match.py`, ss 누적 카운터 | 4.45/14.97/14.16, m, 디스크립터, 4/5 GC 일치, 수신 창 제한 39.9% 모두 재현 |

2차에 비해 나아진 점은 다음과 같다.
- 부트스트랩 구간이 `harness/decisive_ci.py`로 들어와 부록 F가 공개 스크립트로 나온다.
- `safe_runs.py`가 상한 도달 런을 같은 계산(`max_inflight`)으로 표시한다. 논문의 개수와 그림 3 캡션이 이 분류와 맞는다.
- E9는 예측 커밋, 실행 스크립트, 런 로그(`ucx=…`, `RR_CONN_LIMIT=0`), 프록시 로그, 계측 트레이스, 요약이 모두 남아 있다. 원자료에서 논문까지 추적이 끊기지 않는다.

### 4.2 새 함정: 커밋된 캐시가 낡았다 [필수]

- HEAD의 `results/per_request.json.gz`는 v1 커밋(cbac960) 것이다. 308런이고, E9가 없고, 새 주의 런 9개가 '안전'으로 들어 있다.
- 작업 트리에는 327런 캐시가 있지만 커밋되지 않았다(`git status`: `M results/per_request.json.gz`).
- `slo_sensitivity.load_cache()`는 파일이 있으면 CSV와 맞는지 보지 않고 그대로 쓴다. `make_figures_v2.py`와 `decisive_ci.py`에는 `--rebuild`가 없다.
- 커밋된 캐시로 두 스크립트를 돌린 결과(`work_headcache/`)는 다음과 같다.
  - `decisive_ci.py`: 14행 중 **6행만** 출력하고 경고가 없다. E9 행이 모두 빠진다. 31B aiohttp GPU당 4는 두 런, 구간 0.867–0.956으로 나온다.
  - `make_figures_v2.py`: `ValueError: cannot convert float NaN to integer`로 중단된다.
- 고칠 방법은 셋 중 하나다.
  - (a) 캐시를 커밋한다.
  - (b) 캐시를 추적에서 빼고 첫 실행 때 만든다.
  - (c) `load_cache()`가 캐시의 런 ID·safety 집합을 safe_runs.csv와 비교해 다르면 다시 만들게 한다.

  (c)가 가장 안전하다. 두 스크립트에 `--rebuild`도 넣는다.

### 4.3 [참고] 두 계산 경로의 셋째 자리 차이

- `e8_summary.py`(bench.json 직접)와 캐시 경로(최대 간격을 10 µs 단위로 반올림)가 두 점에서 셋째 자리가 다르다.
  - 청크 1,024 GPU당 6: 0.188 대 0.189
  - P 8,192 GPU당 5: 0.365 대 0.366
- 논문 본문은 앞의 값을, 그림은 뒤의 값을 쓴다. 판정 영향은 없다.
- 캐시의 `round(max(l), 5)`를 빼거나, 같은 값을 쓰도록 한 곳으로 모은다.

## 5. 공개 차단 항목 (1·2차 패키징 항목의 현재 상태)

| 항목 | 상태 |
|---|---|
| **[필수] 100 MB 초과 파일** | **미해결.** `results/E5/rr_proxy_E5_26_B3.log` 457 MB가 여전히 추적된다. 50 MB가 넘는 result.json/bench.json 파일 4개(두 쌍, E7 1P2D·2P1D GPU당 6)도 그대로다. 추적 합계는 7.1 GB에서 **7.90 GB**로 늘었다(E9 0.78 GB). result.json이 bench.json을 통째로 중복하는 구조도 그대로다. |
| **[필수] AWS 계정 ID** | **미해결.** RESULTS.md 1068행(S3 버킷 이름)에 있고, 이력에서는 커밋 e03d4de가 들여왔다(값은 적지 않는다). 다른 추적 파일에는 없다. **e03d4de는 사전 등록 커밋 8775497의 조상이다. 이력 정리 계획을 부록 D의 해시와 함께 세워야 한다(⚠️ P1).** |
| **[필수] README** | **미해결.** 아직 "Status: pre-measurement", g5/g6, H100, per dollar, writeup/ 문구다. 재현 명령이 없다. |
| **[필수] aggregate.py 기본 SLO** | **미해결.** 인자를 빼면 tbt 100/400으로 논문과 다른 CSV가 나온다. SLO는 PROTOCOL.md에만 있다. |
| **[필수, 신규] 낡은 캐시** | 4.2절 참조. 깨끗한 클론에서 부록 F와 그림이 재현되지 않는다. |
| **[필수, 신규] 사전 등록 해시** | ⚠️ P1 참조. |
| [필수, 2차 P3 잔여] 판정 근거 스크립트 | 부트스트랩은 해결됐다(`decisive_ci.py`). 31B 프롬프트 길이 구간은 미해결이다(⚠️ P2). 전역 정지는 `e8_summary.py`와 `stall_match.py`로 E8·E9를 덮는다. 2P1D 귀속은 논문에서 철회돼 더 필요 없다. |
| [권장] 버전 고정 | 미해결. uv.lock이나 requirements가 없다. 이번 재생성은 matplotlib 3.11.2였다. 도커 이미지 digest(`vllm/vllm-openai:v0.30.0` 태그만 있음)와 HF 체크포인트 revision도 없다. |
| [권장] 런 매니페스트 | 미해결(❓ 참조). |
| [권장] .gitignore | 미해결. `results/*/bench.log` 등이 두 단계 아래 파일에 적용되지 않는다. |
| [권장] 세션 env, 테라폼 기본값 | 미해결. `results/.session_{A,Ap,C1,P}.env` 4개가 추적된다. `variables.tf`에 개인 `aws_profile`과 `0.0.0.0/0`이 있다. |
| [권장] CITATION.cff, LICENSE | 미해결. 제목과 초록이 v0 이전(g5/g6, per dollar)이고, LICENSE는 writeup/·figures/ 경로를 가리킨다. |
| [권장] 심사 폴더의 절대 경로 | 늘었다. 사용자 홈 절대 경로가 든 추적 파일은 **15개**다(v0 md 3, v0 스크립트 4, v1 md 1, v1 스크립트 7). 세션 스크래치 경로(`<scratch>`)가 든 행도 5개 있다. 논문이 "both mock reviews with their scripts"를 공개한다고 하므로 정리한다. |
| [권장] 결정성 | `make_figures_v2.xfer_stats`와 `ss_*`의 `glob`이 아직 정렬되지 않았다. 이번에는 SVG가 같았지만 파일시스템 순서에 기댄다. |
| [참고] 원고 자리표시 | `\todo{contact email}`, `\todo{draft v2, 2026-10-01}`, `\todo{GitHub URL and Zenodo DOI}`가 남았다. 8xlarge 가격은 아직 Vantage 인용이다(paper/TODO.md). |
| [참고] 옛 그림 폴더 | `paper/figures/`(v0, 1토큰 규칙 전)와 `paper/figures_v1/`(상한 런 포함 분류 전)이 남아 있다. 공개한다면 버전을 표시한다. |

제3자 재현을 막는 순서는 다음과 같다.
1. 457 MB 파일과 7.9 GB 추적량 때문에 GitHub에 올릴 수 없다. 원자료는 Zenodo로 옮기고, result.json에는 meta만 남긴다.
2. 낡은 캐시 때문에 깨끗한 클론에서 부록 F와 그림이 재현되지 않는다(4.2절).
3. 계정 ID를 정리하고 사전 등록 해시를 다시 맞춘다.
4. README에 재현 명령을 적는다. aggregate.py의 기본 SLO는 논문 값으로 바꾼다.

   ```
   python3 harness/aggregate.py results/ -o results/all_runs.csv --slo chat=ttft:1000,tbt:50 --slo doc=ttft:3000,tbt:250
   python3 harness/safe_runs.py results/all_runs.csv -o results/safe_runs.csv     # 저장소 루트에서(상대 glob)
   uv run --with matplotlib python3 harness/slo_sensitivity.py --rebuild -o /tmp/sens   # 캐시 재생성
   uv run --with matplotlib python3 harness/make_figures_v2.py -o paper/figures_v2
   python3 harness/decisive_ci.py --tex
   python3 harness/e8_summary.py results/E9 E9
   ```
5. 31B 구간 스크립트를 harness에 넣는다. 런 매니페스트를 만들고 버전을 고정한다.

## 6. 점수

- **아티팩트 품질 3.5/5**(현재 공개 상태 기준, 1차 3, 2차 3.5)
  - **논문 수치의 재현성 4.5/5.**
    - CSV 두 개, figures.json, SVG 17개, 부록 F, E9 요약이 모두 바이트 또는 내용 단위로 재현된다.
    - E9와 표 2 수치는 전부 맞다.
    - 틀린 것은 서술 수치 셋(#28, #87, #153)과 설정 공개 누락 하나(#22)다. 모두 기존 데이터로 고칠 수 있다.
  - **패키징 1.5/5**(2차 2에서 내려감)
    - 2차의 필수 네 건이 하나도 바뀌지 않았다.
    - 낡은 캐시라는 새 함정이 생겨, 커밋된 상태 그대로는 부록 F와 그림이 재현되지 않는다.
  - ❌ 네 건, ⚠️ P1·P2, 5절의 필수 항목을 반영하면 4.5점이다. ❌ 네 건은 원고만 고치면 되고, 필수 항목의 대부분은 파일 정리다.
- **확신도: 높음.**
  - 파이프라인 다섯 단계를 스크래치에서 직접 다시 돌렸다.
  - E9 수치는 bench.json, 요약, 캐시, 부트스트랩을 각각 따로 대조했다.
  - UCX 혼입은 실행 스크립트와 실행 로그 두 곳에서 확인했다.
  - TTFT 범위와 예측 대조는 판정 규칙을 부하별로 다시 적용해 확인했다.
  - 낡은 캐시 문제는 HEAD 캐시로 두 스크립트를 실제로 돌려 확인했다.

---

## 7. 전체 청구 원장 (v2)

출처 약어는 다음과 같다.
- CSV: 재생성 safe_runs.csv(커밋본과 동일)
- FJ: 재생성 figures_v2/figures.json(커밋본과 동일)
- F1: `decisive_ci.py` 재실행
- SUM9: `e8_summary.py results/E9 E9`
- LOG: results/E*/xfer_*·run_*.log
- SS: E8 ss 샘플
- SM: `stall_match.py`
- CAP: `chk_cap.py`(진행 중 요청 수)
- SCR: 그 밖의 `reviews_v2/r4/chk_*.py`
- RM: RESULTS.md(행 번호)
- CFG: configs/
- GIT: 커밋 기록
- 합계: 두 GPU 합계 요청률

| # | 위치 | 주장 | 출처와 대조 결과 | 판정 |
|---|---|---|---|---|
| 1 | 초록 | AWS 2xlarge, Gemma 4 26B(MoE)·31B(dense), stock vLLM, NIXL/UCX TCP | 표 G1, CFG, serve.sh | ✅ |
| 2 | 초록, RQ1 | 26B 4K 최대 간격 중앙값 48 ms(2,560) → 21 ms(512) | FJ 48.4/21.4 | ✅ |
| 3 | 초록 | 2,560 복제본 대비 약 3× | 26B 4K에서만 3/1. FP8·31B는 2,560 복제본의 지원 부하 없음 | ⚠️ |
| 4 | 초록 | 2,560은 video를 켠 Gemma 4의 최소값 부근 | RM 0단계(2,496) | ✅ |
| 5 | 초록 | 더 작은 청크 대비 어떤 SLO에서도 더 많이 처리하지 못함(30 ms까지) | FJ who_wins 아래 행에 d·D 칸 0개 | ✅ |
| 6 | 초록 | 26B: 1P1D는 GPU당 4 경계, 복제본은 5 | F1 0.954/0.992/0.885; 0.999/1.000 | ✅ |
| 7 | 초록 | 31B 대화 4 대 ≥8 | F1 aiohttp 4 통과·6에서 0.765, 청크 256 8에서 1.000 | ✅ |
| 8 | 초록 | TTFT 비용은 주로 KV 전송 | 61–85%(#121 상수) | ✅ |
| 9 | 초록 | UCX TCP 세그먼트로 3.4× | FJ 14.97/4.45 = 3.36 | ✅ |
| 10 | 1절 | 8xlarge EFA 약 1.6–2× 가격 | Vantage(좌장 확인). TODO에 공식 가격 교체 예정 | ✅(외부) |
| 11 | 1절 | 모의 심사 두 번이 기준선의 두 핸디캡(청크, 프록시 100)을 찾음 | v0·v1 심사 기록 | ✅ |
| 12 | 1절, 3.6 | E9 예측을 측정 전에 커밋 | GIT 8775497 13:29:43 UTC, 첫 E9 런 14:19:44 UTC, 예측 문단 불변. 원격 없음 | ✅ |
| 13 | 1절 | 청크를 약 2,500에 묶었을 때만 약 3배 | #3과 같음 | ⚠️ |
| 14 | 기여 | NIXL은 전송을 최대 네 연결로 나눔 | 좌장·R3 NIXL v1.4.1 소스, SS | ✅ |
| 15 | 3.1 | us-east-1 한 AZ, EFA·ENA Express 없음 | RM, 외부 규격 | ✅(외부) |
| 16 | 3.1 | 단일 흐름 4.97 Gbps | RM 10–11 | ✅ |
| 17 | 3.1 | 배치 그룹 9.54, 8흐름 49.72 Gbps | FJ iperf, RM E4-0 | ✅ |
| 18 | 3.1 | 클라이언트 c6i.xlarge(E7 전), 2xlarge(E7부터) | RM | ✅ |
| 19 | 표 1 | $2.242 / $3.363 | 1차 확인 | ✅ |
| 20 | 표 1 | g7 용도: 입력 길이, 첫 전송 튜닝 | 대역폭 제한(A1), GPU 비교(A9)에도 쓰임 | ⚠️ |
| 21 | 3.1 | vLLM v0.30.0, NIXL 1.4.1 | serve.sh 이미지 태그, RM 5·18 | ✅ |
| 22 | 3.1, 부록 C | 따로 적지 않으면 분리 런은 UCX 7변수 | E9 P 8,192 세 런은 `UCXSET=SEG`(run_E9.sh, run_E9.log) | ❌ |
| 23 | 3.1 | util 0.90(0.42·0.70 예외), 256, 32,768 | util·256 맞음. E1b/E1c 31B FP8은 16,384 | ⚠️ |
| 24 | 3.1 | 분리 쪽 기본값: 두 노드 청크 2,560(E9 한 번 P 8,192), 디코드 256, 스레드 4 | lib_E9 `PCHUNK`, D 청크 2560 | ✅ |
| 25 | 3.2 | 3.8B/25.2B, 30.7B | 모델 카드(저장소 밖) | ❓ |
| 26 | 3.2 | 4K/16K/32K에서 140/260/412.5 MiB | B·D 로그 | ✅ |
| 27 | 3.2 | b_g ≈ 10 KiB, 국소 약 100 MiB, W = 1,024, b_w ≈ 100 KiB | 120/12,288과 152.5/15,616 모두 10.0 KiB. W는 configs/models.md | ✅ |
| 28 | 3.2 | 대화 요청 28–30 MB, 식이 예측 | 로그 평균 25–26 MiB(창 중앙값 24.4–27.0), 식 24.2–25.2 MiB | ❌ |
| 29 | 3.2 | FP8·BF16 280, 31B 560 MiB | LOG | ✅ |
| 30 | 3.2 | Gbps = 0.008389 × MiB/s | 8 × 1,048,576 / 10⁹ | ✅ |
| 31 | 3.3 | 2,496 미만 거부, 모든 모달리티 0이면 통과 | RM 0단계 | ✅ |
| 32 | 3.3 | E8 256–2,048 스윕, E9 26B 512 추가 | CSV | ✅ |
| 33 | 3.3 | 모두 끄면 2,560 기동 실패, 대조군은 image만 | RM 마찰 #27 | ✅ |
| 34 | 3.3 | 복제본 프록시 aiohttp 기본 100 연결 | rr_proxy.py `--conn-limit` 기본 100 | ✅ |
| 35 | 3.3 | E9 전 복제본 9런이 상한 도달 | 도달 11런(2런은 이미 클라이언트 한계 주의) | ⚠️ |
| 36 | 3.3 | E9에서 상한 해제 | run_E9.log `RR_CONN_LIMIT=0` | ✅ |
| 37 | 3.3 | 분리 프록시: E8 전 시험 프록시, E8·E9 aiohttp 무제한 | pd_proxy.py `limit=0` | ✅ |
| 38 | 3.4 | ShareGPT 입력 중앙값 76–141 | CSV 감사 89런 | ✅ |
| 39 | 3.4 | 출력 중앙값 59–177 | 1런 24(E1 31B FP8 kvmatch @12) | ⚠️ |
| 40 | 3.4 | 4,096/16,384/32,000 입력, 512 출력 | CSV | ✅ |
| 41 | 3.4 | 트레이스 600요청, 996/217 | FJ fig11, CSV | ✅ |
| 42 | 3.4 | max(100, ⌈180r⌉), 0.56 이상에서 약 180 s | 산술 | ✅ |
| 43 | 3.4 | 같은 요청률·반복이면 같은 시드 | lib_E9 `SEED=base+1000*REP` | ✅ |
| 44 | 3.5 | 1토큰 규칙은 E8 뒤, 0.899/0.878 → 0.924/0.903 | SCR 재계산, 0.9를 넘은 런은 이 둘뿐 | ✅ |
| 45 | 3.5 | 다른 대화 런은 최대 0.055 올림 | 0.0556(E1 L40S @1 0.917 → 0.972), 반올림 차 | ✅ |
| 46 | 3.5 | 26B BF16 g7e 38 ms, 50 ms = 가장 느린 GPU 26B 스텝 × 5 | RM 82·141 | ✅ |
| 47 | 3.6 | 122 + 5 + 1 = 128 / 455 | CSV(92 + 30) | ✅ |
| 48 | 3.6 | 주의 14 = 5 + 9 | CSV. 사유 표기는 #35 | ✅ |
| 49 | 3.6 | 감사 313 | CSV | ✅ |
| 50 | 3.6 | 첫 5요청 제외 시 최대 0.019 변화 | +0.019, −0.029, 뒤집힘 0(165런) | ⚠️ |
| 51 | 3.6 | TTFT 반복 변동 최대 10% | 세션 안 최대 10.2%(E8 aiohttp GPU당 4), E9 7.4·8.5% | ✅ |
| 52 | 3.6 | 0.9 훨씬 위는 최대 0.03 | 세션 안 0.026, 그림 3이 묶은 GPU당 3은 0.044 | ⚠️ |
| 53 | 3.6 | 0.9 부근 ±0.10 | 0.767–0.975, ±0.104 | ✅ |
| 54 | 3.6 | 낮은 점 0.37–0.64 | FJ 0.369–0.644 | ✅ |
| 55 | 3.6 | 계층 부트스트랩, 시간 블록 20개 | decisive_ci.py. start_times 단조 증가 확인(60런) | ✅ |
| 56 | 그림 1 | 215런(감사 212, 주의 3) | FJ, SCR | ✅ |
| 57 | 그림 1 | 음영 28 = 복제본·단일 21 + 분리 7 | 분리 7 중 2가 주의 런 | ⚠️ |
| 58 | 4.1 | 26B FP8 g7e 복제본 GPU당 0.25: p99 8.6 ms, 48% | CSV E2 B2 r0.5 8.63, 0.52 | ✅ |
| 59 | 4.2 | 48.4/38.8/27.6/21.4 ms | FJ | ✅ |
| 60 | 4.2 | TTFT 132 → 205 ms | FJ | ✅ |
| 61 | 4.2 | 1,024–2,048에서 토큰당 약 24 µs | (52.3 − 27.6)/1,024 = 24.1(구간별 21.9·26.4) | ✅ |
| 62 | 4.2 | 1,024 아래는 더 천천히, 디코드 스텝 약 9 ms | 512–1,024 12.1 µs/토큰. GPU당 1 ITL 중앙값 8.6–8.7 ms | ✅ |
| 63 | 4.2 | 2,560 중앙값이 한도보다 1.6 ms 아래 | 50 − 48.4 | ✅ |
| 64 | 4.2 | 2,048은 52.3 ms | FJ | ✅ |
| 65 | 4.2 | FP8 GPU당 0.5: 62/43/27 ms, 0.13/0.99/1.00 | FJ 62.2/43.2/26.8, 0.133/0.994/1.000 | ✅ |
| 66 | 4.2 | 31B 겹친 프롬프트 <200토큰: 99–100% | SCR 런별 0.985–1.000(합산 0.996) | ✅ |
| 67 | 4.2 | 200–400토큰: 43% | 5런 0.415, E5·E7 4런 0.434 | ⚠️ |
| 68 | 4.2 | 400–800토큰: 12% | 0.117(5런), 0.122(4런) | ✅ |
| 69 | 4.2 | 800 초과: none | 1/323(0.3%) | ⚠️ |
| 70 | 4.2 | 512: 0.44, 2,560과 같음 | FJ 0.442 대 0.450–0.514 | ✅ |
| 71 | 4.2 | 256: 두 런 1.00, 34 ms, TTFT 79 그대로 | FJ 34.1, 79 대 79 | ✅ |
| 72 | 그림 2 | 2,560 점은 E5·E7·E8 반복 합산 | (a)(c)는 5런. (b) FP8은 E7 1런 | ⚠️ |
| 73 | 그림 3 | 상한 런 제외, 1,024의 GPU당 4 이상은 E9 | FJ h2h 계열 | ✅ |
| 74 | 그림 3 | 색·선 모양·평균·최소–최대 | 코드 S1–S5, `series()` | ✅ |
| 75 | 4.3 | 2,560 복제본 GPU당 1 통과, 2 탈락(0.37–0.64, 5런) | FJ | ✅ |
| 76 | 4.3 | 1P1D 3 통과, $2.00 대 $0.63 | SCR 2.003, 0.631(aiohttp) | ✅ |
| 77 | 4.3 | FP8·31B는 2,560 대비 1P1D만 충족 | FJ | ✅ |
| 78 | 4.3 | 상한 해제 청크 1,024: 4에서 3/3(1.000), 5에서 2/2(0.999, 1.000), 6에서 0.19 | F1, SUM9 | ✅ |
| 79 | 4.3 | 청크 512: GPU당 1–4 통과, 4에서 0.985 | SUM9 | ✅ |
| 80 | 4.3 | 1P1D 4 경계: aiohttp 0.885/0.954/0.992(0.873–0.992), 시험 프록시 0.77–0.98 | F1 | ✅ |
| 81 | 4.3 | 5에서 0.18 | FJ 0.176 | ✅ |
| 82 | 4.3 | P 8,192: TTFT 약 500 → 416–451 ms, 0.874/0.976, 5에서 0.365 | SUM9(캐시 경로 0.366). UCX 설정도 달라 귀속이 섞임(#22) | ⚠️ |
| 83 | 4.3 | 디코드 ITL 15.5 대 13.2(GPU당 3), 20.8 대 15.9(4) | CSV itl_p50 15.48/13.17–13.23, 20.72–20.89/15.86–16.07 | ✅ |
| 84 | 4.3 | FP8: 512·1,024·1P1D 모두 GPU당 1 통과 | SCR 1.000/1.000/1.000 | ✅ |
| 85 | 4.3 | 31B 청크 256: GPU당 8까지 통과(1.000) | F1 | ✅ |
| 86 | 4.3 | 31B 1P1D 4 통과(aiohttp 세 런, 시험 프록시 0.885–0.963), 6에서 0.765 | 시험 프록시로는 4 탈락(0.885). 경계 표시 없음 | ⚠️ |
| 87 | 4.3 | 둘 다 통과한 부하에서 복제본 79–359 대 1P1D 260–526 ms | 둘 다 통과한 부하: 78–247 대 255–384 ms | ❌ |
| 88 | 표 2 | 26B 2,560: 1, $2.00, 132 ms | SCR 2.003, 132. 계층 구간 0.922–0.967(경계 아님) | ✅ |
| 89 | 표 2 | 26B 최선: 5(1,024), $0.38, 259–278 ms | SCR 0.381 | ✅ |
| 90 | 표 2 | 26B 1P1D: 3, $0.63, 366 ms(4 경계) | aiohttp 한 런 값. GPU당 3의 세 런을 모두 쓰면 $0.66, 366–374 ms. 열에 프록시 미기재 | ⚠️ |
| 91 | 표 2 | FP8: none / ≥1 ≤$1.87 / ≥1 ≤$1.89 | 청크 512 1.872, 1,024 1.873, 1P1D 1.885 | ✅ |
| 92 | 표 2 | 31B: none / ≥8 ≤$0.67, 117 ms / 4, $1.67, 304 ms | 0.668, 117; 1.674, 런별 중앙값 302.7/304.3/308.1. 경계 표시 없음(#86) | ⚠️ |
| 93 | 표 2 | 비용 정의, $3.363, 클라이언트 제외 | 코드·정의 일치 | ✅ |
| 94 | 4.4 | 격자 TTFT 0.25–5 s, 간격 30–300 ms | `T_GRID`, `B_GRID` | ✅ |
| 95 | 4.4 | 위 행: 40–50 ms 세 워크로드, 30 ms 26B 둘에서 분리 우세 | FJ(TTFT ≥0.5 s 행) | ✅ |
| 96 | 4.4 | 위 행 75 ms 이상 대부분 미결 | FJ | ✅ |
| 97 | 4.4 | 아래 행에 분리 우세 칸 없음 | FJ | ✅ |
| 98 | 4.4 | 26B NVFP4: 결정된 칸 모두 복제본 우세, 30 ms에서 청크 512 3 대 1P1D 2 | FJ. SCR 30 ms: 512는 3에서 1.000·4에서 0.839, 1P1D는 2 통과·3에서 0.66–0.77 | ✅ |
| 99 | 4.4 | FP8: TTFT 0.5 s 이하 복제본 우세, 그 외 미결, 30 ms 0.958 | FJ, F1 | ✅ |
| 100 | 4.4 | 31B: 40–50 ms 복제본 우세, 30 ms 둘 다 실패 | FJ, SCR 0.378 | ✅ |
| 101 | 4.4 | TTFT 0.25 s에서는 복제본만 | FJ(31B 30 ms 칸은 둘 다 실패) | ✅ |
| 102 | 그림 4 | 빗금 = 양쪽 모두 최고 요청률에서 통과 | 한쪽만 censored인 빗금 43칸 | ⚠️ |
| 103 | 4.5 | UCX 기본 8 KB → 4.45 Gbps | FJ | ✅ |
| 104 | 4.5 | 세그먼트만 14.97, 3.4× | FJ | ✅ |
| 105 | 4.5 | 7변수 13.5–14.2, 5–10% 낮음 | LOG 13.46/14.16 | ✅ |
| 106 | 4.5 | 수신 창 제한이 busy의 약 40% | SS P측 누적 rwnd_limited/busy 39.9% | ✅ |
| 107 | 4.5 | g7 첫 튜닝 626 → 466 ms, 0.82 → 0.99 | CSV D d1a/d1d | ✅ |
| 108 | 4.5 | NIXL 분할 규칙(≥1,024, 최소 1,024, 스레드 4) | 좌장·R3 v1.4.1 소스(논문에 파일 위치 미인용) | ✅ |
| 109 | 4.5 | 26B 4K 디스크립터 약 1,900–2,240, 2–3조각 | LOG 창 중앙값 1,826–2,240 | ✅ |
| 110 | 4.5 | 31B 4K 약 4,000–4,500은 4조각, 대화는 한 조각 | LOG 4,046–4,480. 31B 대화 창 중앙값 852–919 | ✅ |
| 111 | 4.5 | 연결 4개가 각 22–27%, 다섯째가 나머지 | SS(26B 25.3/24.6/23.9/23.5/2.9%) | ✅ |
| 112 | 4.5 | 26B 대개 2–3개, 31B 네 개 64% | FJ 0.51 + 0.38, 0.636 | ✅ |
| 113 | 4.5 | 저부하 m: 26B 1.4–1.6, 31B 1.8 | LOG 1.41–1.57, 1.80–1.82 | ✅ |
| 114 | 4.5 | 판정 부하 26B 0.92–1.14 | LOG GPU당 3: 1.12–1.14, 4: 0.92–1.04 | ✅ |
| 115 | 4.5 | 31B 대화 0.81 | E8 0.82/0.81, E9 0.78, E7 0.78–0.82, E5 0.85 | ⚠️ |
| 116 | 4.5 | 31B 네 연결 합계 19–21 Gbps, iperf 네 흐름 38 | 좌장(R3 스크립트), LOG 창 최대 19.0–19.7 | ✅ |
| 117 | 4.5 | 호스트 스테이징 4.7×, 0.5에서 안정 부하 없음 | CSV 2,942/624 = 4.71, 50 s | ✅ |
| 118 | 4.5 | 푸시: 전송 27–36%, TTFT 53–62 ms, 달성률 ≤0.04, 468–533 MiB | RM 1052, FJ fig14 | ✅ |
| 119 | 4.5 | PR 56874는 KV 그룹 하나만 | RM E6 | ✅ |
| 120 | 4.5 | g6e 15분 평균 약 1.2 Gbps | 2차 확인 | ✅ |
| 121 | 4.6, 그림 5 | 61%(84/137), 76%(283/370), 85%, 잔차 28–87 ms | 상수. 31B 283은 창 평균의 평균이고 전송 가중은 297.6(80%, 72 ms) | ⚠️ |
| 122 | 4.6 | 예측 235 대 측정 267(14%), 810–830 대 853 | FJ 항목 | ✅ |
| 123 | 4.6 | 1 Gbps: 예측 약 1.5 s, 측정 2.19 s, M/D/1 약 2.2 s | FJ fig02 2,185 | ✅ |
| 124 | 4.6 | 16K FP8: 520 MiB, 0.3–0.7 s, 프리필 0.8 s, 465–506 ms | 2차 확인 | ✅ |
| 125 | 4.7 | 런당 1–5회, 40–110요청, 55–80 ms | SCR 0–5회, 16–113요청, 50–79 ms | ⚠️ |
| 126 | 4.7 | 청크 1,024 복제본에는 이런 정지가 없음 | 통과 부하(≤5)에서 0회. 붕괴한 6에서는 8회 | ✅ |
| 127 | 4.7 | 시험 프록시 5회 중 4회가 25–40 ms 2세대 GC와 ±100 ms 일치 | SM | ✅ |
| 128 | 4.7 | aiohttp GC 9 ms, 루프 지연 없음 | SM | ✅ |
| 129 | 4.7 | 남은 1회는 서버 113건, 같은 시드 시험 프록시 런에도 같은 시각 | SM, FJ(106.5 s 113요청 대 106.0 s 106요청) | ✅ |
| 130 | 4.7 | 31B aiohttp 정지는 서버 쪽(110·316건), GC·지연 없음 | SM 일치 0, 좌장 MET | ✅ |
| 131 | 4.7 | 상한: 33/33, 393/393, 5에서 간격 실패 0 | CAP(6에서도 746/746) | ✅ |
| 132 | 4.7 | E9: 4에서 1.000, 5에서 0.999–1.000 | CAP, SUM9 | ✅ |
| 133 | 4.8 | 1P2D 0.906(GPU당 3), 2P1D 0.77, 복제본 셋 GPU당 1 통과 | CSV | ✅ |
| 134 | 4.8 | 31B 4K 1 s 불가, 프리필 약 480, 전송 약 280 | CSV 483, LOG 283 | ✅ |
| 135 | 4.8 | 입력 길이: 1P1D 0.96, 복제본 0.23, 완화 0.47/0.17, 32K 전부 실패 | CSV 세션 B | ✅ |
| 136 | 4.8 | 정밀도: 0.97/0.13/0.03, 1P1D 1.00 | FJ fig10 | ✅ |
| 137 | 4.8 | 트레이스: 26B 모두 통과(4, 5.9), TTFT 약 120 ms 높음, 31B 0.05/0.28 | FJ fig11 | ✅ |
| 138 | 4.8 | 정확성(8/8, 0.58/0.17, 40%) | RM E6·E7, 2차 확인 | ✅ |
| 139 | RQ1 | TTFT 비용 약 70 ms, 1,024까지 지원 부하 손실 없음 | FJ +73 ms, 지원 부하 1 → 5 | ✅ |
| 140 | RQ2 | 저부하 61–85% | #121 값 | ✅ |
| 141 | RQ3 | 2,560 대비 50 ms에서 약 3배 | #3과 같음 | ⚠️ |
| 142 | RQ3, 결론 | 256–1,024 대비 어떤 SLO에서도 더 많이 처리 못함, 첫 토큰은 항상 늦음 | FJ, SCR | ✅ |
| 143 | 절차 2 | 청크 조정의 TTFT 중앙값 비용 최대 약 80 ms, 지원 부하 손실 없음 | 26B +73, FP8 +82, 31B 0 | ✅ |
| 144 | 절차 3 | m은 목표 부하에서 약 1로 떨어짐 | LOG | ✅ |
| 145 | 5.3 | 8xlarge vCPU 4배, g6e·g7e GPUDirect RDMA 없음 | 외부 규격 | ✅(외부) |
| 146 | 한계 | 결정 지점 반복 1–3런 | 표 F1에 4런 점 4개 | ⚠️ |
| 147 | 한계 | 상한 도달 9런 제외 | #35와 같음 | ⚠️ |
| 148 | 감사 | 약 $270 | RM 누적 $267(세션별 추정 합), 결제 원장 없음 | ❓ |
| 149 | 부록 A | 그림 속 요청률은 합계, 캡션은 GPU당 | 캡션 A1–A9 대조 일치 | ✅ |
| 150 | 그림 A3 | 같은 날 2,560 복제본 | ShareGPT BF16 복제본 점이 상한 주의 런(결론 영향 없음) | ⚠️ |
| 151 | 그림 A1 | 1·2·3·5 Gbit·무제한의 TTFT·달성률 | FJ fig02 | ✅ |
| 152 | 부록 D | 동등 구간 0.8–1.25 | `classify(hi=1.25, lo=0.8)` | ✅ |
| 153 | 부록 D | E9 예측 넷 적중, 다섯째 실패 | 예측 4의 "시드 10000 GPU당 4 경계(0.85–0.95)"가 빗나감(1.000). 온전히 맞은 것은 셋 | ❌ |
| 154 | 부록 D | 커밋 8775497 | GIT 일치. 계정 ID 커밋 e03d4de가 조상이라 이력 정리 시 해시가 바뀜 | ⚠️ |
| 155 | 표 F1 | 14행의 런 수, 런별 달성률, 95% 구간 | decisive_ci.py 재실행 전부 일치 | ✅ |
| 156 | 표 F1 | 행 라벨 "1P1D test proxy (E5–E8)"(GPU당 4) | 실제 출처는 E7 1런 + E8 3런 | ⚠️ |
| 157 | 표 G1 | 세션별 날짜(UTC), 인스턴스, 모델 | CSV run_id·model, 455 = 세션 합 | ✅ |
| 158 | 표 G1 | A, A′, C1, P는 쓰지 않음 | safe_runs 제외 사유 | ✅ |
