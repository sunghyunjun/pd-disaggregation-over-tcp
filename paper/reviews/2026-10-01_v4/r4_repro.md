# R4 (4차) — 재현성·아티팩트 평가 (paper/en/main.tex v4, 커밋 d0f4c12)

저장소는 읽기만 했고, 감사 전후로 `git status`가 깨끗하다. 산출물과 대조 스크립트(`check1~8.py`)는 `reviews_v4/r4/`에 있다.

## 1. 요약

- **재실행은 결정적이다.** `boundary_model.py`가 만든 JSON은 `paper/figures_v4/boundary.json`과 바이트까지 같고(SHA-256 2133…d15c), 두 번 돌려도 같다. `make_figures_v4.py`의 18개 그림도 같다. SVG는 날짜와 무작위 ID를, PDF는 CreationDate를 빼면 일치하고, `figures.json`은 바이트까지 같다.
- **이전 경로도 그대로 돈다.** `aggregate.py`와 `safe_runs.py`의 CSV는 바이트까지 같다. `make_figures_v3.py`의 17개 그림은 figures_v3·v4와 같고, `decisive_ci.py --tex`의 20행은 부록 F와 수치가 같다. `chunk31_buckets.py`도 돌고, 재생성 그림으로 tectonic 빌드가 성공한다(33쪽).
- **6절의 수치는 스크립트 출력과 모두 맞는다.** 문제는 출력이 무엇을 재는지에 있다. (1) 본문의 경계 수치와 그림 7의 음영은 정의가 다르다. (2) g7 재적합 코드는 자기 적합점을 재현하지 못한다. (3) "seven" 검증 가운데 하나는 사실상 표본 안이고, 개수도 틀렸다. (4) README는 v3에 머물러 있다.

## 2. 점수

- 논문 수치의 재현성: **4.0**
- 공개용 정리: **2.5**
- 종합: **3.5**

## 3. 반드시 고칠 것

**M1. 경계 수치와 그림 7의 정의가 다르다** (L290, 291, 297, 299, 312, 325; 같은 수치가 L32, 51, 354에도 있다)
- 본문 수치는 `first_pd_only`에서 나온다. 이 함수는 T 격자(0.25–9 s, 2^(1/6), 즉 12% 간격; L169)에 1P1D 곡선과 복제본 곡선 사이에 들어가는 칸이 생기는 첫 L을 찾는다. 그림 7은 곡선 교차점부터 음영을 칠한다(`fill_between(..., interpolate=True)`, make_figures_v4.py L39).
- 그래서 두 값이 어긋난다. 교차점과 본문 값을 차례로 적는다.
  - 50 ms: 18.5K 대 "21K"
  - 30 ms: 8.5K 대 "11K"
  - 빠른 연결: 4.5K·2.2K 대 "6K·4K"
  - m = 1.5: 13.8K 대 "19K"
  - b×0.85: 20.7K 대 "25K"
- 격자 방식은 30 ms에서 b×0.85가 경계를 오히려 당기는(9.7K < 10.6K) 인공물도 만든다.
- L290의 "replicas meet any TTFT limit that 1P1D meets up to about 21K"는 모델 기준으로도 거짓이다. 19.5K에서 1P1D는 1.427 s, 복제본은 1.465 s다.
- 교차점 부근의 1P1D 이득은 모델 오차(8%) 안에 있다. 이득이 8%를 넘는 L은 50 ms에서 약 22.3K, m = 1.5에서 17.3K, 30 ms에서 9.6K다.
- 고칠 방향: 정의를 하나로 정하고 본문, 그림, `figures.json` 메타를 맞춘다. 권고안은 L290을 "At a 50 ms gap limit the curves cross near 18.5K tokens, and 1P1D's predicted advantage exceeds the model's 8% TTFT error from about 22K"로 바꾸는 것이다. 코드에는 교차점 함수를 넣고 JSON에 저장한다.

**M2. all-global 주장은 30 ms에서 거짓이다** (L296)
- 30 ms에서 35.7K를 넘으면 복제본은 어떤 청크로도 한도를 못 지킨다. 이때 all-global 1P1D는 9.1–19.3 s의 TTFT 한도를 지킨다.
- 스크립트의 `None`은 T 격자 상한 9 s 때문에 나온 값이다.
- 수정 문안: "At a 50 ms gap limit it meets no TTFT limit that replicas miss up to 64K; at 30 ms it does so only beyond 35K, where no chunk meets the gap limit and its TTFT exceeds 9 s."

**M3. 검증 개수와 성격** (L249, L343)
- 표 3의 check는 복제본 3개와 1P1D 3개, 모두 6개다. "seven"을 "six"로 고친다.
- 잔여 28 ms와 m = 1.5는 E4 배치 그룹의 26B FP8 4K 런에서 왔다. 그림 4 첫 행의 158/165/28 ms이고, 165 ms는 m = 1.49에 해당한다.
- 따라서 4K 배치 그룹 1P1D 검증(362/349)은 같은 구성을 다른 날 반복한 값이다. L249에 다음 문장을 넣는다: "The residual (28 ms) and m = 1.5 come from session E4's 4K placement-group run (Figure 4, first row), so the 4K placement-group check repeats that configuration."

**M4. g7 재적합 코드 불일치** (boundary_model.py L136–144; 원고 L277과 표 3)
- 적합 행은 4K에서 (1,536 토큰, p = 2,560) 청크에 k0를 그대로 쓴다. 평가식 `step7`은 k0·c/2560을 쓴다. 그래서 4K 적합점이 재현되지 않는다(측정 131.2, 모델 123.9).
- L136의 주석 "fixed per-token share taken from g7e ratio"에 해당하는 코드는 없다.
- 이 재적합은 e를 c에 비례시키고, 두 점에서 두 미지수를 푼다. g7e 적합과 같은 방식이 아니므로 "Fitted the same way"는 틀린 표현이다.
- 수정 코드: 반복 안에서 최장 청크를 `step7`로 고르고 `X.append([k/2560, k*(p+k/2)])`로 푼다. 결과는 k0 106.9, b 3.76e-6이다. 32K 간격은 +7.1%로, 원고의 9%가 아니다. 32K TTFT는 −1.1%, 16K TTFT는 −7.4%다.
- 16K TTFT(1,430/1,314, 현재 코드로 −8.1%)도 표본 외 검증인데 표 3에 없다. 행을 추가한다. 고치지 않으면 초록 L32의 "within 8%"가 깨진다.

**M5. b×0.85 민감도가 보정점을 깬다** (L299)
- b×0.85를 g7e 모델에 적용하면 16K 간격이 136.0 ms가 되어, 측정 150.2보다 9.5% 낮다. M4를 고치면 32K 과대추정을 없애는 배율은 약 0.9다.
- 둘 중 하나를 고른다. 16K 너머에서만 b를 줄이는 변형으로 바꾸거나, 이 부작용을 본문에 적는다.

**M6. 지도의 1P1D 쪽 가정을 적는다** (L247, L283, L289)
- 코드는 o(41 ms)와 8,192 청크당 n(d+e)를 더한다(L167). 본문은 "the same aL + bL²/2"라고만 적는다.
- 표 3의 1P1D 검증은 P 청크 2,560과 m = 1.5다. 지도는 8,192와 m = 1이다.
- L289 "1P1D needs 0.42 s"는 측정값 0.35–0.36 s(m ≈ 1.5)와 다르다. "(at m = 1; we measured 0.35–0.36 s at low load)"를 붙이고, m = 1을 택한 이유를 적는다.

**M7. README와 docstring** (README L5, L8–21; boundary_model.py L17)
- README는 아직 "draft v3", figures_v3, `make_figures_v3.py`, "three rounds"를 가리키고 v4 스크립트를 싣지 않는다. 그대로 따르면 원고가 쓰지 않는 그림 폴더가 나온다.
- 추가할 명령 두 줄(순서 의존 포함):
  - `uv run --with numpy python3 harness/boundary_model.py --json paper/figures_v4/boundary.json`
  - `uv run --with matplotlib python3 harness/make_figures_v4.py`
- docstring의 `python3 harness/boundary_model.py`는 numpy가 없으면 실패한다.

## 4. 고치면 좋은 것

- 버전을 고정한다(numpy 2.5.3, matplotlib 3.11.2, uv 0.8.8). `svg.hashsalt`와 `metadata={'CreationDate': None}`을 쓰면 그림이 바이트까지 같아진다.
- 죽은 코드와 하드코딩을 정리한다.
  - `GBPS_PER_MIBS`(L24)는 쓰이지 않고, 대신 리터럴 8.388608이 네 번 나온다.
  - L13의 "lowest rate where ≥10% overlapped"는 구현되지 않았다. 데이터상으로는 27–88%가 겹쳤다.
  - d = 7과 d7 = 12는 보정 런의 itl_p50(6.96–7.11, 10.38–13.50)에서 계산한다. L134 주석의 "10.4–14.8"은 "10.4–13.5"로 고친다.
  - `runs()`에 network N0 필터가 없다(현재 영향 없음).
  - p90은 최근순위 방식이고 다른 스크립트는 보간 방식이다(차이 0.2 ms 이하).
- 원고에 다음 값을 적는다: o = 41 ms, g7의 d7·k0·o7, L·T 격자, 청크 탐색 범위(128–8,192, 간격 16), 그리고 매개변수 3개를 점 4개로 적합해 자유도가 1이라는 사실.
- 오차 상쇄를 밝힌다. 16K 무배치그룹에서 모델의 전송+잔여는 613 ms인데, 측정한 1P1D−복제본 차이는 466 ms다(+32%). 합계가 7% 안에 든 것은 복제본 과소추정이 이를 상쇄했기 때문이다.
- L301의 "48 against 63 ms"는 NVFP4 중앙값과 FP8 p90을 섞었다. 같은 통계로 맞춘다(p90 기준 48.5–49.1 대 62.9).
- L321의 "idle about 70%"는 L207의 "SM active about 30% at 4 requests/s per GPU (41% at 6)"를 따라 쓴다.
- 부록 D에 6절이 사후 분석이라는 점을 한 줄 넣는다.
- 그림 7 범례의 "(as measured)"는 "(m = 1)"로 바꾼다. 8K에서 꺾이는 것은 P 청크 때문이라고 캡션에 적는다.
- 16K 너머의 1P1D 측정은 세션 B의 32K 하나뿐이다(UCX 미조정, 9.3 s 대 3.5 s). 이 사실을 외삽의 한계로 적는다.
- `paper/en/draft.md`와 `paper/ko`는 v3에 머물러 있다. L357과 L530의 "three rounds"도 갱신한다.
- RESULTS.md의 계정 ID는 아직 남아 있다(A16-5, 공개 차단 항목).

## 5. 검증 기록

- 표 3의 11개 값(62.9/63.4, 157/157, 43.6/41.2, 194/189, 27.2/29.0, 239/253, 150.2/150.3, 820/756, 362/349, 482/500, 1,286/1,370, 375.7/411.2, 3,507/3,495): 스크립트와 일치 [검증]
- e 9.0 ms, a 15.1 µs, b 2.65 ns, d 7 ms(보정 런 6.96–7.11): [검증]
- 복제본 오차 8% 이내(−2.6, +5.9, −7.8%)와 1P1D 오차 7% 이내(−3.6, +3.7, +6.5%): [검증]. "seven"은 틀림(M3)
- 32K TTFT 1% 이내, 간격 9%: 현재 코드 기준 [검증], 코드를 고치면 7%(M4)
- 280·520·840 MiB, 6.9 GiB, 220 KiB, 9.54·4.97 Gbps, 28 ms 출처(E4): [검증]
- 그림 7 축·선종·20배(0.05)·m = 1: [검증]. 음영과 본문 경계는 불일치(M1)
- L289–291의 1,584/0.17, 560/0.25, 0.42, 336, 3.5/2.8, 12.7/8.2, 1.75/1.16, 35K: [검증]
- 21K, 11K, 6K/4K, 25K/19K: 격자 출력과는 일치하나 그림과는 불일치 [검증·M1]
- 초록·서론의 48/21 ms, 21–28 ms, 3.4×(14.97/4.45), 61–85%(84/137, 165/193), 192 SLO(8×8×3), 약 3×: [검증]
- 7.2절의 28→42–43 ms, +30·+74·+80–82 ms, 359 대 200 ms, 84 ms/140 MiB/130 ms: [검증]
- 7.2절의 m 0.57–1.14와 11.7 Gbps, 31B SM 30%: 원고 내부와는 일치하나 원자료는 대조하지 않음 [미검증]
- 서론의 1.6–2× 가격과 200–500×: 외부 인용 [미검증]
