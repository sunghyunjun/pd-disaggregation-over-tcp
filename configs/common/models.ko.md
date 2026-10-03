# 모델 후보 매트릭스 (2026-09-24, config.json·HF 공식 저장소 기준)

KV KB/tok = full-attention 층만, BF16 기준(슬라이딩·선형 어텐션 층 제외. 슬라이딩은 윈도 1024로 상한, 선형은 요청당 고정 상태).
KV 예산 ≈ VRAM×0.90 − 가중치 − 1.5 GB. 32K 요청 1개에 필요한 KV = KB/tok × 32K.

| 모델 | 구조 | 총/활성 | KV KB/tok | BF16 GB | 32K 요청 KV | 공식 양자화 |
|---|---|---|---|---|---|---|
| Qwen3-8B | dense GQA | 8B | **144** | 16.4 | 4.6 GB | FP8(Qwen), AWQ(Qwen), NVFP4(nvidia) |
| Qwen3-14B | dense GQA | 14B | 160 | 29.5 | 5.1 | FP8·AWQ(Qwen), NVFP4 |
| Qwen3-30B-A3B | MoE GQA | 30B/3B | 96 | 61 | 3.1 | FP8·GPTQ-Int4(Qwen), NVFP4 |
| Qwen3.5-9B | hybrid (8 full + 24 linear) | 9B | **32** | ~19 | 1.0 | FP8-dyn·w4a16·w8a8(RedHatAI) |
| Qwen3.6-27B | hybrid (16 + 48) | 27B | 64 | ~54 | 2.0 | FP8(Qwen), NVFP4(nvidia) |
| Qwen3.6-35B-A3B | hybrid MoE (10 + 30) | 35B/3B | **20** | ~70 | 0.6 | FP8(Qwen), NVFP4(nvidia·RedHatAI), GPTQ-Int4(3.5) |
| Gemma 4 E4B | hybrid sliding (7 full + 35 sw) | ~8B raw / 4B eff | 28 | ~8 | 0.9 | QAT w4a16-ct(google) |
| Gemma 4 12B | sliding (8 + 40) | 12B | 128 | ~24 | 4.1 | FP8-dyn·NVFP4(RedHatAI), QAT w4a16-ct(google) |
| Gemma 4 26B-A4B | sliding MoE (5 + 25) | 26B/4B | 80 | ~50 | 2.6 | FP8-dyn·NVFP4(RedHatAI·nvidia), QAT q4_0(google), AWQ(커뮤니티) |
| Gemma 4 31B | sliding (10 + 50) | 31B | **320** | ~62 | 10.2 | FP8-block·NVFP4(RedHatAI·nvidia), QAT w4a16-ct(google) |

## GPU별 정밀도 지원
| GPU | VRAM | BF16 | FP8 연산 | INT4(AWQ/GPTQ, Marlin) | NVFP4 |
|---|---|---|---|---|---|
| A10G (g5) | 24 | ✓ | ✗ (가중치만 W8A16) | ✓ | ✗ |
| L40S (g6e) | 48 | ✓ | ✓ | ✓ | ✗ |
| RTX PRO 4500 (g7) | 32 | ✓ | ✓ | ✓ | ✓ |
| RTX PRO 6000 (g7e) | 96 | ✓ | ✓ | ✓ | ✓ |

## 어디에 무엇이 들어가나 (32K 요청 최소 1개, KV 예산 기준)
| 모델·정밀도 | 가중치 GB | g5 24 | g7 32 | g6e 48 | g7e 96 |
|---|---|---|---|---|---|
| Qwen3-8B BF16 | 16.4 | △ KV 3.7 GB → **32K 1개 불가, 16K까지** | ✓ KV 11 | ✓ KV 25 | ✓ KV 68 |
| Qwen3-8B FP8 | 8.2 | ✓ KV 12 (W8A16) | ✓ KV 19 | ✓ | ✓ |
| Qwen3-8B AWQ/NVFP4 | 5.5 | ✓ KV 14 | ✓ | ✓ | ✓ |
| Qwen3.5-9B BF16 | 19 | ✓ KV 1.1 GB = 35K tok (32 KB/tok) | ✓ | ✓ | ✓ |
| Qwen3.6-27B FP8 / NVFP4 | 27 / 14 | ✗ / ✗ | ✗ / ✓ | ✓ / ✓ | ✓ BF16 |
| Qwen3.6-35B-A3B NVFP4 / GPTQ-Int4(3.5) | ~18 / ~18 | ✗ / ✓ | ✓ / ✓ | ✓ FP8 | ✓ BF16 |
| Qwen3-30B-A3B GPTQ-Int4 / FP8 | 16 / 30 | ✓ / ✗ | ✓ / ✗ | ✓ / ✓ | ✓ BF16 |
| Gemma 4 E4B BF16 | 8 | ✓ | ✓ | ✓ | ✓ |
| Gemma 4 12B BF16 / FP8 / w4a16 | 24 / 12 / 7 | ✗ / ✗(FP8 연산 없음) / ✓ | △ / ✓ / ✓ | ✓ / ✓ / ✓ | ✓ |
| Gemma 4 26B-A4B FP8 / NVFP4 / AWQ | 25 / 13 / 17 | ✗ / ✗ / ✓ | ✗(KV 2 GB) / ✓ / ✓ | ✓ / ✗ / ✓ | ✓ BF16 |
| Gemma 4 31B FP8 / NVFP4 / w4a16 | 31 / 16 / 16 | ✗ / ✗ / △ KV 4 GB = 13K tok | ✗ / ✓ KV 11 = 34K / ✓ | ✓ / ✗ / ✓ | ✓ BF16 |

## 실험별 배정 (제안)
- **핵심(E1~E6)**: Qwen3-8B. g7·g6e·g7e는 BF16, **g5는 BF16으로 32K가 안 들어가므로 FP8(W8A16)로 32K, BF16은 16K까지** 둘 다 보고. 같은 모델의 BF16 vs FP8 vs NVFP4가 양자화 축.
- **KV 용량 축(E7, g7e BF16)**: Qwen3.6-35B-A3B(20) → Qwen3.5-9B(32) → Gemma 4 26B-A4B(80) → Qwen3-8B(144) → Gemma 4 31B(320). 16배 범위.
- **양자화 축(g7 Blackwell)**: Qwen3-8B {BF16, FP8, NVFP4} × KV {BF16, fp8}. 큰 모델은 Qwen3.6-27B {FP8, NVFP4}, Gemma 4 26B-A4B {NVFP4}.
- **A10G 양자화 축**: Qwen3-8B {BF16@16K, FP8-W8A16, AWQ}, Gemma 4 12B w4a16-ct(공식 QAT), Qwen3.5-9B BF16(KV가 작아 24GB에서 유일하게 BF16 32K 가능한 9B급).

## 확인 필요 (PD 커넥터)
1. Qwen3.5/3.6 hybrid: 선형 어텐션(Gated DeltaNet) 층의 recurrent state를 NixlConnector가 옮기는가. vLLM 2026-04 "hybrid SSM disagg" 블로그가 Mamba 계열을 다뤘고 GDN도 같은 경로인지 확인. 안 되면 E7에서 제외하고 이슈.
2. Gemma 4 sliding window 층의 KV 블록 전송(열린 질문 1).
3. Qwen3.5/3.6/3.8은 VL 네이티브. 텍스트만 서빙 시 `--limit-mm-per-prompt '{"image":0}'`로 비전 인코더 메모리 절약 여부.
4. A10G에서 FP8 체크포인트는 Marlin W8A16으로 로드되는지(vLLM이 자동 폴백), 속도는 BF16과 비슷하거나 느릴 수 있음 → 기록.

# 인스턴스별 테스트 매트릭스 (2026-09-24 개정: g5는 참조점, Gemma 우선, 양자화 최대 성능 + slow-network PD 최대 효과)

기준: 32K 요청이 동시에 2개 이상 들어갈 KV 예산(KV ≥ 2 × 32K × KB/tok). "ref"는 같은 GPU에서의 비양자화 기준, "max"는 그 GPU에 들어가는 가장 큰 양자화 모델.
KV fp8은 Ada·Blackwell에서만(전송 바이트 절반) → g6e/g7/g7e 전 구성에 on/off 축.

| 인스턴스 | GPU / VRAM | 우선 | 모델 | 정밀도 | 가중치 GB | KV 예산 GB | 32K 동시 | 역할 |
|---|---|---|---|---|---|---|---|---|
| **g7e.2xlarge** | RTX PRO 6000 96 | 1 | Gemma 4 31B | BF16 | 62 | 23 | 2 | ref, KV 최대(320 KB/tok) → PD 최악 |
| | | 1 | Gemma 4 31B | NVFP4 (nvidia/RedHatAI) | 16 | 69 | 6 | **max 양자화 성능** |
| | | 1 | Gemma 4 31B | FP8-block (RedHatAI) | 31 | 54 | 5 | FP8 vs NVFP4 |
| | | 1 | Gemma 4 26B-A4B | BF16 | 50 | 35 | 13 | ref, MoE |
| | | 1 | Gemma 4 26B-A4B | NVFP4 / FP8-dyn | 13 / 25 | 72 / 60 | 27 / 23 | MoE 양자화 |
| | | 2 | Qwen3.6-35B-A3B | BF16 / FP8 / NVFP4 | 70 / 35 / 18 | 15 / 50 / 67 | 23 / 78 / 100+ | KV 최소(20 KB/tok) → PD 최선. hybrid 커넥터 확인 |
| | | 2 | Qwen3.8-27B | BF16 / FP8 / NVFP4 | 54 / 27 / 14 | 31 / 58 / 71 | 15 / 28 / 34 | 27B dense(hybrid) |
| | | 3 | Qwen3-30B-A3B | BF16 / FP8 / NVFP4 | 61 / 30 / 16 | 24 / 55 / 69 | 8 / 18 / 22 | classic GQA MoE(hybrid 리스크 없음) |
| | | 3 | Qwen3-8B | BF16 | 16 | 69 | 15 | 세대 간 앵커 |
| **g7.2xlarge** | RTX PRO 4500 32 | 1 | Gemma 4 26B-A4B | NVFP4 | 13 | 14 | 5 | **주 모델** |
| | | 1 | Gemma 4 31B | NVFP4 | 16 | 11 | 1 | max 모델(16K까지 2개) |
| | | 1 | Gemma 4 12B | BF16 / FP8 / NVFP4 | 24 / 12 / 6 | 3 / 15 / 21 | 0(16K 1) / 3 / 5 | 같은 모델 정밀도 3종 (BF16은 16K 한정) |
| | | 2 | Qwen3.6-35B-A3B | NVFP4 | 18 | 9 | 14 | KV 최소 |
| | | 2 | Qwen3.8-27B | NVFP4 | 14 | 13 | 6 | |
| | | 3 | Qwen3-8B | BF16 / FP8 / NVFP4 | 16 / 8 / 5 | 11 / 19 / 22 | 2 / 4 / 4 | 앵커 + 순수 양자화 축 |
| **g6e.4xlarge** (선택) | L40S 48, NVFP4 ✗ | 2 | Gemma 4 26B-A4B | FP8-dyn | 25 | 17 | 6 | Ada 중간점 |
| | | 2 | Gemma 4 31B | FP8-block | 31 | 11 | 1 | max |
| | | 2 | Gemma 4 12B | BF16 / FP8 | 24 / 12 | 18 / 30 | 4 / 7 | ref 쌍 |
| | | 3 | Qwen3.6-35B-A3B / Qwen3-30B-A3B | FP8 | 35 / 30 | 7 / 12 | 11 / 4 | |
| **g5.2xlarge** (참조) | A10G 24, FP8 연산 ✗ | 4 | Gemma 4 26B-A4B | AWQ (커뮤니티) / QAT q4_0 | 17 | 4 | 1 | Ampere 하한 참조 |
| | | 4 | Gemma 4 12B | QAT w4a16-ct (google) | 7 | 14 | 3 | |
| | | 4 | Qwen3-8B | FP8(W8A16) / AWQ | 8 / 5.5 | 12 / 14 | 2 / 3 | |

## 축 정리
- **양자화 최대 성능**: g7e에서 Gemma 4 31B NVFP4·FP8 vs BF16, 26B-A4B NVFP4 vs BF16(같은 GPU, 같은 모델). g7에서는 BF16 ref가 12B뿐이라 "12B BF16 vs 26B-A4B NVFP4"처럼 **같은 VRAM 예산에서 무엇이 더 나은가**로 묻는다.
- **slow-network PD 최대 효과**: KV/tok이 작고 출력이 긴 조합에서 최대 → Qwen3.6-35B-A3B(20), Gemma 4 26B-A4B(80) + 출력 512 + 채팅형 SLO. 반대 극단은 Gemma 4 31B(320).
- 세대 앵커: Qwen3-8B BF16을 g7·g7e(·g6e·g5)에 공통으로.

## 세션 배정 (쿼타 8 → 16 기준)
| 세션 | 인스턴스 | 쿼타 | 모델 |
|---|---|---|---|
| A (9/27) | g7.2xlarge ×1 | 8 | Gemma 4 26B-A4B NVFP4, Gemma 4 12B BF16/FP8, Qwen3-8B BF16: B1 특성화, 단일 스텝, KV bytes 검증 |
| A′ (평일 1h) | g7e.2xlarge ×1 | 8 | Gemma 4 31B BF16/NVFP4, 26B-A4B BF16, Qwen3.6-35B-A3B BF16: 기동·KV bytes·단일 스텝 |
| B | g7.2xlarge ×2 (+c6i) | 16 | B2 vs P1 N0 + tc 스윕: 26B-A4B NVFP4(주), Qwen3-8B BF16(앵커) |
| C | g7e.2xlarge ×2 (+c6i) | 16 | 31B BF16/NVFP4/FP8, 26B-A4B BF16/NVFP4, 35B-A3B, KV fp8 on/off: 양자화 축 + KV 용량 축 |
| D | g7.2xlarge ×2 / g7e ×2, placement group | 16 | N1 10 Gbps 검증점, 트레이스(Azure·Mooncake), LongBench·HumanEval |
| E (선택) | g6e.4xlarge ×2 (32) / g5.2xlarge ×2 (16) | 16~32 | Ada 중간점 / Ampere 하한 참조 |


## 2026-09-25 결정: Qwen hybrid(3.5 이상, GDN/Mamba) 계열은 핵심 실험에서 제외
- 근거: C1에서 Qwen3.6-35B-A3B FP8이 0.5 req/s부터 요청의 17%에 5배 넘는 디코드 멈춤(admission 시점 패턴). hybrid의 prefix caching 제약(블록 정렬)도 prefix 반복 워크로드 축과 충돌. vLLM 쪽 문제일 수 있으나 이 실험의 범위 밖.
- 처리: 35B-A3B는 "관찰"로 보고서에 한 단락만. 세션 C의 P1 멈춤 확인은 선택(10분)으로 강등.
- 대체: **Qwen3-30B-A3B**(classic GQA MoE, 48층·4 KV 헤드, 96 KB/tok, 공식 FP8·GPTQ-Int4, nvidia NVFP4). g7e에서 BF16 61 GB / FP8 30 GB / NVFP4 16 GB. Gemma 26B-A4B(80 KB/tok, 슬라이딩)와의 MoE 대조이자 KV 용량 축의 중간점.
- Qwen3.8-27B(hybrid dense)도 같은 이유로 제외. dense Qwen 앵커는 Qwen3-8B 유지.
