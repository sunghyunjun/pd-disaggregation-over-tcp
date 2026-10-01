# R3 (네트워크·클라우드·KV 전송) 4차 심사평: 원고 v4

대상: paper/en/main.tex v4. 저장소는 읽기만 했다. 스크립트: `reviews_v4/r3/r3v4_xfer.py`(전송 로그 집계), `r3v4_boundary_sens.py`(`boundary_model.py` 함수를 불러 쓴 민감도).

## 1. 요약

6절 경계 모델의 전송 항은 식 (2)를 m = 1, C_flow = 9.54 Gbps로 계산한다. V(L), 220 KiB/토큰, 경계 위치(50 ms에서 21K, 30 ms에서 11K)는 스크립트와 로그로 재현된다. 그러나 m = 1은 모델이 가정한 저부하에서 분리에 불리하다. 긴 전송은 네 조각으로 고르게 나뉘고, 가장 가까운 실측 사례(31B 4K, 560 MiB)는 m = 1.8이었다. 이 값을 넣으면 50 ms 경계는 약 14K로 당겨진다. 그러므로 초록의 "roughly 20K"는 범위로 써야 한다. "fast link (×0.05)"는 g7e.8xlarge EFA의 대역을 넘지만, ×0.1로 바꿔도 결과가 같아 결론은 선다. all-global 반사실은 이름이 계산과 다르고, 오프로딩 문장은 원격 TCP 적재와 로컬 PCIe 적재를 가르지 않는다. 모두 문안과 기존 스크립트 출력으로 고칠 수 있다.

## 2. 점수

**4.0 / 5.** 측정과 전송 기제 서술은 공개 수준이나, 경계의 헤드라인 수치가 m 하나로 약 7K 토큰 움직이므로 범위와 편향 방향을 밝혀야 한다.

## 3. 반드시 고칠 것

**N1. m = 1의 편향 방향과 경계 범위 (L247, L273, L290, L299, L300; 초록 L32, L51, L312, L354)**
- 표 3은 m = 1.5로 검증했고 지도는 m = 1을 쓴다. m = 1이면 4K 배치 그룹 1P1D 검증점이 431 ms로 실측 362 ms보다 19% 높다[검증].
- 긴 전송에서 m은 오히려 커진다. 26B는 약 16K 토큰부터 디스크립터가 4,096개를 넘어 네 조각으로 고르게 나뉜다[미검증, 블록 구조에서 산술]. 같은 조건인 31B 4K(4,480 디스크립터)는 저부하에서 m = 1.79–1.83이었다(E5–E8 여섯 런)[검증]. 배치 그룹 밖 E2의 16K FP8 쌍(1,286 − 820 ms)도 520 MiB 전송에 m ≈ 1.8–2.0을 함의한다[검증]. 상한은 7변수 묶음에서 관측된 합계 19–21 Gbps, 곧 m ≈ 2.0–2.2다.
- m = 1.8이면 50 ms 경계는 약 14K, 30 ms 경계는 약 6K로 당겨진다. b × 0.85와 함께 넣으면 50 ms 경계는 약 18K다[검증]. 원고의 "19K–25K"는 한쪽 끝만 덮는다.
- 부하 쪽 하방 위험은 장입력에서 오히려 작다. 프리필 노드가 포화일 때 내는 KV 유량은 4K에서 23.5 Gbps지만, 16K에서는 6.9 Gbps, 32K에서는 3.6 Gbps로 한 흐름(9.54 Gbps)보다 낮다[검증, 모델 산술]. 4K에서 m을 떨어뜨린 대기열은 1P1D 장입력에서는 덜 생긴다. 다만 xP1D 팬인이나 all-global KV(32K에서 30 Gbps)에서는 다시 생긴다.
- 문안(L299): "Transfer rate. Transfers above 4,096 descriptors (26B inputs above about 16K) split into four even pieces; the closest measured case, 31B at 4K (560 MiB), ran at m = 1.8 at low load. With m = 1.8 the window opens near 14K tokens at 50 ms and 6K at 30 ms. Our base m = 1, the rate we measured under load at 4K, is pessimistic for disaggregation at low load. At a 50 ms gap limit the window opens between roughly 14K and 25K tokens."
- L300 뒤에 덧붙일 문안: "At long inputs a prefill node produces KV more slowly than one flow carries it (about 7 Gbps at 16K and 3.6 Gbps at 32K), so a 1P1D pair's transfers queue less than at 4K; several prefill nodes per decode node, or an all-global KV cache, bring the queue back."
- 초록·L51·L312·L354의 "roughly 20K"는 "roughly 15–25K"로 바꾼다. 표 3 캡션에는 지도가 m = 1을 쓴 이유를 한 문장으로 적는다.

**N2. "fast link ×0.05"의 해석과 EFA 병치 (L283 캡션, L297, L325)**
- ×0.05는 m = 1 전송 시간의 5%로, 유효 191 Gbps에 해당한다[검증]. g7e.8xlarge의 NIC는 100 Gbps이고 GPUDirect RDMA가 없다[미검증, 3차 R3의 AWS 문서 확인]. EFA로는 많아야 ×0.1 수준이다. 그런데 L325는 EFA 문장 바로 뒤에 "a link 20× faster opens the window at 4–6K"를 둬서, EFA가 20배라고 읽힌다.
- 결론은 이 선택에 둔감하다. ×0.1도 경계 첫 칸이 ×0.05와 같다(50 ms 5.8K, 30 ms 4K)[검증]. ×0.2(인스턴스 전체 50 Gbps를 TCP로 쓰는 경우)는 50 ms에서 8K다[검증].
- 창은 좁다. 5.8K·50 ms에서 231 대 253 ms, 4K·30 ms에서 181 대 253 ms다[검증]. 잔여 87 ms(31B 실측)면 50 ms 창은 8K에서 열린다[검증].
- L297 문안: "With a transfer 10–20× faster than one TCP flow (about 95–190 Gbps effective), the window opens near 6K tokens at 50 ms and 4K at 30 ms, at first only for TTFT limits of about 0.2–0.25 s (8K at 50 ms with an 87 ms residual)."
- L325 문안: "On g7e.8xlarge, EFA's line rate is 100 Gbps without GPUDirect RDMA, about ten times one TCP flow; in the model a tenfold faster transfer gives the same boundary as a twentyfold one (Figure 7, dotted). We did not measure EFA, and the model assumes low load."

**N3. all-global 반사실의 이름 (L283, L296, 범례)**
- 220 KiB = 25 슬라이딩 층 × 8 KiB + 5 전역 층 × 4 KiB(BF16)다[검증, config.json]. 이것은 "슬라이딩 층이 창 없이 모든 토큰을 보관할 때"의 크기다. "every layer were global"로 읽으면 전역 층 형상(KV 헤드 2 × 512)으로 30층 × 4 KiB = 120 KiB/토큰이 된다[검증]. 120 KiB로 계산하면 50 ms·m = 1에서는 여전히 창이 열리지 않고, m = 1.8에서는 약 42K에서 열린다[검증]. 연산량(b)은 그대로 두었다는 점도 밝힌다.
- L296의 "meets no TTFT limit that replicas miss up to 64K"는 30 ms 패널에서 틀린다. 약 35K를 넘으면 복제본은 어떤 청크로도 한도를 못 지키고, 1P1D(all-global)는 9.1–19.3 s로 지킨다[검증]. "at TTFT limits up to about 9 s"로 한정한다.
- 문안: "a KV cache as large as if the sliding-window layers kept every token (220 KiB per token in BF16), with compute unchanged".

**N4. KV 오프로딩 문장 (L69, L319)**
- "same size"는 전체 프롬프트가 적중할 때만 맞다. 부분 적중이면 접두부 KV만 오고, 저장소가 슬라이딩 층 KV를 모든 토큰에 대해 보관하면 더 커질 수 있다[미검증].
- "84 ms to move 140 MiB"는 NIXL의 네 연결 분할(m ≈ 1.47) 덕분이다[검증, E5 84.1 ms]. 저장소가 TCP 연결 하나를 쓰면 m ≤ 1이므로 123 ms 이상 걸린다[검증, 산술]. 비교 대상인 130 ms에는 적재로도 없어지지 않는 고정 비용(스케줄링, 첫 디코드 스텝)이 들어 있다.
- 로컬 CPU 계층은 같은 바이트를 PCIe로 옮긴다. 수십 GB/s로, 우리 TCP 경로 1.7 GB/s보다 한 자릿수 빠르다[미검증, 추정].
- L69 문안: "Loading a full prompt's KV cache from another node moves at least V(L), the bytes of a disaggregated transfer; loading it from local CPU memory moves the same bytes over PCIe rather than the network."
- L319 문안: "If KV caches are reused across nodes, loading one over TCP takes V(L)/(m × C_flow), with m ≤ 1 if the store uses one connection. For 26B NVFP4 at 4K this is 84–123 ms for 140 MiB against a colocated TTFT of about 130 ms, part of which loading does not remove, so remote loading at 4K saves GPU time more than TTFT; longer prompts favor loading. A local CPU tier is a different regime. We measured neither."

**N5. 4K 일치 주장 (L289)**
"1P1D needs 0.42 s"는 m = 1 값이다. 실측은 362–384 ms(GPU당 0.5–1)다[검증]. "0.42 s at m = 1 (0.33 s at m = 1.5; measured 0.36–0.38 s)"로 쓴다.

**N6. FP8 체크포인트 서술 (L98)**
RedHatAI FP8-dynamic은 가중치 FP8(채널별)과 활성값 FP8(토큰별 동적)을 쓰는 W8A8이다. weight-only가 아니다[검증, config.json]. KV는 BF16이 맞다(kv_cache_scheme 없음).

## 4. 고치면 좋은 것

1. 향후 과제로 한 문장을 넣는다. 층별·청크별 겹침 전송이 하이브리드 모델에서 동작하면, 16K 이상에서는 전송(m = 1에서 16K 0.46 s, 32K 0.74 s)이 프리필(0.64 s, 1.98 s)보다 짧으므로 거의 숨길 수 있다[검증, 모델 산술]. 모델이 빼놓은 또 하나의 상방이다.
2. 범례 "hybrid KV (as measured)"는 곡선 전체를 실측으로 오해하게 한다. "(this checkpoint's KV, m = 1)"로 바꾼다.
3. 결론의 "plan on about one flow's rate"에 "under load; long transfers reached about 1.5–1.8 flows at low load"를 붙인다.
4. `boundary_model.py` 민감도 출력에 m = 1.8, ×0.1, ×0.2, 잔여 87 ms, 120 KiB 행을 더한다.
5. 초록의 "only disaggregation meets both limits"는 "disaggregation meets TTFT limits that replicas cannot"로 바꾼다. 32K에서도 3.5 s 이상의 한도에서는 둘 다 지킨다.

## 5. 검증 기록

| 수치 | 원고 | 결과 |
|---|---|---|
| FP8 V(4K) = 280 MiB | L102 | 로그 280.0(E7 26F·26H) [검증] |
| FP8 V(16K) ≈ 520 MiB | L176, 표 3 | NVFP4 로그 260 × 2. FP8 16K 전송 로그는 없다(E2 미기록) [검증, 산술] |
| 32K 840 MiB·6.9 GiB, 220 KiB = 25 × 8 + 5 × 4 | L296 | 840, 6.875 GiB, config.json [검증]; 전역 형상이면 120 [검증] |
| 경계 21,247/10,624, m 1.5 19,484/7,512, fast 5,793/4,096, b × 0.85 25,268; m 1.8 13,777/6,317 | L290–299 | 재실행 일치, m 1.8은 신규 [검증] |
| 4K 1P1D 362/384 ms, 모델 349(m 1.5)/431(m 1) | L289, 표 3 | [검증] |
| FP8 4K m 1.46–1.61, 31B 4K m 1.79–1.83 | L160 | E7·E5–E8 로그 [검증] |
| E2 16K 차이 466/506 ms → m ≈ 1.8–2.0 | L176 | [검증] |
| D 세션 16K 268–281 ms, 32K 375–406 ms → m 1.56–1.86(4.97 기준) | 신규 | [검증] |
| 84 ms/140 MiB, 동시 배치 TTFT 130 ms, 한 흐름 123 ms | L319 | E5 84.1, figures.json 130 [검증] |
| 제공 KV 11.7 Gbps; KV 유량 23.5/6.9/3.6 Gbps; ×0.05 = 191 Gbps | L205, 신규, L297 | 산술 [검증] |
| g7e.8xlarge 100 Gbps·GDR 없음, 로컬 PCIe 적재 속도 | L325, 신규 | [미검증] |
