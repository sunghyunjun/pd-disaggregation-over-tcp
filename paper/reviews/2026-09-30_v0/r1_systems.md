# Reviewer 1 (LLM 서빙 시스템) 심사평

## 요약
RDMA 없이 AWS 단일 GPU 인스턴스끼리 TCP(vLLM v0.30.0, NIXL/UCX)로 PD 분리를 측정한 연구다. Gemma 4 26B(MoE)와 31B(dense)를 1~3노드에서 돌렸다(389런 중 256런 채택). 분리가 늘리는 TTFT는 KV 전송 시간이고, 실효 전송률은 흐름당 상한의 1.3–1.7배라고 주장한다. 요청별 최대 간격 50 ms SLO에서 26B 4K 입력은 GPU당 지원 부하가 1.5–4배, 비용이 약 3배 개선되고, 31B 대화는 분리만 SLO를 충족한다고 보고한다. 결과는 체크리스트와 "grow the bottleneck side" 규칙으로 요약된다.

## 강점
- 요청 단위 원자료를 보존해 같은 런을 SLO 격자로 다시 판정했다(Fig 8, A7). 결론이 SLO에 얼마나 의존하는지 스스로 드러낸 점이 이 논문의 가장 큰 가치다.
- UCX TCP 세그먼트를 8 KB에서 256 KB로 올려 전송률을 2배로 만든 것은 즉시 쓸 수 있는 발견이다. Dynamo 문서가 TCP에서 보고한 약 100 MB/s("KV Transfer BW ~100 MB/s")와 비교하면 의미가 더 커진다.
- 오염 런 128개 제외, 3회 반복, 경계점 표기 등 데이터 위생이 좋다. 실패한 기법(host staging, 스레드 수, 레이어별 PR, push)도 공개했다.
- 한계 절이 솔직하고 "we do not claim to be the first"로 헤지했다.

## 주요 약점

**1. [필수] 복제본 기준선의 청크 크기가 튜닝되지 않았다. 헤드라인 이득을 지울 수 있는 잠재적 치명 결함이다.**
- 위치: §3.1 "The chunked-prefill size was 2,560 tokens", §4.5, §4.6.
- 문제: `results/safe_runs.csv`의 256런이 모두 `chunk=2560`이다. 실험 노트(RESULTS.md 77행)를 보면 2560은 성능 때문에 고른 값이 아니다. 2048이 "청크 2048은 mm 검사로 거부(마찰 #4)"되어 강제된 값이다. 논문 자신의 데이터가 이 값이 경계선에 있음을 보여 준다. §4.6은 "For 26B at 4K, the replicas' p90 maximum gap sits at 50–65 ms, right on the 50 ms line"이라고 쓴다. 원자료(E5/E7, 26_B2, 4K)에서 복제본은 GPU당 1 req/s일 때 시스템 ITL p99가 약 41 ms이고, `stall_req_frac`이 0.92–0.99인데도 달성률은 0.93–0.97이다. 즉 멈춤은 거의 모든 요청에서 일어나지만, 그 크기는 2560토큰이 섞인 스텝 하나(약 40–50 ms)에 해당해 50 ms 한계를 겨우 넘거나 넘지 않는다. 청크를 1024–1536으로 줄이면 GPU당 2 req/s에서도 50 ms 안에 들어갈 가능성이 크다.
- 중요한 이유: 1.5–4배 지원 부하 이득과 3배 비용 절감이 이 한 노브에 달려 있다. Sarathi-Serve와 TaiChi(청크 크기를 "slider"로 둔다)가 바로 이 상충을 다룬다. 강한 공동 배치 기준선이 없으면 헤드라인 결론이 성립하지 않을 수 있다.
- 조치:
  - 복제본에 `--max-num-batched-tokens` {512, 1024, 1536, 2560}을 스윕한다. serve.sh에 이미 있는 `--limit-mm-per-prompt '{"image":0}'`로 mm 제약이 풀리는지 먼저 확인한다.
  - `--long-prefill-token-threshold`와 `--max-num-partial-prefills`도 시험한다.
  - Fig 8의 각 셀을 "그 SLO에서 가장 잘 튜닝된 복제본"과 비교한다.
  - 공정성을 위해 P 노드의 청크 확대(디코드를 보호할 필요가 없음)와 D 노드의 `--max-num-seqs` 조정도 함께 보고한다.

**2. [필수] 31B 대화에서 "only disaggregation meets the SLO"의 메커니즘이 입증되지 않았다.**
- 위치: §4.5 "The dense model's decode step is long enough that even short prefills push gaps over 50 ms", 초록 "for the dense 31B model in chat only disaggregated configurations met the SLO".
- 문제: 원자료(E5/E7, 31_B2, ShareGPT, 2 req/s)에서 31B 복제본은 ITL p50 25.6 ms, p99 약 45 ms이고 `stall_req_frac`이 0이다. 탈락 원인은 큰 멈춤이 아니다. 요청별 최대 간격이 디코드 스텝(25 ms)의 2배인 50 ms를 살짝 넘는 것이다. 100토큰 안팎의 프리필 하나가 dense 31B의 스텝을 2배로 늘린다는 설명은 연산량만으로는 부족하다. 혼합 배치가 full CUDA graph에서 piecewise 모드로 빠지는 런타임 효과일 수 있고, ShareGPT의 긴 꼬리 프롬프트가 2560 청크에 걸린 것일 수도 있다. 게다가 절대 50 ms는 31B 스텝의 2배, 26B 스텝(6.5 ms)의 7.7배다. 모델 간에 같은 절대 기준을 쓰면 dense 모델에서 분리가 유리하게 보이도록 편향된다. Sarathi식 상대 기준(strict 5배)을 쓰면 125 ms가 되고, 그 구간은 Fig 8에서 차이가 없다("at 100 ms or more both approaches passed up to the highest measured rate"). 실험 노트도 처음에는 31B의 채팅 TBT를 125 ms(5× step)로 잡았다.
- 조치: 스텝 단위 트레이스(혼합 대 디코드 전용 스텝 시간, 스텝 안의 프리필 토큰 수별)와 요청별 최대 간격 히스토그램을 제시한다. "k× decode step" 기준의 판정도 병기한다. 초록의 해당 문장에는 "at a 50–75 ms gap limit, i.e. 2–3× the decode step" 같은 조건을 붙여 완화한다.

**3. [필수] 식 (1)과 "almost entirely"가 과장되어 있고, 바이트/토큰 선형 가정이 하이브리드 어텐션에서 틀린다.**
- 위치: 초록 "The time that disaggregation adds to the first token is almost entirely KV-cache transfer time, and a simple formula predicted it before we measured it", §4.3.
- 오버헤드 중 전송 비중: 26B NVFP4는 137 ms(267 − 130) 중 84 ms(61%), 31B는 370 ms 중 283 ms(76%), E4는 193 ms 중 165 ms(85%)다. "almost entirely"보다 "60–85%"가 정확하다. 잔차(53–87 ms)는 RDMA처럼 전송이 빨라질수록 바닥값이 되므로, Discussion의 RDMA 외삽에도 영향을 준다.
- 검증: 사전 예측은 2점뿐이고 둘 다 과소예측이다(235 대 267, 810–830 대 853). 단일 노드 TTFT는 다른 런에서 가져왔고, P 노드는 디코드 간섭이 없으므로 단일 노드 TTFT를 기저로 빼는 분해 자체가 깔끔하지 않다. 부하 항도 없다. 1P1D TTFT p50은 1/6/8 req/s에서 267/374/527 ms로 오른다. 체크리스트 2번은 운영 부하에서 쓰이므로 저부하 점 2개로는 부족하다.
- 선형 가정: 노트의 실측 전송량은 4K 140 MB, 16K 260 MB, 32K 412 MB다(RESULTS.md 458–463행). 토큰당 바이트가 34 KB에서 16 KB, 13 KB로 줄어든다. 슬라이딩 윈도우 층의 KV가 윈도우 길이에서 멈추기 때문이다. §4.3의 예 "where the per-flow cap is about 5 Gbps, a 16K input to 26B FP8 needs more than a second for the transfer alone"은 선형 외삽(16,384 × 약 68 KB ≈ 1.1 GB)으로 보인다. 실측 기반이면 BF16 KV 기준 약 520 MB이고, 6.5 Gbps 실효에서 약 0.64 s다.
- 조치:
  - 전송량을 V(L) = L·b_global + min(L, W)·b_local로 모델링한다.
  - TTFT는 서버 타임스탬프로 분해한다(P prefill 시간, NIXL xfer 시간, D 대기, 프록시 홉, D의 마지막 프롬프트 토큰 재계산).
  - 전체 PD 점에 대한 hold-out 예측 오차를 이용률 대비로 보고하고, 대기열 항을 넣거나 식의 적용 범위를 저부하로 명시한다.

**4. [필수] m = 1.3–1.7의 원인 설명이 검증되지 않았고, 노트와도 어긋난다.**
- 위치: §4.2 "It exceeds the cap slightly because NIXL splits a request's KV cache into several pieces carried on several connections; 31B, with more pieces, reached 1.68×", "The remaining headroom lies in the number of connections, not in settings."
- 문제: 노트(RESULTS.md 518, 454행)는 UCX TCP가 엔드포인트 쌍당 소켓 하나(`dev_num_paths=1`)이고 NIXL `num_workers=1`이며, 스레드 16개는 효과가 없었다고 적는다. 흐름 수가 원인이라면 조각이 훨씬 많은 31B가 1.68배에 그칠 이유가 없다. 짧은 전송(약 100 ms)에 대한 흐름당 버스트 허용이나 UCX 레인 분리(AM 대 RNDV) 같은 대안도 배제되지 않았다. 소스 확인은 노트에 "v0.11.0 계열"로 기록되어 있어 실행 버전(v0.30.0)과 다르다. 같은 설정 안의 구간별 실효 대역폭 편차(8.4–17.2 Gbps)도 본문에 없다.
- 조치: 전송 중 `ss -tni`로 P–D 사이 ESTAB 연결 수와 소켓별 바이트를 제시한다. 140/280 MB 단발 iperf 단일 흐름도 측정해 버스트 효과를 가른다. 실행 중인 컨테이너의 정확한 vLLM/NIXL/UCX 버전으로 소스를 재확인한다. 확인하지 못하면 인과 문장은 가설로 낮추고, "headroom lies in the number of connections"도 가설로 표기한다. m은 적합한 상수이지 도출한 값이 아니라고 밝힌다.

**5. [필수] 관련 연구 누락으로 기여가 과대 포지셔닝되었다.**
- TaiChi(arXiv 2508.01989)가 이미 "aggregation is optimal for tight time-to-first-token (TTFT) and relaxed time-per-output-token (TPOT), while disaggregation excels for strict TPOT and relaxed TTFT"라고 밝혔다. RQ3/§4.6의 결론과 같다. 이 논문은 그 경계를 TCP 조건에서 정량화한 연구로 위치시켜야 한다.
- EcoServe(OSDI'26, arXiv 2504.18154)는 NVLink/InfiniBand가 없는 커머디티 이더넷 클러스터에서 완전 분리가 불리하다고 보고 부분 분리(PaDG)를 제안한다. 가장 가까운 선행 연구다.
- ThunderServe(MLSys'25)와 HexGen-2(ICLR'25)는 클라우드 이더넷이나 이기종 네트워크에서 phase splitting을 한다(ThunderServe는 전송용 4비트 KV 양자화까지 한다). 따라서 §2의 "All of them assume a fast interconnect such as RDMA or NVLink, or emulate one in their evaluation"과 충돌한다.
- Etalon(fluidity-index, arXiv 2407.07000)과 Andes(QoE)는 TBT 백분위가 요청별 멈춤을 가린다는 점을 이미 지적했다. 기여 1("a per-request SLO evaluation")은 새 발견이 아니라 기존 관점의 적용으로 재서술해야 한다. DistServe도 요청 단위 attainment를 쓴다.
- pull 방식 KV 전송의 설계 근거는 KVDirect(arXiv 2501.14743)를 인용한다.

**6. [권장] 라우터가 비대칭이다.**
- 위치: §3.1 "Load generation and request routing ran on a separate CPU instance."
- 문제: PROTOCOL.md 고정 조건은 "프록시: 두 구성 모두 같은 프록시 프로세스를 거침"이다. 실제로는 복제본에 aiohttp `harness/rr_proxy.py`, PD에 vLLM 테스트 코드 `tests/v1/kv_connector/nixl_integration/toy_proxy_server.py`를 썼고, 논문에는 적혀 있지 않다. 노트 기준 PD 프록시의 클라이언트 CPU 사용량은 약 2배다. 프록시 오버헤드 점검(노트 B1)은 rr_proxy 대 직결, ShareGPT 1 req/s만 비교했다. 50 ms 최대 간격은 프록시 지터에 민감하다.
- 조치: 프록시를 공개한다. 각 프록시로 단일 노드를 통과시켜 요청별 최대 간격의 지터 바닥값을 측정한다. 가능하면 같은 프록시를 쓰고, llm-d의 decode-first 흐름 같은 실운영 라우터와의 차이를 언급한다.

**7. [권장] 비율 규칙에 교란 요인이 있고 일반화가 과하다.**
- 위치: §4.5 "Chat needs more decode capacity", §5.1 RQ4, 체크리스트 4번.
- 문제: 2P1D 대화 붕괴는 디코드 연산 용량 부족이 아니다. `--max-num-seqs 256` 상한 때문이며, 그때 KV 사용률은 43%, 선점은 0이었다. 노트(987행)도 "상한은 `--max-num-seqs`라 설정 여지가 있다(미측정)"라고 적는다. 3노드로는 1:2와 2:1만 시험할 수 있고, 모델 2개와 vLLM 버전 1개다. "grow the bottleneck side"는 DistServe/Splitwise 배치 원리의 재진술에 가깝다.
- 조치: 상한을 올려 2P1D를 재측정하고, 규칙은 관찰로 낮춘다. 또는 GPU당 프리필 처리량 대 SLO 하 디코드 수요로 비율을 정량 예측하고, 그 예측을 측정으로 검증한다.

**8. [권장] 격자 해상도와 적용 범위가 불명확하다.**
- "1.5–4×"는 격자 해상도에서 나온 범위다(복제본은 GPU당 1 req/s 통과·2 탈락, 1P1D는 3 통과·4 탈락). 그런데 초록과 §4.7의 비용은 "about 3×"라는 점값으로 쓴다. 복제본 1.25/1.5/1.75, 1P1D 3.5 지점을 추가하고, 비용도 범위로 보고한다.
- TTFT = prefill + transfer와 "31B, 4K input: no configuration holds the SLO reliably"라는 결론은 stock pull-after-prefill 커넥터에 한정된다. Splitwise식 레이어별 겹치기를 쓰면 전송 항이 대부분 가려져 31B 4K(prefill 약 480 ms + transfer 약 280 ms)는 결론이 달라질 수 있다. 이 범위를 초록과 체크리스트에 명시한다.

## 사소한 지적
- 정확성 검사(§4.8)의 결과가 본문에 없다. "whether long prompts shared enough content words"라는 기준도 모호하다. 노트에 있는 바이트 일치 수(재기동 후 8/8)와 첫 분기 위치를 보고한다.
- host staging의 "75× at 1 request/s" 저하는 구현상 병리일 가능성이 크다(노트에 g7 호스트 30 GiB에서 OOM 기록). 이를 "did not help"가 아니라 구현 문제로 표기한다. UCX TCP가 GPU 메모리를 보내는 실제 경로(cuda_copy를 거친 host bounce buffer)와 8 vCPU 노드에서의 CPU 부담을 설명한다. 노트에는 P 부하가 오를수록 전송률이 떨어졌다는 기록(4.05 → 3.13 Gbps)이 있다.
- "Faster GPUs narrow the gap"(§4.4, Fig A2)은 GPU 속도가 정밀도, KV dtype, 전송 튜닝 여부와 교란되어 있다. 0.14에서 0.97로 뛴 것은 GPU가 아니라 NVFP4 전환의 효과다.
- Fig A1은 송신측 합산 tc 제한이므로 흐름당 상한과 다르다. "Artificially limiting bandwidth shows that this cap sets TTFT"는 둘을 혼동한다(m > 1일 때 합산 제한과 흐름당 제한은 다르게 작동한다).
- §4.4–4.5 본문은 총 req/s("at 2 requests/s", "8 requests/s was borderline"), 그림은 GPU당 req/s를 섞어 쓴다. 단위를 통일한다.
- `--max-num-seqs 256`, 청크 2560을 쓴 이유, 사용한 프록시를 §3.1에 명시한다.
- 출력 512 고정은 요청이 멈춤에 노출되는 시간을 늘려 최대 간격 탈락 확률을 키운다. 랜덤 토큰 입력은 MoE 전문가 부하를 비현실적으로 만들 수 있다. 토큰당 멈춤률이나 Etalon식 지표를 보조로 제시한다.
- Dynamo 문서 인용: "does not state the model or input length"는 해당 표 행 기준으로는 맞다. 다만 같은 페이지의 다른 측정은 Llama-3.1-8B-Instruct와 p5.48xlarge를 명시하고, TCP 행에는 "~100 MB/s"가 있다. 이 수치를 인용하면 세그먼트 튜닝 발견의 의미가 선명해진다.
- Fig 1은 단일 노드와 복제본을 같은 마커로 묶는다. 분리해 표시한다.

## 저자에게 묻는 질문
1. `--limit-mm-per-prompt '{"image":0}'` 설정에서 청크 2048 이하가 기동되는가? 복제본을 1024로 돌려 본 적이 있는가?
2. 31B에서 혼합 스텝과 디코드 전용 스텝의 시간 분포는 어떤가? 혼합 배치의 cudagraph 모드는 무엇인가?
3. 전송 중 P–D 사이 TCP 연결은 몇 개인가(31B와 26B 각각)?
4. 1P1D 6 req/s에서도 실효 전송률 약 14 Gbps가 유지되는가, 아니면 0.5 req/s에서만 측정한 값인가?
5. §4.3의 16K 예시는 어떤 전송량으로 계산했는가?
6. D 노드의 max-num-seqs를 올리면 2P1D 대화 결과가 바뀌는가?

## 점수
- 점수: 2 (weak reject, 워크숍/인더스트리 트랙 기준, 현재 형태).
- 청크 스윕 후에도 이득이 유지되고 5번 포지셔닝을 고치면 3–4로 오른다.
- 확신도: 4.

## 참고 링크
- TaiChi: https://arxiv.org/abs/2508.01989
- EcoServe: https://arxiv.org/pdf/2504.18154 (OSDI'26: https://www.usenix.org/conference/osdi26/presentation/du)
- ThunderServe: https://arxiv.org/abs/2502.09334
- HexGen-2: https://arxiv.org/abs/2502.07903
- Etalon: https://arxiv.org/abs/2407.07000
- KVDirect: https://arxiv.org/abs/2501.14743
- vLLM issue #52607: https://github.com/vllm-project/vllm/issues/52607
- Dynamo disagg communication guide: https://docs.nvidia.com/dynamo/v1.3.0/kubernetes-deployment/operate/disagg-communication

## 검토 근거 파일 (읽기만 함)
- paper/en/main.tex
- paper/en/main.pdf
- results/safe_runs.csv
- RESULTS.md
- PROTOCOL.md
- harness/serve.sh
- harness/serve_pair.sh
- harness/rr_proxy.py
