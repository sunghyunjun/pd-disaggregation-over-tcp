# Reviewer 5 리뷰: 영어 문장, 구조, 그림·표

## 요약
TCP로만 연결된 단일 GPU 클라우드 노드에서 PD 분리 서빙이 언제 이득인지 측정한 논문이다. 결론은 대부분 수치로 받쳐져 있고, 한계와 반례도 숨기지 않는다. 표현 면에서 가장 큰 문제는 네 가지다. 초록 안에 서로 모순되는 일반화가 있다. 요청률 단위가 본문과 그림에서 섞여 있다. SLO 이름("chat SLO")이 워크로드 이름과 겹친다. 핵심 그림(8, 9, A5, A7)의 글자가 인쇄 크기에서 4~5pt라 읽기 어렵다. 영어는 대체로 정확하지만, 번역투(“Two things did not help or hurt”, “has a cost at all”)와 용어 흔들림이 곳곳에 있다.

## 강점
- 제목이 질문 형태이고 초록이 수치로 답한다. 결론의 네 조건 요약은 실무자에게 바로 쓸모가 있다.
- §4.1(시스템 백분위가 요청별 끊김을 숨긴다)이 평가 방법을 먼저 정당화한다. 논리 순서가 좋다.
- 사전 예측과 실측의 비교, 날짜가 다른 측정에 대한 경고, borderline 표시, 제외한 런의 수처럼 한계를 스스로 적는 부분이 신뢰를 준다.
- 파랑·주황 팔레트에 마커 모양과 선 모양을 함께 부호화했다. 빨강·초록 구분에 의존하는 곳은 없다.

## 주요 약점

1. **[필수] 초록의 모순과 과잉 일반화** (초록, §4.4 끝)
   - “For chat-length inputs it brought no gain”은 바로 앞 문장의 “for the dense 31B model in chat only disaggregated configurations met the SLO”와 충돌한다. §4.4의 “For chat-length inputs, measurements on other GPUs showed either no difference or replicas doing better”도 마찬가지다. “for the MoE 26B model”로 한정해야 한다.
   - “When a service must keep every gap between tokens under 50–75 ms, disaggregation wins”는 §4.6의 26B FP8 chat 결과(g7e, 모든 SLO에서 replicas 우세, 0.3–0.7×)와 맞지 않는다. “for 4K inputs or the dense model” 같은 한정이 필요하다.

2. **[필수] 요청률 단위 혼용** (§4.4, §4.5, 표 2, 그림 5·6·7·A5)
   - 그림 6·7의 x축은 GPU당 요청률이다. 그런데 31B 문단(“0.43–0.49 … at 2 requests/s”, “1P1D passed at 4 requests/s”, “1P1D at 0.25 … 2P1D at 0.75”), 표 2, 그림 5 패널 제목, 그림 A5 행 라벨은 전체 요청률을 쓴다. 26B 4K 문단만 GPU당 요청률을 쓴다.
   - 독자는 수치마다 2나 3으로 나눠야 그림과 맞출 수 있다. 전부 “per GPU”로 통일하거나, 모든 수치에 “total”이나 “per GPU”를 붙이는 편이 낫다.

3. **[필수] “chat SLO” 명명이 워크로드명과 충돌** (§3.5 이후 전반)
   - “chat attainment”가 4K 입력 실험에 계속 쓰이고(§4.2, §4.4, 그림 5·6·A2), §4.5에는 4K 입력에 대해 “chat goodput”까지 나온다.
   - “strict SLO (1 s/50 ms)”와 “relaxed SLO (3 s/250 ms)”처럼 워크로드와 무관한 이름으로 바꾸기를 권한다.

4. **[필수] 정확성 검사의 결과가 빠짐** (§4.8 둘째 문단)
   - 무엇을 비교했는지만 적고 결과를 적지 않았다. 짧은 프롬프트 6개의 출력이 단일 노드와 일치했는지, 긴 프롬프트에서 “shared enough content words”의 기준과 결과가 무엇인지 한 문장으로 넣어야 한다. 긴 프롬프트에서 완전 일치를 기대하지 않는 이유(비결정성)도 한 구절 필요하다.

5. **[필수] 1.5–4× 범위의 유도 과정이 본문에 없음** (초록, §4.5, RQ1)
   - 본문에는 “the gain is 3×; conservatively it is at least 1.5×”만 있고 4×는 나오지 않는다.
   - 유도는 한 줄이면 된다. replicas의 한계는 GPU당 1~2 사이, 1P1D의 한계는 3~4 사이이므로 비율은 1.5~4다.

6. **[필수] 데이터 선별 서술의 모순** (§3.6)
   - “All measurements ran with the prefix cache disabled” 바로 뒤에 “Some early runs had it enabled”가 온다. “All reported measurements”로 고쳐야 한다.
   - 389−128=261인데 본문은 “remaining 256”이라고 한다. 주의 런 5개를 뺀 것으로 보이는데, 그 5개는 그림에 속 빈 마커로 나온다. 산식(389−128−5=256)과 처리 방식(그림에 표시, 판정에서 제외)을 명시해야 한다.
   - “runs that met discard rules”에서 규칙이 무엇인지 적어야 한다.

7. **[필수] 참고문헌** (refs.bib)
   - arXiv @misc 6건([6] PrfaaS, [7] PDD, [9] TetriInfer, [11] P/D-Serve, [13] semi-PD, [18] Beyond the Buzz)이 unsrtnat에서 eprint 없이 “…, 2026.”로만 출력된다. 찾을 수 없는 인용이다. `journal = {arXiv:2604.15039}`나 `note = {arXiv:…}` 같은 방식으로 명시해야 한다.
   - 저자 표기가 일관되지 않다. 전원 표기(DistServe, vLLM, llm-d 블로그 8인)와 “and others” 절단(Mooncake 3인, Sarathi-Serve 1인, semi-PD 1인, Beyond the Buzz 1인)이 섞여 있다.
   - 제목 대소문자가 소실된다(“Prefill-as-a-service”, “Beyond the buzz”, “Gemma 4 model card”). 중괄호로 보호해야 한다. “Mcallister”는 “{McAllister}”로 고쳐야 한다.
   - [8]은 “2026. June 23, 2026.”로 연도가 중복된다.
   - Sarathi-Serve(OSDI 24)에 페이지가 없다.
   - vLLM 문서는 “latest” URL이라 버전이나 접근일이 필요하다. 웹 문서 전반에 접근일을 넣기를 권한다.
   - PR #56874는 각주로, Issue #52607은 참고문헌으로 처리해 기준이 다르다.

8. **[권장] RQ 번호와 서술 순서 불일치, RQ 답과 체크리스트의 중복**
   - Results는 RQ2→RQ3→RQ1/RQ4 순서로 진행한다. RQ 번호를 서술 순서에 맞추기를 권한다.
   - RQ4와 체크리스트 4는 사실상 같은 문장이고(“Grow the bottleneck side”), RQ2는 체크리스트 2·3과, RQ3는 체크리스트 1·2와 겹친다. §5.1은 한 줄 답으로 줄이고 체크리스트를 실무용 산출물로 남기기를 권한다.

9. **[권장] §4.8이 잡탕이고 §4.7에 이질적 내용이 섞임**
   - 트레이스 결과는 §4.5 끝의 검증 문단으로 옮길 수 있다.
   - 정확성 검사는 §3.6으로, push 모드와 layer-wise 패치(PR #56874)는 §4.2(효과 없었던 전송 대안)로 옮기기를 권한다.
   - §4.7(Cost)의 단일 노드 GPU 간 비교(L40S vs RTX PRO 6000, 9.2×)는 §4.4 “Faster GPUs” 문단에 속한다.
   - 부록 B(Practical pitfalls)는 본문에서 참조되지 않는다. 기여 목록의 “settings and techniques that did not help”에서 연결하기를 권한다.

10. **[권장] 도입부에 결과 미리보기가 없음**
    - 첫 두 페이지에 핵심 답이 수치로 없다. 결론의 네 조건 문장을 도입부 끝에 “Key findings”로 넣고, 그림 9를 단순화한 티저 그림을 두면 실무자가 1쪽에서 답을 얻는다.
    - 초록(242단어)은 숫자가 14개로 촘촘하다. 389/256, 1.3–1.7× 같은 세부를 빼고 180단어 안팎으로 줄이기를 권한다.
    - 제목 질문에 대한 한 문장 답(“when the service must tightly bound stalls and the transfer fits the TTFT budget”)이 결론에만 있다. 초록 끝과 도입부 끝에도 두기를 권한다.

11. **[권장] 용어 통일** (결정 → 대안)
    - replicas → replica configuration / aggregated serving(Dynamo 인용) / colocation(2장 소제목) / “Rep ×2”(그림 A4)
    - maximum gap → max ITL / maximum-gap limit / gap limit / “max token-gap limit”(그림 8 제목) / “allowed max gap between tokens”(그림 8 축) / “max ITL budget”(그림 A7 축)
    - TTFT budget → TTFT limit / “allowed wait for first token”(그림 8) / first-token limit
    - per-flow cap → single-flow limit / “One TCP flow limit”(그림 2) / “per-connection bandwidth”(결론) / effective bandwidth / effective transfer rate
    - bytes per input token(식 1) → KV bytes per token(결론)
    - client router → client-side router / request router / disaggregated router
    - supported load → “load each GPU can serve within the SLO”(초록) / per-GPU capacity / per-GPU supported load
    - SLO goodput → SLO-meeting tokens / chat goodput
    - placement group → cluster placement group / PG(표 C1)
    - 미정의 약어: SLO(초록 첫 사용), SM(2장), EFA(5.2), UCCL(2장·5.2), UCX, NIXL(본문에서 풀이 없음), KV, “PG”
    - “pull-based connector”(3.1)는 첫 사용에서 정의가 없고 §4.8에서야 push와 대비된다. 3.1에서 “(the decode node reads the KV cache from the prefill node)”를 붙여야 한다.

12. **[권장] 비용 표의 상한·하한 표시와 가격 정보** (표 2, 표 1, §4.7)
    - 26B chat은 양쪽 모두 측정 최고 요청률에서도 통과했으므로 지원 부하는 하한이고 비용은 상한이다. “≤$0.63”로 표시해야 한다.
    - §4.7의 L40S 비용($3.15)은 g6e 가격을 쓴 값인데, 표 1 캡션은 “Costs use the g7e on-demand price”라고만 한다. 인스턴스별 시간당 가격 열과 공칭 네트워크 대역폭 열을 표 1에 추가해야 한다.

13. **[권장] 같은 조건의 수치 불일치와 과도한 유효숫자**
    - 26B NVFP4, 4K, 1 req/s, placement group의 분리 TTFT가 §4.3·그림 3에서는 267 ms, §4.4에서는 269 ms다. 다른 날(E5, E7) 측정이라면 그렇게 밝혀야 한다.
    - “3.0–4.05 to 7.07–8.49 Gbps”, “13.58–14.43 Gbps”, “4.967 and 4.966 Gbps”는 유효숫자가 섞여 있거나 과하다. 소수 첫째 자리로 통일하기를 권한다(4.967/4.966은 차이를 보이려는 목적이므로 유지 가능).

14. **[권장] 임계값 정당화의 비대칭** (§3.5)
    - 1 s TTFT는 한 문단을 들여 정당화하는데, 결론을 좌우하는 50 ms 최대 gap은 근거가 없다(2장의 Sarathi-Serve 5×/25× 언급뿐). 한두 문장의 근거를 추가하기를 권한다.
    - “median input about 80–100 tokens”처럼 중앙값을 범위로 적은 이유(샘플 부분집합 차이 등)를 밝혀야 한다.

## 문장 교정 제안

| 위치 | 원문 | 제안 |
|---|---|---|
| 초록 | We ran vLLM with NIXL/UCX over TCP on three AWS single-GPU instance types and served … 389 measurement runs in total, of which 256 passed a data-quality audit. | Using stock vLLM with NIXL/UCX over TCP, we served Gemma 4 26B (mixture-of-experts) and 31B (dense) on one to three single-GPU AWS instances of three types (256 audited runs). |
| 초록 | The time that disaggregation adds to the first token is almost entirely KV-cache transfer time, and a simple formula predicted it before we measured it. | Most of the time disaggregation adds to the first token is KV-cache transfer, and a simple formula predicted TTFT within 12% before we measured it. |
| 초록 | raised the load each GPU can serve within the SLO | raised the per-GPU load served within the service-level objective (SLO) |
| 초록 | For chat-length inputs it brought no gain | For the MoE 26B model with chat-length inputs it brought no gain |
| 초록 | a checklist that decides in advance whether disaggregation is worth deploying | a checklist that helps decide, before deployment, whether disaggregation is worth it |
| 1장 | and their token stream stalls | and their token streams stall |
| 1장 | The price of disaggregation is the KV-cache transfer, and prior systems put it on fast links. | Disaggregation pays for this with a KV-cache transfer, which prior systems run over fast links. |
| 1장 | the range of inference GPUs has grown, many cloud instances carry one GPU each, and on rented infrastructure the network is not ours to choose. | fleets mix GPU generations, many cloud instances have a single GPU, and tenants of rented infrastructure cannot choose the network. |
| 1장 | Measurements that show how slow it is, and under which conditions, are scarce. | Yet few public measurements show how slow TCP transfer actually is, or when disaggregation still pays off. |
| 1장 | we take the published design as implemented in open-source tools (vLLM and NIXL) and measure when disaggregation pays off across TCP links between rented cloud GPU nodes | we take disaggregation as it ships in open-source vLLM with NIXL and measure when it pays off over TCP between rented single-GPU cloud nodes |
| 1장 | We study settings where GPUs lack a fast interconnect … and we measure the case of TCP between nodes. | (삭제: 앞 문단과 중복) |
| 1장 RQ1 | Can disaggregation raise the throughput that meets a service-level objective (SLO goodput) even over slow TCP links? | Can disaggregation raise SLO goodput, the throughput of requests that meet a service-level objective (SLO), even over TCP? |
| 기여 | evidence that the TTFT overhead equals the KV transfer time, and a model of it that we validated by predicting results before measuring them | evidence that KV transfer time dominates the TTFT overhead, and a simple model that predicted it before measurement |
| 2장 | places resources for each phase against its latency target | provisions each phase separately for its own latency target |
| 2장 | keeps a unified KV storage | keeps KV storage unified |
| 2장 | We did not find a study of the same setting, but our search was not exhaustive, so we do not claim to be the first. | To our knowledge no prior study measures this setting, although our search was not exhaustive. |
| 3.1 | Within the zone a single TCP flow was capped at about 4.97 Gbps | Within the zone a single TCP flow reached at most 4.97 Gbps (iperf) |
| 3.1 | The nominal 50 Gbps of g7e was reached only by aggregating eight flows (49.72 Gbps). | g7e reached its nominal 50 Gbps only with eight parallel flows (49.72 Gbps, inside a placement group). |
| 3.1 | The chunked-prefill size was 2,560 tokens and GPU memory utilization 0.90. | We set the chunked-prefill size to 2,560 tokens and vLLM's GPU memory utilization to 0.90 in all configurations. |
| 3.2 | We mainly used NVIDIA's NVFP4 (4-bit floating point) checkpoints, and FP8 (weight-only) and BF16 checkpoints for comparison. | We mainly used NVIDIA's NVFP4 (4-bit floating-point) checkpoints and, for comparison, FP8 (weight-only) and BF16 checkpoints. |
| 3.2 | 31B NVFP4 transfers 560 MB | 31B NVFP4 transfers 560 MB per 4K-token request |
| 3.3 | $x$ prefill and $y$ decode nodes are written $x$P$y$D | We write a configuration with x prefill and y decode nodes as xPyD. |
| 3.5 | Supported load is the highest request rate with attainment of at least 0.9 | Supported load is the highest measured request rate with attainment of at least 0.9 |
| 3.6 | All measurements ran with the prefix cache disabled. | All reported measurements ran with the prefix cache disabled. |
| 3.6 | Median TTFT moved by less than 5% across repeats and matched the previous day's measurement closely | Median TTFT varied by less than 5% across repeats and agreed closely with the previous day's measurement |
| 3.6 | Only points with attainment between 0.85 and 0.95 varied by up to ±0.09 across repeats, enough to flip the verdict | Attainment varied by up to ±0.09 across repeats; this can flip the verdict only for points between 0.85 and 0.95, which we mark as borderline. |
| 4장 머리 | Section 4.1 fixes the evaluation method. | Section 4.1 motivates evaluating each request individually. |
| 4.1 | These stalls occur when another request's prefill is scheduled in between. | These stalls occur when the scheduler runs another request's prefill between two decode steps. |
| 4.2 | Next, the cloud's per-flow cap limited the transfer. | Once the software was tuned, the cloud's per-flow cap became the limit. |
| 4.2 | It exceeds the cap slightly because NIXL splits … | It exceeds the single-flow cap because NIXL splits … |
| 4.2 | In contrast, a 1 MB segment, 16 NIXL threads, or larger rendezvous fragments all stayed within 13.58–14.43 Gbps and had no effect | By contrast, further tuning (a 1 MB segment, 16 NIXL threads, or a larger UCX rendezvous fragment size) left the rate at 13.6–14.4 Gbps |
| 4.2 | The instance's total bandwidth was still available | The instance still had spare aggregate bandwidth |
| 4.2 | Artificially limiting bandwidth shows that this cap sets TTFT | Throttling the sender's bandwidth confirms that the flow cap sets TTFT |
| 4.2 | Two things did not help or hurt. | Two other factors: host staging hurt, and network credits did not matter. |
| 4.2 | slowed TTFT by 4.7× | increased TTFT 4.7× |
| 4.3 | The relation can be written as | We model this as |
| 4.3 | where m (1.3–1.7) reflects spreading the transfer over several connections | where m (1.3–1.7 in our two-node runs) is the effective number of parallel connections |
| 4.3 | We wrote this model down before the three-node measurements and compared. | We wrote this model down before the three-node measurements and then checked it against them. |
| 4.4 | Input length decides. | Input length decides the winner. |
| 4.4 | This run predates transfer tuning, so disaggregation was at a disadvantage and still led by a wide margin. | This run predates transfer tuning, so disaggregation ran at a disadvantage yet still led by a wide margin. |
| 4.4 | A faster GPU has shorter decode steps and can absorb more prefill interference. | A faster GPU has shorter decode steps, so each interfering prefill delays decoding less. |
| 4.4 | with NVFP4 replicas cope to a degree and the gap narrows | with NVFP4, replicas also pass at this load |
| 4.4 | The FP8 and BF16 checkpoints keep a BF16 KV cache and transfer twice as much; differences in prefill speed are mixed in, and we did not isolate the transfer share. | The FP8 and BF16 checkpoints keep a BF16 KV cache and transfer twice as many bytes. Because prefill speed also differs across precisions, we did not isolate the transfer's share. |
| 4.5 | because its single decode node could not hold the gap limit | because its single decode node could not keep gaps under 50 ms |
| 4.5 | Server metrics explained why 2P1D collapsed there | Although excluded from verdicts, the 16 requests/s-per-GPU runs show why 2P1D collapsed: |
| 4.5 | and KV usage was only 43% | while KV-cache usage was only 43% |
| 4.5 | In short, the ratio should grow the bottleneck side: | In short, add nodes to the bottleneck side: |
| 4.6 | the same runs can be re-judged under other SLOs | the same runs can be re-evaluated under other SLOs |
| 4.6 | For 31B chat, disaggregation alone passed only at 40–75 ms | For 31B chat, only disaggregation passed, and only for gap limits of 40–75 ms |
| 4.6 | In contrast, for FP8 chat on g7e, replicas were better under every SLO (0.3–0.7×). | In contrast, for 26B FP8 chat on g7e, replicas served more under every SLO (disaggregated/replica ratio 0.3–0.7). |
| 4.6 | so disaggregation has nothing to offer | so disaggregation offers no benefit |
| 4.6 | the value of that trade depends on how much the service dislikes stalls | the value of that trade depends on how strictly the service must bound stalls |
| 4.7 | for 31B chat only the disaggregated configuration has a cost at all | for 31B chat only the disaggregated configuration serves any SLO-meeting load |
| 4.7 | GPU differences also grow once an SLO is applied | An SLO also magnifies differences between GPUs |
| 4.8 | The push mode, where prefill writes the KV cache instead of decode reading it, cut transfer time … | In push mode the prefill node writes the KV cache to the decode node instead of the decode node reading it. Push cut transfer time … |
| 4.8 | …supports only models with a single KV-cache group and stalled on the first request with hybrid-attention Gemma 4 | …supports only models with a single KV-cache group; with hybrid-attention Gemma 4 it stalled on the first request |
| 5.2 | Heavier weights, dense models, and longer inputs make it more likely. | Heavier weights, dense models, and longer inputs make exceeding it more likely. |
| 5.2 | Fix defaults that are bottlenecks first | First fix default settings that bottleneck the transfer |
| 6장 | One model family (Gemma 4), both with hybrid attention. | One model family (Gemma 4); both models use hybrid attention. |
| 6장 | join measurements from different days | combine measurements from different days |
| 7장 | disaggregated serving can raise SLO goodput, conditionally | disaggregated serving can raise SLO goodput, but only under specific conditions |
| 7장 | Its TTFT overhead is the KV transfer time and can be computed in advance. | Its TTFT overhead is mostly KV transfer time, which can be estimated in advance. |

## 그림·표별 지적

인쇄 크기 기준 글자 크기(SVG 폭을 본문 폭 468pt로 환산한 값): 그림 8 눈금 약 4.4pt, 그림 9 약 5pt, A7 셀 숫자 약 3.9pt, A5 행 라벨 약 5pt. 최소 6~7pt로 키워야 한다.

그림 속 제목의 형식도 일관되지 않다. 그림 1·3·A2·A3·A5는 굵은 결론형 제목, 그림 4·5·6·7·8·9·A1·A4·A6은 회색 설명형 부제, 그림 2는 제목이 없다. 한 형식으로 통일하거나, 캡션이 있으므로 그림 속 제목을 없애기를 권한다.

- **그림 1**
  - 범례는 “Replicas / single node”인데 캡션과 본문은 “18 replica runs”라고 한다. 단일 노드를 포함한다는 사실을 명시해야 한다.
  - “50 ms” 라벨이 상단 점들과 겹친다. x축의 10¹/10² 표기는 10, 20, 50, 100으로 바꾸기를 권한다.
  - 그림 속 제목이 절 제목과 같다.
  - TTFT p99 < 1 s로 거른 이유(“to isolate the gap criterion”)를 캡션에 적어야 한다.
- **그림 2**
  - 혼자 한 페이지(6쪽)를 차지하며 여백이 약 60%다.
  - 회색 점이 주황 막대 가장자리에 겹쳐 잘 보이지 않는다. 막대 오른쪽으로 옮기기를 권한다.
  - 캡션은 “four alternative settings (… and so on)”인데 본문은 세 가지만 든다. 네 번째를 밝혀야 한다.
  - (a)의 x축(1, 2, 4, 8)은 log2 척도가 적절하다.
  - 캡션이 색 이름(“Blue bars / Orange bars”)만으로 구분한다. 위치(“left/right bar in each pair”)도 함께 적기를 권한다.
- **그림 3**
  - 예측 눈금은 3~4번째 막대에만 있다. 캡션에 이를 명시해야 한다.
  - 첫 막대의 residual이 0이다(158+324=482). 잘라낸 값인지 밝혀야 한다.
  - 평균 전송 시간과 중앙값 TTFT를 한 막대에 섞었다(residual은 파생값). 캡션에 적어야 한다.
  - y축 라벨(“26B FP8 · 4K · 0.5 req/s / no placement group”)이 작다.
- **그림 4**
  - (a)에서 16K·32K의 replicas 마커가 1P1D 마커 뒤에 가려진다.
  - 4K·16K·32K를 등간격으로 두고 선으로 이어 선형 보간처럼 보인다. 범주형임을 알 수 있게 하기를 권한다.
- **그림 5**
  - 캡션에 점선(0.9)과 SLO 종류가 없다.
  - 가운데 패널(4K, 2 req/s)은 본문에서 언급되지 않는다.
  - 패널 제목의 요청률이 전체 기준임을 표시해야 한다.
- **그림 6**
  - (b)에서 판정에 쓰는 점은 x=8 하나뿐이다. 속 빈 점(16)까지 선으로 이으면 추세처럼 보인다. 선 없이 속 빈 점만 두거나 회색으로 처리하기를 권한다.
  - (b)의 주석 문구가 2P1D의 속 빈 마커와 충돌한다.
  - (b)에서 1P2D와 Replicas (3)이 16에서 겹친다.
  - 범례가 (a)에만 있다.
- **그림 7**
  - (b)에서 범례를 0.9 점선이 관통해 “Replicas (3)”에 취소선이 그어진 것처럼 보인다.
  - (a)에 3노드 데이터가 없다는 사실을 캡션에 적어야 한다.
  - (a)의 4.0 지점 오차 막대(0.863–0.944)가 거의 보이지 않는다.
  - 본문이 인용하는 요청률(전체)과 x축(GPU당)이 다르다(약점 2).
- **그림 8** (10초 테스트 실패)
  - 패널 10개와 범례 7종 때문에 요지를 얻는 데 30초 이상 걸린다.
  - 개선안: 그림 속 제목을 결론형으로 바꾼다(“Disaggregation wins only at tight gap limits (left); replicas or undecidable elsewhere”).
  - 개선안: 쓰이지 않는 “Similar (0.8–1.25×)” 범주를 제거한다.
  - 개선안: 본 논문 SLO 박스를 굵게 한다. 해치 위에서는 거의 보이지 않는다.
  - 개선안: 반복되는 축 라벨을 공유 축으로 정리한다.
  - 개선안: 본문에 필요한 패널만 남기고 나머지는 부록으로 옮기기를 검토한다.
  - “Chat (ShareGPT)” 행 라벨이 둘째 열 옆에 있다. 다른 행처럼 맨 왼쪽으로 옮겨야 한다.
  - 16K 행에는 열 제목이 없다.
  - 아주 옅은 “Neither” 셀이 흰 배경과 거의 구분되지 않는다.
  - 어떤 분리 구성과 어떤 replica 구성을 비교했는지(A7 제목의 “best config of each kind”)가 캡션과 본문(§4.6)에 없다. **[필수]**
- **그림 9**
  - 10초 안에 요지를 얻기 어렵다. 캡션이 결론을 말하지 않는다. “Top: replicas reach the first token sooner. Bottom: disaggregation keeps gaps shorter.”를 추가하기를 권한다.
  - 26B 패널의 로그 눈금(100000, 50000, 20000…)이 빽빽하다.
  - 31B chat 하단 패널에는 y 눈금이 “50” 하나뿐이라 본문 수치(70–90 vs 35–48)를 읽을 수 없다.
  - 26B chat 패널은 클라이언트 한계로 속 빈 점(TTFT 100 s 수준)까지 선이 이어져 축 범위를 지배한다.
  - 범례의 파선 패턴(Replicas (3), 1P2D)이 인쇄 크기에서 보이지 않는다.
  - 이 그림은 p90, 그림 3·A1·A4·A6은 p50을 쓴다. 이유를 한 줄로 적어야 한다.
- **그림 8·9 배치**: 각각 떠다니는 페이지 한 장씩(12, 13쪽)을 차지하고 수직 중앙에 놓여 여백이 크다. `\@fptop=0pt`나 `[t]` 배치로 정리할 수 있다.
- **그림 A1**: x축에 수치(1, 2, 3, 5)와 “no limit”이 등간격으로 섞여 있다. 범주형임을 알 수 있게 하기를 권한다.
- **그림 A2**
  - 범례 상자가 첫 그룹의 “0.84” 라벨과 겹친다.
  - 제목 “replicas hold only with a fast GPU and light weights”에 placement group 조건이 빠져 있다.
  - g7 막대만 NVFP4이면서 튜닝 전 측정이라 비교 조건이 섞여 있다(캡션에 일부 언급).
- **그림 A3**
  - 파선과 실선의 짙은 파랑이 거의 완전히 겹쳐 “dashed: first day”를 구분하기 어렵다.
  - “KV 226k”의 단위(토큰)를 표기해야 한다.
- **그림 A4**: 라벨 “Rep ×2”를 “Replicas (2)”로 통일해야 한다. x축 라벨이 작다.
- **그림 A5**
  - 제목 “Repeats only disagree near the 0.9 threshold”는 그림 자체와 모순된다. 26B replicas (2) 4K 4 req/s 행은 0.47–0.64(전날 0.37)로 크게 흩어진다. “Disagreement flips the verdict only near 0.9”로 고쳐야 한다. **[필수]**
  - 행 라벨의 요청률은 전체 기준이다.
- **그림 A6**
  - pull과 push가 모두 주황 계열이다. 파랑/주황으로 바꾸기를 권한다.
  - 제목의 “not the SLO”는 “not attainment”가 정확하다.
- **그림 A7**
  - 3×3 배치가 그림 8의 행(워크로드)×열(설정) 배치와 달라 대조하기 어렵다. 같은 배치로 맞춰야 한다.
  - 축 라벨 용어(“TTFT budget”, “max ITL budget”)가 그림 8(“allowed wait for first token”, “allowed max gap between tokens”)과 다르다.
  - 핵심 정보(“best config of each kind”)가 그림 속 제목에만 있고 캡션에는 없다.
  - ≤/≥ 이탤릭 셀 숫자가 약 3.9pt다.
- **표 1**
  - 인스턴스별 시간당 가격과 공칭 네트워크 대역폭 열이 필요하다(약점 12).
- **표 2**
  - “Workload” 열 이름을 “Setup”으로 바꾸고, 요청률이 total인지 명시해야 한다.
  - 26B chat의 비용은 상한이므로 “≤”를 붙여야 한다.
  - “no supported load” 반복은 “—”와 각주로 바꾸기를 권한다.
- **표 C1**
  - 폴더명 “C1”이 “Table C1”과 충돌한다.
  - 절 번호가 하드코딩되어 있다. `\ref`를 써야 한다.
  - “26B, 31B FP8”은 중의적이다. 31B FP8은 본문에 나오지 않는다.
  - “plumbing runs”는 “setup/smoke-test runs”로 바꾸기를 권한다.
- **기타 형식**
  - 제목 줄바꿈으로 “RDMA?”가 홀로 남는다. 수동 줄바꿈(“…Disaggregation\\ Pay Off Without RDMA?”)이 필요하다. 단일 GPU가 핵심 조건이므로 부제에 “Single-GPU Cloud Instances”를 넣는 것도 검토할 만하다.
  - 참고문헌 [5]와 [20]에 URL 때문에 단어 간격이 벌어진다. `xurl` 사용을 권한다.
  - Acknowledgments에는 감사 대상 없이 비용만 적혀 있다. “Funding” 문장으로 옮기기를 권한다.
  - 주황 placeholder 3개(contact email, draft 날짜, GitHub/Zenodo)는 예상된 것으로 확인했다.
  - .log 파일이 없어 overfull box는 확인하지 못했다. 눈으로 본 범위에서 본문 밖으로 넘친 줄은 없었다.

## 과장 표현 목록
- “almost entirely KV-cache transfer time”(초록, §4.3): 그림 3의 26B NVFP4는 추가 TTFT 137 ms 중 전송이 84 ms(61%)다. 31B는 76%, 26B FP8 placement group은 85%다. “most of”로 바꾸거나 비율을 적어야 한다.
- “equals the KV transfer time”(기여 목록), “can be computed in advance”(결론).
- “a simple formula predicted it before we measured it”(초록): 사전 예측은 두 점뿐이고 오차는 약 12%(235 대 267 ms)와 3~5%다. 오차를 적어야 한다.
- “the two reductions are nearly equal”: 실제로는 159 대 131 ms다.
- “exceeds the cap slightly”: 실제로는 1.32–1.68배다.
- “matched the prediction exactly”: 계산값이므로 “as computed”가 정확하다.
- “Replicas always have a faster first token”: “in all our measurements”로 한정해야 한다.
- “disaggregation is effectively the only option”(FP8/BF16): “the only configuration that met the SLO”가 정확하다.
- “Faster GPUs narrow the gap”: 가장 빠른 GPU에서도 FP8 replicas는 0.14였다. 차이를 좁힌 것은 NVFP4와 placement group이다.
- “The remaining headroom lies in the number of connections, not in settings”: 시험한 설정은 네 가지뿐이다. “not in the settings we tried”로 한정해야 한다.
- “Network credits … were not a constraint”: 15분, 한도의 18% 부하에서만 확인했다. “at our load”로 한정해야 한다.
- “Only points with attainment between 0.85 and 0.95 varied”(§3.6)와 그림 A5 제목: 약점 6과 그림 A5 항목 참조.
- “checklist that decides in advance”, “judged before measuring from four numbers”: 체크리스트 1번은 replicas의 요청별 최대 gap을 실측해야 판단할 수 있다. 이 값은 결론이 든 네 숫자에 없다.
- 초록의 “disaggregation wins”와 “For chat-length inputs it brought no gain”(약점 1).
- “31B, chat: only disaggregation meets the SLO”(§4.5 소제목): 1 s/50 ms 기준에서만 성립한다. §4.6에서 100 ms 이상이면 양쪽 모두 통과했다. 소제목에 “under the 50 ms gap limit”을 붙이기를 권한다.

## 점수
- 표현(presentation): **3/5**. 초록의 모순, 단위 통일, 그림 글자 크기, 참고문헌을 고치면 4까지 올라갈 수 있다.
- 확신도: **4/5**. 원문 main.tex, refs.bib, PDF 23쪽 전부, 그림 8·9·6·7·A7의 고해상도 렌더링을 대조해 확인했다.
