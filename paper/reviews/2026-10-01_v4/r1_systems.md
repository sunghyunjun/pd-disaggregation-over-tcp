# R1 (LLM 서빙 시스템, vLLM 스케줄러) 4차 심사: draft v4 "Chunk First"

검증 스크립트: `reviews_v4/r1/a1–a6_*.py` (저장소 루트에서 실행). 저장소는 읽기만 했다. 행 번호는 paper/en/main.tex 기준이다.

## 1. 요약

v4는 측정 결과(RQ1, RQ2)를 유지하고, 26B FP8·g7e 런에 맞춘 단계 시간 모델로 긴 입력의 경계(RQ3)를 예측한다. 모델 t(c,p)=d+e+ac+bc(p+c/2)는 vLLM v0.30.0 V1 스케줄러의 저부하 동작(고정 토큰 예산, 청크 위치, 한 단계가 곧 한 간격)을 대체로 옳게 담고, TTFT 식 o+n(d+e)+aL+bL²/2도 정확하다. 문제는 경계의 수치와 강도다. 본문 수치(21K, 11K, 19–25K, 4–6K)는 그림 7의 곡선 교차점(18.7K, 8.6K)과 정의가 다르다. 4점·3모수 적합의 불확실성은 본문 범위보다 훨씬 넓다(한 점씩 빼고 맞추면 14–33K). 초록·결론의 "only disaggregation meets both limits"에는 TTFT 한정어가 없고, all-global 반사실은 한쪽만 바꾼 비교다. 모두 기존 데이터와 스크립트로 고칠 수 있다.

## 2. 점수: 3.5 / 5

4–5절 측정은 v3 수준으로 공개할 수 있다. 6절의 방향(긴 입력, 작은 KV, 빠른 링크일수록 분리 유리)은 타당하지만, 점 추정처럼 쓰인 경계 수치와 근거 없는 인과 문장을 고쳐야 한다.

## 3. 반드시 고칠 것

**3.1 경계의 정의가 본문과 그림에서 다르다 (287–291, 297–299, 312, 325, 32, 51, 354행).**
본문 수치는 `first_pd_only()`가 L 격자와 TTFT 격자(0.25 s부터 약 12% 간격)에서 "분리만 충족" 칸을 처음 찾은 지점이다. 그림 7의 음영과 287행의 정의("orange below blue")는 곡선 교차다. 교차점은 50 ms에서 18.7K(TTFT 1.36 s), 30 ms에서 8.6K(0.65 s)다 [검증]. 그래서 290행 "replicas meet any TTFT limit that 1P1D meets up to about 21K"는 모델과 어긋난다. 20K에서 1P1D는 1.47 s, 복제본은 1.53 s다 [검증]. 교차 기준으로 m=1.5는 19.5K가 아니라 13.8K, 빠른 링크는 4–6K가 아니라 4.7K(50 ms)와 2.2K(30 ms)다 [검증]. 30 ms 빠른 링크의 "4K"는 TTFT 격자 하한 0.25 s에 걸린 값이다.
제안: 정의를 하나로 정하되 모델 오차를 반영한다. "The curves cross near 19K tokens at 50 ms and 9K at 30 ms; 1P1D's predicted TTFT is lower by more than the model's 8% out-of-sample error from about 22K and 10K." (복제본/1P1D ≥ 1.08인 첫 지점 22.2K, 9.5K [검증].)

**3.2 경계의 불확실성을 실제 크기대로 보고한다 (277, 299, 32, 312, 354행).**
- 4점에 3모수라 자유도가 1이다. 한 점씩 빼고 맞추면 50 ms 교차는 14.1K(512 제외, d+e=20.3 ms)에서 32.8K(4K·2,560 제외, d+e=10.3 ms)까지, 30 ms 교차는 5.3K에서 16.7K까지 움직인다 [검증]. 경계를 좌우하는 것은 c→0 외삽 절편인 단계당 고정비 d+e(16.0 ms)다.
- 경계 근처 청크(30 ms에서 240–370, 50 ms에서 336–528토큰)는 측정 범위(512–2,560)의 끝이나 밖이다. 서버 로그상 v0.30.0은 `max_cudagraph_capture_size` 512, FULL_AND_PIECEWISE였다 [검증, results/Ap·E6]. 512토큰 이하 단계는 CUDA graph, 1,024·2,560 단계는 eager로 돈다. 512 점의 과대 예측(간격 +1.8 ms, TTFT +6%)과 1,024 점의 과소 예측(−2.4 ms)은 이 불연속과 맞는다. 512토큰 이하 단계의 d+e를 2 ms 낮추면 30 ms 교차가 8.6K에서 11.1K로, 4 ms면 13.5K로 간다 [검증].
- 16K 표본 밖 오차는 둘 다 분리에 불리하다(복제본 TTFT −7.8%, 1P1D +6.5%). 보정하면 50 ms 교차는 14.4K다 [검증]. 저부하 지도에 m=1을 쓴 것도 보수적이다. 표 3 점검은 m=1.5를 썼고, m=1.5면 13.8K다.
- b×0.85는 1P1D 프리필도 줄이므로 30 ms 경계는 오히려 당겨진다(격자 기준 10.6K→9.7K [검증]). 277행 "which favors disaggregation"은 50 ms에서만 맞다.
제안(299행): "Across leave-one-out fits, the out-of-sample errors at 16K, and the low-load transfer rates we measured (m = 1–1.5), the 50 ms crossing ranges from about 14K to 33K tokens; the model locates the boundary within a factor of about 1.5, not to a point." 초록·결론의 "roughly 20K"는 "roughly 15–30K"로 바꾼다.

**3.3 "only disaggregation meets both limits"에 TTFT 한정어와 모델·GPU를 붙인다 (32, 51, 312, 354행).**
논문의 엄격 SLO(1 s, 50 ms)에서 기준 모델에는 분리만 충족하는 길이가 없다. 1P1D TTFT가 14.4K에서 1 s를 넘는데 교차는 18.7K이기 때문이다. m=1.5에서도 15.6–16.2K의 좁은 띠뿐이다 [검증]. 또 이 지도는 저부하 단일 요청의 지연 충족 가능성이지 RQ2의 GPU당 SLO 굿풋이 아니다. 모델로 계산한 GPU당 프리필 상한은 모든 길이에서 복제본이 1:1 분리 이상이다(16K 0.95 대 0.79, 32K 0.29 대 0.25 req/s/GPU [검증]). 제목의 "Pays Off"도 이 점을 감안해야 한다.
제안(초록): "...predicts that for 26B FP8 on g7e, beyond roughly 15–30K input tokens, only disaggregation can meet some TTFT limits above about 1 s together with a 50 ms gap; at our 1 s limit neither side meets the SLO there." 312행에 "This is latency feasibility at low load, not goodput per GPU."를 더한다.

**3.4 all-global 반사실은 전송량 하나만 바꿨다 (296, 312, 32, 341행).**
스크립트는 1P1D 전송량만 220 KiB/token으로 키우고 복제본의 b와 d는 하이브리드 값으로 둔다. 모든 층이 전역이면 슬라이딩 층도 접두사 전체에 주의를 계산하므로 복제본 단계도 길어진다. 예시로 b를 3배로 두면 약 32K부터 복제본에는 50 ms를 지키는 청크가 없다 [검증, 예시 계산]. "Hybrid attention is what lets disaggregation over TCP take over"는 뒷받침되지 않는다.
제안(296행): "With the transfer volume of an all-global cache (220 KiB per token) and the replicas' step time unchanged, 1P1D meets no TTFT limit that replicas miss up to 64K. This isolates the transfer volume; a model with only global attention would also lengthen the replicas' steps, which we did not model." 초록의 "as with hybrid attention"은 "a small per-token KV volume relative to the link"로 바꾼다.

**3.5 표 3과 g7 점검을 바로잡는다 (249, 269–270, 277, 343행; `harness/boundary_model.py`).**
- "seven measurements it was not fitted to"는 g7e에서 여섯 개다(복제본 TTFT 3, 1P1D 3). g7 두 개를 더하면 여덟 개다.
- g7 적합은 "the same way"가 아니다. 고정비 e 없이 k0·c/2560을 쓰고, 적합 때는 주의 항으로, 예측 때는 단계 전체로 최장 청크를 고른다. 그래서 자기 적합점인 4K 간격도 재현하지 못한다(131.2 대 123.9 [검증]). 일관되게 다시 맞추면 32K 간격 초과는 9%가 아니라 7.1%, TTFT는 −1.1%다 [검증]. 이 점검은 e 항, 곧 단계 수 기제를 시험하지 않는다.
- 빠진 표본 밖 행을 더한다. g7 16K TTFT는 1,430 대 1,314다(일관 적합 1,324, −7.4%) [검증]. g7e 16K의 −7.8%와 같은 방향이다.
- 277행의 원인 설명("sliding-window layers' attention stops growing")은 원고 3.2절의 W=1,024와 맞지 않는다. 슬라이딩 층 비용은 보정 구간(4K–16K)에서 이미 포화해 a에 흡수된다. "We do not know why; candidates include attention-kernel efficiency at long prefixes and the single run per point."로 바꾼다.

**3.6 7.2절 4단계의 KV 적재 비교를 고친다 (319행).**
재계산 비용은 콜로케이션 TTFT(130 ms)가 아니라 고정 오버헤드 o를 뺀 프리필 시간, 약 90 ms다 [미검증, NVFP4의 o를 FP8 적합값 41 ms로 가정]. 84 ms는 NIXL/UCX P→D pull의 값이고 LMCache 원격 적재는 재지 않았다. 하이브리드 KV 그룹 지원도 확인해야 한다. 이 논문이 시험한 계층별 겹침 패치는 KV 그룹이 둘 이상인 모델을 지원하지 않았다. 적재 경로가 모든 층을 전체 길이로 저장하면 26B NVFP4 4K는 140 MiB가 아니라 약 440 MiB(약 260 ms)이고 재계산이 이긴다 [검증, 식 1].
제안: "...loading one moves V(L) only if the offloading path keeps the hybrid layout, which we did not check (the layer-wise patch we tried supported one KV-cache group only). For 26B NVFP4 at 4K, moving 140 MiB at our measured rate took about 84 ms against about 90 ms of prefill (colocated TTFT minus fixed overhead); we did not measure LMCache's transfer path."

**3.7 비디오 하한 문구를 시험한 범위에 맞춘다 (231, 32, 310행).**
원고 3.3절이 시험한 구성은 셋이다. 이미지를 끈 구성과 이미지·오디오를 끈 구성은 거부됐고, 셋 다 끈 구성은 허용됐다. "whenever video input was enabled"는 두 구성을 일반화한 것이다. 2,496이 비디오 항목 하나의 예산이라는 추론은 타당하지만, 항목당 프레임을 줄여 예산을 낮추는 설정은 시험하지 않았다.
제안(231행): "rejected chunks below 2,496 tokens, one video item's budget at default settings, in both configurations we tested that kept video enabled". 초록은 "as vLLM v0.30.0 required for Gemma 4 whenever we kept video input enabled"로 바꾼다.

## 4. 고치면 좋은 것

- 144행 2,048 이상치는 모델로 설명된다. 4K를 2,048로 나누면 두 번째 조각이 p=2,048에서 시작하고, 2,560으로 나누면 두 번째 조각은 1,536토큰이다. NVFP4의 512·1,024·1,536·2,560 점으로 맞추고 2,048을 예측하면 52.6 ms, 실측도 52.6 ms다 [검증]. 멀티모달 설정을 원인으로 볼 필요가 줄고, 표본 밖 점검이 하나 생긴다.
- d 고정: 디코드 단계는 문맥과 함께 길어진다. E2 FP8 ITL 중앙값은 4K(0.25/GPU) 5.9 ms, 16K(0.125/GPU) 7.1 ms이고, g7 하위 25% ITL은 4K 10.3, 16K 11.2, 32K 11.9 ms다 [검증]. 고정하면 긴 입력에서 복제본 단계를 과소평가하므로 분리에 불리하다. 간격과 TTFT에는 d+e만 들어가 d와 e가 따로 식별되지 않는다는 점도 적는다.
- 위치 적응 청크: 고정 예산은 마지막 청크에 맞춰지므로 앞쪽 단계 예산이 남는다. 위치마다 최대 청크를 쓰면 교차가 50 ms에서 18.7K→30K, 30 ms에서 8.6K→12.1K로 간다 [검증, 모델]. 스케줄러 정책을 후속 과제로 적을 만하다.
- d+e≈16 ms의 해석: MoE에서 수백 토큰 청크는 거의 모든 전문가를 읽는다. FP8 가중치 약 25 GB를 약 1.8 TB/s로 읽으면 약 14 ms다 [미검증, 사양 값]. 맞다면 단계 수 벌점은 MoE에서 크고 밀집 모델에서 작다. 301행에 이 점과, NVFP4는 KV도 절반이라 방향이 모호하다는 점을 적는다.
- 저부하의 범위(32K에서 프리필 이용률 0.1은 약 0.03 req/s/GPU)와 동일 길이 프롬프트 가정을 본문에 적는다. 58행 "four measurement pitfalls"는 v4 구성과 맞지 않는다.

## 5. 검증 기록

- `boundary_model.py` 재실행: e 9.03 ms, a 15.107 µs, b 2.652 ns, o 41 ms, 표 3의 13개 값 일치 [검증]
- d: 적합 런 ITL 중앙값 6.96–7.11 ms. 적합점은 모두 단일 런. 16K는 27%만 프리필과 겹쳤고 p90 150.2는 그 군집 안 [검증]
- 격자 기준: 21,247/1.587 s, 10,624/0.794 s, b×0.85 25,268, m=1.5 19,484, 빠른 링크 5,793·4,096, all-global 없음 [검증]
- 교차 기준: 18,658, 8,555, m=1.5 13,777, 빠른 링크 4,664·2,233 [검증]
- 4K 1,584/0.17 s, 560/0.25 s, 1P1D 0.42 s; 32K 3.53 대 2.79 s; 64K 12.70 대 8.18 s; 16K·30 ms 1.75 대 1.16 s; c=128 한계 35.7K; 840 MiB, 6.9 GiB [검증]
- 빼고 맞추기, 16K 오차 보정, 엄격 SLO 띠, 프리필 상한, g7 일관 적합 [검증, 모델 계산]
- 26B NVFP4 간격 중앙값 48.4/38.8/27.6/21.4 ms, TTFT 132→205 ms, 1,024·GPU당 5에서 42.0–42.8 ms, GPU당 4에서 359 대 200 ms [검증]
- 84 ms·130 ms: figures.json의 그림 4 값과 일치 [검증, 원자료 재계산 아님]
- CUDA graph 캡처 상한 512 [검증, 로그]; 전문가 가중치 읽기 14 ms [미검증]
