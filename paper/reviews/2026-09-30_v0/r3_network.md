# Reviewer 3 (네트워크·클라우드) 심사평

**점수 3/5 (보완 후 채택 가능), 확신도 4/5.** 필수 수정은 7건이다. 네트워크 결론의 방향은 대체로 맞다. 그러나 m의 메커니즘, 식 1의 형태, 단위, 크레딧 검증 방법에 결론을 바꿀 수 있는 틈이 있다.

## 요약
AWS 단일 GPU 노드 사이에서 vLLM·NIXL·UCX TCP로 PD 분리를 측정한 논문이다. 네트워크 쪽 주장은 네 가지다.
1. 첫 토큰 벌점은 KV 전송 시간이다.
2. 실효 전송률은 흐름당 상한의 1.3~1.7배다(m).
3. UCX 세그먼트를 조정한 뒤에는 설정으로 더 얻을 여유가 없었다.
4. 네트워크 크레딧은 제약이 아니었다.

## 강점
- iperf 흐름 수 스윕(1·2·4·8), 배치 그룹 유무, 노브 4종을 같은 부하 지점에서 나란히 쟀다.
- 식 1을 측정 전에 적어 두었고, 요청별 원자료를 공개한다.
- UCX에서 RX 세그먼트가 TX보다 작으면 엔진이 뜨지 않는 문제처럼 실무에 쓸모 있는 마찰을 기록했다.

## 주요 약점

**1. [필수] m의 메커니즘이 검증되지 않았고 자체 수치와도 맞지 않는다 (§4.2).**
- 문제 문장은 "It exceeds the cap slightly because NIXL splits a request's KV cache into several pieces carried on several connections"다.
- 노트(RESULTS.md)의 NIXL 분할 규칙(조각 = max(⌈N/threads⌉, 1024) 디스크립터, threads 기본 4)대로면 이상적 배수는 다음과 같다.
  - 26B NVFP4(2,240개 → 1024/1024/192): 약 2.2배
  - 26B FP8(약 1,908개 → 1024/884): 약 1.9배
  - 31B(4,480개): 4배 이상
- 실측은 1.40/1.46/1.68이다. 연결당 효율은 64%, 78%, 42% 이하로, 연결이 늘수록 떨어진다.
- 흐름당 상한과 별개로 공유 병목이 있다는 뜻이다. 후보는 8 vCPU에서 UCX 진행 스레드가 맡는 cuda_copy 스테이징과 syscall이다.
- 전송 중 소켓 수를 센 적이 없다(ss, tcpdump 기록 없음). 1.3~1.7배를 "slightly"라고 부르는 것도 부정확하다.
- 따라서 §4.2와 체크리스트 3번의 "The remaining headroom lies in the number of connections, not in settings"는 근거가 부족하다.
- 수정: 전송 중 `ss -tin`으로 5-tuple 수와 소켓별 전송률을 보인다. split_batch_size를 낮춘 패치로 연결 수와 전송률의 관계를 확인한다. 그 전까지는 가설로 표기한다.

**2. [필수] 식 1의 "bytes per input token"은 상수가 아니다.**
- 26B NVFP4 전송량은 4K 140, 16K 260, 32K 412 MiB다(RESULTS.md 세션 B). 이 세 값은 100 MiB + 10 KiB × L에 정확히 맞는다(4096 → 140, 16384 → 260, 32000 → 412.5). 슬라이딩 윈도우 층이 고정 성분을 만든다. 4K 기준 "about 34 KB per input token"을 그대로 외삽하면 16K는 2.1배, 32K는 2.7배 과대평가된다.
- 그래서 §4.3의 "a 16K input to 26B FP8 needs more than a second for the transfer alone"은 자체 데이터와 어긋난다.
  - FP8 체크포인트(BF16 KV)면 2×260 = 520 MiB이고, 6.55 Gbps에서 0.64 s, m=1이라도 0.88 s다.
  - E2b 실측(16K, 배치 그룹 없음, g7e FP8)에서 PD와 복제본의 TTFT p50 차이는 465 ms(1,285.6 − 820.2)와 506 ms(1,318.1 − 811.9)에 그친다.
- m도 전송 크기에 따라 달라진다. 노트(E5 "조각 수와 전송 크기" 표)에는 25 MB에서 0.37~0.54, 105 MB에서 0.77~0.95로 적혀 있다. 채팅 규모에서 m이 1보다 작다는 사실이 본문에 없다.
- 26B의 140 MB는 세션 B에서 이미 측정한 값이어서 "The transfer volume matched the prediction exactly"의 "예측"이라 보기 어렵다.
- 수정: 전송량 B(L)를 아핀 형태로 쓰고, 고정 전송 비용 t0를 넣거나 m(B) 표를 싣는다. 16K 예시를 고친다(16K가 1초 예산에 못 드는 이유는 프리필 약 0.8 s + 전송이지 전송 단독이 아니다).

**3. [필수] 식 1에 대기열 항이 없다.**
- 부록 A1의 tc 수치(4K, 0.5 req/s, 기준 471 ms 중 전송 약 155 ms, 비전송 약 316 ms)는 M/D/1 항을 더하면 설명된다. 1 Gbps(iperf 0.995)에서 S ≈ 1.18 s, ρ = λS ≈ 0.59, Wq = ρS/(2(1−ρ)) ≈ 0.85 s다.
  - 대기열 없는 예측: 약 1.50 s
  - 대기열 포함 예측: 약 2.35 s
  - 실측: 2.19 s (p50과 평균의 차이는 감안)
  - 2 Gbps: 대기열 없음 0.91 s, 포함 1.03 s, 실측 0.954 s. 3 Gbps: 0.71 / 0.76 / 0.744 s.
- 31B 예측이 맞은 것도 오차 상쇄로 보인다. m≈1.4를 썼다면 전송 예측은 약 335 ms인데 실측은 283 ms이고, 잔차가 87 ms다. 26B의 전송 84 ms 적중은 FP8 4K(E4)에서 보정한 m을 거의 같은 크기의 전송에 적용한 것이라 표본 밖 검증으로 보기 약하다.
- 노트의 잔차 범위는 −26~+87 ms인데 본문은 양수 값(53, 87)만 보고한다.
- 수정: 항별 예측값과 잔차 전체 범위를 공개하고, ρ = λ·S 대기열 항을 추가한다. 식 1이 저부하 근사임을 명시한다.

**4. [필수] 단위와 실효 전송률 정의가 일관되지 않다.**
- vLLM은 MB를 bytes/2^20으로 계산하고, Throughput은 total_mb / total_time(합계 비율)이다(docs.vllm.ai stats 페이지 latest 판으로 확인, v0.30.0 판은 미확인). 2,240 × 64 KiB = 146,800,640 B = 140 MiB로 딱 맞으므로 논문의 "MB"는 MiB다.
- 그런데 Gbps 환산은 10진으로 했다(140 MB/84 ms = 13.3 Gbps). 그 결과 m이 4.9% 낮게 나왔다(1.32/1.46/1.68 → 1.38/1.53/1.76). "about 34 KB per input token"도 35.8 kB(= 35 KiB)다.
- 그림 2 캡션의 정의 "bytes / transfer time"대로면 280/324.2 ms = 6.91 Gbps, 280/165 ms = 13.6 Gbps다. 본문의 6.55, 13.96과 다르다.
- 그림 값은 `harness/make_figures.py:185`에 노트 수치를 그대로 옮겨 적은 것(`eff = [6.55, 13.96]`)이라 공개 원자료에서 재현되지 않는다.
- 동시 전송이 겹치면 합계 비율은 링크 전송률이 아니라 전송당 전송률이다. 둘을 구분해야 m을 해석할 수 있다.
- 수정: 정의를 하나로 정하고 MiB/GiB를 표기한다. 공개 원자료에서 값을 계산하고, E4의 1초 NIC 카운터(`results/E4/collect/*_nic.txt`)와 대조한다.

**5. [필수] 튜닝 내용이 다 공개되지 않았고 원인 귀속이 불분명하다.**
- §3.1은 "We raised UCX's TCP segment size from the default 8 KB to 256 KB"라고만 쓴다. 실제로 바꾼 변수(D1d)는 일곱 개다: `UCX_TCP_TX_SEG_SIZE=256k UCX_TCP_RX_SEG_SIZE=256k UCX_TCP_MAX_IOV=16 UCX_TCP_MAX_POLL=-1 UCX_TCP_SNDBUF=8m UCX_TCP_RCVBUF=8m UCX_RNDV_FRAG_SIZE=host:4M,cuda:8M`.
- 하나씩 되돌리는 절제 실험이 없다. E4는 더 올리는 방향(1 MB, 16스레드, 16M 조각)만 쟀다. §4.2의 "raising it to 256 KB doubled the rate"는 귀속이 확인되지 않았다.
- 호스트 버퍼 모드는 기본 UCX에서도 7.3~9.4 Gbps가 나왔다(D1b). 따라서 8 KB 효과는 GPU 메모리 스테이징 경로에 한정된 것일 수 있다. 이 수치는 메커니즘 해석에 중요한데 본문에 없다.
- 네트워크 환경 보고가 빠져 있다: MTU 9001(E4 카운터상 패킷당 약 8.5 KB), RTT(g5에서만 0.16~0.17 ms 측정), 커널, 혼잡 제어, ENA 드라이버, iperf3 버전과 옵션, net.core.wmem_max/rmem_max.
- 하네스에 sysctl 설정이 없다. wmem_max를 올리지 않았다면 SNDBUF=8m는 Linux 기본값 기준 약 416 KiB로 조용히 잘리고, 명시적 SO_SNDBUF는 자동 조정도 끈다. BDP가 약 0.1~0.2 MB라 병목은 아니겠지만 보고는 필요하다.
- 수정: 환경변수 전체를 싣고 TX_SEG 단독 절제 실험을 추가하며, 위 환경 정보를 보고한다.

**6. [필수] 크레딧 주장이 잘못된 방법으로 검증됐다 (§4.2 마지막 문단).**
- AWS 명세(ac.html, 직접 확인)상 g6e.2xlarge는 기준 5.0 / 버스트 20 Gbps다. g7.2xlarge는 40 / 60 Gbps다. g7e.2xlarge는 50 Gbps 고정이라 크레딧 대상이 아니다.
- 따라서 "18% of the cap"은 "기준 대역폭의 18%"로 고쳐야 한다(흐름당 상한과 기준 대역폭이 우연히 같은 5 Gbps다).
- 더 중요한 문제가 있다. 단일 흐름(≤5 Gbps)은 기준 대역폭 5 Gbps를 넘지 않는다. 그래서 부하 전후의 단일 흐름 iperf(4.967 → 4.966)로는 크레딧 소진을 잡아낼 수 없다. 소진되면 합계가 기준으로 떨어지는데 단일 흐름은 그 아래에 있기 때문이다. 여러 흐름으로 사후 측정해야 한다(4흐름 19.86은 부하 전에만 쟀다).
- "averaged 0.91 Gbps"는 측정값이 아니라 요청당 230 MB(4,096 × 57.6 KB)를 가정한 계산값이다. E3 노드의 NIC 수집 파일은 0줄이다. 논문이 다른 곳에서 쓰는 FP8 4K 280 MiB로 계산하면 1.12 Gbps(기준의 22%)다.
- "Two things did not help or hurt"는 틀린 문장이다. 호스트 스테이징은 성능을 떨어뜨렸다.
- 수정: 크레딧 주장을 측정한 부하 범위(g6e, 0.5 req/s, 15분)로 한정하고, 위 문장들을 고친다.

**7. [필수: 서술 / 권장: 실험] 빠진 대안이 있고 문제 설정 전제를 밝혀야 한다.**
- ENA Express(단일 흐름 최대 25 Gbps)는 2xlarge를 지원하지 않는다. g6e.12xlarge, g7.24xlarge, g7e.12xlarge 이상부터다(ena-express.html, 직접 확인). 본문에 쓰면 오히려 설정의 현실성이 강해진다. 노트는 기본 설정 시절의 가설(라이브러리가 천장)로 ENA Express를 우선순위에서 내렸는데, 이후 튜닝 뒤 흐름당 상한이 병목이 되었으므로 논의를 다시 해야 한다.
- EFA는 단일 GPU인 g6e.8xlarge, g7.8xlarge, g7e.8xlarge에서 지원된다(ac.html, 직접 확인). "단일 GPU라서 RDMA가 없다"는 전제는 실제로는 인스턴스 크기를 고른 결과다. §1의 "Rented cloud GPUs often have neither"와 §5.2의 "With RDMA or AWS EFA … we did not measure that baseline"에 이 점을 밝히고, 8xlarge+EFA와의 비용 비교를 논의해야 한다.
- 인프라 관점에서 "설정"에 해당하는 다른 대안도 있다.
  - g7e.2xlarge는 ENI를 4개까지 붙일 수 있고, UCX 레일은 장치 단위라 ENI를 추가하면 레일이 생긴다(노트는 "ENA 1개라 레일 무효"로 정리했을 뿐 ENI 추가는 시험하지 않았다).
  - AWS 문서가 단일 흐름 대역폭을 늘리는 방법으로 직접 권하는 MPTCP.
  - NCCL 소켓 병렬화(NCCL 기반 커넥터), Mooncake TE, UCCL.

**8. [권장] 부록 A1의 tc는 흐름당 상한이 아니라 합계 상한이다.**
- `tc qdisc replace dev $IF root tbf ...`로 인터페이스 루트에 걸었으므로 모든 흐름의 합계를 제한한다.
- 흐름당 상한 4.97이 이미 걸린 상태에서 tbf 5 Gbps를 더하자 TTFT가 25% 늘었다(471 → 587 ms). 두 제약이 다르다는 증거다. 이 5 Gbps 점은 그림 A1에는 있지만 본문에는 없다.
- 수정: "Artificially limiting bandwidth shows that this cap sets TTFT"를 "link bandwidth"로 바꾸고 5 Gbps 점을 본문에서 설명한다.

**9. [권장] 호스트 스테이징 결과를 해석하려면 프로파일이 필요하다.**
- 0.25 req/s에서 요청당 약 2.3 s가 추가됐다(2,942 − 624 ms). 140 MiB의 PCIe 복사(수십 ms 이내)로는 설명되지 않는 크기다. 8.73 GiB 호스트 미러 전체를 약 4 GB/s로 복사하는 시간과 비슷하다(추정). nsys 프로파일이 필요하다.
- 1 req/s의 75배는 불안정한 대기열(서비스 시간 > 도착 간격)에서 나온 값이라 측정 길이(180 s)에 따라 달라진다. 비율 대신 최대 안정 요청률을 보고한다.
- 측정 조건도 명시한다: g7(호스트 30 GiB 중 22 GiB 사용), GPU 메모리 점유율 0.70. 호스트 메모리가 큰 g7e에서도 같은지 알 수 없다.
- 링크 전송률은 7.3~9.4 Gbps로 올랐다는 사실(비용이 vLLM 복사로 옮겨 갔을 뿐)을 함께 적는다.

**10. [권장] 일반화 범위를 밝힌다.**
- 흐름당 상한은 AWS의 정책이다. GCP 문서는 VPC 밖으로 나가는 5-tuple 상한과 머신 계열별 단일 흐름 수치를 따로 적는다(검색 요약만 봤고 원문은 확인하지 않았다).
- m(1.3~1.7)도 이 AWS 설정과 NIXL 1.4.1·vLLM v0.30.0의 분할 규칙에 묶인 상수다.
- 수정: 초록과 한계 절에서 범위를 밝힌다. 다른 클라우드에서 쓸 수 있도록 iperf3 -P 1과 -P N 측정 절차를 제시한다. 결론의 "per-connection bandwidth"를 "측정한 연결당 대역폭 × 실제 동시 연결 수"로 정의한다.

## 사소한 지적
- §3.1 "reached only by aggregating eight flows": 5~7흐름은 측정하지 않았다. 4흐름이 38.1 Gbps였으므로 "with eight"가 정확하다.
- 4.97 Gbps는 5 Gbps에서 MTU 9001 기준 TCP/IP 헤더(약 0.6%, 5 × 8949/9001 ≈ 4.97)를 뺀 값과 일치한다. 이 확인을 본문에 넣으면 좋다. 9.54는 문서의 "up to 10 Gbps" 범위 안이다.
- 그림 2 캡션 "four alternative settings": 회색 점 4개 중 13.86은 기준 설정을 다시 잰 값이다. 대안 설정은 세 개다.
- 같은 280 MiB 전송인데 디스크립터 수가 로그 창마다 1,589~2,148로 달라진다(`xfer_full_E4.log`). 본문과 노트의 조각 수 추론에 불확실성이 있다.
- 4.97이 g5·g6e·g7·g7e 네 쌍 모두에서 나왔다는 점을 명시한다.
- RTT를 어디에도 보고하지 않는다. TCP 논문이라면 필수 정보다.

## 저자에게 묻는 질문
1. 전송 한 건이 쓰는 TCP 연결은 몇 개이고, 소켓별 전송률은 얼마인가?
2. 사전 예측에 쓴 m 값과 항별 예측값(전송, 잔차)은 무엇인가?
3. wmem_max/rmem_max, 혼잡 제어 알고리즘, tcp_slow_start_after_idle은 어떻게 설정되어 있었나?
4. 8xlarge+EFA나 ENI 추가를 검토했나? 2xlarge를 고른 이유는 무엇인가?
5. 실효 전송률은 vLLM의 합계 비율로 계산했나? 동시 전송이 겹칠 때는 어떻게 해석하나?
6. TX_SEG_SIZE만 256 KB로 올린 단독 측정이 있나?
7. 호스트 버퍼 모드의 추가 2.3 s는 어느 복사에서 생기나?

## 확인한 문서
- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-network-bandwidth.html (직접 확인: 배치 그룹 밖 단일 흐름 5 Gbps, 클러스터 배치 그룹 최대 10 Gbps, MPTCP, ENA Express 최대 25 Gbps, "up to" 인스턴스의 크레딧)
- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ena-express.html (직접 확인: 지원 인스턴스 목록)
- https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html (직접 확인: g6e/g7/g7e 기준·버스트 대역폭, EFA·ENA Express 지원, 최대 ENI 수)
- https://docs.vllm.ai/en/latest/api/vllm/distributed/kv_transfer/kv_connector/v1/nixl/stats/ (직접 확인, latest 판: `/ 2**20`, `total_mb / total_time_seconds`)
- https://docs.cloud.google.com/compute/docs/network-bandwidth (검색 요약만, 원문 미확인)
- UCX 소스: 원문을 확인하지 않았고, RESULTS.md의 인용에 의존했다.

## 검토한 저장소 자료
- paper/en/main.tex
- RESULTS.md (세션 P, B, D, E2~E5)
- harness/make_figures.py
- results/E2/run_E2b.log
- results/E4/collect/ip-172-31-90-227/xfer_full_E4.log
- results/E4/collect/*/collect_*_nic.txt
- configs/tc.md, configs/run_D2.sh
