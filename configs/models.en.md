*English translation of `models.md`; the Korean file is the original.*

# Model candidate matrix (2026-09-24, based on config.json and official HF repositories)

KV KB/tok = full-attention layers only, BF16 basis (sliding-window and linear-attention layers excluded. Sliding window is capped at window 1024; linear attention has a fixed per-request state).
KV budget ≈ VRAM×0.90 − weights − 1.5 GB. KV needed for one 32K request = KB/tok × 32K.

| Model | Structure | Total/active | KV KB/tok | BF16 GB | 32K request KV | Official quantizations |
|---|---|---|---|---|---|---|
| Qwen3-8B | dense GQA | 8B | **144** | 16.4 | 4.6 GB | FP8(Qwen), AWQ(Qwen), NVFP4(nvidia) |
| Qwen3-14B | dense GQA | 14B | 160 | 29.5 | 5.1 | FP8, AWQ(Qwen), NVFP4 |
| Qwen3-30B-A3B | MoE GQA | 30B/3B | 96 | 61 | 3.1 | FP8, GPTQ-Int4(Qwen), NVFP4 |
| Qwen3.5-9B | hybrid (8 full + 24 linear) | 9B | **32** | ~19 | 1.0 | FP8-dyn, w4a16, w8a8(RedHatAI) |
| Qwen3.6-27B | hybrid (16 + 48) | 27B | 64 | ~54 | 2.0 | FP8(Qwen), NVFP4(nvidia) |
| Qwen3.6-35B-A3B | hybrid MoE (10 + 30) | 35B/3B | **20** | ~70 | 0.6 | FP8(Qwen), NVFP4(nvidia, RedHatAI), GPTQ-Int4(3.5) |
| Gemma 4 E4B | hybrid sliding (7 full + 35 sw) | ~8B raw / 4B eff | 28 | ~8 | 0.9 | QAT w4a16-ct(google) |
| Gemma 4 12B | sliding (8 + 40) | 12B | 128 | ~24 | 4.1 | FP8-dyn, NVFP4(RedHatAI), QAT w4a16-ct(google) |
| Gemma 4 26B-A4B | sliding MoE (5 + 25) | 26B/4B | 80 | ~50 | 2.6 | FP8-dyn, NVFP4(RedHatAI, nvidia), QAT q4_0(google), AWQ(community) |
| Gemma 4 31B | sliding (10 + 50) | 31B | **320** | ~62 | 10.2 | FP8-block, NVFP4(RedHatAI, nvidia), QAT w4a16-ct(google) |

## Precision support per GPU
| GPU | VRAM | BF16 | FP8 compute | INT4(AWQ/GPTQ, Marlin) | NVFP4 |
|---|---|---|---|---|---|
| A10G (g5) | 24 | ✓ | ✗ (weights only, W8A16) | ✓ | ✗ |
| L40S (g6e) | 48 | ✓ | ✓ | ✓ | ✗ |
| RTX PRO 4500 (g7) | 32 | ✓ | ✓ | ✓ | ✓ |
| RTX PRO 6000 (g7e) | 96 | ✓ | ✓ | ✓ | ✓ |

## What fits where (at least one 32K request, by KV budget)
| Model and precision | Weights GB | g5 24 | g7 32 | g6e 48 | g7e 96 |
|---|---|---|---|---|---|
| Qwen3-8B BF16 | 16.4 | △ KV 3.7 GB → **not even one 32K request, up to 16K** | ✓ KV 11 | ✓ KV 25 | ✓ KV 68 |
| Qwen3-8B FP8 | 8.2 | ✓ KV 12 (W8A16) | ✓ KV 19 | ✓ | ✓ |
| Qwen3-8B AWQ/NVFP4 | 5.5 | ✓ KV 14 | ✓ | ✓ | ✓ |
| Qwen3.5-9B BF16 | 19 | ✓ KV 1.1 GB = 35K tok (32 KB/tok) | ✓ | ✓ | ✓ |
| Qwen3.6-27B FP8 / NVFP4 | 27 / 14 | ✗ / ✗ | ✗ / ✓ | ✓ / ✓ | ✓ BF16 |
| Qwen3.6-35B-A3B NVFP4 / GPTQ-Int4(3.5) | ~18 / ~18 | ✗ / ✓ | ✓ / ✓ | ✓ FP8 | ✓ BF16 |
| Qwen3-30B-A3B GPTQ-Int4 / FP8 | 16 / 30 | ✓ / ✗ | ✓ / ✗ | ✓ / ✓ | ✓ BF16 |
| Gemma 4 E4B BF16 | 8 | ✓ | ✓ | ✓ | ✓ |
| Gemma 4 12B BF16 / FP8 / w4a16 | 24 / 12 / 7 | ✗ / ✗(no FP8 compute) / ✓ | △ / ✓ / ✓ | ✓ / ✓ / ✓ | ✓ |
| Gemma 4 26B-A4B FP8 / NVFP4 / AWQ | 25 / 13 / 17 | ✗ / ✗ / ✓ | ✗(KV 2 GB) / ✓ / ✓ | ✓ / ✗ / ✓ | ✓ BF16 |
| Gemma 4 31B FP8 / NVFP4 / w4a16 | 31 / 16 / 16 | ✗ / ✗ / △ KV 4 GB = 13K tok | ✗ / ✓ KV 11 = 34K / ✓ | ✓ / ✗ / ✓ | ✓ BF16 |

## Assignment per experiment (proposal)
- **Core (E1~E6)**: Qwen3-8B. BF16 on g7, g6e, and g7e; **on g5, BF16 does not fit 32K, so report both FP8 (W8A16) at 32K and BF16 up to 16K**. BF16 vs FP8 vs NVFP4 of the same model is the quantization axis.
- **KV capacity axis (E7, g7e BF16)**: Qwen3.6-35B-A3B(20) → Qwen3.5-9B(32) → Gemma 4 26B-A4B(80) → Qwen3-8B(144) → Gemma 4 31B(320). A 16x range.
- **Quantization axis (g7 Blackwell)**: Qwen3-8B {BF16, FP8, NVFP4} × KV {BF16, fp8}. Large models: Qwen3.6-27B {FP8, NVFP4}, Gemma 4 26B-A4B {NVFP4}.
- **A10G quantization axis**: Qwen3-8B {BF16@16K, FP8-W8A16, AWQ}, Gemma 4 12B w4a16-ct (official QAT), Qwen3.5-9B BF16 (small KV, the only 9B-class model that fits BF16 32K in 24GB).

## To confirm (PD connector)
1. Qwen3.5/3.6 hybrid: does NixlConnector move the recurrent state of the linear-attention (Gated DeltaNet) layers? The vLLM 2026-04 "hybrid SSM disagg" blog covered the Mamba family; check whether GDN takes the same path. If not, exclude from E7 and file an issue.
2. KV block transfer for Gemma 4 sliding-window layers (open question 1).
3. Qwen3.5/3.6/3.8 are VL native. When serving text only, does `--limit-mm-per-prompt '{"image":0}'` save vision encoder memory?
4. On A10G, is the FP8 checkpoint loaded as Marlin W8A16 (vLLM falls back automatically)? Speed may be similar to or slower than BF16 → record.

# Per-instance test matrix (revised 2026-09-24: g5 as reference point, Gemma first, maximum quantization performance + maximum slow-network PD effect)

Criterion: a KV budget that fits at least 2 concurrent 32K requests (KV ≥ 2 × 32K × KB/tok). "ref" is the unquantized baseline on the same GPU, "max" is the largest quantized model that fits on that GPU.
KV fp8 only on Ada and Blackwell (halves transfer bytes) → an on/off axis for every g6e/g7/g7e configuration.

| Instance | GPU / VRAM | Priority | Model | Precision | Weights GB | KV budget GB | Concurrent 32K | Role |
|---|---|---|---|---|---|---|---|---|
| **g7e.2xlarge** | RTX PRO 6000 96 | 1 | Gemma 4 31B | BF16 | 62 | 23 | 2 | ref, largest KV (320 KB/tok) → worst case for PD |
| | | 1 | Gemma 4 31B | NVFP4 (nvidia/RedHatAI) | 16 | 69 | 6 | **max quantization performance** |
| | | 1 | Gemma 4 31B | FP8-block (RedHatAI) | 31 | 54 | 5 | FP8 vs NVFP4 |
| | | 1 | Gemma 4 26B-A4B | BF16 | 50 | 35 | 13 | ref, MoE |
| | | 1 | Gemma 4 26B-A4B | NVFP4 / FP8-dyn | 13 / 25 | 72 / 60 | 27 / 23 | MoE quantization |
| | | 2 | Qwen3.6-35B-A3B | BF16 / FP8 / NVFP4 | 70 / 35 / 18 | 15 / 50 / 67 | 23 / 78 / 100+ | smallest KV (20 KB/tok) → best case for PD. Check hybrid connector |
| | | 2 | Qwen3.8-27B | BF16 / FP8 / NVFP4 | 54 / 27 / 14 | 31 / 58 / 71 | 15 / 28 / 34 | 27B dense (hybrid) |
| | | 3 | Qwen3-30B-A3B | BF16 / FP8 / NVFP4 | 61 / 30 / 16 | 24 / 55 / 69 | 8 / 18 / 22 | classic GQA MoE (no hybrid risk) |
| | | 3 | Qwen3-8B | BF16 | 16 | 69 | 15 | cross-generation anchor |
| **g7.2xlarge** | RTX PRO 4500 32 | 1 | Gemma 4 26B-A4B | NVFP4 | 13 | 14 | 5 | **main model** |
| | | 1 | Gemma 4 31B | NVFP4 | 16 | 11 | 1 | max model (2 at up to 16K) |
| | | 1 | Gemma 4 12B | BF16 / FP8 / NVFP4 | 24 / 12 / 6 | 3 / 15 / 21 | 0(16K 1) / 3 / 5 | same model, three precisions (BF16 limited to 16K) |
| | | 2 | Qwen3.6-35B-A3B | NVFP4 | 18 | 9 | 14 | smallest KV |
| | | 2 | Qwen3.8-27B | NVFP4 | 14 | 13 | 6 | |
| | | 3 | Qwen3-8B | BF16 / FP8 / NVFP4 | 16 / 8 / 5 | 11 / 19 / 22 | 2 / 4 / 4 | anchor + pure quantization axis |
| **g6e.4xlarge** (optional) | L40S 48, NVFP4 ✗ | 2 | Gemma 4 26B-A4B | FP8-dyn | 25 | 17 | 6 | Ada midpoint |
| | | 2 | Gemma 4 31B | FP8-block | 31 | 11 | 1 | max |
| | | 2 | Gemma 4 12B | BF16 / FP8 | 24 / 12 | 18 / 30 | 4 / 7 | ref pair |
| | | 3 | Qwen3.6-35B-A3B / Qwen3-30B-A3B | FP8 | 35 / 30 | 7 / 12 | 11 / 4 | |
| **g5.2xlarge** (reference) | A10G 24, FP8 compute ✗ | 4 | Gemma 4 26B-A4B | AWQ (community) / QAT q4_0 | 17 | 4 | 1 | Ampere lower-bound reference |
| | | 4 | Gemma 4 12B | QAT w4a16-ct (google) | 7 | 14 | 3 | |
| | | 4 | Qwen3-8B | FP8(W8A16) / AWQ | 8 / 5.5 | 12 / 14 | 2 / 3 | |

## Axis summary
- **Maximum quantization performance**: on g7e, Gemma 4 31B NVFP4 and FP8 vs BF16, 26B-A4B NVFP4 vs BF16 (same GPU, same model). On g7 the only BF16 ref is 12B, so the question becomes **which is better under the same VRAM budget**, as in "12B BF16 vs 26B-A4B NVFP4".
- **Maximum slow-network PD effect**: largest where KV/tok is small and outputs are long → Qwen3.6-35B-A3B(20), Gemma 4 26B-A4B(80) + output 512 + chat-style SLO. The opposite extreme is Gemma 4 31B(320).
- Generation anchor: Qwen3-8B BF16 common to g7 and g7e (and g6e, g5).

## Round assignment (quota 8 → 16 basis)
| Round | Instances | Quota | Models |
|---|---|---|---|
| A (9/27) | g7.2xlarge ×1 | 8 | Gemma 4 26B-A4B NVFP4, Gemma 4 12B BF16/FP8, Qwen3-8B BF16: B1 characterization, single decode step, KV bytes verification |
| A′ (weekday 1h) | g7e.2xlarge ×1 | 8 | Gemma 4 31B BF16/NVFP4, 26B-A4B BF16, Qwen3.6-35B-A3B BF16: startup, KV bytes, single decode step |
| B | g7.2xlarge ×2 (+c6i) | 16 | B2 vs P1 N0 + tc sweep: 26B-A4B NVFP4 (main), Qwen3-8B BF16 (anchor) |
| C | g7e.2xlarge ×2 (+c6i) | 16 | 31B BF16/NVFP4/FP8, 26B-A4B BF16/NVFP4, 35B-A3B, KV fp8 on/off: quantization axis + KV capacity axis |
| D | g7.2xlarge ×2 / g7e ×2, placement group | 16 | N1 10 Gbps verification point, traces (Azure, Mooncake), LongBench, HumanEval |
| E (optional) | g6e.4xlarge ×2 (32) / g5.2xlarge ×2 (16) | 16~32 | Ada midpoint / Ampere lower-bound reference |


## Decision 2026-09-25: Qwen hybrid family (3.5 and later, GDN/Mamba) excluded from the core experiments
- Grounds: in C1, Qwen3.6-35B-A3B FP8 showed decode stalls of more than 5x on 17% of requests from 0.5 req/s (a pattern at admission time). The hybrid prefix caching constraint (block alignment) also conflicts with the prefix-repetition workload axis. It may be a vLLM-side problem, but it is outside the scope of this experiment.
- Handling: 35B-A3B gets one paragraph in the report as an "observation". The P1 stall check in round C is downgraded to optional (10 minutes).
- Replacement: **Qwen3-30B-A3B** (classic GQA MoE, 48 layers, 4 KV heads, 96 KB/tok, official FP8 and GPTQ-Int4, nvidia NVFP4). On g7e: BF16 61 GB / FP8 30 GB / NVFP4 16 GB. A MoE contrast to Gemma 26B-A4B (80 KB/tok, sliding) and the midpoint of the KV capacity axis.
- Qwen3.8-27B (hybrid dense) is excluded for the same reason. The dense Qwen anchor stays Qwen3-8B.
