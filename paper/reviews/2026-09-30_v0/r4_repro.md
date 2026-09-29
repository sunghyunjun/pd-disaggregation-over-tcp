# Reviewer 4 — 재현성·아티팩트 평가 (pd-without-rdma, paper/en/main.tex)

대상 저장소: <repo> (읽기 전용으로 다뤘다. 저장소 파일은 하나도 바꾸지 않았다)
재생성 산출물: 이 폴더의 all_runs_regen.csv, safe_regen.csv, figs/

## 0. 요약

- 수치 약 105개를 대조했다. 범위는 초록, 3~5절, 표 2(비용), 표 C1, 부록 그림 캡션이다. 결과는 ✅ 72, ⚠️ 23, ❌ 6, ❓ 4.
- 파이프라인 재실행: 스크래치 폴더에서 네 단계를 차례로 돌렸다.
  1. `harness/aggregate.py results/ --slo chat=ttft:1000,tbt:50 --slo doc=ttft:3000,tbt:250`
  2. `harness/safe_runs.py`
  3. `uv run --with matplotlib harness/make_figures.py`
  4. `harness/slo_sensitivity.py`

  결과는 커밋본과 완전히 같았다. all_runs.csv 389행의 주요 열(attain, goodput, tbt_p99, ttft_p50, stall_req_frac)이 모두 일치했다. safety 분류(안전 256, 주의 5, 제외 128)도 같았다. figures.json과 sensitivity.json은 dict 단위로 동일했다. 따라서 CSV에서 나오는 모든 수치는 신뢰할 수 있다.
- 문제는 CSV 바깥 수치에 몰려 있다. 전송 로그에서 나온 값, RESULTS.md 인용값, make_figures.py에 상수로 박힌 값(그림 3·4)이 그렇다. 패키징 문제도 있다. 100 MB 넘는 파일, 계정 ID, README가 여기에 해당한다.

## 1. 청구 원장 (claim ledger)

출처 약어는 다음과 같다.
- CSV: results/safe_runs.csv
- FJ: paper/figures/figures.json
- SJ: paper/figures/sensitivity.json
- RM: RESULTS.md(줄 번호)
- LOG: results/*/run_*.log, xfer 로그

| # | 위치 | 주장 | 출처와 대조 결과 | 판정 |
|---|---|---|---|---|
| 1 | 초록, 3.6 | 389 runs | CSV 389행 | ✅ |
| 2 | 초록, 3.6 | 256 passed audit | 안전 256 | ✅ |
| 3 | 3.6 | removed 128 | 제외 128(캐시 122, 기동 실패 5, 폐기 1) | ✅ |
| 4 | 3.6 | 122 prefix-cache runs | 92 + 30 = 122 | ✅ |
| 5 | 3.6 | 5 caution | 주의 5(E5 ShareGPT ≥32) | ✅ |
| 6 | 4.1, 그림 1 | 166 runs with TTFT p99 < 1 s | FJ n_runs 166(주의 2건 포함) | ✅ (⚠️ #8 참고) |
| 7 | 4.1 | 25 runs p99 ≤ 50 ms and attain < 0.9 | ≤50과 <50 모두 25 | ✅ |
| 8 | 4.1, 그림 1 | 18 replica runs | 18건 중 1건은 단일 노드 26F_single_kvmatch @20 | ⚠️ |
| 9 | 4.1, 그림 1 | 7 disaggregated runs | 7건 중 2건은 '주의'(E5 1P1D @32, 1P2D @48) | ⚠️ |
| 10 | 4.1 | system p99 8.6 ms | E2 B2 4K 0.5, tbt_p99 8.63 | ✅ |
| 11 | 4.1 | 48% 요청에 예산 초과 간격 | stall 0.48, 1 − 0.52(TTFT p99 180 ms라 실패는 모두 간격) | ✅ |
| 12 | 4.1 | attainment 0.52 | 0.52 | ✅ |
| 13 | 4.2 | 3.0–4.05 → 7.07–8.49 Gbps | RM 523~545 | ✅ (귀속은 ⚠️ #A1) |
| 14 | 4.2 | TTFT 626 → 466 ms @0.25 | CSV d1a 626, d1d 466 | ✅ |
| 15 | 4.2 | chat attain 0.82 → 0.99 @1 | d1a 0.822, d1d 0.989 | ✅ |
| 16 | 3.1, 4.2 | 단일 흐름 4.97 Gbps | RM 10·517·925 | ✅ |
| 17 | 3.1, 4.2 | PG 9.54 Gbps | RM 889 | ✅ |
| 18 | 3.1, 그림 3a | 8 flows 49.72 Gbps(1/2/4: 9.54/19.06/38.11) | RM 889~892 | ✅ |
| 19 | 4.2, 그림 3b | 6.55 Gbps(1.32×) | (6.91+6.19)/2 = 6.55. 캡션 정의(0.5 req/s, bytes/time)대로면 6.91 | ❌ |
| 20 | 4.2, 그림 3b | 13.96 Gbps(1.46×) | 회색 점 네 개(13.86/14.43/13.99/13.58)의 평균이지 따로 잰 값이 아님 | ⚠️ |
| 21 | 4.2 | 31B 1.68× | RM 1014: 16.1/9.54 | ✅ |
| 22 | 4.2 | 13.58–14.43 Gbps(knob 무효) | RM 917~921 값과는 일치. 전 구간 로그 재계산 시 13.1~13.3(바이트/가중 평균) 또는 13.8~13.9(구간 평균), 스크립트 없음 | ⚠️ |
| 23 | 4.2, 그림 A1 | TTFT 471/744/954/2185 ms | FJ fig02, CSV D p1_best와 p1_tcfix | ✅ |
| 24 | 4.2, 그림 A1 | attain 1.00/0.92/0.55/0 | FJ | ✅ |
| 25 | 4.2 | host staging 4.7× @0.25, 75× @1 | CSV 2942/624 = 4.71, 50029/670 = 74.7 | ✅ |
| 26 | 4.2 | 15분 평균 0.91 Gbps, 18% | RM 829의 계산값(230 MB 사용). 280 MB면 1.12 Gbps(22%) | ❌ |
| 27 | 4.2 | iperf 4.967/4.966 Gbps | RM 827 | ✅ |
| 28 | 4.3 | 평균 전송 324 → 165 ms | RM 909. 324는 E2 마지막 10초 구간(8건). 165는 xfer_a_tuned 런 | ✅ (런 혼합 ⚠️) |
| 29 | 4.3 | TTFT 482 → 351 ms | CSV E2 P1tuned 482, E4 P1tuned_pg 351 | ✅ |
| 30 | 4.3 | 351 − 165 = 186, single-node 158 | 산술 맞음. 158은 E2 복제본 둘(B2) 값 | ⚠️ |
| 31 | 3.2 | 26B NVFP4 4K 140 MB, 34 KB/token | 로그 Avg MB 140.0 × 57회. 140e6/4096 = 34.2 KB | ✅ |
| 32 | 3.2 | 26B FP8 4K 280 MB | E2/E4 로그 280.0 | ✅ |
| 33 | 3.2, 4.3 | 31B 560 MB, 137 KB/token | RM 1004~1014 | ✅ |
| 34 | 4.3 | 26B 예측 235, 실측 267(130+84+53) | CSV E5 266.6. RM 1007 | ✅ |
| 35 | 4.3 | 31B 예측 810–830, 실측 853(483+283+87) | CSV E5 852.9. RM 1008 | ✅ (사전 기록 ❓) |
| 36 | 4.3 | 첫 디코드 스텝 25 ms 대 6.5 ms | RM 130·153 | ✅ |
| 37 | 4.3 | 16K 26B FP8 @5 Gbps는 전송만 1초 초과 | KV가 입력 길이에 선형이 아님(26B NVFP4 4K/16K/32K = 140/260/412.5 MB). E2 16K PD TTFT 1,286 ms, 복제본 820 ms. 로그 전송 243~337 ms | ❌ |
| 38 | 4.4 | 4K chat 0.96 대 0.23 | FJ fig05 | ✅ |
| 39 | 4.4 | 16K doc 0.47 대 0.17 | FJ fig05 | ✅ |
| 40 | 4.4 | 16K에서 복제본 TTFT > 1 s, 16K chat 둘 다 실패, 32K 전부 실패 | CSV B B2 16K TTFT p50 1470, FJ 0/0 | ✅ |
| 41 | 4.4 | 복제본 0.02–0.14, 분리 0.83–0.98 | FJ fig06: 0.022/0.022/0.139, 0.839/0.828/0.983 | ✅ |
| 42 | 4.4 | NVFP4 + PG 복제본 0.97 | FJ 0.972 | ✅ |
| 43 | 4.4 | 정밀도별 0.97/0.13/0.03, 분리 1.00 | FJ fig10: 0.972/0.133/0.028, 1.0 × 3 | ✅ |
| 44 | 4.4 | 복제본 실패는 전부 간격, TTFT p99 < 1 s | CSV 26F/26H_B2 TTFT p99 165~321 ms | ✅ |
| 45 | 4.4 | chat 16에서 모든 정밀도에 이득 없음, BF16 둘 다 실패 | BF16 1P1D 0.665 대 복제본 0.356 | ⚠️ |
| 46 | 4.4 | 분리 TTFT 269/362/448 ms | CSV E7 26/26F/26H_1P1D @1 | ✅ |
| 47 | 4.5 | 복제본 둘 @2/GPU 0.37–0.64(4회) | FJ 0.367/0.644/0.604/0.478 | ✅ |
| 48 | 4.5 | 복제본 셋 0.69 | 0.694 | ✅ |
| 49 | 4.5 | 1P1D @3/GPU 1.00 | 1.0(1회) | ✅ |
| 50 | 4.5 | 1P1D @4/GPU 0.84 | 0.836 | ✅ |
| 51 | 4.5 | 3×, 보수적으로 ≥1.5× | 3/1, 3/2 | ✅ |
| 52 | 4.5 | 1P2D 9 req/s 0.906 | 0.906 | ✅ |
| 53 | 4.5 | 1P2D 12 req/s TTFT 중앙값 14.3 s | CSV 14,287 ms | ✅ |
| 54 | 4.5 | 2P1D 9 req/s 0.77 | 0.769(TTFT 376 ms로 정상, 간격 실패) | ✅ |
| 55 | 4.5 | 2P1D chat 48에서 시퀀스 256, 대기 868, KV 43% | 공개 데이터 없음(E5 collect 269 샘플, prom.txt는 프리필 노드 0). '주의' 런 | ❌ |
| 56 | 4.5 | 26B chat @8/GPU 모두 통과 | 0.968~0.981 / 0.978 / 0.972~0.98 / 0.979 / 0.904 | ✅ |
| 57 | 4.5 | 31B chat 복제본 0.43–0.49(4회) | 0.439/0.447/0.489/0.431 | ✅ |
| 58 | 4.5 | 31B chat 1P1D @4 req/s 0.98 | 0.982(합계 4 = GPU당 2) | ✅ (표기 ⚠️) |
| 59 | 4.5 | 31B chat 1P1D @8 0.863–0.944 | FJ | ✅ |
| 60 | 4.5 | 31B 4K 1P1D @0.25, 2P1D @0.75 모두 4회 중 1회만 ≥ 0.9 | 0.87/0.85/0.89/0.91. 0.815/0.793/0.815/0.97 | ✅ |
| 61 | 4.5 | 31B 프리필 약 480 ms, 전송 약 280 ms | 483, 283 | ✅ |
| 62 | 4.5 | 2P1D 290, 1P2D 177, 복제본 셋 8 tok/s | E5 290.0/176.9/7.9. E7 반복 2P1D 282/288/344 | ⚠️ |
| 63 | 표 2 | 26B 4K 2노드 복제본 $1.98 @2 | 계산 1.977(평균 굿풋 944.5 × 4회) | ✅ |
| 64 | 표 2 | 1P1D $0.63 @6 | 0.631 | ✅ |
| 65 | 표 2 | 3노드 복제본 $1.89 @3 | 1.890 | ✅ |
| 66 | 표 2 | 1P2D $0.69 @9 (경계) | 0.694 | ✅ |
| 67 | 표 2 | 26B chat $0.63/$0.63 @16 | 0.630/0.631 | ✅ |
| 68 | 표 2 | 31B chat 1P1D $2.58 @4 | 2.580 | ✅ |
| 69 | 표 2 | 31B chat 복제본, 31B 4K 모두 지원 부하 없음 | FJ null | ✅ |
| 70 | 표 2 | 비용식 $3.363 × GPUs / (goodput × 3600) × 1e6 | make_figures f12와 일치, 반복 평균 굿풋 사용(민감도는 최솟값) | ✅ (방법 차이 ⚠️) |
| 71 | 4.7, 초록 | 약 3× 저렴 | 1.98/0.63 = 3.14, 1.89/0.69 = 2.74 | ✅ |
| 72 | 4.7 | L40S $3.15 | 계산 $3.144(g6e 요금 $2.242/h 역산). 표 1 캡션은 g7e 요금만 언급 | ❌ |
| 73 | 4.7 | PRO 6000 KV-matched $0.34 | 평균 굿풋 2,743 → 0.341 | ✅ |
| 74 | 4.7 | 9.2× | 3.144/0.341 = 9.22 | ✅ |
| 75 | 4.7 | 지원 부하 1 대 16 req/s | E1 L40S @1 0.917. E7 @16 0.933/0.953/0.949, @20 0.779 | ✅ |
| 76 | 4.8 | 트레이스 약 4, 약 5.9, 약 3.7 req/s | FJ 3.96/3.95, 5.88/5.87/5.83, 3.74/3.68 | ✅ |
| 77 | 4.8 | 분리가 약 120 ms 느림 | 44 대 162~170 | ✅ |
| 78 | 4.8 | 31B 0.05 대 0.28 | 0.048, 0.275~0.287 | ✅ |
| 79 | 4.8 | 푸시 전송 27–36% 단축 | RM 1046~1052: 282 → 205, 329 → 210. 단, 기록 바이트 468~533 대 560 MB | ✅ (단서 ⚠️) |
| 80 | 4.8 | TTFT 중앙값 53–62 ms 단축 | 852 → 799, 888 → 826 | ✅ |
| 81 | 4.8 | 달성률 ±0.04 | 0.86 → 0.82, 0.63 → 0.66 | ✅ |
| 82 | 4.6 | 26B 4K 50 ms에서 3.0× | SJ 26b_4k 3.0 (T ≥ 0.75) | ✅ |
| 83 | 4.6 | 26B 4K ≥75 ms에서 ≤2× | ≤1.3~≤2.0(상한값) | ✅ |
| 84 | 4.6 | 26B 4K ≤40 ms에서 D만 통과 | T ≥ 0.5에서 D. T = 0.25는 '–'(50 ms 이상은 R) | ✅ (범위 ⚠️) |
| 85 | 4.6 | 31B chat 40–75 ms에서 D만, ≥100 ms 둘 다 통과 | T ≥ 0.75에서 성립. T = 0.5는 ≤0.5~0.6, T = 0.25는 R | ⚠️ |
| 86 | 4.6 | 31B 4K: 1 s 둘 다 실패, 1.5 s는 D만 | 40~200 ms에서 성립. 300 ms 열은 1 s에서 R, 1.5 s에서 ≤0.6 | ⚠️ |
| 87 | 4.6 | 16K는 2 s(g7e FP8), 5 s(g7)에서 D만 | SJ 26f_16k_e2 T = 2 D, 26n_16k_g7 T = 5 D | ✅ |
| 88 | 4.6 | 26B chat 구분 불가 | 전부 '?'(0.25/30만 R) | ✅ |
| 89 | 4.6 | FP8 chat 모든 SLO에서 복제본 우세 0.3–0.7× | R 또는 0.3~0.7(≤ 포함) | ✅ |
| 90 | 초록, RQ3 | ≥100 ms면 차이가 대부분 사라짐 | 해당 셀 대부분이 '?'나 '≤'. 100 ms에서 g7 4K(T 0.75~5)와 31B 4K(T ≥ 1.5)는 D만 통과 | ⚠️ |
| 91 | 초록, RQ1 | 지원 부하 1.5–4× | 구간 논리로 성립. 본문은 4×를 설명하지 않음 | ⚠️ |
| 92 | 4.6, 그림 16 | 26B 4K 복제본 p90 최대 간격 50–65 ms | SJ 48/49/64, 48/49/57 → 48~64 | ⚠️ |
| 93 | 4.6 | 31B chat 70–90 대 35–48 ms | 75/81/89 대 33/39/48 | ⚠️ |
| 94 | 4.6 | 26B chat 복제본 약 30 ms | 29/31/28/31 | ✅ |
| 95 | 4.6 | 복제본은 항상 첫 토큰이 빠름 | 주의 점(복제본 셋 @48) 하나 예외 | ✅ |
| 96 | 3.6 | TTFT 중앙값 변동 < 5% | 최대 5.1%(26F_single @16), 나머지 ≤ 4.5% | ⚠️ |
| 97 | 3.6 | 0.85–0.95 구간 지점만 ±0.09 흔들림 | 26B 4K 복제본 @4: 0.478~0.644(평균 0.58), 전날 0.367 | ❌ |
| 98 | 2절, 4.2, RQ2 | m = 1.3–1.7 | 1.32(또는 1.39)/1.46/1.68 | ✅ |
| 99 | 3.4 | ShareGPT 중앙값 입력 80–100, 출력 100–150 | 런별 입력 76~141, 출력 59~177(1건 24) | ⚠️ |
| 100 | 3.4 | Azure 600요청, 중앙값 996/217 | CSV 23런 전부 996/217/600 | ✅ |
| 101 | 3.4 | 각 런 180 s | 요청 수 = max(100, rate × 180)이라 0.25 req/s는 약 400 s. 트레이스 100~160 s | ⚠️ |
| 102 | 부록 그림 A5 | 위 네 행은 반복과 전날 모두 1.00 | 1P2D @6 0.999/0.998, 2P1D @6 전날 0.999 | ⚠️ |
| 103 | 그림 3 캡션 | 회색 점 = four alternative settings | 넷 중 하나(13.86)는 튜닝 기준 자체 | ⚠️ |
| 104 | 감사의 글 | 약 $220 | 기록된 세션 비용 합 약 $181(P·A′·E1·E2 미기재) | ❓ |
| 105 | 3.1, 4.2 | 전송 두 배의 원인은 세그먼트 크기 | D1d는 UCX 변수 7개를 동시에 변경. 단독 대조 없음 | ⚠️ (#A1) |
| 106 | 4.3 | 예측을 측정 전에 적음 | 예측이 git에 처음 나오는 커밋이 결과 커밋 39acfbe와 같음 | ❓ |
| 107 | 4.8 | 정확성 검사 수행 | 결과와 판정 기준이 본문에 없음(gate_E6 JSON은 있음) | ❓ |
| 108 | 표 C1 | 폴더별 날짜, 인스턴스, 모델, 절 | 날짜(run_id)와 모델(CSV) ✅. 인스턴스는 RM 서술로만 확인(CSV instance_type 불신) ❓. 절 번호 누락 ⚠️ | ✅/❓/⚠️ |
| 109 | 표 1 | g7 RTX PRO 4500 32 GB, g6e L40S 48 GB, g7e PRO 6000 96 GB | RM 73·661 | ✅ |
| 110 | 3.1 | vLLM v0.30.0, 청크 2560, util 0.90 | serve.sh 이미지 태그, run 스크립트. KV 맞춤 런은 util 0.42, D1b는 0.70 | ✅ |

집계는 대략 ✅ 72, ⚠️ 23, ❌ 6, ❓ 4이다. 혼합 판정 행은 주 판정으로 셌다.

## 2. ❌ 상세와 수정 문구

1. **[필수] 16K 전송 1초 주장 (4.3절 끝, #37)**
   - 하이브리드 어텐션이라 KV가 입력 길이에 선형이 아니다.
     - 26B NVFP4 전송량은 4K 140 MB, 16K 260 MB, 32K 412.5 MB다(results/B·D 로그의 `Avg MB per transfer`).
     - FP8(BF16 KV)이면 16K는 약 520 MB다. 6.5 Gbps에서 약 0.6 s다.
   - E2 실측(배치 그룹 없음, 약 5 Gbps)은 다음과 같다.
     - 16K 1P1D TTFT p50은 1,286 ms(0.25 req/s), 복제본은 820 ms다.
     - run_E2b.log의 전송 평균은 243 ms(2건)와 337 ms(7건)다.
   - 수정 문구: "where the per-flow cap is about 5 Gbps, a 16K input to 26B FP8 already spends about 0.8 s in prefill, and the transfer (about 0.3–0.6 s) pushes TTFT past the 1 s chat budget."
   - 식(1), 3.2절, 체크리스트 2번에는 다음을 추가한다. "For hybrid-attention models the KV bytes per input token fall with input length (26B NVFP4: 34 KB at 4K, 16 KB at 16K, 13 KB at 32K); use the measured KV size for the target length."
2. **[필수] 0.91 Gbps (4.2절, #26)**
   - RM 829의 계산값이다. 계산에 쓴 230 MB는 57.6 KB × 4096, 즉 vLLM의 KV 계정값이다.
   - 같은 모델의 실제 전송량은 280 MB다. 그러면 0.5 × 280 MB = 140 MB/s ≈ 1.12 Gbps로 약 22%다.
   - 수정 문구: "the average transfer load at 0.5 requests/s is about 1.1 Gbps (0.5 × 280 MB, computed), about 22% of the cap".
3. **[필수] 256/868/43% (4.5절, #55)**
   - E5 수집기 시계열은 보충 측정 때 `>`로 덮어써졌다(RM 마찰 #21). collect_*_prom.tsv에는 각 269 샘플만 남아 있다.
   - 해당 런 폴더의 prom.txt는 첫 노드, 즉 프리필 노드 값이라 전부 0이다.
   - 이 지점은 '주의' 런이다.
   - 수정: 수치를 빼거나, "values read from the decode server's live metrics during this client-limited run; the time series was not retained"라고 각주를 단다.
4. **[필수] 반복 변동 (3.6절, #97)**
   - 수정 문구: "Points well above 0.9 varied by at most 0.03 across repeats. Points near the threshold (0.85–0.95) varied by up to ±0.09, enough to flip the verdict; we mark them borderline. Low-attainment points also varied (26B 4K replicas at 4 requests/s: 0.48–0.64, previous day 0.37) but never approached 0.9."
5. **[필수] L40S 비용 (4.7절과 표 1, #72)**
   - "$3.15"를 "$3.14"로 고친다.
   - 표 1 캡션에 "g6e.2xlarge $2.242 per hour for the L40S comparison"을 추가한다. g7e 요금을 쓰면 $4.72가 되기 때문이다.
6. **[필수] 그림 3b 6.55 (#19)**
   - 6.55는 (6.91 + 6.19)/2로 정확히 일치한다. 이는 E2의 0.5 req/s와 1 req/s 평균이다.
   - 캡션대로 0.5 req/s 하나와 bytes/transfer time 정의를 쓰면 6.91 Gbps, 1.39×다.
   - 13.96도 회색 점 네 개의 평균이다(#20).
   - 수정: 추정 방식을 하나로 정하고 스크립트로 계산한다. 예를 들어 0.5 req/s 런 전 구간의 바이트 합을 전송 시간 합으로 나눈다. 캡션도 그 정의로 맞춘다. 결론 m ≈ 1.3–1.7은 그대로다.

## 3. ⚠️ 상세

[필수]
- **A1 (#105, #13)**: 3.1절 "We raised UCX's TCP segment size from 8 KB to 256 KB"와 4.2절 "raising it to 256 KB doubled the rate"에 문제가 있다.
  - D1d가 실제로 바꾼 설정은 `UCX_TCP_TX_SEG_SIZE=256k UCX_TCP_RX_SEG_SIZE=256k UCX_TCP_MAX_IOV=16 UCX_TCP_MAX_POLL=-1 UCX_TCP_SNDBUF=8m UCX_TCP_RCVBUF=8m UCX_RNDV_FRAG_SIZE=host:4M,cuda:8M`다(configs/run_E*.sh의 TUNED).
  - 세그먼트만 바꾼 대조 런은 없다.
  - 수정 문구: "raising the segment size to 256 KB, together with related buffer settings (Appendix)". 부록에는 전체 목록을 넣는다.
- **#22**: RM 917~920의 knob 표 값(165/158/161/170 ms와 13.86/14.43/13.99/13.58 Gbps)은 xfer_full_E4.log 전 구간으로 다시 계산해도 나오지 않는다.
  - 전 구간 재계산 값은 가중 평균 전송 시간 168~170 ms, 바이트/시간 13.1~13.3 Gbps, 구간 처리량 평균 13.8~13.9 Gbps다.
  - 런 로그의 마지막 10초 스냅샷이나 다른 필터를 쓴 것으로 보인다.
  - 결론(효과 없음)은 더 강해진다. 수치는 스크립트로 다시 만든다.

[권장]
- #8, #9: 그림 1 캡션을 "18 replica or single-node runs and 7 disaggregated runs (2 of them client-limited)"로 고친다. 166건에 주의 2건이 포함된다는 점도 밝힌다(본문은 "All results use the remaining 256 runs"라고 적는다).
- #28, #30: 351 ms(P1tuned_pg 런)와 165 ms(xfer_a_tuned 런, TTFT 357)는 다른 런이다. 158 ms는 단일 노드가 아니라 E2 복제본 둘의 TTFT다(다른 날, 배치 그룹 없음). "the replica TTFT of 158 ms"로 고친다.
- #45: "For chat at 16 requests/s neither configuration benefited with NVFP4 or FP8, and with BF16 neither passed (1P1D 0.67, replicas 0.36)."
- #58: 31B chat 문단의 "2 requests/s", "4 requests/s", "8 requests/s"는 합계 기준이다. 그림 x축은 GPU당이다. 26B 문단처럼 "per GPU"로 통일한다.
- #62: "290 tokens/s (E5; 282–344 over four runs)".
- #79: 푸시가 기록한 바이트(468~533 MB)가 끌어오기(560 MB)보다 적고 원인은 확인되지 않았다(RM 1052). 전송 시간 단축에 이 차이가 섞였을 수 있다고 한 줄 적는다.
- #84~#86: 민감도 문장에 성립 범위를 붙인다. 예: "for TTFT limits of 0.5 s or more", "for TTFT limits of 0.75 s or more", "for gap limits up to 200 ms".
- #90: "When gaps of 100 ms or more are acceptable, the measured advantage shrinks to at most about 2× or cannot be resolved within the measured rates (the replicas' limit lies beyond our rate grid)."
- #91: 4.5절에 구간 논리를 한 문장 넣는다. "Replicas' supported load lies in [1, 2) and 1P1D's in [3, 4) requests/s per GPU, so the gain is between 1.5× and 4× (3× at the measured points)."
- #92, #93: "48–64 ms", "75–89 ms versus 33–48 ms".
- #96: "within about 5%".
- #99, #101: "median input about 75–140 tokens (typically about 100), output about 100–150". 요청 수는 "each point sends max(100, 180 × rate) requests; trace replays send 600 requests"로 적는다.
- #102: 그림 A5 캡션을 "all repeats and the previous run are at least 0.998"로 고친다.
- #108: 표 C1 절 번호를 보완한다. E2는 4.1·4.2·4.3·4.4·4.6, E5는 4.1·4.3·4.5·4.6·4.7, B는 4.1·4.4·4.6이다. D는 4.1 그림 1에도 포함된다.
- #70: 비용(표 2)은 반복 평균 굿풋을, 민감도(그림 15·17)는 반복 최솟값 굿풋을 쓴다. 방법 절에 한 줄 밝힌다.

## 4. ❓ 상세

- #106 "we validated by predicting results before measuring them": 예측 235 ms와 810~830 ms가 git에 처음 나오는 커밋은 39acfbe(2026-09-27T20:51+09)다. 같은 커밋이 E5 결과도 넣었다. configs/run_E5.sh(커밋 2574eae, 17:07)에도 예측은 없다. 저장소만으로는 선후를 검증할 수 없다. 사전 기록이 따로 있으면 인용하고, 없으면 "estimated before the three-node session (not independently time-stamped)"로 약하게 쓴다.
- #107: 4.8절은 정확성 검사 방법만 적고 결과를 적지 않는다. RM 1054~1060에 따르면 다음과 같다.
  - 판정 기준은 100자 미만 바이트 일치, 긴 출력은 5자 이상 영단어를 40% 이상 공유하는 것이다.
  - 26B는 단일 노드 자체가 비결정적이다.
  - 31B는 늦은 위치에서 단어가 갈린다.
  - 모든 출력이 정답이다.

  기준과 결과를 한두 문장으로 넣는다.
- #104: $220은 기록된 세션 비용 합(A 6.3, C1 14, B 23, D 19, E3 7.3, E4 6.3, E5 37.5, E6 11, E7 약 57 = 약 $181)에 기록 없는 P·A′·E1·E2를 더한 값으로 보인다. 결제 확정치로 확인하기를 권한다.
- #108 인스턴스: CSV instance_type은 B가 클라이언트 값(c6i.xlarge), D와 E가 빈칸이다. RM 1078도 이 열을 신뢰할 수 없다고 적는다. vllm 열도 237/261이 공란이다. 인스턴스는 RM 서술로만 확인된다.

## 5. 재현성 평가

강점:
- 요청별 원자료(bench.json 389개)와 per_request.json.gz(2.4 MB)가 추적된다.
- 네 단계 명령으로 CSV, 그림, 민감도 JSON이 바이트 단위로 재생성된다. 직접 확인했다. slo_sensitivity는 캐시가 있으면 읽기만 한다.
- 측정 스크립트(configs/run_*.sh, harness/*.sh)와 테라폼이 모두 들어 있다. 도커 이미지 태그 vllm/vllm-openai:v0.30.0도 명시돼 있다.

제3자를 막는 것:
- **[필수] GitHub 푸시 불가**
  - results/E5/rr_proxy_E5_26_B3.log가 457 MB로 100 MB 한도를 넘는다.
  - 50~55 MB 파일이 4개 있다(E7 1P2D/2P1D r18의 result.json과 bench.json).
  - 추적 파일 합계는 5.4 GB이고, 팩은 769 MB다.
  - result.json이 bench.json 본문을 통째로 담고 있어 약 두 배 중복이다.
  - 권고: 원자료는 Zenodo 아카이브나 LFS로 옮긴다. result.json은 meta만 남긴다. 프록시 로그는 압축하거나 제외한다.
- **[필수] 그림 3·4 하드코딩**
  - make_figures.py의 f03(cap, eff, knobs, iperf)과 f04(분해 막대)는 RESULTS.md 수치를 상수로 넣었다.
  - E2의 run 로그는 전송 지표 줄이 잘려(`Avg MB per transfe…`) 일부 필드가 없다. E2 4K 0.5의 전송 시간도 마지막 구간 8건뿐이다.
  - 권고: xfer 로그 파서(예: harness/xfer_rates.py)와 추정식 정의를 추가한다. 원자료가 부분적인 값은 그림에서 표시한다(캡션에 이미 일부 적혀 있다).
- **[필수] README가 낡았다**
  - README는 여전히 "Status: pre-measurement", writeup/, H100 NVLink reference, g5/g6을 적고 있다.
  - 재현 절차가 없다. 집계 SLO 인자는 PROTOCOL.md 388~393(한국어)에만 있다.
  - 권고: README에 네 명령을 적는다. `aggregate.py results/ -o results/all_runs.csv --slo chat=ttft:1000,tbt:50 --slo doc=ttft:3000,tbt:250` → `safe_runs.py results/all_runs.csv -o results/safe_runs.csv` → `uv run --with matplotlib python3 harness/make_figures.py` → `uv run --with matplotlib python3 harness/slo_sensitivity.py`. 논문 빌드 명령(tectonic)도 적는다.
- **[권장] 환경 고정**
  - 분석용 requirements나 uv.lock이 없어 matplotlib 버전이 고정되지 않았다. JSON은 같지만 PDF와 SVG는 달라질 수 있다.
  - 도커 이미지는 태그만 있고 digest가 없다.
  - HF 체크포인트 revision이 기록되지 않았다.
  - NIXL과 UCX 버전이 논문에 없다(RM P 절에 NIXL 1.4.1).
- **[권장] 런 매니페스트**
  - 런별 인스턴스 타입, AZ, 배치 그룹, UCX 설정, GPU util, 날짜를 담은 파일이 필요하다.
  - 지금은 results/D·E1·E2·E3에 env_B.json 복사본이 있다.
  - results/E3에는 B·D·E2 세션의 프록시 로그(toy_proxy_B.log, toy_proxy_D_*.log 등)가 섞여 있다.
- **[권장] .gitignore**: `results/*/bench.log`, `sar.txt`, `prom.txt`, `dmon.txt` 패턴은 두 단계 아래 런 폴더의 파일에 적용되지 않는다. 그래서 의도와 달리 전부 추적된다. 공개 범위를 정하고 패턴을 고친다(`results/**/bench.log`).
- **[권장] PROTOCOL 대비 이탈 명시**
  - PROTOCOL은 H100 NVLink 참조점, g5, 요청 단위 부트스트랩 신뢰구간(1000회), 모든 점의 워밍업 30요청을 정했다. 논문에는 이것이 없다.
  - RM 1077에 따르면 워밍업은 E7에서만 했다. 앞 세션은 첫 5요청을 빼도 달성률 차이가 +0.019 이내이고 판정이 뒤집힌 런은 0이다.
  - 이 내용을 한계나 부록에 적는다.
- **[권장] 잃어버린 원자료 명시**
  - E5 디코드 노드 시계열(마찰 #21)
  - E7 세 번째 노드 시계열(마찰 #23)
  - E2와 E3 초반의 전송 로그 일부

## 6. 공개 전 정리할 것 (값은 적지 않았다)

- **[필수]** RESULTS.md:1068의 S3 버킷 이름에 AWS 계정 ID(12자리)가 들어 있다. 가려야 한다.
- **[권장]**
  - results/.session_A.env, .session_Ap.env, .session_C1.env, .session_P.env에 종료된 인스턴스의 공인 IP와 인스턴스 ID가 있다.
  - results/*/env_*.json에 인스턴스 ID와 AMI가 있다.
  - 위험은 낮지만 지우는 편이 좋다.
- **[권장]** infra/terraform/variables.tf의 aws_profile 기본값이 개인 프로필 이름이다. allowed_ssh_cidr 기본값은 0.0.0.0/0이고, network.tf에 0.0.0.0/0 규칙이 있다. 재현자를 위해 안전한 기본값으로 바꾼다.
- **[참고]** RESULTS.md에 IAM 사용자 이름(terraform-admin)과 보안 그룹 이름이 나온다. 위험은 낮다.
- 스캔 결과 발견되지 않은 것: AWS 액세스 키(AKIA…), HF 토큰, 개인 키, 로컬 홈 경로, 이메일 주소. bench.json 안의 `arn:aws:…` 문자열은 ShareGPT 대화 본문, 즉 제3자 텍스트다.
- CITATION.cff의 제목과 초록이 옛 버전이다(g5/g6, per dollar). LICENSE의 경로(writeup/, figures/)도 현재 구조와 다르다.

## 7. 점수

- **아티팩트 품질 3/5**(현재 공개 상태 기준).
  - CSV 기반 결과의 재현성은 5점 수준이다.
  - 감점 이유는 전송·네트워크 수치(하드코딩, 추정식 불일치, 부분 로그)와 패키징(100 MB 초과 파일, 계정 ID, 낡은 README)이다.
  - 필수 항목을 반영하면 4~5점이다.
- **확신도: 높음.**
  - 파이프라인을 직접 재실행해 일치를 확인했다.
  - ❌ 항목은 모두 원자료(CSV, 전송 로그, 수집기 파일)로 대조했다.
  - 6.55 = (6.91 + 6.19)/2는 수치가 정확히 맞는다. 다만 작성 경위는 직접 확인하지 못했다.
