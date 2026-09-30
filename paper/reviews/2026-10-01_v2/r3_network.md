# Reviewer 3 (네트워크·클라우드) 3차 심사평

대상: "Chunked Prefill or Disaggregation? Prefill–Decode Serving over TCP on Single-GPU Cloud Instances" (paper/en/main.tex, draft v2, 2026-10-01, 25쪽)
판정 요지: **4/5, 확신도 4/5.** 2차 필수를 나눈 8개 항목 가운데 4개는 반영됐고, 3개는 대부분, 1개(환경 정보)는 부분 반영이다. 전송 기제 서술은 이제 소켓 데이터와 NIXL 소스에 대체로 맞는다. 다만 이번에 공개 데이터를 다시 보니 새로 고칠 곳이 네 군데 나왔다. (1) E9의 P 청크 8,192 런은 UCX 설정도 바꿨는데 원고는 이를 밝히지 않는다. 이 런의 판정 부하 전송률은 원고의 m 범위 밖이다. (2) "31B chat transfers, which are not split"은 원고가 적은 분할 규칙과 스스로 어긋난다. (3) 7변수 묶음의 기제 문장이 부록 C와 서로 다르다. 실제 기제(수신 창 배율 2)는 ss에 직접 찍혀 있다. (4) 그림 5(c)는 2차 필수 지적 그대로 남았다. 새 실험은 필요 없다. 모두 원고 수정과 기존 데이터 재집계로 끝난다.

---

## 요약

v2에서 네트워크 쪽 주장은 다음과 같이 바뀌었다.
1. 초록에서 "four TCP connections, 1.5–1.8×"가 빠졌다. 전송 비용은 "a larger UCX TCP segment made 3.4× faster"로만 남았다.
2. §4.5 둘째 문단이 NIXL 분할 규칙(1,024 디스크립터 하한), 26B 2~3조각과 31B 4조각, 공유 연결(다섯째)을 설명한다.
3. m을 "effective rate / C_flow"로 다시 정의했다. 저부하 1.4–1.6(26B)과 1.8(31B), 판정 부하 0.92–1.14(26B), 31B 대화 0.81을 보고한다.
4. 31B 4연결 합계 19–21 Gbps를 "a shared per-node limit that we did not identify"로 적고, "More connections alone are therefore not a sure lever"로 바꿨다.
5. 7변수 묶음을 "13.5–14.2 Gbps, 5–10% lower … receive window for about 40% of its busy time"로 고쳤다.
6. 식 (1)을 일반형 V(L) = b_g·L + b_w·min(L, W)로 쓰고, W = 1,024, b_w ≈ 100 KiB로 적었다. 단위 환산은 Gbps = 0.008389 × MiB/s로 바로잡았다.
7. EFA 문단에 vCPU 4배와 libfabric 경로 차이를 넣었다.

이 가운데 2의 기본 골격, 4, 6의 계수, 단위 환산은 내가 다시 확인한 데이터·소스·설정과 맞는다. 특히 식 (1)은 원고가 쓴 것보다 강하게 뒷받침된다. Hugging Face config.json에서 계수를 직접 계산할 수 있고, 대화 런의 전송량을 입력 길이로부터 0.1 MiB까지 맞힌다(권장 5). 반면 다음 네 가지는 데이터와 어긋나거나 빠졌다.
- E9-5(1P1D, P 청크 8,192)는 **UCX 세그먼트만** 설정으로 돌았다(`configs/run_E9.sh:25` `UCXSET=SEG`, `results/E9/run_E9.log` "ucx=SEG"). 원고 §3.1과 부록 C는 "E4–E9 모두 7변수"라고 적는다. 이 런의 판정 부하 전송은 같은 시드의 E8 7변수 런보다 **느렸다**(m 0.65–0.81 대 0.88–1.04).
- 31B 대화 전송의 31–35%(바이트 기준 75–80%)는 1,024 디스크립터를 넘는다. 원고의 규칙대로라면 나뉘는 전송이다.
- 7변수 묶음은 소켓 버퍼를 8 MB로 "고정"하지 않았다. 커널 한도에 잘렸고, 그 결과 D 쪽 수신 창 배율(wscale)이 2로 정해졌다. 광고할 수 있는 창의 상한은 262,140 B다.
- 그림 5(c) 제목·캡션과 "kept all four busy 64% of the time"은 TCP busy 시간 기록(평균 1.94연결)과 맞지 않는다.

---

## 2차 지적 반영 점검

좌장이 넘긴 여덟 항목(2차 필수 1–5를 나눈 것)부터 본다.

| # | 2차 지적 | 판정 | v2의 근거 / 남은 문제 |
|---|---|---|---|
| 1 | 26B 전송 조각 수(4연결 아님, 2~3조각) | **반영** | 초록에서 "four TCP connections"가 빠졌다. §4.5: "A 26B 4K transfer … in two or three pieces, a 31B 4K transfer … in four". 기여 목록도 "splitting of a transfer over up to four connections"로 바뀌었다. 남은 것은 규칙 서술의 정밀도다("pieces of at least 1,024", 디스크립터 범위 → 권장 8). |
| 2 | 다섯째 연결의 역할 | **대부분** | "a chat-sized transfer as a single piece on a shared connection", "a fifth, shared one carried the rest". 역할은 맞게 적었다. 그러나 4K 런에서도 1,024 디스크립터 미만인 전송이 통째로 이 연결로 가서 두 배 가까이 걸린다는 점(꼬리)은 없다. "chat-sized"도 31B에는 맞지 않는다(필수 2). |
| 3 | 공유 상한 약 19–21 Gbps | **반영** | "With all four connections busy, 31B transfers aggregated 19–21 Gbps, about half of what four iperf flows reached (38 Gbps), which points to a shared per-node limit that we did not identify." 좌장 D6의 표현 그대로다. 다만 이 상한은 7변수 묶음에서만 관측됐고, 그때 송신자는 네 연결이 모두 움직일 때도 busy의 39%를 수신 창에 막혀 있었다. 이 조건을 적어야 한다(권장 7). |
| 4 | "more connections … remaining lever" 철회 | **반영** | "More connections alone are therefore not a sure lever." §5.3의 "m depends on NIXL's thread count"도 "NIXL's splitting rule belongs to one version"으로 바뀌었다. |
| 5 | m의 정의와 부하 의존 | **대부분** | "m = effective rate / C_flow"로 정의했고, 저부하·판정 부하·31B 대화 값을 보고한다. 체크리스트 3도 "m measured at the target load"로 바뀌었다. 남은 문제는 세 가지다. 통계 종류(10초 창 중앙값인지 전송 가중 평균인지)가 없다. 31B 대화 0.81의 설명("not split")이 틀렸다. E9-5의 0.65–0.81이 빠졌다(필수 1·2). |
| 6 | 7변수 묶음이 느린 이유는 수신 창 | **대부분** | "13.5–14.2 Gbps, 5–10% lower … limited by the receive window for about 40%". 수치는 맞다(런 내 증분 39–44%, 31B 38–45%). 그러나 "it fixes the socket buffers at 8 MB"는 틀렸다. 부록 C의 "capped by the kernel's maximums"와도 모순된다. 기제는 wscale 2다(필수 3). |
| 7 | 환경 정보 | **부분** | NIXL 1.4.1은 들어갔다. MTU 9001·MSS 8949, 혼잡 제어 cubic, 배치 그룹 최소 RTT, 커널, rmem_max·wmem_max, UCX 버전, iperf 옵션, 4.97 = 5 × 8949/9001은 여전히 없다(필수 3). |
| 8 | Gbps 환산 | **반영** | "Gbps = 0.008389 × MiB/s". 1 MiB/s = 8,388,608 bit/s = 0.0083886 Gbps다. 맞다. |

2차 권장과 사소 지적의 반영은 다음과 같다.

| 2차 항목 | 판정 | 비고 |
|---|---|---|
| 권장 6 대기열 계산(S, λ, ρ, 통계) | 부분 | "explains"가 "is consistent with"로 바뀌었다. S = 1.18 s, λ = 0.5/s, ρ = 0.59와 비교 통계(중앙값 2.19 s)는 없다. M/D/1 평균으로 계산하면 1.5 + 0.85 = 2.35 s이고, 원고의 "about 2.2 s"와 차이가 난다(권장 10). |
| 권장 7 "세그먼트가 이득 전부" 범위 | 부분 | §4.5 첫 문단은 g7 D 세션의 TTFT 이득을 "the seven-variable change"로 정확히 귀속했다. 그러나 §3.1의 "the TCP segment size accounts for the gain"은 범위 한정 없이 남았다. E9-5를 보면 이 비교는 판정 부하에서 성립한다고 말할 수 없다(필수 1). |
| 권장 8 EFA 교란 | 반영 | vCPU 4배와 libfabric 경로를 적었다. MPTCP·ENI·UCCL 한 문장은 없다(좌장 D9는 한 문장만 요구). 추가할 교란이 두 가지 있다(권장 9). |
| 권장 9 그림 5(c) 지표·간격 | **미반영** | 제목 "Four connections per P–D pair", 캡션 "Share of transfer time … every 0.1 s"가 그대로다. 좌장 A7의 요구 사항이다(필수 4). |
| 권장 10 나뉘지 않은 전송의 꼬리 | 미반영 | 권장 8로 다시 적는다. |
| 권장 11 호스트 스테이징 조건 | 부분 | GPU 메모리 0.70이 §3.1에 들어갔다. 링크 전송률(7.3–9.4 Gbps)은 없다. |
| 사소 1(단위식) | 반영 | |
| 사소 2(1.5–1.8의 통계) | 미반영 | 필수 2. |
| 사소 3(그림 5 윗제목 합계율) | 미반영 | 그림에는 여전히 "(0.5 and 0.25 requests/s)"로 찍혀 있고, 캡션은 GPU당 0.25·0.125다. |
| 사소 4(g7.2xlarge 가격 "--") | 미반영 | |
| 사소 5(크레딧 문장에 g7) | 미반영 | g7.2xlarge는 AWS 표 기준 40/60 Gbps다(직접 확인). |
| 사소 7(푸시 MiB) | 반영 | "468–533 MiB". |
| 사소 8("22–27%", 기본 조건 21.5%) | 미반영 | |
| 사소 9(4.97이 네 쌍 모두) | 미반영 | |
| 사소 10(스레드별 엔드포인트는 D 쪽) | 반영 | P 쪽 서술이 빠졌다. |

---

## 강점

- **전송 기제 서술이 데이터 쪽으로 돌아왔다.** 초록의 과잉 주장이 빠졌다. 분할 규칙, 조각 수, 공유 연결, 공유 상한, "not a sure lever"가 모두 소켓 표본·소스와 맞게 적혔다. 2차에서 가장 컸던 문제(필수 1·2)가 풀렸다.
- **m을 연결 수가 아니라 비율로 정의했다.** 판정 부하에서 1 근처로 떨어진다는 사실도 본문과 체크리스트에 들어갔다. 실무자가 저부하 값을 그대로 쓰는 위험이 크게 줄었다.
- **식 (1)의 일반형은 정확하다.** 계수를 모델 설정에서 직접 유도할 수 있고, 대화 런 전송량을 입력 길이만으로 0.1 MiB까지 맞힌다(아래 권장 5). 원고가 스스로 쓴 것보다 강한 결과다.
- 원자료 공개 수준이 여전히 높다. ss 원문, vLLM 전송 로그, 노드별 sar, 런별 입력 길이가 모두 있다. 그래서 이번 심사의 새 지적(창 배율, 대화 분할 비율, E9-5 비교)도 전부 저자 데이터로 확인할 수 있었다.
- EFA 문단이 "EFA면 이긴다"는 인상을 주지 않게 바뀌었다. 전송 항만 줄고 잔차·디코드 배치·청크 트레이드오프는 남는다는 구분이 정확하다.

---

## 주요 약점

### [필수 1] E9-5(P 청크 8,192)의 UCX 설정을 밝히지 않았고, 그 런의 전송 데이터가 원고 주장의 범위 밖이다

**문제.** 원고는 세 곳에서 E9-5가 7변수 묶음을 썼다고 읽히게 쓴다.
- §3.1: "Unless stated otherwise, disaggregated runs used seven UCX environment variables".
- 부록 C: "The tuned set used in sessions E4–E9".
- §4.3, 그림 3 캡션, 부록 D, 표 F1은 "8,192-token prefill chunk"만 말한다.

그런데 E9-5는 **세그먼트 크기 두 변수만** 썼다. 근거는 셋이다. `configs/run_E9.sh:25`의 `PCHUNK=8192 PROXY_KIND=aio UCXSET=SEG`, `configs/lib_E9.sh:19`의 `SEG="… UCX_TCP_TX_SEG_SIZE=256k UCX_TCP_RX_SEG_SIZE=256k"`, `results/E9/run_E9.log`의 "[26_1P1D_aio_p8192] proxy=aio ucx=SEG pchunk=8192"다. 커밋된 예측 5(RESULTS.md "P 청크 8,192 + UCX 세그먼트만")에도 적혀 있다. 즉 저자는 알고 있었고 원고에서만 빠졌다. 이 런은 두 변수를 동시에 바꾼 것이다.

**전송 데이터.** 같은 요청률·반복 번호는 시드가 같으므로 E8 7변수 aiohttp 런과 짝지어 비교할 수 있다(`r3v2_xfer.py`).

| GPU당 4, 26B 4K | UCX | P 청크 | 첫 토큰 p50 | 평균 전송(전송 가중) | 10 s 창 중앙값 | m (창 중앙값 / 가중) | 창 p90÷평균 |
|---|---|---|---|---|---|---|---|
| E8 #0 | 7변수 | 2,560 | 526 ms | 139.6 ms | 8.77 Gbps | 0.92 / 0.88 | 1.43 |
| E8 #1 | 7변수 | 2,560 | 477 ms | 118.6 ms | 9.88 Gbps | 1.04 / 1.04 | 1.34 |
| E8 #2 | 7변수 | 2,560 | 499 ms | 123.5 ms | 9.70 Gbps | 1.02 / 1.00 | 1.36 |
| **E9 #0** | **세그먼트만** | 8,192 | 451 ms | **190.0 ms** | **6.50 Gbps** | **0.68 / 0.65** | 1.65 |
| **E9 #1** | **세그먼트만** | 8,192 | 416 ms | **165.1 ms** | **7.77 Gbps** | **0.81 / 0.75** | 2.05 |

- 짝지은 시드에서 전송은 46–50 ms **느려졌다**. 첫 토큰 중앙값에서 평균 전송을 뺀 나머지는 386 → 261 ms, 358 → 251 ms로 107–125 ms 줄었다. 거친 분해지만, 원고가 보고한 첫 토큰 개선(약 500 → 416–451 ms)은 전송이 나빠졌는데도 프리필 쪽에서 더 크게 벌어서 생긴 것이다.
- 원인은 링크 용량이 아니다. P 노드 sar(1초, 헤더 포함)의 평균 송신률은 두 세션 모두 제공 부하 9.4 Gbps와 같았다. 1초 최고치는 E8 7변수가 12.4–12.9 Gbps(GPU당 3–4, 8런), E9-5가 15.2 Gbps였다(`r3v2_sar.py`). 창 안 전송 시간의 퍼짐(p90÷평균 1.65–2.05 대 1.34–1.43)은 전송이 더 자주 겹쳤다는 해석과 맞는다. P 청크 8,192에서는 4K 프리필 둘이 한 스텝에서 끝나 KV 전송이 짝으로 출발할 수 있다. 가설로 적는다.
- GPU당 5에서는 차이가 더 크다. E9-5의 전송 가중 평균은 922 ms(창 중앙값 438 ms, m 0.13–0.28)이고, E8 7변수는 177 ms(m 0.69)다. 그런데 이때도 P 노드 송신 평균은 11.70 Gbps로 제공 부하(11.74)와 같았고, 1초 최고치는 17.1 Gbps였다. 전송 시간의 대부분이 링크 밖(양쪽 호스트의 처리·대기)에서 쓰였다는 뜻이다(권장 6).

**왜 필수인가.** 세 가지 주장이 걸린다.
1. §4.3의 "Raising the prefill chunk to 8,192 tokens cut 1P1D's median TTFT"는 두 변수의 합이다. 귀속을 밝혀야 한다.
2. "At the loads where our verdicts were decided it fell to 0.92–1.14 for 26B"는 E9-5를 빼야 성립한다. 이 런은 판정 표(F1)에 들어 있는 결정적 점이다.
3. §4.5의 "segment sizes alone … 5–10% faster"는 GPU당 0.25에서만 쟀다. 판정 부하에서 세그먼트만 쓴 유일한 점은 7변수보다 느렸다. 교란돼 있어서 UCX 설정의 효과인지 P 청크의 효과인지 가를 수는 없다. 그러므로 "세그먼트만이 더 빠르다"를 판정 부하로 일반화하면 안 된다.

**수정.**
- §3.1: "Unless stated otherwise, disaggregated runs used seven UCX environment variables …; the E9 run with an 8,192-token prefill chunk used the two segment sizes only."
- §4.3: "Raising the prefill chunk to 8,192 tokens, in a run that also used the segment sizes alone, cut 1P1D's median TTFT … Its transfers were slower than with the seven-variable set at the same seeds (165–190 against 119–140 ms on average), so the gain came from the prefill side."
- §4.5 m 문장: "0.92–1.14 for 26B (3–4 requests/s per GPU; 0.65–0.81 in the 8,192-token prefill run)".
- 부록 C: "used in sessions E4–E9 except the E9 prefill-chunk run". 부록 D와 표 F1의 해당 행에도 "segment sizes only"를 붙인다.
- 체크리스트 3의 "(it fell to about 1 in our runs)"는 "(0.65–1.14 at the loads we tested, lower for small transfers)"로 바꾼다.

### [필수 2] "31B chat transfers, which are not split"은 원고의 분할 규칙과 어긋난다. m의 통계도 하나로 정해야 한다

**31B 대화의 분할.** 대화 런의 입력 길이(result.json `input_lens`)로 전송별 디스크립터 수를 계산했다. 블록 구조는 26B 4K의 2,240 = 5 × 128 + 25 × 64(전역 32토큰 블록, 슬라이딩 16토큰 블록)에서 읽었다. 이 예측은 vLLM 로그의 평균 디스크립터 수와 맞는다(26B 402/413/404 = 로그 402/413/404, 31B 785–861 대 로그 785–845). 대화 전송에서는 블록 병합이 거의 없다는 뜻이다(`r3v2_chat_eq1.py`).

| | 26B 대화(E5·E7, GPU당 8) | 31B 대화(E8·E9, GPU당 4·6) |
|---|---|---|
| 입력 평균 / 중앙값 / 최대 | 226–232 / 99–112 / 1,023 | 220–242 / 93–116 / 1,023 |
| 1,024 디스크립터를 넘기 시작하는 입력 | 약 593토큰 | **약 290토큰** |
| 나뉘는 전송(개수 / 바이트) | 12–13% / 38–43% | **31–35% / 75–80%** |
| m (창 중앙값, 해당 부하) | 0.57–0.60 (GPU당 8) | 0.79–0.82 (GPU당 4, 7런) |

31B 대화 바이트의 4분의 3 이상이 나뉘는 전송에 실려 간다. 그러므로 "31B chat transfers, which are not split, reached 0.81"은 틀린 설명이다. m이 1 아래인 이유는 다른 데 있다. 나뉘는 대화 전송은 대부분 1,024 디스크립터(128 MiB) 조각 하나와 작은 나머지로 쪼개져 사실상 한 연결의 속도로 끝난다. 작은 전송에는 부피와 무관한 고정 비용이 섞인다. 31B 대화의 m은 부하에 따라서도 움직인다. GPU당 1–2에서는 0.94–1.05, 4에서 0.79–0.82, 6에서 0.52–0.57이다.

같은 이유로 §4.5의 "a chat-sized transfer as a single piece on a shared connection"도 한정해야 한다. 26B는 입력 약 590토큰 미만(대화 전송의 88%), 31B는 약 290토큰 미만(65%)일 때만 맞는다.

**m의 통계.** 같은 전송에 세 가지 통계가 섞여 있다.
- 31B 4K "m = 1.8"은 10초 창 중앙값(17.28 Gbps)이다. 전송 가중 평균으로는 15.77 Gbps, m = 1.65다.
- 그림 8의 31B 전송 283 ms는 E5 창 평균들의 평균이다. 전송 가중 평균은 297.6 ms다(E8에서는 297.9 ms).
- 식 (2)에 m = 1.8을 넣으면 274 ms가 나와 그림 8의 283 ms와도 다르다.

좌장 A8이 "정의를 캡션에 적고 하나로 맞춘다"고 요구한 부분인데 반영되지 않았다. 26B에서는 창 중앙값과 가중 평균이 거의 같아(1.47 대 1.48) 문제가 작다. 31B에서는 9% 차이다. 식 (2)가 평균 TTFT 분해라면 전송 가중 평균이 맞다.

**수정.**
- "31B chat transfers, which are not split, reached 0.81"을 다음으로 바꾼다. "31B chat transfers, of which about a third (three quarters of the bytes) exceed 1,024 descriptors but split into one 1,024-descriptor piece and a small remainder, reached 0.79–0.82 at 4 requests/s per GPU (0.94–1.05 at 1–2)."
- "a chat-sized transfer"는 "a transfer under 1,024 descriptors (26B inputs under about 590 tokens, 31B under about 290)"로 쓴다.
- m의 정의에 통계를 붙인다. 예: "transfer-weighted mean rate over a run". 1.8은 1.65로 바꾸거나 "median of 10 s windows"라고 적는다. 그림 8의 전송 막대도 같은 통계로 맞춘다.

### [필수 3] 7변수 묶음의 기제 문장을 고치고, 환경 문단을 넣는다

**기제.** §4.5는 "it fixes the socket buffers at 8 MB, which disables the kernel's buffer autotuning"이라고 쓰고, 부록 C는 "the fixed 8 MB buffers were capped by the kernel's maximums"라고 쓴다. 한 원고 안에서 서로 다르다. ss 원자료에는 이보다 직접적인 증거가 있다.

| 조건(E8 ss) | D 쪽 wscale (송신,수신) | D가 광고할 수 있는 최대 창 | D rcv_ssthresh | P rwnd_limited ÷ busy (런 내 증분) | P 연결당 busy 중 전송률 |
|---|---|---|---|---|---|
| UCX 기본 | 7,7 | ≥ 8 MiB | 0.46–5.46 MB | 0–8% | 3.8–4.2 Gbps |
| 세그먼트만 | 7,7 | ≥ 8 MiB | 3.49–5.47 MB | 0% | 7.1–8.4 Gbps |
| 7변수, 26B | **7,2** | **262,140 B** | 358,614–370,235 B | **39–44%** | 7.25–7.57 Gbps |
| 7변수, 31B | **7,2** | **262,140 B** | 363,430–371,896 B | **38–45%** (단독 연결 66%) | 7.56–8.91 Gbps |

- 7변수 두 런에서만 D(수신자) 쪽 수신 창 배율이 2다. 파일 전체 표본 9,045개와 17,695개가 모두 그렇다.
- Linux v6.8 `tcp_output.c`(직접 받아 읽음)에 따르면 `SO_RCVBUF`로 버퍼를 잠그면 연결 시점에 `window_clamp = tcp_full_space(sk)`가 되고(3864–3866행), 배율은 `ilog2(min(space, window_clamp)) − 15`로 정해진다(239–244행). 이후 광고 창은 `65535U << rcv_wscale`을 넘지 못한다(298행).
- 8 MB 요청이 기본 `rmem_max`(212,992 B)로 잘려 버퍼가 425,984 B가 되면 배율은 2가 된다. rcv_ssthresh 약 360–372 KB(= 425,984 × 약 0.85)도 이 값과 맞는다. rmem_max 값 자체는 기록이 없으므로 이 부분은 추론이다. 배율 2는 관측이다.
- P 쪽 수신 배율이 7인 것은 수동 연결 쪽이 버퍼를 잠그지 않았기 때문으로 보인다. 데이터는 P→D로 흐르므로 D의 배율이 결정한다.

그러니 정확한 서술은 "8 MB로 고정"이 아니다. "8 MB를 요청했지만 커널 한도에 잘렸고, 그 때문에 연결 시점에 수신 창 배율이 2로 정해져 창이 256 KiB에 묶였다"이다. 실무적 함의도 달라진다. 연결이 맺힌 뒤 rmem_max를 올려도 소용없다. 배율은 핸드셰이크 때 정해지기 때문이다.

**환경 문단(2차 필수 5, 좌장 A7).** v2에는 NIXL 버전만 들어갔다. 필요한 값은 이미 공개 데이터에 있다.
- MTU·MSS: `pmtu:9001 mss:8949`(ss)
- 혼잡 제어: 전 연결 `cubic`
- 배치 그룹 안 최소 RTT: 27–31 µs(26B 7변수 D 쪽 `minrtt`), 전 조건 26–88 µs
- 수신 창 배율: 위 표
- 커널: 클라이언트 sar 머리말 `6.8.0-1064-aws`. GPU 노드 커널은 기록이 없으므로 "not recorded"라고 적는다.
- UCX 버전: 기록이 없으면 "bundled with the NIXL 1.4.1 wheel; version not recorded"라고 적는다.
- 4.97 Gbps = 5 × 8949/9001(= 4.971)이다. 배치 그룹의 9.54 Gbps는 10 × 8949/9001(= 9.94)의 96%다. 그러므로 "documented: 10 Gbps"와 같다고 하기보다 "9.54 Gbps measured (documented 10)"로 두고, C_flow에는 측정값을 쓴다고 밝힌다(원고는 이미 그렇게 쓰고 있다).

**수정.**
- §4.5: "The full set of seven UCX variables gave 13.5–14.2 Gbps, 5–10% lower: its 8 MB socket buffers were capped by the kernel's default limit, which fixed the receiver's TCP window scale at 2 when the connection opened (256 KiB maximum window) and left the sender receive-window-limited for about 40% of its busy time."
- 부록 B 함정 항목: "Setting UCX_TCP_SNDBUF/RCVBUF below the kernel limits pins the window scale at connection time; raise net.core.rmem_max/wmem_max first or leave them unset."
- §3.1 또는 부록 C에 위 환경 문단을 넣는다.

### [필수 4] 그림 5(c)와 "kept all four busy 64% of the time"

그림 5(c)는 v1 그대로다(`paper/figures_v2/v1_transfer.pdf`를 렌더해 확인). 세 가지가 남아 있다.
- 제목 "Four connections per P–D pair"는 바로 위 본문("two or three pieces")과 모순된다.
- 캡션 "Share of transfer time … from socket samples every 0.1 s"는 실제 지표와 다르다. 실제 표본 간격은 중앙값 120.5 ms이고, 지표는 "120 ms 표본 안에서 64 KiB 넘게 움직인 연결 수"다. 26B 전송(73–93 ms)은 표본 간격보다 짧다.
- 본문의 "a 31B transfer kept all four busy 64% of the time"은 TCP busy 기록과 맞지 않는다. P 쪽 `busy`(송신 대기열이 비지 않은 시간) 증분의 합을 전송 시간의 합으로 나누면, 31B 4K 전송 중 데이터가 걸려 있던 연결은 평균 **1.94개**다(각 연결은 평균 298 ms 가운데 약 145 ms만 busy). 네 연결이 64% 동안 모두 busy였다면 평균은 2.56 이상이어야 한다.

**수정.** 좌장 A7 문안대로 제목을 "Connections that moved data within a 0.12 s sample"로 바꾸고, 캡션에 표본 간격과 26B 전송 길이를 적는다. 본문은 "in 64% of the 0.12 s samples taken during 31B transfers, all four connections moved data; on average about two connections had data outstanding at a time"로 쓴다. 그림 윗제목의 "(0.5 and 0.25 requests/s)"는 합계이므로 "total"을 붙이거나 GPU당으로 바꾼다. 패널 (b)는 7변수 런 하나(14.2)만 보이는데 본문은 두 런(13.5–14.2)을 말한다. 두 번째 런을 점으로 더하거나 본문을 맞춘다.

### [권장 5] 식 (1)은 설정에서 유도되고 대화 전송량까지 정확히 맞는다. 그 증거로 바꿔 쓴다

**W = 1,024는 맞다.** `google/gemma-4-26B-A4B-it`, `nvidia/Gemma-4-26B-A4B-NVFP4`, 31B 두 판의 config.json을 직접 받아 확인했다.
- 26B: `sliding_window: 1024`, 층 30개(슬라이딩 25, 전역 5), 슬라이딩 KV 헤드 8 × 256, 전역 KV 헤드 2 × 512(`global_head_dim`), `attention_k_eq_v: true`.
- FP8 KV에서 b_w = 25 × 8 × 256 × 2(K,V) × 1 B = **100 KiB**, b_g = 5 × 2 × 512 × 2 × 1 B = **10 KiB**다. b_g가 10 KiB라는 것은 `attention_k_eq_v`인데도 vLLM이 K와 V를 따로 저장한다는 뜻이다. 4K–32K 기울기 10 KiB/토큰이 이를 확인한다.
- 31B: 슬라이딩 50층 × 16 × 256, 전역 10층 × 4 × 512, 같은 창이다. b_w = 400 KiB, b_g = 40 KiB, V(4,096) = 160 + 400 = 560 MiB로 로그와 정확히 맞는다.

원고의 "consistent with W = 1,024 and b_w ≈ 100 KiB"는 긴 입력만으로 끌어낸 것이다. 긴 입력에서는 b_w·W = 100 MiB만 식별되고 W와 b_w는 따로 정해지지 않는다(W = 512, b_w = 200 KiB도 같은 값을 준다). 설정에서 계수를 유도하면 이 모호함이 사라진다.

**대화 확인은 원고보다 정확하게 할 수 있다.** 원고는 "chat requests of a few hundred tokens moved 28–30 MB, as the formula predicts"라고 쓴다. 실제 값은 다음과 같다(`r3v2_chat_eq1.py`).
- 26B 대화의 전송 가중 평균은 25.1–26.4 MiB다(E5·E7의 1P1D·1P2D·2P1D 11런). 28–30은 10초 창 평균의 윗부분이다.
- 입력은 평균 226–232, **중앙값 99–112**토큰이다. §3.4의 "median input 76–141"을 읽은 독자가 V(141) ≈ 15 MiB를 계산하면 28–30과 두 배 차이가 난다.
- 로그된 입력 길이에 식 (1)과 vLLM 블록 반올림(슬라이딩 16토큰, 전역 32토큰)을 적용하면 26B 25.1/25.8/25.2(E7), 25.1/25.9(E5), FP8 50.3, 31B 105.0/105.6(E8)·107.6/98.2(E9) MiB가 나온다. **로그 값과 소수 첫째 자리까지 같다.**

**수정.** "consistent with"를 설정 유도로 바꾼다("25 sliding-window layers × 8 KV heads × 256 × 2 bytes = 100 KiB; 5 global layers × 2 × 512 × 2 = 10 KiB; W = 1,024 from the model configuration"). 대화 문장은 "chat requests (mean input about 230 tokens, median about 100) moved 25–26 MiB on average, which Eq. (1) with vLLM's 16- and 32-token blocks reproduces from the logged input lengths to within 0.1 MiB"로 바꾼다. 31B 계수(40, 400 KiB)도 한 줄 적는다. 단위 "MB"는 MiB로 고친다.

### [권장 6] 부하에서의 m에는 링크 밖의 시간이 섞인다. 작은 전송은 m이 더 낮다

식 (2)의 m은 "vLLM이 D 쪽에서 잰 전송 시간"으로 정의된다. 이 시간은 링크 전송뿐 아니라 요청 게시, 랑데부, P 쪽 스테이징, 완료 처리, 겹친 전송의 대기를 모두 포함한다. 두 관찰이 이 점을 보여 준다.
- **E9-5 GPU당 5:** 평균 전송 922 ms인데 P 노드 NIC 평균은 제공 부하와 같은 11.7 Gbps였고 1초 최고치는 17.1 Gbps였다. 링크는 여유가 있었다.
- **26B 대화 GPU당 8(합계 16 req/s):** 25 MiB 전송이 38–40 ms 걸렸다. 한 흐름 상한으로는 22 ms다. m은 0.55–0.60이다. 그런데 이때 링크 평균 부하는 16 × 25.2 MiB/s ≈ 3.4 Gbps였다. GPU당 16에서는 m = 0.38이다.

또 10초 창 단위로 보면 평균 디스크립터 수와 전송률이 함께 움직인다(26B 4K GPU당 3–4, 188창, r = 0.53). 1,700개 미만인 창은 7.1 Gbps, 2,000개 이상인 창은 9.8 Gbps였다(`r3v2_desc_rate.py`). 부하가 오를 때 m이 떨어지는 데에는 대역 공유 말고도 조각 수가 줄어드는 몫이 있을 수 있다. 상관일 뿐이므로 가설로만 적는다.

**수정.** "m falls with load"에 "partly for reasons outside the link (host-side handling and overlapping transfers), and it is lower for small transfers (0.4–0.6 for 25 MiB 26B chat transfers)"를 덧붙인다. 식 (2)가 대화 크기에 쓰이려면 고정 항 t₀를 두거나(T ≈ t₀ + V/(m·C)) 크기 구간별 m을 표로 준다. 좌장 A8이 요구한 m 표에 E9-5와 대화 크기 행을 더하면 된다.

### [권장 7] 공유 상한 약 20 Gbps는 7변수 묶음에서만 관측됐다. 그 조건을 적는다

19–21 Gbps는 E8의 31B 4K 7변수 런 하나에서 나온 값이다. 이 런에서는 네 연결이 모두 움직이는 표본에서도 송신자가 busy 시간의 39%(중앙값)를 수신 창에 막혀 있었다(`r3v2_rwnd_bound.py`). 단독 연결 구간에서는 79%였다.

표본 시점의 srtt(중앙값 0.18 ms)로 계산한 정적 창 상한(연결당 262,140 B/srtt의 합)은 약 47 Gbps다. 관측 합계보다 높다. 따라서 256 KiB 창 상한 하나로 20 Gbps를 설명할 수는 없다. 그러나 창이 자주 닫혔다는 것은 수신자(D)가 소켓을 비우는 속도가 병목에 끼어 있다는 뜻이다. 2차에서 내가 제시한 "P 쪽 단일 워커" 가설과는 다른 쪽을 가리키는 증거이기도 하다.

세그먼트만 조건에서는 31B를 재지 않았다. 그러므로 이 상한이 노드의 성질인지 7변수 묶음의 성질인지는 모른다. 26B에서 P 노드 NIC의 1초 최고치는 7변수(E8)에서 12.9 Gbps를 넘지 않았고, 세그먼트만(E9-5)에서는 15.2–17.1 Gbps까지 올라갔다. 다만 P 청크와 프리필 처리율이 함께 바뀌었으므로 이것으로 판단할 수는 없다.

**수정.** "which points to a shared per-node limit" 앞에 "with the seven-variable set, under which the sender was receive-window-limited for about 40% of its busy time even with four connections active,"를 넣는다. "per-node"는 "shared"로 줄인다. 좌장 D6의 "we did not identify it"은 그대로 둔다.

### [권장 8] NIXL 분할 규칙의 서술을 소스에 맞추고, 나뉘지 않은 4K 전송의 꼬리를 적는다

- "splits the list only when it holds at least 1,024 descriptors, in pieces of at least 1,024"는 마지막 조각에서 틀린다. 소스(`ucx_backend.cpp` v1.4.1 675–683행)는 `chunk_size = max(N / threads, 1024)`, `num_chunks = ceil(N / chunk_size)`다. 마지막 조각은 작다. 26B 4K의 1024/1024/192가 그 예다. 정확한 문장은 다음과 같다. "into pieces of max(N/4, 1,024) descriptors, the last one smaller".
- "about 1,900–2,240 descriptors"는 저부하 값이다. 부하에서는 10초 창 평균이 1,108–2,240(E8, 워밍업 창 제외), 1,344–2,132(E9)였다. 같은 140 MiB인데 디스크립터 수가 흔들리는 이유(연속 블록 병합)는 여전히 설명이 없다.
- 1,024 미만으로 떨어진 4K 전송은 공유 연결로 통째 간다. 이 경우 한 흐름 상한에서 26B는 약 123 ms(평소 78–84 ms), 31B는 약 0.55 s(평소 0.27–0.30 s)가 걸린다. 2차 ss 분석에서 런당 0–3회 관측했다. 2차 권장 10의 한 문장을 넣는다.
- 세션 D의 스레드 16 실험(D1c, TTFT 626 → 621 ms, RESULTS.md 525행)은 1,024 하한이 예측하는 결과다. 좌장 A7 문안에도 있었다. 분할 규칙의 독립 증거로 한 문장 넣는다. 한계 절의 "NIXL's four threads"도 "(16 threads made no difference in one early test)"로 보완한다.

### [권장 9] EFA 문단에 넣을 사실 두 가지

AWS 문서 두 쪽을 2026-10-01에 직접 확인했다(아래 목록).
- **GDR의 범위.** g6e.8xlarge와 g7e.8xlarge는 GDR No, g7.8xlarge는 GDR Yes다. g7e.12xlarge 이상도 GDR Yes다. 원고의 "without GPUDirect RDMA on g6e and g7e"는 "on the g6e and g7e 8xlarge sizes"로 좁힌다. GDR이 없으면 EFA 경로에서도 KV를 호스트 메모리로 스테이징해야 한다. 이 논문이 직접 잰 호스트 스테이징(TTFT 4.7배)은 TCP 경로의 vLLM 스테이징이라 같은 경로는 아니다. 그래도 "EFA would shrink the transfer term"이 g6e·g7e 8xlarge에서 보장되지 않는다는 점은 한 구절로 적을 만하다.
- **NIC 대역.** 8xlarge는 vCPU만이 아니라 인스턴스 대역도 바뀐다. g6e는 2xlarge 5/20 Gbps에서 8xlarge 25 Gbps로, g7e는 50에서 100 Gbps로, g7은 40/60에서 100 Gbps로 커진다. "the comparison would change more than the network"에 이 값을 넣으면 구체적이다.

### [권장 10] 1 Gbps 대기열 검산의 수치를 적는다(2차 권장 6 잔여)

S = 140 MiB ÷ 1 Gbps ≈ 1.17–1.18 s, λ = 0.5/s(합계), ρ = 0.59다. M/D/1 평균 대기는 0.83–0.85 s이고, 저부하 예측 1.5 s에 더하면 약 2.35 s다. 실측 2.19 s는 중앙값이다. 원고의 "about 2.2 s"가 어떤 통계인지 밝히고, S·λ·ρ를 한 괄호에 적는다. 좌장 A8에 있는 항목이다.

---

## 사소한 지적

1. 초록의 "a larger UCX TCP segment made 3.4× faster"에 "at low load"를 붙인다. 판정 부하의 비교는 필수 1 때문에 성립하지 않는다.
2. RQ2 답("the UCX segment size limits first and the per-flow cap and NIXL's splitting limit next")에 공유 상한을 넣는다. §4.5에는 있는데 답에는 빠졌다.
3. 결론의 "a KV transfer that can be estimated before deployment"는 좌장 A10 문안("roughly estimated at low load")대로 바꾼다. §4.6은 이미 "a low-load estimate"라고 쓴다.
4. §5.3의 "measure one flow and several flows with iperf first"만으로는 이 논문이 찾은 공유 상한(iperf 4흐름의 절반)을 놓친다. "and time one real KV transfer at the target size"를 덧붙인다.
5. 표 1의 g7.2xlarge 가격이 여전히 "--"다(2차 사소 4).
6. 크레딧 문장에 g7.2xlarge(40/60 Gbps, 세션 B·D)를 넣는다(2차 사소 5).
7. "each carried 22–27% of the bytes"는 기본 조건에서 21.5%인 연결이 있다. "about a quarter each over a run"이 정확하다(2차 사소 8).
8. 4.97 Gbps가 네 인스턴스 쌍에서 모두 같았다는 점을 적는다(2차 사소 9).
9. "8 KB", "256 KB" 세그먼트는 UCX 단위("8k", "256k")로 KiB다. 본문 다른 곳은 MiB를 쓰므로 맞춘다.
10. 호스트 스테이징 문장에 그때의 링크 전송률(7.3–9.4 Gbps)을 한 구절로 적는다. 비용이 링크가 아니라 복사로 옮겨 갔다는 해석이 그래야 가능하다(2차 권장 11).
11. §4.5 첫 문단 "13.5–14.2 Gbps"의 13.46은 toy 프록시 런이다. 둘 다 GPU당 0.25지만 프록시와 서버 이력이 다르다는 점을 괄호로 적는다.

---

## 저자에게 묻는 질문

1. E9-5에서 UCX를 세그먼트만으로 바꾼 이유는 무엇인가? P 청크만 바꾼 대조점(7변수 + P 청크 8,192)이나 세그먼트만 + P 청크 2,560 점이 있는가? 없다면 첫 토큰 개선의 귀속을 어떻게 쓸 계획인가?
2. GPU 노드의 `net.core.rmem_max`·`wmem_max`와 커널 판은 무엇이었나? D 쪽 wscale 2가 기본 rmem_max(212,992)로 설명되는지 한 값으로 확인해 달라.
3. 31B 4K를 세그먼트만(또는 rmem_max를 올린 7변수)으로 한 번 재면 19–21 Gbps 상한이 남는가? 이 한 점으로 "공유 상한이 노드의 성질인가, 7변수 묶음의 성질인가"를 가를 수 있다.
4. E9-5 GPU당 5에서 평균 전송 922 ms는 어디서 쓰였나? P NIC는 제공 부하만큼만 보냈다. D 쪽 엔진 루프, NIXL 완료 처리, P 쪽 읽기 응답 가운데 무엇이 대기했는지 로그로 가를 수 있는가?
5. 같은 140 MiB 전송의 디스크립터가 부하에서 1,100 안팎까지 줄어드는 이유는 무엇인가? 이것이 분할 조각 수를 줄여 m을 낮추는가(창 단위 r = 0.53)?
6. 그림 8의 31B 전송 막대(283 ms)와 식 (2)의 m(1.8)을 전송 가중 평균(298 ms, 1.65)으로 맞추면 잔차 범위(28–87 ms)가 어떻게 바뀌는가?
7. 대화 전송에서 블록 병합이 거의 없고(예측 디스크립터 = 로그) 4K 전송에서는 병합이 많은 이유가 vLLM 블록 할당 순서에 있는가?

---

## 점수·확신도

- **점수 4/5** (네트워크·클라우드 절 기준, 2차 3.5에서 올림). 2차에서 가장 무거웠던 세 서술(초록의 "four connections", "remaining lever", "m = 연결 수")이 모두 고쳐졌다. 공유 상한도 과장 없이 들어갔다. 식 (1)의 일반형은 설정과 데이터 양쪽에서 정확히 뒷받침된다. 남은 필수 네 건은 모두 문장·그림·부록 수정이다. 그중 E9-5의 설정 누락(필수 1)은 판정 표에 든 점의 조건을 잘못 적은 것이므로 공개 전에 반드시 고쳐야 한다. 네 건 모두 판정의 방향(청크를 조정한 복제본이 같거나 높다)을 바꾸지 않는다. E9-5의 전송이 느렸다는 사실은 오히려 분리 쪽에 불리한 조건이었다는 뜻이다.
- **확신도 4/5.** vLLM 전송 로그, ss 원자료, 노드 sar, 런별 입력 길이를 직접 다시 집계했다. config.json과 Linux v6.8 소스는 직접 받아 확인했다. NIXL v1.4.1 소스는 2차 때 받은 사본을 다시 읽었다. 확신이 낮은 곳은 세 군데다. rmem_max 값은 추론이다(기록 없음). E9-5 전송 둔화의 원인(전송 겹침)은 가설이다. UCX가 연결 전에 SO_RCVBUF를 거는지는 소스로 확인하지 못했다(관측된 배율 비대칭이 그렇게 가리킬 뿐이다).

---

## 확인한 문서와 도구

**웹 자료 (2026-10-01)**
- https://huggingface.co/{google/gemma-4-26B-A4B-it, google/gemma-4-31B-it, nvidia/Gemma-4-26B-A4B-NVFP4, nvidia/Gemma-4-31B-IT-NVFP4, RedHatAI/gemma-4-26B-A4B-it-FP8-dynamic}/resolve/main/config.json — **직접 받음(curl).** sliding_window 1024, 층 구성, head_dim 256, global_head_dim 512, KV 헤드 수, attention_k_eq_v. 사본은 스크래치 `reviews_v2/r3/*.json`.
- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/efa.html — **직접 확인(WebFetch).** g6e.8xlarge·g7e.8xlarge GDR No, g7.8xlarge·g7e.12xlarge GDR Yes, 전부 RDMA read/write Yes, "NIXL integrates with Libfabric 1.21.0 and later", 추가 비용 없음.
- https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html — **직접 확인(WebFetch, 표 원문 grep).** 대역: g6e.2xlarge 5.0/20.0, g6e.8xlarge 25, g7.2xlarge 40.0/60.0, g7.8xlarge 100, g7e.2xlarge 50, g7e.8xlarge 100 Gbps. 8xlarge EFA ✓, ENA Express ✗(g7e.12xlarge만 ✓). vCPU 8 대 32.
- https://raw.githubusercontent.com/torvalds/linux/v6.8/net/ipv4/tcp_output.c — **직접 받음(curl).** 205–247행(tcp_select_initial_window), 298행(65535U << rcv_wscale), 3864–3880행(SOCK_RCVBUF_LOCK → window_clamp). 사본은 스크래치 `reviews_v2/r3/tcp_output_v6.8.c`. 실제 노드 커널(6.8.0-106x-aws)의 배포판 패치와는 대조하지 않았다.
- NIXL v1.4.1 `src/plugins/ucx/ucx_backend.cpp` — 2차 때 curl로 받은 사본(`reviews_v1/nixl_v141/`)을 다시 읽었다(645–646, 675–683, 776–780, 809–810행). 이번에 다시 받지는 않았다.
- UCX 소스 — 확인하지 않았다(스크래치의 ucx-master 사본에는 C 소스가 없다).
- Vantage 가격 — 이번에 다시 받지 않았다(2차 값 1.57–2.02배 사용).

**재분석 스크립트 (읽기 전용, 스크래치 `reviews_v2/r3/`)**
- `r3v2_xfer.py`: vLLM 전송 로그 → 전송 가중·창 중앙값 Gbps, m, 디스크립터, p90÷평균
- `r3v2_chat_eq1.py`: 입력 길이 → 식 (1) 예측 전송량·디스크립터·분할 비율(대화 런)
- `r3v2_desc_rate.py`: 창 단위 디스크립터 수와 전송률의 관계
- `r3v2_sar.py`: P 노드 NIC 1초 송신률(E8·E9)
- `r3v2_rwnd_bound.py`: 활동 연결 수별 합계, srtt, 창 상한, rwnd_limited 비율, wscale
- 2차 스크립트 `reviews_v1/r3_ss_busy.py`(busy·rwnd 증분)를 v2 수치 확인에 다시 돌렸다.

**검토한 저장소 자료**
- paper/en/main.tex(v2), paper/figures_v2/v1_transfer.pdf·v1_ttft.pdf(렌더 확인), figures.json
- paper/reviews/2026-09-30_v1/r3_network.md, r6_chair.md(A7, A8, D6, D9)
- configs/run_E9.sh, configs/lib_E9.sh, results/E9/run_E9.log, summary_E9.md, xfer_E9/*.log, collect/*/sar
- results/E8/ss/*.txt(8개), xfer_E8/*.log, summary_E8.md, run_E8.log, run_E8x.log, collect/ip-172-31-87-176/sar
- results/E5·E7 xfer 로그와 대화 런 result.json(input_lens)
- RESULTS.md(세션 A′, D, E8, E9 절)
