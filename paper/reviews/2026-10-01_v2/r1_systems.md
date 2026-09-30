# Reviewer 1 (LLM 서빙 시스템) 3차 심사평 — v2

대상: "Chunked Prefill or Disaggregation? Prefill–Decode Serving over TCP on Single-GPU Cloud Instances" (paper/en/main.tex, draft v2, 2026-10-01, PDF 25쪽)
근거: v2 원고와 PDF, figures_v2/figures.json, 세션 E9 원자료(19런의 bench.json·prom.txt, collect의 prom.tsv·sar·dmon, metrics_E9 디코드 서버 히스토그램 스냅샷, xfer_E9, proxy_trace_E9), E8 전송 로그, RESULTS.md의 E9 예측·결과 절, 커밋 8775497, harness 코드(slo_sensitivity.py, safe_runs.py, rr_proxy.py), configs/run_E9.sh·lib_E9.sh. 저장소는 읽기만 했다.
재현 스크립트(`reviews_v2/r1/`):
- `r1_e9_server.py`: E9 런별·노드별 서버 지표(실행·대기 요청 수, 초당 스텝, 스텝당 토큰, 평균 ITL, 프롬프트 처리율, KV 사용률)
- `r1_e9_stalls.py`: 디코드 엔진 ITL 히스토그램 전후 차분과 프록시가 받은 상류 간격의 묶음(5 ms 안에 15개 이상)
- `r1_map_cells.py`: 그림 4 아래 줄의 칸별 판정, 구성·요청률별 달성률(50 ms·30 ms), 절단 여부
- `r1_ttft_itl.py`: 청크·구성·부하별 TTFT p50/p99, ITL 중앙값·평균, TPOT, 요청별 최대 간격 p50/p90
- `r1_e9_extra.py`: 부하별 KV 전송 시간·m·동시 전송 수(E8 대 E9), 디코드 노드 수신 Gbps(sar), 실패 원인 분해(TTFT 대 간격), 반복 평균 규칙으로 다시 낸 판정
- GPU SM 사용률(dmon)과 대기 사유 라벨은 인라인으로 확인했다. 대기 사유는 prom.tsv에 라벨이 없어 두 줄의 순서(capacity, deferred)를 prom.txt에 맞춰 가정했다.

수치 표기: "측정"은 원자료에서 직접 계산한 값, "추정"은 측정값으로 만든 모형의 값이다.

## 요약

v2는 2차 심사의 필수 항목을 사전 등록한 측정(E9)으로 해결했다. 복제본 프록시 상한을 풀자 청크 1,024 복제본은 GPU당 4를 세 시드 모두 1.000, 5를 두 런 0.999/1.000으로 통과했다. GPU당 6의 붕괴는 서버 포화다(서버 대기 평균 18–19, 스텝당 1,019–1,024토큰). 청크 512는 26B의 30 ms 칸과 FP8의 30–40 ms 칸을 뒤집었다. 시드도 1P1D와 짝을 맞췄다. 예측은 측정 50분 전에 커밋했고(13:29 UTC, 첫 런 14:19 UTC) 이후 고치지 않았다. 결론의 방향("tuned-chunk replicas matched or beat TCP disaggregation … 3× only vs 2,560-token replicas")은 이제 데이터와 맞는다. 반복 평균 규칙으로 다시 계산해도 엄격 SLO 칸의 판정은 그대로다(굿풋 비 0.45–0.76).

남은 문제는 네 가지다.
1. 범위 표현. "never served more under any SLO we tested"는 문자 그대로는 맞다. 그러나 그림 4 아래 줄 192칸 중 85칸(44%)은 판정할 수 없는 칸이다. FP8은 64칸 중 48칸이 그렇다. 판정 불가 칸에서는 "at least as much"를 주장할 수 없다.
2. 절차 2의 "512–1,024 tokens … cost at most about 80 ms of median TTFT and no supported load". 청크 512의 첫 토큰 비용은 GPU당 4에서 +159 ms이고, TTFT p99는 1.12 s다. 스텝 예산으로 추정한 처리 한계는 GPU당 약 4.5로, 청크 1,024(측정 포화점 약 5.7)보다 낮다. 작은 청크의 처리량 비용이 절차에 빠져 있다.
3. E9 P 청크 8,192 시험. UCX 설정도 함께 바꿨는데(세그먼트 두 변수만) 원고에 적지 않았다. GPU당 5에서는 P 대기열이 줄어든 대신 KV 전송이 쌓였다(평균 0.92 s, 동시 8.7건, 링크 지속 약 11 Gbps). 이 논문 RQ2의 핵심 사실인데 원고에 없다. 부하에서의 m 범위와 절차 3·4도 이 데이터와 맞지 않는다.
4. "Part of 1P1D's gap cost is structural"의 근거로 쓴 중앙 ITL은 복제본의 이봉 분포 때문에 오해를 부른다. 이 지표는 본 심사자가 2차에서 제안했으므로 여기서 정정한다. 26B GPU당 4에서는 평균 ITL(TPOT)도, 요청별 최대 간격 중앙값도 같다. 구조 비용은 31B 대화에서 드러난다(P GPU 활성 32–41%, D 100%).

넷 다 원고 수정과 기존 데이터 재분석으로 고칠 수 있다. 결론을 뒤집는 것은 없다.

## 2차 지적 반영 점검

| 항목 | 판정 | 근거(v2 위치·수치) |
|---|---|---|
| R1-1(2차) 복제본 프록시 연결 상한 100 | 반영 | §3.3 둘째 항목, §4.7 둘째 문단, 부록 B, 주의 런 9개 제외. E9 재측정: 청크 1,024 GPU당 4 ×3 1.000, 5 ×2 0.999/1.000, 6 0.19. GPU당 6은 서버 포화다(두 노드 스텝당 1,019–1,024토큰, 스텝 간격 39.1–39.3 ms, 서버 대기 평균 17.7–19.1, 최대 48–49; `r1_e9_server.py`). 클라이언트 CPU는 전체 2–7% |
| R1-2 "분리만 가능" 칸이 측정하지 않은 청크에 기댐 | 반영 | E9 청크 512. 26B: 30 ms에서 GPU당 3 통과(한 런, 1.000, 최대 간격 p90 27.7 ms), 1P1D는 2. FP8: 30 ms GPU당 1에서 0.958. 예측(15–25 ms)대로 GPU당 1·2에서 21.4/23.8 ms |
| R1-3 반복 수 비대칭 | 반영 | 청크 1,024 GPU당 4를 시드 8007/9007/10007로 3회. 1P1D aiohttp와 같은 시드다 |
| R1-4 디코드 노드 자체 멈춤 | 대부분 반영 | §4.7: 31B 사건을 서버 쪽으로 귀속했고, 26B 한 건도 서버 쪽으로 적었다. 가설 한 줄은 없다. 구조 비용의 근거 지표는 약점 4 |
| R1-5 분리 쪽 튜닝 범위 | 반영, 새 문제 | §3.1 "The disaggregated side kept its defaults", 한계 절. P 청크 8,192를 측정했다. 그러나 UCX 묶음을 함께 바꾼 사실이 빠졌다(약점 3) |
| R1-6 연결 수 귀속, E4 스레드 16 | 대부분 반영 | §4.5에 NIXL 분할 규칙(1,024 디스크립터 하한), 31B 공유 상한 19–21 Gbps, "More connections alone are therefore not a sure lever". E4 스레드 16 무효 결과는 없다 |
| R1-7 TaiChi·SARATHI | 반영 | §2 "SARATHI introduced chunked prefill", TaiChi 슬라이더. TaiChi 인스턴스 서술은 조금 부정확하다(약점 8) |
| R1-8 식 (1) 정의역 | 반영 | 일반형 $V(L)=b_g L + b_w \min(L,W)$, 대화 전송량 28–30 MB |
| R1-9 "default deployment" | 반영 | RQ3 "near the minimum vLLM imposes on Gemma 4 with video input enabled". `--long-prefill-token-threshold`는 언급하지 않았다(선택 항목) |
| R1-10 청크–멈춤 관계 | 대부분 반영 | §4.2 "roughly the time of a step that carries a full chunk", 같은 설정 안의 기울기 24 µs/토큰, 2,048 역전 공개. 절차 2는 과잉이다(약점 2) |
| R1-11 긴 입력 적용 범위 | 반영 | §4.4 끝, 한계 절 셋째 항목 |
| 좌장 A1 26B 4K 동률 | 반영(E9로 대체) | E9로 "5 대 3(4에서 경계)"가 됐다. 반복 수와 시드 모두 대칭이다 |
| 좌장 A2 프록시 상한 공개·판정 제외 | 반영 | §3.3, §3.6, §4.7, 부록 B, 그림 3 캡션, TTFT 중앙값 한정어. 사소: E5 26_B3 대화 GPU당 16(진행 중 최대 1,680)은 여전히 "CPU limit"로 분류돼 있다 |
| 좌장 A4 30–40 ms 조건 | 반영(E9로 대체) | 청크 512 측정으로 칸 자체가 바뀌었다 |
| 좌장 A5 전역 정지 GC형·서버형 분리 | 부분 | GC형 4/5, 서버형 26B 1건과 31B 전부, 2P1D 귀속 철회, "Removing …" 문장 삭제. 남은 것: 런별 사건 표가 없다. "then received a burst of tokens"가 모든 사건 서술에 남아 있다(GC형에만 해당). 서버형 가설 한 줄이 없다. E9에서는 "서버 쪽"이 엔진 쪽과 API 프로세스 쪽으로 다시 갈린다(약점 5) |
| 좌장 A6 디코드 노드 기제 | 부분 | §4.3에 구조 문장을 넣었다. 근거 지표가 오해를 부른다(약점 4). 결론의 "Its benefit, keeping other requests' prefills out of the decode steps, is also what chunked prefill provides"는 정도(청크 크기만큼)와 분리의 비용을 담지 않는다 |
| 좌장 A7 전송 기제 | 대부분 반영 | 분할 규칙, 공유 상한, 7변수 묶음의 rwnd 제한 40%, m 재정의. 남은 것: E4 스레드 16, 그림 5(c)의 표본 간격(0.1 s가 26B 전송 73–93 ms보다 길다) 한계, 부하별 m 표(약점 3) |
| 좌장 A10 문구 | 부분 | RQ3 "default" 수정, TaiChi·SARATHI 반영. 남은 것: §3.3과 부록 B의 "the check passes only when images, audio, and video are all disabled"는 시험하지 않은 조합(video만 끔)까지 말한다. 결론의 "a KV transfer that can be estimated before deployment"는 저부하에만 맞다(약점 3) |
| 좌장 A13 분리 쪽 고정 노브와 범위 | 반영 | §3.1 끝 문장, 한계 절 다섯째 항목, §4.4 끝의 4K·대화 범위 |
| E9-1 청크 512 | 수행, 예측 적중 | 최대 간격, 첫 토큰 증가(+44–57 ms, GPU당 1–2), 30 ms 통과, 지원 부하 4 |
| E9-2 청크 1,024 상한 해제 | 수행, 예측 적중 | 4 ×3, 5 ×2, 6 ×1 |
| E9-3 FP8 청크 512 | 수행 | 0.5·1에서 50 ms 1.000. 30 ms는 GPU당 1에서 0.958이다. 원고가 맞고, RESULTS.md 해석 절의 "0.5·1 모두 1.000"은 틀렸다 |
| E9-4 31B 경계값 | 수행, 일부 빗나감 | 복제본 GPU당 8 통과, 1P1D GPU당 6 탈락(0.765). 시드 10000 GPU당 4의 "경계(0.85–0.95)" 예측은 1.000으로 빗나갔는데, 부록 E는 이를 세지 않는다(약점 6) |
| E9-5 P 청크 8,192 | 수행, 공개 누락 | 예측 "GPU당 4 통과"가 빗나간 것은 부록 E에 적었다. UCX 세그먼트만(`run_E9.sh` 25행 `UCXSET=SEG`) 동시 변경은 원고에 없다(약점 3) |

## 강점

- 사전 등록이 실제로 작동했다. 예측을 측정 50분 전에 커밋했고, 결과 절은 예측 대조를 ✅/✗로 적었다. 빗나간 예측(P 8,192의 GPU당 4 통과)도 원고 부록 E에 올렸다. 1차의 "예측 선후를 입증할 수 없다"는 약점을 이번에는 커밋 이력으로 해소했다.
- 결정적 비교점의 시드를 짝지었다. 청크 1,024 복제본과 1P1D aiohttp가 GPU당 4에서 같은 세 시드를 쓴다. 이 분야 측정 논문에서 드물게 깔끔한 대조다.
- 복제본의 GPU당 6 붕괴가 서버 한계라는 것이 서버 지표로 확인된다. 청크 1,024의 프롬프트 처리 한계(GPU당 약 23.2K 토큰/s, 4K 입력으로 약 5.7 req/s)가 측정됐다. 새 프록시 산물이 없다는 뜻이다.
- 결론이 판정 규칙에 견고하다. 반복 평균 규칙으로 다시 계산하면 26B 1 s/50 ms 0.75, 40 ms 0.76, 30 ms 0.64, 31B 0.45로, 모두 "replicas serve more"(≤0.8)다(`r1_e9_extra.py` 4절).
- 두 기준선(청크 2,560, 조정 청크)을 나란히 두고, 분리가 이기는 조건을 "청크를 줄일 수 없을 때"(Gemma 4의 video 예산 2,496)로 좁혔다. 실무자에게 바로 쓸모 있는 결론이다.
- E9의 1P1D 런에서 프록시 계측을 유지해, 루프 지연이 없고 GC가 짧다(최대 13.7 ms)는 것을 보였다. 1P1D 쪽 실패가 프록시 산물이 아님을 확인할 수 있다.

## 주요 약점

### 1. [필수] "never served more / at least as much"는 판정할 수 있었던 칸으로 한정해야 한다

- 위치: 초록 "Against smaller chunks it never served more under any SLO we tested, down to 30~ms", §1 "in every SLO we tested, replicas with a tuned chunk served at least as much as disaggregation over TCP", RQ3 "it served no more in any SLO we tested", 결론 "it served no more under any SLO we tested", 그림 4 캡션 "Hatched: both sides still passed at their highest measured rate".
- 문제:
  - 그림 4 아래 줄 192칸의 판정 분포는 다음과 같다(`r1_map_cells.py`, figures.json과 일치). 분리 우세 0칸, 복제본 우세 76칸, 복제본만 23칸, 둘 다 실패 8칸, 판정 불가 85칸(44%)이다. 워크로드별 판정 불가는 26B NVFP4 9/64, 26B FP8 48/64, 31B 대화 28/64칸이다.
  - FP8은 양쪽 모두 GPU당 1까지만 쟀다. 1P1D는 E7 시험 프록시 한 런씩이고 복제본은 E8·E9 한 런씩이다. TTFT 0.5 s 이하를 빼면 순위를 알 수 없다. "at least as much"는 이 칸들에서 입증되지 않는다.
  - 26B 완화 칸(TTFT ≥3 s × 간격 ≥100 ms)에서는 P 청크 8,192 1P1D가 측정 최고 요청률 GPU당 5를 통과했다(굿풋 2,236–2,414, 절단). 복제본 1,024는 GPU당 6에서 서버 포화로 탈락했다(2,452, 비절단). 그래서 분리 쪽 비율의 하한은 0.91–0.98이다. 분리가 같거나 더 많이 처리할 가능성이 배제되지 않는다. 반대로 복제본도 완화 간격에서 더 큰 청크(1,536–2,048)를 GPU당 4 이상에서 재지 않았다(청크 1,536 GPU당 4는 상한 도달로 제외). 양쪽 다 측정하지 않은 여유가 있다.
  - 조정 청크 대 분리의 비교는 GPU 두 대(1P1D 대 복제본 두 개)뿐이다. 3노드 분리(1P2D, 2P1D)는 그림 4 분리 쪽 최선 후보에 들어 있지만, 3노드 조정 청크 복제본은 없다.
  - 캡션의 빗금 정의는 코드와 다르다. `classify()`는 한쪽만 절단이어도 비율을 가를 수 없으면 판정 불가로 둔다. 범례도 "Cannot tell within measured rates"라고 쓴다. 26B 완화 칸은 분리 쪽만 절단이다.
- 중요한 이유: 초록과 결론의 문장은 전 영역에서 용량이 우세하다고 읽힌다. 실제로 입증된 것은 "판정 가능한 칸에서는 예외 없이 복제본 우세"다. 이 문장도 충분히 강하고 방어할 수 있다.
- 조치:
  - 초록 문안: "Against smaller chunks, no SLO we could decide favored disaggregation: for 26B it was borderline at 4 requests/s per GPU while replicas held 5, and for 31B chat it was borderline at 4 while replicas held at least 8. Cells with relaxed gap limits, and 26B FP8 beyond a 0.5~s TTFT limit, could not be ranked within our measured rates."
  - §1과 결론: "in every SLO cell we could decide (107 of 192, two GPUs), replicas with a tuned chunk served more".
  - 그림 4 캡션: "Hatched: a side still passed at its highest measured rate, so the ratio cannot be resolved."
  - §4.4 둘째 항목(FP8) 뒤에 26B 완화 칸의 사정을 한 줄 적는다: "at TTFT ≥3 s and gaps ≥100 ms, 1P1D with an 8,192-token prefill chunk still passed 5 requests/s per GPU, its highest measured rate."

### 2. [필수] 절차 2가 작은 청크의 처리량 비용을 빠뜨렸다

- 위치: §5.2 둘째 항목 "in our runs 512--1,024 tokens (26B) and 256 tokens (31B chat) cost at most about 80~ms of median TTFT and no supported load", RQ1 "at a TTFT cost of about 70~ms".
- 측정(`r1_ttft_itl.py`, 26B 4K, TTFT 중앙값):

| GPU당 | 2,560 | 2,048 | 1,536 | 1,024 | 512 |
|---|---|---|---|---|---|
| 1 | 132 | 138 | 145 | 161 | 205 |
| 2 | 136 | 142–144 | 149–150 | 167–168 | 216–218 |
| 3 | – | 152–153 | 159–160 | 182 | 235 |
| 4 | – | – | (173, 상한 런) | 200 | 359 (p99 1,122) |

  청크 512의 비용은 부하가 오르면 커진다. GPU당 1에서는 +73 ms(대 2,560), GPU당 4에서는 +159 ms(대 1,024)다. GPU당 4에서 청크 512 런의 실패 1.5%는 전부 TTFT 초과다(간격 실패 0). 청크 1,024는 0이다.
- 기제: 청크는 디코드 토큰을 포함한 스텝 예산이다. 복제본 한 대가 견디는 프롬프트 처리율은 대략 (청크 − 실행 중 디코드 수) ÷ (꽉 찬 스텝 시간)이다.
  - 청크 1,024(측정): GPU당 6에서 두 노드 모두 스텝당 1,019–1,024토큰, 스텝 간격 39.1–39.3 ms, 실행 중 114개로 포화했다. 프롬프트 23.2K 토큰/s/GPU, 4K 입력으로 약 5.7 req/s/GPU다. GPU당 5에서 이용률은 약 0.88이다.
  - 청크 512(추정): 스텝당 토큰과 스텝 간격의 저부하–GPU당 4 선형 맞춤(41→374토큰, 9.3→20.4 ms, 약 33 µs/토큰)으로 보면, 꽉 찬 512토큰 스텝은 약 25 ms다. GPU당 4에서 실행 중 디코드는 42–43개다. 한계는 약 (512 − 42) ÷ 25 ms ≈ 18.8K 토큰/s, 곧 약 4.5 req/s/GPU다. GPU당 4(16.4K 토큰/s)에서 이용률 약 0.87, GPU당 5에서는 과부하다.
  - 저자의 사전 등록 예측 1도 같은 이유를 적었다("청크가 작아 프리필 처리량이 줄어 1,024보다 높지는 않음"). 원고의 절차는 이 예측과 어긋난다.
- 중요한 이유: "Tune the chunk first"를 따르는 실무자는 스택이 허락하는 가장 작은 청크를 고르기 쉽다. 그러면 간격 한도는 넉넉히 지키면서 처리량과 TTFT 꼬리를 잃는다. 절차는 이 논문의 가장 실용적인 산출물이므로 정확해야 한다.
- 조치:
  - 절차 2 문안: "Use the largest chunk whose full-chunk step fits the gap limit, not the smallest the stack allows. The chunk also bounds the prefill rate a replica sustains, roughly (chunk − running decodes) / (time of a full step): for 26B about 5.7 requests/s per GPU at 1,024 tokens (measured at saturation) and an estimated 4.5 at 512, whose median TTFT at 4 requests/s per GPU was 359~ms against 200~ms at 1,024."
  - RQ1의 "without losing supported load down to 1,024 tokens"는 맞다. 512에 대해서는 "512 tokens passed up to 4, the highest rate we measured for it"를 덧붙인다.
  - [권장] 절차 3의 판정 기준을 부등식으로 쓴다. 청크 c는 두 조건을 함께 만족해야 한다. 꽉 찬 스텝 시간 $t(c)$ ≤ 간격 한도, 그리고 $\lceil L/(c-B)\rceil \cdot t(c)$ + 대기 ≤ TTFT 한도다($B$는 실행 중 디코드 수). 둘을 동시에 만족하는 c가 없는 곳이 분리를 검토할 영역이다. 예를 들어 26B 16K 입력, 청크 1,024면 약 18스텝 × 39 ms ≈ 0.7 s가 대기 전 프리필 시간이다(추정). 이 식은 한계 절의 "16K and longer inputs"가 왜 남은 영역인지를 수치로 설명한다.

### 3. [필수] E9 P 청크 8,192 시험은 UCX 설정도 함께 바꿨고, GPU당 5에서 전송 경로가 병목이 됐다

- 위치: §3.1 "(one E9 test used 8,192 on the prefill node)", §4.3 "Raising the prefill chunk to 8,192 tokens cut 1P1D's median TTFT … but did not change the verdicts", §4.5 "At the loads where our verdicts were decided it fell to 0.92--1.14 for 26B (3--4 requests/s per GPU)", RQ2, §5.2 셋째 항목 "$m$ measured at the target load (it fell to about 1 in our runs)", 넷째 항목 "raise UCX's TCP segment size (send and receive together, without pinning socket buffers)", 결론 "a KV transfer that can be estimated before deployment".
- 사실 1(공개 누락): `configs/run_E9.sh` 25행은 `PCHUNK=8192 PROXY_KIND=aio UCXSET=SEG serve_pd …`다. P 청크와 UCX 묶음(7변수 → 세그먼트 두 변수)을 함께 바꿨다. 사전 등록 예측 5에는 이 변경이 적혀 있지만 원고에는 없다. 비교 대상인 E8 1P1D aiohttp는 7변수 묶음이다.
- 사실 2(전송 로그, `r1_e9_extra.py` 1·2절, 모두 측정):

| 구성 | GPU당 | 평균 전송 | 10초 창 p90 최대 | m | 평균 동시 전송 | KV 트래픽 |
|---|---|---|---|---|---|---|
| E8 aiohttp, P 2,560, 7변수 | 3 | 109 ms | 172 ms | 1.13 | 0.6 | 6.7 Gbps |
| 〃 | 4 (3런) | 119–140 ms | 199–282 ms | 0.88–1.04 | 0.9–1.1 | 8.9 Gbps |
| 〃 | 5 | 177 ms | 355 ms | 0.69 | 1.6 | 10.6 Gbps |
| E9 aiohttp, P 8,192, 세그먼트만 | 4 (2런) | 165–190 ms | 647–694 ms | 0.65–0.75 | 1.3–1.4 | 8.5–8.9 Gbps |
| 〃 | 5 | 922 ms | 5,794 ms | 0.13 | 8.7 | 11.1 Gbps |

  디코드 노드 수신량(sar, 1 s 단위)은 GPU당 5에서 평균 11.1 Gbps, 중앙값 11.1, 최대 16.8 Gbps였다. 전송 8.7건이 쌓여 있는 동안에도 링크는 약 11 Gbps에 머물렀다. 단일 31B 전송이 네 연결로 낸 19–21 Gbps에 못 미친다.
- 해석:
  - E9 GPU당 5에서 P 노드는 따라갔다. 프롬프트 처리 40.5K 토큰/s는 제공량과 같고, 대기는 평균 0.9, 최대 10–12다. TTFT p50 940 ms의 대부분은 전송 대기(평균 0.92 s)다. D 노드에서는 원격 KV를 기다리는 요청이 최대 59개까지 쌓였다. E8(P 2,560)에서는 P 대기열(TTFT p50 1.45 s)이 도착을 늦춰 전송이 쌓이지 않았다.
  - 따라서 26B 4K 1P1D의 GPU당 5 한계에는 세 가지가 겹친다. P 처리량, TCP 전송 경로, 디코드 쪽 간격이다. P를 풀면 전송이 드러난다. 간격 실패만으로도 39%라서(E9, TTFT와 무관한 간격 실패 16%) 판정은 바뀌지 않는다. 그러나 "TCP 위의 분리가 어디서 막히는가"는 이 논문의 질문이고, 그 답이 원고에 없다.
  - 교란: 부하에서 느려진 원인이 세그먼트만 설정인지, P 8,192가 두 요청의 프리필을 한 스텝에서 끝내 전송을 쌍으로 내보낸 탓인지 가를 수 없다. GPU당 4에서도 E9 전송이 E8보다 1.2–1.6배 길었다(평균 165–190 대 119–140 ms, p90 최대 650–700 대 200–290 ms). 절차 4의 "without pinning socket buffers" 권고는 저부하(GPU당 0.25–0.5) 절제 실험만 근거로 한다. 부하에서 얻은 유일한 세그먼트만 데이터는 더 느렸다.
  - 부하에서 vLLM이 보고하는 전송 시간은 NIXL 대기 시간을 포함한다. 그래서 부하에서의 m은 링크의 성질이 아니라 대기열의 결과다.
- 조치:
  - §3.1과 §4.3에 "with only the two UCX segment-size variables"를 넣는다. 부록 E의 예측 5 서술에도 넣는다.
  - §4.3 문안: "With the larger prefill chunk the prefill node kept up at 5 requests/s per GPU, but KV transfers queued instead (mean 0.92~s against 0.18~s with the 2,560-token prefill chunk) while the decode node received about 11~Gbps, and 39\% of requests also exceeded the gap limit."
  - §4.5의 m을 부하 표로 바꾼다: GPU당 3–4에서 0.65–1.13, GPU당 5에서 0.13–0.69이고, 부하에서는 대기를 포함한다고 적는다.
  - 절차 3에 트래픽 점검을 넣는다: "Check that the offered KV traffic, request rate × $V(L)$, stays well below the rate the pair sustains under concurrent transfers (about 11~Gbps sustained and 17~Gbps at peak for our 26B pair, below the 19--21~Gbps a single four-piece transfer reached). A single transfer's $m$ overstates capacity under load." "(it fell to about 1 in our runs)"는 "(0.65--1.1 at 3--4 requests/s per GPU in our 26B runs)"로 고친다.
  - 절차 4를 한정한다: "segment sizes alone were about 5\% faster at low load; we did not compare the two sets under load."
  - 결론의 "can be estimated before deployment"를 "can be estimated at low load; under load, transfers queue"로 고친다.
  - [권장] 세그먼트만과 7변수 묶음을 P 청크 2,560에서 GPU당 4·5로 비교하는 런 서너 개면 교란이 풀린다.

### 4. [필수] "structural" 문장의 근거 지표를 바꿔야 한다 (본 심사자의 2차 제안 정정)

- 위치: §4.3 "Part of 1P1D's gap cost is structural: at equal GPU count its decode node carries the decodes of both GPUs' requests, and its median inter-token latency was 15.5 against 13.2~ms at 3 requests/s per GPU and 20.8 against 15.9~ms at 4", RQ2 "the decode node's doubled batch adds to the gaps", §5.3 "the decode node's doubled batch".
- 문제: 중앙 ITL은 판정과 관계없는 지표다. 복제본의 ITL은 이봉 분포다. 디코드만 싣는 짧은 스텝이 대부분이고, 청크를 실은 스텝이 드물게 길다. 그래서 중앙값만 낮아 보인다. 판정에 쓰는 지표로는 26B에서 차이가 없다(`r1_ttft_itl.py`, 측정).
  - 평균 ITL(= TPOT): GPU당 3에서 1P1D 15.7 대 복제본(1,024) 16.7 ms, GPU당 4에서 20.5–20.9 대 20.7–20.9 ms, GPU당 5에서 28.5–28.6 대 28.5–29.3 ms다.
  - 요청별 최대 간격 중앙값: GPU당 3에서 27.6 대 33.8 ms, GPU당 4에서 33.8–36.9 대 36.4–37.2 ms다. 1P1D가 같거나 짧다.
  - 서버 쪽 평균 스텝 간격도 GPU당 4에서 D 20.9–21.2 ms, 복제본 20.8–21.1 ms로 같다.
  - 이 중앙 ITL 비교는 본 심사자가 2차 약점 4에서 제안했고, 좌장 A6이 받아들였다. 잘못된 지표였으므로 정정한다.
- 26B GPU당 4에서 1P1D를 떨어뜨린 것은 전형적인 간격이 아니라 드문 사건과 TTFT 꼬리다. E9 P 8,192 시드 8007 런(0.874)에서 디코드 엔진은 사건 한 번(112 스트림, 최대 69 ms)을 기록했고, 이것으로 요청의 7.8%가 간격을 넘었다. TTFT 초과 6.9%는 P와 전송 대기다. E8 aiohttp 시드 10007(0.885)도 서버 쪽 사건 한 번이다(113건).
- 구조 비용이 실제로 드러나는 곳은 31B 대화다. 1:1 고정 비율에서 짧은 프롬프트는 P GPU를 놀리고 D GPU에 디코드를 몰아준다.
  - GPU당 6에서 P 노드는 프롬프트를 초당 2.6K 토큰만 처리했다. dmon의 SM 활성률은 P 41%, D 100%다(GPU당 4에서는 32% 대 100%).
  - D는 평균 89개(최대 126) 스트림을 싣고 평균 ITL 39.0–39.5 ms였다. 복제본 청크 256은 GPU당 8에서 노드당 52–55개, 35.1 ms였다.
  - 26B 4K에서는 P의 SM 활성률이 GPU당 4에서 68–69%, 5에서 83%로 비율이 대체로 맞았다.
- 조치: §4.3 문장을 바꾼다. 문안: "At equal GPU count, 1P1D fixes a 1:1 split between the phases. For 26B with 4K inputs the split was balanced up to 4 requests/s per GPU: 1P1D's mean inter-token latency (20.5--20.9 against 20.7--20.9~ms) and median longest gap (33.8--36.9 against 36.4--37.2~ms) matched the replicas', and it lost on rare decode-server pauses and the TTFT tail. For 31B chat the prefill GPU was busy 32--41\% of the time while the decode node carried 89 streams on average at 39~ms per token at 6 requests/s per GPU; replicas carried 52--55 per node at 35~ms at 8." RQ2와 §5.3의 "doubled batch"도 이에 맞춘다.

### 5. [권장] 디코드 서버 API 프로세스의 간격: 튜닝하지 않은 분리 쪽 요인이 하나 더 있다

- 근거(`r1_e9_stalls.py`, 측정): vLLM v1의 ITL 히스토그램은 엔진 코어 타임스탬프로 계산한다(`vllm/v1/metrics/stats.py`: `itl = engine_core_timestamp - req_stats.last_token_ts`, main 브랜치 확인. v0.30.0에서도 같은지는 확인이 필요하다). 엔진이 기록한 간격과 프록시가 상류에서 받은 간격을 비교하면 다음과 같다.
  - 26B P 8,192, GPU당 4, 시드 8007: 엔진 >50 ms 112건, 프록시 >50 ms 112건으로 일치한다(사건 한 번).
  - 26B P 8,192, GPU당 5: 엔진 >50 ms 348건(모두 75–100 ms 구간), 프록시 >50 ms 4,496건, >75 ms 348건이다. 엔진이 50 ms 이하로 기록한 간격 약 4,150개를 프록시는 50–75 ms로 받았다. 이 구간 엔진 평균 ITL이 28.6 ms이므로 엔진 밖에서 20 ms 이상 늦어진 경우가 흔하다.
  - 31B GPU당 6: 엔진 >50 ms 116건(모두 100 ms 초과, 사건 한 번), 프록시 827건이다. 약 711개가 엔진 밖에서 50 ms를 넘었다. 이 런에서 TTFT와 무관한 간격 실패는 21%다.
  - 같은 구간에서 프록시 루프 지연 기록은 0이고, GC는 최대 8.7 ms(31B는 13.7 ms 한 번)다. 클라이언트 CPU는 전체 2–7%다.
- 해석: 한계 부하 근처의 50 ms 초과 간격 대부분은 엔진 코어와 프록시 사이에서 생겼다. 즉 디코드 서버의 API 프로세스(출력 처리, 역토큰화, SSE)나 그 사이의 전달 경로다. 1P1D에서 이 프로세스는 GPU 두 대 몫의 스트림을 혼자 처리한다. 26B GPU당 5에서 동시 스트림은 150–213개, 생성 토큰은 초당 5,050개다. 복제본은 노드마다 그 절반이다. 원고의 "server-side"는 이 둘을 섞는다.
- 영향: 26B GPU당 5는 TTFT만으로도 실패하므로 판정이 바뀌지 않는다. 31B GPU당 6은 E9 요약의 "정지 제외 0.969"가 보여 주듯 이 사건들에 걸려 있다. API 쪽 간격을 줄이면 31B 1P1D 한계가 4에서 6으로 오를 수 있다. 그래도 복제본(≥8)보다는 낮다.
- 조치: §4.7에 한 문장을 넣는다: "Near the limit most over-limit gaps arose between the decode engine and the proxy (4,496 seen by the proxy against 348 in the engine's histogram for 26B at 5 requests/s per GPU), which points at the decode server's API process; it serves the streams of both GPUs." §3.1의 기본값 목록에 "one API server process on the decode node"를 더한다. 가능하면 D의 API 서버 프로세스를 늘려 31B GPU당 6을 한 번 잰다(v0.30.0이 이 구성을 지원하는지 먼저 확인한다).

### 6. [권장] 사전 등록 대조를 하위 예측 단위로 적는다

- 위치: 부록 E "four of five held, and the fifth (1P1D with an 8,192-token prefill chunk passing 4 requests/s per GPU) did not".
- 문제: 예측 4의 후반("GPU당 4건(시드 10000)은 경계(0.85~0.95)")은 1.000으로 빗나갔다. 예측 1의 "1,024보다 높지는 않음"은 청크 512를 GPU당 5에서 재지 않아 판정할 수 없다. 빗나간 두 하위 예측은 모두 분리에 유리한 방향이다. 이 점도 적어야 공정하다. 사전 등록의 가치는 빗나간 것까지 세는 데 있다.
- 조치: "All but two sub-predictions held; both misses concerned 1P1D at 4 requests/s per GPU (31B chat passed where we predicted borderline; 26B with an 8,192-token prefill chunk was borderline where we predicted a pass), and the claim that 512-token replicas would not exceed 1,024-token ones was not tested." 하위 예측 수를 세어 함께 적는다. RESULTS.md 해석 절의 FP8 30 ms "0.5·1 모두 1.000"도 GPU당 1 0.958로 고친다.

### 7. [권장] 경계 표기와 원가 비교를 대칭으로 맞춘다

- 26B 1P1D GPU당 4(0.885/0.954/0.992, 구간 0.873–0.992)는 "borderline"으로 쓰면서, 31B 1P1D GPU당 4(0.903/0.924/1.000, 구간 0.887–1.000)는 표 2와 초록에서 경계 표시 없이 "4"로 쓴다. 두 점 모두 구간이 0.9를 포함한다. 좌장 A11의 수치 정의("any repeat within 0.85–0.95, or a repeat-level interval that contains 0.9")를 본문에 넣고 두 점 모두 경계로 표시한다.
- 표 2의 원가 $0.38 대 $0.63(1.66배)은 1P1D의 지원 부하 3을 쓴다. 반복 평균 규칙이면 1P1D는 GPU당 4에서 굿풋 1,847 토큰/s/GPU, 원가 약 $0.51로 1.33배다(`r1_e9_extra.py` 4절, 추정 아닌 재계산). 두 값을 함께 적으면 격자 한 칸의 효과가 드러난다.
- 반복 평균 규칙의 민감도(좌장 A11)를 부록에 한 줄로 싣는다. 결과는 위 강점에 적은 대로 견고하다.

### 8. [권장] 관련 연구: 이 결과가 직접 답하는 주장을 인용한다

- vLLM 문서(refs.bib의 `vllmdocs`, 본문에는 인용하지 않았다)는 "Disaggregated prefill DOES NOT improve throughput"라고 쓰고, 분리의 동기로 꼬리 ITL 제어를 들며 이를 청크 크기를 손으로 조정하는 것보다 믿을 만하다고 설명한다. 이 논문은 바로 그 주장을 클라우드 TCP에서 시험했다. 인용하고 결과로 답하는 한 문장을 넣는다.
- TaiChi 서술: 원문은 prefill-heavy와 decode-heavy 인스턴스를 두고, 세 슬라이더가 두 인스턴스의 비율과 청크 크기를 조절한다고 쓴다. "combines aggregated and disaggregated instances"는 원문에 맞게 고친다. TaiChi의 결론("disaggregation excels for strict TPOT and relaxed TTFT")과 이 논문의 결과(조정 청크 복제본이 30 ms 최대 간격에서도 우세)는 방향이 다르다. 차이의 후보(평균 TPOT 대 요청별 최대 간격, 빠른 인터커넥트, 모델과 규모)를 한 문장으로 적는다.
- DistServe는 청크 프리필 계열(DeepSpeed-MII SplitFuse)을 기준선으로 두고 분리가 이긴다고 보고했다. 이 결과와의 차이도 한 줄 적는다.
- SARATHI(청크 프리필 제안), Sarathi-Serve(stall-free 배칭과 청크 크기 절충), EcoServe(상용 인터커넥트 클러스터, 부분 분리) 서술은 원문과 맞는다.

### 9. [권장] 좌장 필수 항목 중 남은 문구

- E4에서 NIXL 스레드를 16으로 올려도 전송률이 같았다는 결과를 §4.5에 한 문장으로 넣는다(A7). 1,024 디스크립터 하한이 예측하는 결과다. 다만 동시 전송이 쌓이는 부하에서는 스레드 수가 다르게 작용할 수 있으므로(약점 3의 지속 11 Gbps), 부하에서는 시험하지 않았다고 적는다.
- 그림 5(c) 캡션에 표본 간격(0.1 s)이 26B 전송(73–93 ms)보다 길다는 한계를 적는다(A7).
- §3.3과 부록 B의 "passes only when images, audio, and video are all disabled"를 시험한 조합으로 좁힌다(A10).
- §4.7의 "then received a burst of tokens"는 GC형 사건에만 붙인다(A5).
- 결론의 "Its benefit, keeping other requests' prefills out of the decode steps, is also what chunked prefill provides"는 정확하지 않다. 청크 프리필은 프리필을 스텝에서 빼는 것이 아니라 스텝마다 크기를 제한한다. 문안: "Chunked prefill bounds, rather than removes, the prefill work in each decode step; with a well-chosen chunk that bound was enough in every SLO cell we could decide."
- 한계 절의 "decode node limited to 256 sequences"는 실제로 묶이지 않았다는 사실을 함께 적으면 반론을 미리 막는다. D 노드 실행 중 요청은 GPU당 4에서 최대 106–111, 5에서 최대 213이었다.

## 사소한 지적

- 표 2 FP8 행: 1P1D는 E7 시험 프록시 한 런씩, 복제본은 E8·E9 한 런씩으로 날짜가 다르다. 캡션에 적는다(2차 사소 지적, 미반영).
- 표 2 31B 복제본 "≥8"은 GPU당 8의 한 런이다(최대 간격 p90 44.4 ms). GPU당 6 런(E8, 0.998)은 상한 도달로 제외돼, 4와 8 사이에 감사 통과 런이 없다. 캡션이나 본문에 적는다.
- §4.4의 "512-token replicas passed 3 requests/s per GPU"(30 ms)는 한 런이다. 표 F1에 이 점(26B 512, GPU당 3, 30 ms, 1.000)을 추가한다. 30 ms 칸의 판정을 정하는 점이다.
- E9에서도 복제본 프록시(rr_proxy)는 계측하지 않았다. 복제본 쪽 프록시 멈춤이 있었다면 복제본에 불리하게만 작용한다는 점을 한 줄 적는다.
- 기여 목록의 "the reference proxy"는 "vLLM's test proxy for NIXL"로 쓴다.
- 한계 절에 출력 512 고정(요청이 멈춤에 노출되는 시간이 길다)과 무작위 토큰 입력(MoE 전문가 라우팅이 비현실적일 수 있다)이 여전히 없다(1·2차 사소 지적).
- §3.6의 주의 런 사유: E5 26_B3 대화 GPU당 16은 좌장 확인에서 진행 중 최대 1,680으로 연결 상한이 원인이었다. safe_runs.csv는 여전히 "클라이언트 프록시 한계 구간"이다. 제외되는 것은 같으므로 판정 영향은 없다.
- §4.2의 31B 구간 "none above 800"은 "almost none (1 of 323)"이 정확하다(좌장 A9).
- 부록 A 도입부의 "Rates printed inside them are totals"는 좋다. 그림 A2·A4의 부제에도 같은 표기가 필요한지 확인한다.

## 질문

1. v0.30.0에서 디코드 노드의 API 서버 프로세스를 늘릴 수 있는가? 늘리면 31B GPU당 6과 26B GPU당 5의 엔진 밖 간격(프록시 4,496 대 엔진 348)이 줄어드는가?
2. P 청크 2,560에서 세그먼트만과 7변수 묶음을 GPU당 4·5로 비교하면 전송 시간은 어떻게 되는가? E9의 느린 전송은 UCX 설정 탓인가, P 8,192가 전송을 쌍으로 내보낸 탓인가?
3. 26B 전송이 여러 건 겹칠 때 연결별 바이트 몫은 어떤가? 조각이 앞쪽 워커 두세 개에 몰려 네 연결을 다 쓰지 못하는가? 지속 11 Gbps와 단일 31B 전송의 19–21 Gbps 사이의 차이는 어디서 오는가?
4. 청크 512를 GPU당 5(또는 4.5)에서 재면 추정한 처리 한계(약 4.5 req/s/GPU)가 맞는가?
5. 16K 입력에서 청크 1,024 복제본(대기 전 프리필 약 0.7 s로 추정)과 조정한 1P1D를 비교하면, 절차 3의 부등식이 분리를 고르는 첫 지점이 되는가?
6. 31B 대화의 1:1 불균형(P SM 32–41%)을 고려하면, GPU 세 대에서 1P2D 대 조정 청크 복제본 세 대 비교는 결과를 바꿀 수 있는가?

## 점수

- 점수: 4 / 5 (accept with minor revisions, 실무자용 프리프린트 기준). 2차 3점에서 올린다. 2차 필수 1–3을 사전 등록한 측정으로 해결했다. 결론은 판정 규칙과 반복 구조에 견고하다. 결론의 방향을 흔드는 약점은 남아 있지 않다.
- 남은 필수 네 항목(판정 불가 칸의 범위 표현, 절차 2의 처리량 비용, E9-5의 UCX 동시 변경과 전송 병목, 구조 문장의 근거 지표)은 모두 원고 수정과 기존 데이터로 해결된다. 새 측정은 필요 없다. 권장 2·3번의 짧은 측정(세그먼트 대 7변수 교란 분리, D API 프로세스)은 논문의 RQ2를 강하게 만들지만 공개 조건은 아니다.
- 확신도: 4. 서버 지표, 전송 로그, 히스토그램, 판정 코드를 직접 재계산했다. 청크 512의 처리 한계는 선형 맞춤에 의한 추정이다. API 프로세스 해석은 엔진과 프록시 기록의 차이에서 나온 추론이며, 대기 사유 라벨은 순서를 가정했다.
