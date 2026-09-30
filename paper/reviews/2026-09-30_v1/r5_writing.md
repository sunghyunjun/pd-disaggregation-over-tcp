# Reviewer 5 (2차): 영어 문장, 구조, 그림·표

대상: "Chunked Prefill or Disaggregation? Prefill–Decode Serving over TCP on Single-GPU Cloud Instances" (paper/en/main.tex, main.pdf 22쪽, draft v1 2026-09-30)
근거: main.tex 전문, PDF 22쪽 전부(본문 그림 7개는 200 dpi로 따로 렌더링), figures_v1/*.svg 텍스트 추출, 1차 리뷰 r5_writing.md, 좌장 r6_chair.md(C절, A11·A12), main_v0.tex. 저장소는 읽기만 했다.
그림 번호는 v1 기준이다. v0 → v1 대응: v0 그림 6·7 → A4·A5, 그림 4·5 → A2·A3, A2 → A9, A4 → A6, A5 → A7, A6 → A8. v0 그림 8·9·A7은 v1 그림 4로 대체됐다.

## 요약

v1은 논문의 질문을 "RDMA 없이 분리가 이득인가"에서 "청크 프리필과 분리 중 무엇을 고를까"로 바꿨다. 두 기준선(청크 2,560 복제본, 최적 청크 복제본)을 함께 보고하고, 모의 리뷰 때문에 결론이 뒤집혔다는 사실까지 밝혔다. 이 정직함이 논문의 가장 큰 자산이 됐다. 1차에서 지적한 초록 모순, "chat SLO" 명명, 정확성 결과 누락, 데이터 선별 산식, 50 ms 정당화는 모두 고쳐졌다. 본문 텍스트의 요청률도 GPU당으로 통일됐다.

남은 문제는 네 가지다.
1. 부록 그림과 그림 5 부제에 전체 요청률이 그대로 남아 있다. 그림 A7 제목("Repeats only disagree near the 0.9 threshold")은 1차에서 [필수]였는데 고쳐지지 않았고, 이제 고쳐진 §3.6 본문과도 어긋난다.
2. 초록이 약 260단어로 v0(246)보다 길어졌다. 핵심 수치 몇 개에 한정어가 빠졌다. "about 3×"에는 워크로드가, "the only option"에는 측정한 청크 범위가, "9.5 Gbps per-flow cap"에는 placement group 조건이 없다.
3. 본문과 그림 4가 어긋나는 문장이 있다. RQ1 답("almost in proportion"), 체크리스트 1("It equals… one full chunk"), RQ3 답("as a default Gemma 4 deployment is")처럼 데이터보다 넓게 일반화한 문장도 있다.
4. 부록 그림 9개가 본문에서 한 번도 참조되지 않는다. Results의 순서도 RQ 번호와 맞지 않는다(RQ1 → RQ3 → RQ2).

모두 원고와 그림 라벨만 고치면 해결된다.

## 1차 지적 반영 점검

| 1차 항목 | 판정 | 근거 |
|---|---|---|
| 1. 초록 모순("chat no gain" vs 31B, "50–75 ms wins" vs 26B FP8 chat) | 반영 | 초록을 새로 썼고 두 모순 문장은 사라졌다. 새 초록에 한정어가 빠진 곳은 주요 약점 2에 적었다. |
| 2. 요청률 단위 혼용 | 부분 반영 | 본문은 §3.4 "We report rates per GPU unless stated otherwise"로 통일했고, 전체 요청률에는 "in total"을 붙였다(§4.8 trace). 본문 그림 2·3·4·6·7도 GPU당이다. 그런데 그림 5 부제("0.5 and 0.25 requests/s")는 전체 요청률이다. A1 부제 "0.5 req/s", A2 부제 "0.5 req/s", A7 행 라벨 14개, A8 x축 "0.25/0.5 req/s", A9 제목 "1 req/s"도 전체 요청률인데 캡션에 밝히지 않았다. A3과 A6은 캡션에 "totals"라고 밝혔다. |
| 3. "chat SLO" 명명 | 반영 | strict/relaxed SLO로 바꿨고, 그림에도 "Strict-SLO attainment"와 "(a) Strict SLO (1 s / 50 ms)"를 썼다. "chat SLO"는 SVG 텍스트까지 0건이다. 남은 것은 "budget" 혼용(그림 1 "50 ms budget", A1 "TTFT budget 1 s", 본문 4회)과 그림 3의 y축이 "Strict-SLO attainment"가 아닌 점이다. |
| 4. 정확성 검사 결과 | 반영 | §4.8 Correctness에 31B 일치, 8/8 바이트 일치, 26B 게이트(0.40, 보정 ≥0.58/≤0.17), 전원 통과를 적었다. 문장이 길고 "late … (30–160 characters in)"가 모순처럼 읽힌다(교정 제안 참조). |
| 5. 1.5–4× 유도 | 반영(대체) | 헤드라인이 "about 3×"로 바뀌었고 §4.3과 표 2에서 3 대 1로 유도된다. 격자 분해능은 §6에서 "resolved to 1 request/s per GPU"로 밝혔다. 다만 3×가 격자 값의 비라는 점은 초록에 없다. |
| 6. 데이터 선별 서술 | 반영 | "All reported runs", 122+5+1=128, 436−128−5=303이 모두 명시됐다. "1 discarded run"의 폐기 사유는 여전히 없다(사소). §3.6의 ±0.09 문장은 고쳐졌지만 그림 A7 제목은 그대로다(아래 [필수] 1). |
| 7. 참고문헌 | 부분 반영 | arXiv 번호 출력, {McAllister}, 제목 대소문자(Beyond the Buzz, Prefill-as-a-Service, Gemma 4 model card), 연도 중복을 고쳤다. EcoServe의 OSDI 26 제목과 게재는 USENIX 페이지에서 확인했다. 남은 것: [1] Sarathi-Serve의 저자 절단과 페이지 누락, 저자 표기 혼용("et al." 1인·3인 뒤 절단 vs 전원), 접근일 표기는 [5][6][7]에만 있음, [6] "Elastic fabric adapter"와 "user guide"의 소문자화, [25] "2026. Published June 23.", PR #56874는 각주이고 Issue #52607은 참고문헌인 불균형. |
| 8. RQ 순서, RQ 답과 체크리스트 중복 | 부분 반영 | 중복은 해소됐다(§5.1은 짧은 답, §5.2는 절차). 순서는 여전히 어긋난다. RQ1은 §4.2, RQ3은 §4.3–4.4, RQ2는 §4.5–4.6에서 답한다. |
| 9. §4.8 잡탕 | 대부분 반영 | push와 PR #56874가 §4.5로 옮겨졌고, 비용 절은 표 2로 흡수됐다. §4.8 첫 줄에 "sessions before E8 … 2,560-token replicas" 경고를 달았다(좋은 처리다). 부록 B는 여전히 본문에서 참조되지 않는다. |
| 10. 도입부 결과 미리보기, 초록 길이 | 미반영 | 도입부는 "That sweep changed the paper's conclusion"이라고만 하고 결론을 말하지 않는다. 초록은 약 260단어(12문장)로 오히려 길어졌다. 제목 질문에 대한 한 문장 답("choose the chunk first…")은 결론에만 있다. |
| 11. 용어 통일 | 부분 반영 | replicas/colocated, strict/relaxed, per-flow cap, TTFT limit은 크게 나아졌다. 남은 것: 본문 "longest gap" 대 그림 "max gap"(그림 2·3·4), "gap limit"(9회) 대 "stall limit"(4회), "budget"(본문 4회·그림 2개), "NIXL's four connections"(기여, RQ2, §5.3, 결론) 대 "four worker threads of vLLM's NIXL connector"(§4.5), "reference proxy"(기여) 대 "test proxy"(10회), "Rep ×2"(A6) 대 "Replicas (2)". SLO는 본문 어디에서도 풀어 쓰지 않았다(첫 사용이 RQ3). UCCL, NIXL, UCX, ENA Express도 풀이가 없다. "pull-based connector"는 §3.1에서 정의됐다(반영). |
| 12. 비용 표 상한·하한, 가격 | 대부분 반영 | 표 2에 ≥/≤와 g7e 단가가 들어갔고, 표 1에 $/hour 열이 생겼다. 네트워크 대역폭 열은 없다. g7 가격은 "–"인데 이유가 없다. 표 2의 31B chat 1P1D "4"에는 표 자신의 규칙대로 "≥"가 붙어야 한다. |
| 13. 같은 조건 수치 불일치, 유효숫자 | 반영 | 267/269 문제는 267 하나로 정리됐고, 유효숫자도 정돈됐다. |
| 14. 임계값 정당화 비대칭 | 반영 | §3.5에 사전 등록 5×스텝에서 절대 50 ms로 바꾼 이유와 "five times the 26B decode step on the slowest GPU"를 넣었다. |
| 그림 글자 크기 | 부분 반영 | 본문 새 그림은 인쇄 크기 최소 약 6pt다(그림 4 눈금 6.0pt, 그림 5 6.0pt). 그림 6 행 라벨은 5.8pt, 그림 7 GC 라벨은 5.6pt다. 부록은 A7 행 라벨 5.1pt, A3 막대 값 5.0pt, A6 x 라벨 5.4pt로 1차와 같은 수준이다. |
| 그림별 1차 지적(v0 → v1) | 부분 반영 | 반영: 그림 4에 "best configuration of each kind" 명시, 본 논문 SLO 윤곽 굵게, "Similar" 범주가 실제로 쓰임, 그림 A1 5 Gbps 점. 미반영: A7 제목(1차 [필수]), A8 주황 단일 계열과 "not the SLO", A9 범례가 "0.84" 라벨과 겹침, A5(b) 범례를 0.9 점선이 관통, A4(b) 판정 제외 점까지 선 연결, A6 "Rep ×2", A1·A2 범주형 x축의 등간격 연결선, 그림 1 단일 노드 마커 미분리. |
| 기타 형식 | 부분 반영 | 제목 줄바꿈 문제는 새 제목으로 해소됐고, xurl이 추가됐다. Acknowledgments는 여전히 감사 대상 없이 비용만 적었다. 표 E1(구 C1)의 "26B FP8, 31B FP8" 중의성이 남았다. |

## 강점

- 새 제목과 도입부 첫 문단이 두 해법(chunked prefill, disaggregation)을 같은 문제에 대한 두 답으로 소개한다. 1쪽 만에 논문이 무엇을 비교하는지 분명하다.
- "A mock peer review of our first draft pointed out that this baseline was untuned … That sweep changed the paper's conclusion, and we report both baselines." 같은 서술은 드물게 정직하다. 그림 4의 위·아래 행(청크 2,560 대 최적 청크)이 이 정직함을 그림 한 장으로 보여 준다.
- 그림 2(v1_chunk_stall)는 10초 테스트를 통과한다. 청크가 줄면 최대 간격이 줄고, 50 ms선 위아래가 명도로 갈린다. 메커니즘 그림으로 좋다.
- 과장이 크게 줄었다. "almost entirely"는 "61% … 76% … 85%"와 분자·분모로 바뀌었다. 식 1은 아핀으로 고쳐졌고, 식 2는 "low-load estimate"로 한정됐다. "The repository history cannot prove that order"라고 적었고, 크레딧 논증도 계산으로 바꿨다.
- §3.5의 "one long pause in a 500-token answer is 0.2% of its gaps and vanishes from percentile statistics, yet it is the pause a user sees"는 지표 선택을 한 문장으로 정당화하는 좋은 문장이다.
- 사전 등록 이탈 부록(D)과 한계 목록이 구체적이다. §4.8 첫 줄의 조건 경고도 좋은 처리다.
- 색은 계속 파랑(복제본)과 주황(분리)의 의미 체계를 지킨다. 명도와 선 모양, 마커로도 이중 부호화했다.

## 주요 약점

1. **[필수] 그림 속 전체 요청률 잔존과 그림 A7 제목**
   - 논문은 §3.4에서 "We report rates per GPU unless stated otherwise"라고 선언했다. 그런데 다음 그림 텍스트는 전체 요청률이고, 캡션에도 밝히지 않았다.
     - 그림 5 부제 "(0.5 and 0.25 requests/s)": 캡션은 0.25와 0.125 per GPU다.
     - A1 부제 "4K input at 0.5 req/s": 캡션은 0.25 per GPU다.
     - A2 부제 "0.5 req/s": 캡션은 0.25 per GPU다.
     - A7 행 라벨 14개: 예를 들어 "26B NVFP4 replicas (2) · 4K · 4 req/s"는 §4.3의 "failed at 2 (0.37–0.64 in five runs)"와 같은 점이다.
     - A8 x축 "0.25 req/s / 0.5 req/s": TTFT 약 850 ms로 보아 GPU당 0.125/0.25다.
     - A9 제목 "4K input at 1 req/s": 캡션은 0.5 per GPU다.
   - A3과 A6은 캡션에서 totals라고 밝혔지만, 선언한 규칙과 어긋나므로 GPU당으로 바꾸기를 권한다(A3: 0.5/1/8, A6: 2.0/2.0/1.9/1.85 등).
   - 그림 A7 제목 "Repeats only disagree near the 0.9 threshold"는 그림 자체(0.47–0.64, 전날 0.37)와 §3.6 수정 문장("low points varied more (0.37–0.64)")에 모두 어긋난다. "Disagreement flips a verdict only near 0.9"로 고쳐야 한다. 1차에서도 [필수]였다.

2. **[필수] 초록: 한정어 누락과 길이**
   - "Against replicas at a 2,560-token chunk, disaggregation served about 3× more requests per GPU under a 50 ms gap limit." 3×는 26B NVFP4 4K에만 해당한다. 26B FP8과 31B chat에서는 청크 2,560 복제본이 한 점도 통과하지 못했다. 워크로드를 적어야 한다. TTFT 1 s 조건도 초록 어디에도 없다.
   - "Disaggregation remained the only option when the gap limit was tighter than chunking reached": 26B의 1,024 미만 청크는 측정하지 않았다(§4.4 caveat, §6). "the only configuration that passed among the chunks we measured"로 한정해야 한다.
   - "lifted it 1.5–1.8× above the 9.5 Gbps per-flow cap": 9.5 Gbps는 placement group 안의 값이다. 밖에서는 4.97 Gbps다(§3.1). 초록과 도입부 어디에도 placement group이 나오지 않는데, 본문 결과는 모두 placement group 조건이다.
   - "so their longest gap is set by the chunked-prefill size": 31B chat에서는 청크보다 짧은 프롬프트 길이가 간격을 정한다(§4.2). "bounded by"가 정확하다.
   - "NIXL spread each transfer": 네 연결은 vLLM NIXL 커넥터의 워커 스레드에서 나온다(§4.5).
   - 길이는 약 260단어, 12문장으로 v0보다 길다. 제목 질문에 대한 답(결론의 "choose the chunk first, and disaggregate when no acceptable chunk meets the stall limit")이 초록에 없다. 대신 전송 세부(8 KB, 3.4×, 네 연결)가 마지막 두 문장을 차지한다. 아래에 약 220단어 재작성안을 붙인다. 수치는 본문과 대조했지만, 저자가 다시 확인해야 한다.

   > Prefill–decode (PD) disaggregation is usually deployed over RDMA or NVLink; the cheapest single-GPU cloud instances have neither. We ask when disaggregation over TCP beats colocated replicas that use chunked prefill. On AWS 2xlarge instances in a cluster placement group, we served Gemma 4 26B (mixture of experts) and 31B (dense) with stock vLLM and NIXL/UCX over TCP, and judged each request by its time to first token (TTFT) and its longest gap between output tokens. A replica stalls for one scheduler step whenever another request's prefill joins that step, so its chunk size decides the comparison. Under a 1 s TTFT and 50 ms gap limit, disaggregation served about 3× more requests per GPU than replicas at a 2,560-token chunk for 26B with 4K inputs, and only it passed for 26B FP8 and 31B chat. Against replicas at the best chunk we measured (1,024 or 256 tokens), it served the same or less with a later first token, and won only at gap limits of 30–40 ms that no measured chunk reached. Its TTFT cost is mostly the KV transfer, which a larger UCX TCP segment sped up 3.4× and four parallel connections lifted above the per-flow cap. Tune the chunk first; disaggregate only when no acceptable chunk meets the gap limit. We release the harness and per-request data.

3. **[필수] 본문 서술과 그림·수치의 불일치**
   - §4.4 둘째 항목 "the two are similar at 75 ms and above for 26B"는 그림 4 아래 행과 다르다. 26B NVFP4에서 "similar"는 TTFT 1 s 이상에서만 나타나고, 0.5–0.75 s에서는 모든 간격 한계에서 "replicas serve more"다. 26B FP8은 50 ms 이상이 대부분 "cannot tell"이다. "at 50 ms for 26B NVFP4"도 TTFT 1 s 이하에서만 성립한다(1.5 s 이상은 similar).
   - 표 1 캡션 "All main-text results come from g7e"는 사실이 아니다. §4.5의 첫 튜닝 세션(626 → 466 ms)과 호스트 스테이징, §4.8의 input length는 g7이다. 그림 1은 모든 GPU의 감사 통과 런을 모았다.
   - §3.1 "one of them, the TCP segment size, accounts for the whole gain"은 부록 C "the two segment sizes alone"과 어긋난다. UCX 변수 일곱 개 중 둘(TX, RX)이다.
   - §3.2 "we convert them to Gbps as MiB × 8 × 1.048576/s"는 단위가 틀렸다. 이 식은 Mbit/s를 준다. "1 MiB = 8.39 Mbit"로 쓰면 된다.
   - §4.5 "468–533 MB … against 560 for pull"만 MB로 남았다. §3.2 규칙대로 MiB로 써야 한다.
   - 표 2의 31B chat 1P1D "4 (aiohttp proxy), ≤$1.67"에서 비용에는 ≤가 붙었는데 부하에는 ≥가 없다. 1P1D는 4에서만 측정했다(§4.4). "≥4"로 써야 표 자신의 캡션 규칙과 맞는다.
   - §3.6은 "For decisive points we report 95% intervals"라고 약속하지만, 논문 전체에 구간은 하나뿐이다(§4.3 "interval 0.950–0.997"). 표 2의 통과 한계와 첫 탈락 점, 그리고 §4.3의 "passed 4 only narrowly (0.903 and 0.924)"에 구간을 붙이거나, 약속 문장을 줄여야 한다.
   - §3.6의 borderline 정의("points near 0.9")에 수치가 없다. 그림 A7은 0.85–0.95를 쓴다. 이 정의를 쓰면 §4.3 "replicas passed 1 request/s per GPU"(청크 2,560)도 borderline 표시 대상인지 확인해야 한다.
   - §4.2 31B 구간 서술이 "<200, 400–800, >800"이라 200–400 구간이 빠졌다.

4. **[필수] 데이터보다 넓은 일반화** (과장 목록에도 적었다)
   - RQ1 답의 "Shrinking the chunk shortened it almost in proportion": 청크가 2.5배 줄 때 간격은 1.7배 줄었다(48 → 28 ms). 비례가 아니라 고정 디코드 스텝을 포함한 아핀 관계다. "roughly linearly"로 고쳐야 한다.
   - RQ1 답의 "A replica's longest gap is the time of a step that carries a full chunk"와 체크리스트 1의 "It equals the time of a step carrying one full chunk": 4K 입력에서만 참이다. 채팅에서는 같은 복제본에 겹친 가장 긴 프롬프트가 정한다(§4.2 자신의 결과).
   - RQ3 답의 "Against replicas stuck at a 2,560-token chunk, as a default Gemma 4 deployment is": 본문 근거가 없다. §3.3은 "2,496 미만을 거부한다"까지만 말한다. vLLM의 기본 `max-num-batched-tokens`가 2,560도 아니다. "close to the minimum vLLM v0.30.0 allows for Gemma 4 unless every modality is disabled"로 바꿔야 한다.
   - 결론의 "is exactly what chunked prefill provides by other means"는 논문 자신의 30 ms 결과(청크로는 도달하지 못하고 분리만 통과)와 모순된다.

5. **[필수] 부록 그림 9개와 부록 B가 본문에서 참조되지 않음**
   - `\ref{fig:bwsweep|inputlen|quant|scale26|scale31|trace|repeat|push|gpuspeed}`가 본문에 0회다.
   - 대응 문장이 이미 있다. §4.6 tc 1 Gbps → A1, §4.8 Input length → A2, Weight precision → A3, Three nodes → A4·A5, Real trace → A6, §3.6 repeats → A7, §4.5 push → A8.
   - A9(GPU별 비교)는 v0의 "Faster GPUs" 문단이 사라진 뒤 본문 대응이 전혀 없다. 표 1의 g6e "cross-GPU comparison"도 이 그림 하나로만 남았다. 한 줄로 본문에 연결하거나, 이 그림을 뺄지 결정해야 한다.
   - 부록 B(Practical pitfalls)는 기여 3("three pitfalls")에서 연결하기를 권한다.

6. **[권장] Results 순서와 RQ 번호, 전방 참조**
   - 현재 흐름은 4.1 → 4.2(RQ1) → 4.3–4.4(RQ3) → 4.5–4.6(RQ2) → 4.7 → 4.8이다.
   - §4.3은 aiohttp 프록시와 1P1D의 borderline 원인에 기대는데, 그 설명은 §4.7에 있다. §4.4의 "disaggregation's TTFT, which includes an 80–300 ms transfer"는 §4.6에 기댄다.
   - 권고: RQ2와 RQ3의 번호를 바꿔 서술 순서에 맞추고, §4.7(프록시 정지)을 §4.3 바로 뒤로 옮긴다. 그러면 "head-to-head → 1P1D가 4에서 흔들린 이유 → SLO 지도 → 전송 → TTFT 비용"이 된다. 헤드라인은 앞에 두고 전방 참조는 하나(TTFT 0.25 s 행)만 남는다.

7. **[권장] 도입부에 결과가 없음**
   - 도입부 셋째 문단은 "That sweep changed the paper's conclusion"에서 멈춘다. 독자는 2쪽까지 읽어도 무엇이 바뀌었는지 모른다.
   - 기여 목록 앞에 두세 문장을 넣기를 권한다. 예: "Against replicas at the chunk size our stack first accepted, disaggregation over TCP served about 3× more load per GPU. Against replicas with a tuned chunk it served the same or less and always reached the first token later; it won only when the gap limit was tighter than any chunk we measured could reach."

8. **[권장] 용어 통일(남은 것)**
   - 간격: 본문 "longest gap", 그림 "max gap"(그림 2 y축, 그림 3 y축, 그림 4 x축과 범례). 그림을 "Longest gap (ms)"와 "Longest-gap limit (ms)"로 맞춘다.
   - 한계: "gap limit"과 "stall limit"을 "gap limit" 하나로 쓴다. "budget"(§4.6 "a 1 s budget", 체크리스트 3 "TTFT budget", 그림 1·A1)은 "limit"으로 쓴다.
   - 멈춤: 요청별 "stall"과 전역 사건("global events", "global stalls", "proxy stalls")을 구분한다. 전역 사건은 "global pause"로 통일하기를 권한다.
   - 연결: "NIXL's four connections"와 "NIXL's thread count"를 "the four worker threads of vLLM's NIXL connector"로 통일한다. 기여 목록의 "reference proxy"는 "vLLM's test proxy for NIXL"로 바꾼다.
   - 약어: SLO를 첫 사용(RQ3)에서 "service-level objective (SLO)"로 풀어 쓴다. UCX, NIXL, UCCL은 첫 사용에서 한 구절로 설명한다. 표 E1의 "KV matching"(그림 A7의 "KV matched")은 본문에 정의가 없다.
   - 복제본 표기: RQ3의 "tuned colocation"은 "replicas with a tuned chunk"로, A6의 "Rep ×2/×3"은 "Replicas (2)/(3)"로 쓴다.

9. **[권장] 그림 가독성과 겹침**(그림·표별 지적 참조): 그림 3(b)의 파랑 선 가림, 그림 5(b) x 라벨 충돌, 그림 7의 GC 선과 주황 스파이크 겹침, A4·A5·A9의 범례 겹침, 부록 5pt대 글자.

10. **[권장] 참고문헌과 LaTeX 형식**
    - `\texttt{--limit-mm-per-prompt}`가 PDF에서 "–limit-mm-per-prompt"(en dash 하나)로 찍힌다(pdftotext로 확인). `\texttt{-{}-limit-mm-per-prompt}`로 써야 한다. 명령행 인자라 독자가 그대로 복사할 수 있으므로 중요하다.
    - 표 E1의 p열이 양쪽 정렬돼 "26B      NVFP4/FP8,"처럼 벌어진다. `>{\raggedright\arraybackslash}p{…}`를 쓴다.
    - 부록 A 제목이 두 줄로 넘어간다. "Additional figures (pre-E8 sessions, 2,560-token replicas)"처럼 줄인다.
    - 참고문헌의 남은 항목은 1차 반영 점검 표 7행에 적었다. [15] TaiChi는 제목에 시스템 이름이 없어 본문의 "TaiChi"와 연결되지 않는다. `note = {TaiChi}`나 제목 뒤 "(TaiChi)"를 붙인다.
    - Acknowledgments는 "Funding"으로 바꾸거나, 감사 문장을 넣는다.

## 문장 교정 제안

| 위치 | 원문 | 제안 |
|---|---|---|
| 초록 | so their longest gap is set by the chunked-prefill size: for 26B with 4K-token inputs it fell from 48 to 28 ms as the chunk shrank from 2,560 to 1,024 tokens. | so the chunked-prefill size bounds their longest gap: for 26B with 4K-token inputs, shrinking the chunk from 2,560 to 1,024 tokens cut the median longest gap from 48 to 28 ms. |
| 초록 | Against replicas at a 2,560-token chunk, disaggregation served about 3× more requests per GPU under a 50 ms gap limit. | Under a 1 s TTFT and 50 ms gap limit, disaggregation served about 3× more requests per GPU than replicas at a 2,560-token chunk for 26B with 4K inputs, and only it passed for 26B FP8 and 31B chat. |
| 초록 | for 26B with 4K inputs, 3–4 requests/s per GPU against the replicas' 4; for 31B chat, 4 against at least 6. | for 26B with 4K inputs, 3 (borderline at 4) requests/s per GPU against the replicas' 4; for 31B chat, at least 4 (the highest rate measured) against at least 6. |
| 초록 | Replicas also always delivered the first token sooner. | In every configuration we measured, replicas also delivered the first token sooner. |
| 초록 | Disaggregation remained the only option when the gap limit was tighter than chunking reached (30 ms for 26B, 30–40 ms for its FP8 variant). | Only disaggregation passed when the gap limit was tighter than any chunk we measured could reach (30 ms for 26B NVFP4, 30–40 ms for 26B FP8). |
| 초록 | UCX's default 8 KB TCP segment slowed that transfer 3.4×, and NIXL spread each transfer over four TCP connections, which lifted it 1.5–1.8× above the 9.5 Gbps per-flow cap. | Raising UCX's TCP segment from its 8 KB default to 256 KB sped that transfer up 3.4×, and vLLM's NIXL connector spread it over four TCP connections, lifting it 1.5–1.8× above the 9.5 Gbps per-flow cap inside a placement group. |
| 초록 끝(추가) | (없음) | Tune the chunk size first, and disaggregate only when no acceptable chunk meets the gap limit. |
| 1장 3문단 | We first compared disaggregation against replicas at the chunk size our stack initially accepted. A mock peer review of our first draft pointed out that this baseline was untuned, so we added a session that swept the replicas' chunk size. That sweep changed the paper's conclusion, and we report both baselines. | Our first comparison used replicas at a 2,560-token chunk, the smallest our initial configuration accepted. An AI-assisted mock review of that draft flagged this baseline as untuned, so we ran another session that swept the replicas' chunk size. The sweep reversed our main conclusion, and we report both baselines. |
| RQ1 | what sets the stalls of colocated replicas, and how far does chunked prefill go? | what sets the stalls of colocated replicas, and how far can a smaller chunk shorten them? |
| RQ3 | serve more SLO-meeting load than tuned colocation? | serve more load that meets a service-level objective (SLO) than replicas with a tuned chunk size? |
| 기여 3 | and the reference proxy's garbage collection produces stalls that look like disaggregation's | and garbage collection in vLLM's test proxy for NIXL causes global pauses that are easily mistaken for a cost of disaggregation |
| 2장 | Our results reproduce that boundary on TCP-connected single-GPU nodes and add the chunk size as the variable that moves it. | We observe the same boundary on TCP-connected single-GPU nodes and measure how far the replicas' chunk size moves it. |
| 3.1 | Section 4.5 shows that one of them, the TCP segment size, accounts for the whole gain. | Section 4.5 shows that two of them, the TCP send and receive segment sizes, account for the whole gain. |
| 3.2 | vLLM reports these volumes as "MB"; they are mebibytes, and we convert them to Gbps as MiB × 8 × 1.048576/s. | vLLM labels these volumes "MB", but they are mebibytes (1 MiB = 8.39 Mbit), and we convert them accordingly. |
| 3.3 | With every modality disabled, a 2,560-token chunk failed at engine start, so the 2,560 control in E8 kept images disabled only. | With every modality disabled, however, a 2,560-token chunk failed at engine start, so the E8 control at 2,560 tokens disabled images only (Section 6 lists this difference). |
| 3.6 | Sessions E7 and E8 warmed every server with 30 requests; earlier sessions did not, which changed attainment by at most 0.019 when we dropped each run's first five requests. | Sessions E7 and E8 warmed every server with 30 requests. Earlier sessions did not; dropping the first five requests of their runs changed attainment by at most 0.019. |
| 3.6 | points near 0.9 varied by up to ±0.09 and could flip a verdict, and we call them borderline; low points varied more (0.37–0.64). | points near 0.9 varied by up to ±0.09, enough to flip a verdict; we call a point borderline if any repeat falls between 0.85 and 0.95. Points far below 0.9 varied more (0.37–0.64 at one point). |
| 4.2 | we could not tell whether the even split of a 4K input into two 2,048-token pieces or the different multimodal setting of the 2,560 control causes this. | we cannot tell whether splitting a 4K input into two full 2,048-token pieces or the different multimodal setting of the 2,560 control caused this. |
| 4.2 | when the longest prompt prefilled on the same replica during a request's decode had fewer than 200 tokens, 99–100% of requests kept every gap under 50 ms; with 400–800 tokens, 12% did; above 800 tokens, none did. A 512-token chunk therefore did not help | when the longest prompt that the same replica prefilled while a request was decoding had fewer than 200 tokens, 99–100% of requests kept every gap under 50 ms; with 200–400 tokens, [x]% did; with 400–800, 12%; above 800, none. A 512-token chunk still lets one step carry a 512-token prompt, so it did not help |
| 4.3 | Per GPU the two approaches support about the same load; the replicas deliver the first token in about 200 ms against about 500 ms for 1P1D at 4 requests/s per GPU; and at their supported loads the replicas cost $0.49 against $0.63 per million tokens. | Per GPU, the two approaches support about the same load. At 4 requests/s per GPU the replicas deliver the first token in about 200 ms, against about 500 ms for 1P1D, and at their supported loads they cost $0.49 per million tokens against $0.63. |
| 4.4 둘째 항목 | Replicas serve more at 40 ms for 26B NVFP4 and 31B chat, and at 50 ms for 26B NVFP4; the two are similar at 75 ms and above for 26B. | Replicas serve more at 40 ms for 26B NVFP4 and 31B chat. For 26B NVFP4 they also serve more at 50 ms with TTFT limits up to 1 s, and at every gap limit with TTFT limits of 0.5–0.75 s; with looser TTFT limits the two are similar. For 26B FP8 above 40 ms the map cannot decide. |
| 4.5 | Because the instance's aggregate bandwidth grows almost linearly with flows (Figure 5a), more connections, not other UCX settings, are the remaining lever; we did not test that. | Because the instance's aggregate bandwidth grows almost linearly with the number of flows up to 50 Gbps (Figure 5a), more connections are the likely remaining lever; the other UCX settings did not help, and we did not test more connections. |
| 4.5 | Staging the KV cache through host memory slowed TTFT 4.7× at 0.125 requests/s per GPU on g7 and had no stable load at 0.5. | Staging the KV cache through host memory raised TTFT 4.7× at 0.125 requests/s per GPU on g7 and could not sustain 0.5 requests/s per GPU. |
| 4.5 | its logged volume was 468–533 MB per request against 560 for pull, which we could not explain. | vLLM logged 468–533 MiB per request for push against 560 MiB for pull, a difference we cannot explain. |
| 4.6 | The residual, 28–87 ms, covers the decode node's first step, scheduling, and the proxy hop, and it would remain with RDMA. | The residual (28–87 ms) covers the decode node's first step, scheduling, and the proxy hop; RDMA would not remove it. |
| 4.6 | It also shows why long inputs fail: for 26B FP8 at 16K inputs, about 520 MiB take roughly 0.3–0.7 s on top of a prefill of about 0.8 s. We measured 1P1D's TTFT 465–506 ms above the replicas' there, beyond a 1 s budget. | The relation also explains why long inputs fail: for 26B FP8 at 16K inputs, the 520 MiB transfer adds roughly 0.3–0.7 s to a prefill of about 0.8 s. We measured 1P1D's TTFT 465–506 ms above the replicas', which puts it past the 1 s limit. |
| 4.7 제목 | A pitfall: proxy stalls that look like disaggregation's | A pitfall: proxy pauses that mimic disaggregation stalls |
| 4.7 | The test proxy therefore made our earlier disaggregated limits conservative, and it explains the collapse of our three-node 2P1D configuration | These global pauses therefore made our earlier disaggregated limits conservative, and they also explain the collapse of our three-node 2P1D configuration |
| 4.8 Correctness | long outputs diverged only in late, near-tied tokens (30–160 characters in) … calibrated at ≥0.58 for true pairs and ≤0.17 for swapped prompts | long outputs diverged only at near-tied tokens, 30–160 characters into the answer … (in calibration, outputs of the same prompt scored at least 0.58 and outputs of swapped prompts at most 0.17) |
| 5.1 RQ1 | Shrinking the chunk shortened it almost in proportion | Shrinking the chunk shortened it roughly linearly, though not in proportion, |
| 5.1 RQ2 | which the UCX segment size limits first and the per-flow cap times NIXL's connection count limits next | which is limited first by the UCX segment size and then by the per-flow cap times the effective number of busy connections, m |
| 5.1 RQ3 | Against replicas stuck at a 2,560-token chunk, as a default Gemma 4 deployment is, | Against replicas at a 2,560-token chunk, close to the minimum vLLM v0.30.0 allows for Gemma 4 unless every modality is disabled, |
| 5.2 항목 1 | It equals the time of a step carrying one full chunk. | With long inputs it equals the time of a step that carries a full chunk; with short prompts, the time of the step that carries the longest co-scheduled prompt. |
| 7장 | Its benefit, protecting decodes from other requests' prefills, is exactly what chunked prefill provides by other means. | Chunked prefill provides the same benefit, protecting decodes from other requests' prefills, to a degree set by the chunk size. |
| 7장 | which a single UCX setting and NIXL's parallel connections make far cheaper than the defaults suggest | which a larger UCX TCP segment and the connector's parallel connections make far cheaper than with default settings |

## 그림·표별 지적

인쇄 크기 기준 최소 글자(SVG 폭을 `\includegraphics` 폭으로 환산): 그림 1 5.5pt(음영 주석), 2 6.4pt, 3 6.7pt, 4 6.0pt, 5 6.0pt, 6 5.8pt, 7 5.6pt, A1 5.9pt, A2 6.5pt, A3 5.0pt, A4 6.2pt, A5 6.6pt, A6 5.4pt, A7 5.1pt, A8 6.7pt, A9 7.2pt. 본문 그림은 대체로 6pt 이상이다. 부록 A3·A6·A7은 6pt 이상으로 키우기를 권한다.

본문 그림의 회색 부제는 캡션과 거의 같은 말을 되풀이한다(그림 2·3·5·7). 1차에서 지적한 제목 형식 불일치는 "회색 부제 + 굵은 패널 제목"으로 통일됐다. 이제 부제의 요청률만 캡션과 맞추면 된다.

- **그림 1 (fig01)**
  - 음영 주석의 "50 ms budget"은 "limit"으로 바꾼다.
  - 1차 지적(단일 노드 마커 분리, x축 10¹/10² 표기, 그림 속 제목 = 절 제목)은 그대로다. 우선순위는 낮다.
- **그림 2 (v1_chunk_stall)**
  - y축 "Per-request max gap"은 본문 용어대로 "Per-request longest gap"으로 바꾼다.
  - (a)의 2,048 점은 다른 멀티모달 설정의 대조군과 비교된다는 교란이 있다. 본문에만 있으니 캡션에도 한 구절 넣는다.
  - (a)의 "50 ms" 라벨이 48 마커에 닿는다.
  - 청크 축은 범주형(비등간격)이라는 점을 캡션에 적거나, 1차 권고대로 표시한다.
  - 밝은 점 = 중앙값 > 50 ms라는 명도 부호화는 녹색약 독자에게도 안전하다. 좋다.
- **그림 3 (v1_head_to_head)**
  - 범례 7개 중 "chunk 1536"과 "chunk 512", "chunk 1024"와 "chunk 256"의 모양이 같다. 패널로만 구분된다. 패널별 범례나 선 끝 직접 라벨이 낫다.
  - (b)에서 청크 1,024 복제본(짙은 파랑)이 1P1D 사각형 뒤에 완전히 가려진다. 본문은 "both … passed"라고 하는데 그림에서는 한쪽이 보이지 않는다. x를 약간 어긋나게 두거나(dodge) 마커 크기를 달리한다.
  - (a) x=4에 네 계열이 겹쳐, 결정적 점인 1P1D aiohttp의 min–max(0.885–0.992)가 보이지 않는다.
  - y축 "Attainment (TTFT ≤ 1 s, max gap ≤ 50 ms)"는 다른 그림처럼 "Strict-SLO attainment"로 쓴다.
  - 본문의 "(Figure 3, dotted lines)"에 맞춰 캡션에 "dotted: 2,560-token replicas"를 넣는다.
- **그림 4 (v1_who_wins)**
  - 1차의 [필수](어떤 구성을 비교했는지)가 해결됐고, 두 행 구성이 논문의 새 이야기를 가장 잘 보여 준다.
  - 남은 것: 비율의 방향(분리 ÷ 복제본 SLO 굿풋)이 캡션에 없다. "Neither meets the SLO"는 거의 흰색이라 배경과 구분되지 않는다. 옅은 점무늬나 X 표시를 권한다.
  - x축 "Max-gap limit"은 "Longest-gap limit"으로, 범례 "TTFT 1 s, max gap 50 ms"는 "Strict SLO (1 s, 50 ms)"로 바꾼다.
  - 본 논문 SLO 셀에 비율(예: 위 행 3.0×, 아래 행 0.75×)을 적으면, 초록의 "about 3×"와 "same or less"가 그림에서 바로 읽힌다.
  - §4.4 서술과의 불일치는 주요 약점 3에 적었다.
- **그림 5 (v1_transfer)**
  - 부제 "(0.5 and 0.25 requests/s)"는 전체 요청률이다. "(0.25 and 0.125 requests/s per GPU)"로 고친다. (a)는 iperf라 "at low load"가 해당하지 않는다.
  - (b)의 x 라벨 "Segment 256 KB only"와 "Seven UCX variables"가 붙어서 "256 KB onlyvariables"로 읽힌다. 줄바꿈이나 약어("Default", "SEG 256 KB", "All 7")를 쓴다.
  - 캡션 "bars are medians"는 실제로는 검은 가로선이다. "black lines are medians"로 쓴다.
  - (c) 제목 "Four connections per P–D pair"는 26B가 대부분 2–3개만 동시에 썼다는 본문과 긴장이 있다. "Connections busy at once"가 내용과 맞는다.
  - (a)의 선형 x축에서 1과 2가 붙는다. log2 축을 권한다.
- **그림 6 (v1_ttft)**
  - 모형 추정 눈금이 26B NVFP4와 31B 두 행에만 있다(사전 예측이 두 점뿐이라서). 캡션에 적는다.
  - 행 순서(FP8, NVFP4, 31B)와 본문 서술 순서(NVFP4, 31B, FP8)가 다르다.
  - 주석 "transfer 85% of added"는 "of added TTFT"로 쓴다. 본문도 FP8에만 "(165 of 193 ms)"가 없다.
- **그림 7 (v1_proxy_gc)**
  - (a)에서 GC와 겹친 두 스파이크(약 90 s, 162 s)가 파란 점선 뒤에 가려져, 이 그림이 보여야 할 "일치"가 오히려 안 보인다. 스파이크를 굵게 하거나 위에 마커를 두고, GC는 음영 띠로 바꾼다.
  - 107 s 사건이 두 런에 같은 시각에 나온다는 것이 서버 측 정지의 증거인데, 캡션에 없다. "The event at 107 s appears in both runs (server-side pause)"를 넣는다.
  - GC 라벨이 5.6pt다.
  - 캡션 "within the same 5 ms"는 교정 제안처럼 "ended in the same 5 ms bin"으로 쓴다.
- **그림 A1 (fig02)**: 부제 "0.5 req/s"(전체)와 캡션 "0.25 requests/s per GPU"가 다르다. "TTFT budget 1 s"를 쓴다. x축 1, 2, 3, 5, no limit이 등간격이다.
- **그림 A2 (fig05)**: 부제 "0.5 req/s"(전체)다. 4K/16K/32K를 선으로 이어 보간처럼 보인다.
- **그림 A3 (fig10)**
  - 패널 제목의 요청률이 전체다(캡션에 명시됨). 논문 규칙대로 GPU당으로 바꾸기를 권한다.
  - 막대 값 5.0pt, "1.00 1.00 / 1.00 0.98" 라벨이 붙어 있다. (a)(b)(c) 표기가 없다.
- **그림 A4 (fig08)**: (a)에서 x=2의 min–max 막대가 범례 "Replicas (2)" 글자를 관통한다. (b)에서 주석 "hollow marker … not used for verdicts"를 2P1D 속 빈 마름모가 가린다. 판정에 쓰지 않는 16의 속 빈 점까지 선을 이어 추세처럼 보인다(1차 지적).
- **그림 A5 (fig09)**: (b)에서 0.9 점선이 범례 "Replicas (3)"을 관통한다(1차 지적 그대로). Replicas (3)이 Replicas (2) 뒤에 가려진다.
- **그림 A6 (fig11)**: "Rep ×2/×3"는 "Replicas (2)/(3)"으로 쓴다. x 라벨이 5.4pt다.
- **그림 A7 (fig13)**
  - 제목은 [필수]다(주요 약점 1).
  - 행 라벨 14개가 전체 요청률인데 캡션에 없다. 행 라벨이 5.1pt다.
  - 범례가 아래 두 행의 점 영역에 걸친다.
  - "KV matched"는 정의가 없다.
- **그림 A8 (fig14)**
  - x축 "0.25/0.5 req/s"는 전체 요청률로 보인다. 캡션에 단위가 없다.
  - 부제 "push trims the median, not the SLO"는 "not attainment"가 정확하다.
  - pull과 push가 모두 주황 계열이다. 둘 다 분리 구성이라 의미상 일관되기는 하므로 우선순위는 낮다.
- **그림 A9 (fig06)**
  - 제목 "4K input at 1 req/s"는 전체 요청률이다(캡션은 0.5 per GPU).
  - 범례 "1P1D"가 "0.84" 라벨 위에 겹친다(1차 지적 그대로).
  - 네 막대가 GPU, 정밀도, 튜닝 여부, placement group을 한꺼번에 바꾼다. 제목 "replicas hold only with a fast GPU and light weights"는 이 교란을 덮는다. 본문 참조도 없다.
- **표 1**
  - 캡션 "All main-text results come from g7e"는 틀렸다(주요 약점 3).
  - g7 가격 "–"의 이유가 없다. 비용 계산에 쓰지 않았다면 "not used for costs"라고 적는다.
  - 네트워크 열(g6e 5 Gbps 기준/20 Gbps 버스트, g7e 50 Gbps 고정, g7 ?)을 추가하면 §4.5 크레딧 문단과 §3.1이 표 하나로 받쳐진다.
- **표 2**
  - 31B chat 1P1D에 "≥4"를 쓴다.
  - 첫 셀만 "1 req/s"로 단위가 붙어 있다. 캡션에 단위가 있으니 숫자만 쓴다.
  - "none"은 "none (≥0.5)"처럼 측정 범위를 적는다.
  - 결정적인 1P1D 4(borderline)와 31B chat 4(0.903, 0.924)는 † 표시를 권한다.
  - TTFT의 차이(200 대 500 ms)가 이 비교의 절반인데 표에 없다. "median TTFT at supported load" 열을 추가하기를 권한다.
  - "Workload" 열에 정밀도가 섞여 있으니 "Setup"으로 바꾼다.
- **표 E1**
  - p열 양쪽 정렬로 단어 간격이 벌어진다.
  - E1 행 "26B FP8, 31B FP8"은 31B FP8이 본문에 없어 중의적이다.
  - "KV matching"은 정의가 없다.
  - 본문(§3.6)은 "maps sessions to data folders"라고 하는데, 표에는 폴더가 없고 규칙(`results/<session>/`)만 있다. 문장을 "lists the sessions"로 바꾼다.

## 과장 표현

- 초록 "about 3× more requests per GPU": 26B NVFP4 4K에만 해당한다. 1 req/s 격자의 비(3 ÷ 1)라는 점도 드러나지 않는다.
- 초록 "Disaggregation remained the only option": 1,024 미만 청크(26B)는 측정하지 않았다. "the only configuration that passed among those we measured"가 정확하다.
- 초록 "Replicas also always delivered the first token sooner", RQ3 "always had lower TTFT": "in every configuration we measured"로 한정한다.
- 초록 "their longest gap is set by the chunked-prefill size", RQ1 "a step that carries a full chunk", 체크리스트 1 "It equals": 4K 입력에서만 성립한다.
- 초록 "the 9.5 Gbps per-flow cap": placement group 조건이 빠졌다.
- 2장 "add the chunk size as the variable that moves it": TaiChi도 청크 크기를 조절 노브로 쓴다(좌장 A10). "measure how far the chunk size moves it"로 낮춘다.
- §4.5 "more connections, not other UCX settings, are the remaining lever": 검증하지 않았다("we did not test that"와 한 문장 안에서 충돌한다). "which is why its rate is higher"도 "which likely explains"가 적절하다.
- §4.7 "so it is a server-side pause tied to the request sequence": 같은 시드의 두 런이 일치한 한 사례에서 나온 추론이다. "most likely"를 붙인다.
- §4.7 "The test proxy therefore … and it explains the collapse of … 2P1D": 제거한 사건에는 서버 측 사건도 포함된다. 주어를 "these global pauses"로 바꿔야 논리가 맞는다.
- RQ1 "almost in proportion": 48 → 28 ms(1.7배)는 청크 2.5배 감소에 비례하지 않는다.
- RQ3 "as a default Gemma 4 deployment is": 근거가 없다.
- 체크리스트 3 "m between 1.5 and 2"와 "KV volume from Eq. (1)":
  - m은 한 커넥터 버전에서 140 MiB와 560 MiB 두 전송 크기로만 쟀다. 작은 전송에서는 m이 1보다 작을 수 있다(좌장 A6).
  - 식 1의 상수(100 MiB + 10 KiB·L)는 26B NVFP4 전용이다. 다른 모델에서는 "measure the per-request volume from vLLM's log"라고 써야 한다.
- 결론 "exactly what chunked prefill provides by other means": 논문 자신의 30 ms 결과와 모순된다.
- 결론 "which can be estimated before deployment": 식 2는 저부하 근사이고, 사전 추정 오차는 14%와 3–5%였다. "roughly estimated at low load"로 쓴다.
- 그림 A7 제목 "Repeats only disagree near the 0.9 threshold": 그림 자체와 모순된다.
- 그림 A9 제목 "replicas hold only with a fast GPU and light weights": GPU, 정밀도, 튜닝, placement group이 동시에 바뀐 비교다.
- 그림 5(c) 제목 "Four connections per P–D pair": 26B는 주로 2–3개가 동시에 움직였다. 연결은 넷이지만 동시 사용은 적다는 점이 m = 1.5의 이유이므로 제목이 오해를 부른다.

## 점수·확신도

- 표현(presentation): **4/5** (1차 3/5). 이야기가 한 줄로 정리됐고 초록의 모순이 사라졌다. 과장도 대부분 걷혔다. [필수] 1–5(그림 속 전체 요청률과 A7 제목, 초록 한정어, 본문–그림 불일치, 일반화 문장, 부록 참조)를 고치면 4.5까지 갈 수 있다. 모두 원고와 그림 라벨 작업이다.
- 확신도: **4/5**. main.tex 전문과 PDF 22쪽 전부를 읽었다. 본문 그림 6개(2–7)는 200 dpi로 따로 렌더링해 확인했고, 모든 SVG의 텍스트를 추출해 요청률 표기와 용어를 대조했다. 글자 크기는 SVG 폭과 포함 폭으로 환산했다. `--` 렌더링은 pdftotext로, EcoServe 서지는 USENIX와 arXiv 페이지로 확인했다. 원자료 수치(예: 31B 200–400 토큰 구간 값)는 다시 계산하지 않았다.
