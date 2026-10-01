# R5 (4차): 글쓰기, 구조, 그림

대상: "Chunk First: When Prefill–Decode Disaggregation Pays Off over TCP" (paper/en/main.tex v4, main.pdf 33쪽)
근거: main.tex 전문, v3와의 차이, 3차 r6_meta.md, PDF 렌더링(그림 7은 200 dpi), `make_figures_v4.py`의 `fig_boundary`, `boundary_model.py`, `figures_v4/boundary.json`. 저장소는 읽기만 했다. 줄 번호는 main.tex 기준이다. 단어 수는 명령어를 뺀 산문 기준(`r5/wc_*.py`)이다. 저자 집계에는 캡션과 표가 더해져 있지만, 절감 폭은 그대로 옮겨 쓸 수 있다.

## 1. 요약

재구성은 성공했다. 제목, 초록, 41행, RQ 세 개, 4·5·6절 제목이 "청크를 먼저 조정하고, 안 되는 곳에서 분리를 검토한다"는 한 줄로 이어진다. RQ1(비용의 크기) → RQ2(4K·대화 맞대결) → RQ3(모델로 본 경계)의 순서도 자연스럽다. 6절은 첫 단락과 한계 절(343행)에서 예측임을 밝힌다.

문제는 세 가지다.
1. **초록과 결론의 장입력 주장에 TTFT 한도 조건이 빠졌다.** 그래서 독자는 이 주장을 논문의 엄격 SLO(1 s, 50 ms)에 대한 것으로 읽는다. 그런데 boundary.json을 보면 엄격 SLO에서 모델이 예측하는 분리 전용 구간은 없다. 50 ms에서 복제본은 약 15.7K, 1P1D는 약 14.4K 토큰에서 1 s를 넘는다. 21K의 교차점은 TTFT 1.59 s에서 생긴다.
2. **그림 7과 본문이 한 곳에서 어긋난다.** 그림 7의 범례 하나는 예측을 측정처럼 읽히게 한다.
3. **용어가 흩어지고 분량이 다시 늘었다(v3 대비 약 +1,380단어).** "window"가 네 가지 뜻으로, 경계는 다섯 가지 말로 쓰인다. 결과 요약이 초록, "In short", §7.1, 결론에서 네 번 반복되고, §8 함정 절은 논의 뒤에 떨어져 있다.

초록, 그림 5·6·7, 표 2, §7.2만 읽는 실무자는 4K·대화의 메시지는 제대로 받지만, 장입력은 "20K를 넘으면 엄격 SLO에서 분리가 이긴다"로 잘못 받는다. §7.2는 그림 7도 KV 크기 조건도 언급하지 않는다.

## 2. 점수

**4.0 / 5.** 재구성과 6절의 예측 표시는 좋지만, 장입력 주장의 범위, 그림 7과 본문의 불일치, 용어 난립을 고쳐야 오독을 막는다. 모두 원고와 그림 수정이다.

## 3. 반드시 고칠 것

**M1. 장입력 주장에 TTFT 한도 띠를 넣는다(32, 51, 290, 312, 354행).**
- 근거(boundary.json): 50 ms에서 1P1D만 지키는 칸은 TTFT 1.59 s 이상에서만 생긴다(32K에서 2.8–3.5 s, 64K에서 8.2–12.7 s). 30 ms에서는 교차점이 10.6K(0.79 s)라서, 1 s 한도에서도 약 12K–14K에 생긴다.
- 290행 뒤에 다음 문장을 넣는다.
  > "Under our strict SLO (1 s, 50 ms) the model predicts no such region: replicas pass 1 s up to about 16K tokens and 1P1D only up to about 14K. At 50 ms the region starts at TTFT limits of about 1.6 s; at a 30 ms gap it appears under 1 s between about 12K and 14K tokens."
- 초록, "In short", RQ3, 결론에도 "at TTFT limits above about 1.5 s"를 넣는다(5절 초록안 참조).
- 그림 7에 1 s와 3 s 가로 기준선을 긋는다. 이 사실이 그림 한 장으로 보인다.

**M2. 전역 KV 문장이 그림 7(b)와 어긋난다(296, 312행).**
- 296행은 "1P1D meets no TTFT limit that replicas miss up to 64K"라고 쓴다. 그런데 그림 7(b)에서 약 35.7K부터는 어떤 청크도 30 ms를 지키지 못하고, 갈색 대시는 주황 칸 안을 지난다(그 지점에서 9.1 s).
- 민감도 결과의 `None`은 TTFT 격자가 8.98 s에서 끝나서 생긴 값이다.
- 문안: "…up to 64K at a 50 ms gap limit and for TTFT limits up to 9 s; at 30 ms, beyond about 35K, where no chunk fits, it meets only limits above about 9 s."
- 같은 줄 "Hybrid attention is what lets…" → "A small KV cache, here from hybrid attention, is what lets…". 모델에서는 V(L)을 줄이는 수단이면 무엇이든 같은 효과를 낸다.

**M3. 그림 7(v4_boundary)을 고친다.**
1. 범례 "hybrid KV (as measured)"는 예측 그림에서 측정값처럼 읽힌다. "(this checkpoint's KV)"로 바꾼다.
2. 예측 표시가 작은 회색 윗제목뿐이다. 패널 제목을 "(a) Model, gap limit 50 ms"로 바꾼다.
3. 색 규칙(파랑 = 복제본, 주황 = 분리)과 녹색약용 이중 부호화(선 모양과 명도 세 단계)는 지켰다. 그러나 갈색 긴 대시는 그림 5에서 "1P1D, 프리필 청크 8,192"를 뜻하고, 그림 7의 1P1D 곡선은 모두 8,192 프리필을 가정한다. 전역 KV는 주황 계열의 얇은 dash-dot으로 바꾸고 곡선 끝에 직접 라벨을 단다.
4. 보정/외삽 경계의 회색 대시는 갈색 대시와 명도·모양이 비슷하다. 얇은 실선으로 바꾸고 외삽 구간은 옅은 빗금으로 칠한다. "calibrated ≤16K"는 2K–4K도 보정한 것처럼 읽히므로, x축의 4K와 16K에 보정점 마커를 둔다.
5. 표 3의 4K 측정값(청크 1,024는 194 ms, 512는 239 ms, 1P1D는 362 ms)을 속 빈 마커로 겹친다. 주황 곡선(0.42 s, m = 1)이 측정값보다 높다는 점도 함께 보인다.
6. 회색 "Neither meets the TTFT limit" 영역 안으로 빠른 연결 점선이 지난다. "Neither replicas nor 1P1D over TCP (this KV)"로 쓴다.
7. y축 첫 눈금이 0.25라서 2K의 복제본 값(0.11 s)이 읽히지 않는다. 0.125 눈금을 더한다.
8. 범례 "5% of TCP transfer time"과 캡션 "20× faster"를 맞춘다. 주황 곡선의 8K 꺾임(프리필 둘째 스텝)과 파랑 곡선의 계단(청크 수 올림)을 캡션에 적는다.

**M4. 수치와 통계의 표기가 어긋난다.**
- 249행과 343행은 "seven measurements"라고 쓰는데, 열거는 3 + 3 = 6이다. 표 3의 "check" 행도 여섯이다. 일곱째(외삽 점검인지)를 밝히거나 "six"로 고친다.
- 표 3의 "longest gap"은 p90이고, 그림 2와 본문은 중앙값을 쓴다. 표 3 열 머리를 "longest gap (p90)"으로 바꾼다.

**M5. 6절이 지표를 바꾼다는 사실을 밝힌다(236행, 그림 7 캡션).**
- RQ2는 GPU당 굿풋을 비교한다. 6절은 저부하에서 어느 쪽이 두 한도를 지킬 수 있는지를 본다.
- 236행 끝에 넣는다: "Unlike Section 5, the map asks which side can meet both limits at low load, not how much load each serves per GPU."
- 제목의 "Pays Off"에 맞춰 결론 끝에 한 문장을 둔다: "Disaggregation over TCP paid off when the chunk could not shrink; our model predicts it can also pay off for inputs beyond about 20K tokens with small KV caches and TTFT limits of seconds."

**M6. §7.2 절차 5에 6절의 결과를 연결한다(320행).** 지금은 그림 7도, KV 조건도 없다.
> "Consider disaggregation over TCP only where no chunk meets both limits (Figure 7 predicts this beyond about 20K tokens at a 50 ms gap and TTFT limits above 1.5 s, for 26B FP8 on g7e) and the KV cache is small enough for Eq. (2) to fit the TTFT limit: …"

**M7. 최악의 문장 10개와 대체 문안**
1. 32행: "tuned chunks left no SLO we could rank in which disaggregation served more" → "against tuned chunks, disaggregation served more per GPU under none of the SLOs our measured rates could rank". 초록에서 SLO를 처음 쓸 때 풀어 쓴다.
2. 32행: "as vLLM requires for Gemma 4 with video input" → "near the 2,496-token floor vLLM sets for Gemma 4 with video input". 2,560이라는 값 자체를 vLLM이 요구하지는 않는다.
3. 24행 부제: "a Calibrated Boundary" → "a Calibrated Model". 보정한 것은 모델이고, 경계는 예측이다.
4. 51행의 RQ1 답은 비용이 아니라 해법을 말한다. → "a prefill chunk stalled co-scheduled decodes for about one step, 48 ms at 2,560 tokens and 21 ms at 512 (26B, 4K, 1 request/s per GPU), and disaggregation added 137–370 ms of TTFT at low load, 61–85% of it KV transfer (RQ1)."
5. 247행: "the same $aL + bL^2/2$"는 $n_P(d+e)$가 빠져 있고, m = 1을 고른 이유도 없다. → "…plus the transfer with $m = 1$, the rate at the loads that decided our verdicts, and a 28 ms residual."
6. 289행: "the model agrees with our measurements" → "the model puts the largest chunk for a 50 ms gap at about 1,600 tokens (TTFT 0.17 s), between the measured 1,024 (43.6 ms) and 2,560 (62.9 ms)". 1,600 토큰 청크는 측정한 적이 없다.
7. 290행: "replicas meet any TTFT limit that 1P1D meets up to about 21K tokens" → "for inputs up to about 21K tokens, replicas meet every TTFT limit that 1P1D meets".
8. 291·297–299·325행: 정의 없이 쓴 "the window opens"를 287행에서 정의한 이름으로 바꾼다. 문안: "We call the shortest input at which only 1P1D meets both limits the crossover length." 이후 "the crossover length is about 11K at 30 ms"처럼 쓴다.
9. 310행 → "No. Against replicas with a 256–1,024-token chunk, disaggregation over TCP served more under none of the SLOs our measured rates could rank, down to 30 ms gap limits, and its median TTFT was higher at every load where both passed."
10. 176행: "beyond a 1 s budget" → "beyond a 1 s TTFT limit". 113행의 끝 문장 "Under the earlier rule, these two…"는 앞 문장을 되풀이하므로 지운다.

**용어 통일**
| 개념 | 현재 | 권고 |
|---|---|---|
| 요청별 최대 간격 | longest gap, longest inter-token gap, longest step(317행, 그림 7 캡션) | 관측은 "longest gap", 모델은 "step time". 243행에서 "longest gap = longest step"을 한 번 정의한다 |
| 청크 | tuned, best(표 2), best measured(그림 6), workable(320행), admissible | 측정은 "tuned chunk"(180행에서 정의), 모델은 "largest admissible chunk" |
| 경계 | boundary, turning point, runs out, take over, window | "crossover length", 절 제목만 "boundary" |
| window | 슬라이딩 창 W, TCP 수신 창, vLLM 10 s 창, 분리 전용 구간 | 앞의 셋만 남긴다 |

## 4. 고치면 좋은 것

**분량 절감안(우선순위순, 산문 단어)**
| 순위 | 내용 | 예상 절감 |
|---|---|---|
| 1 | §8(335–337행, 389단어)과 그림 8을 부록 B로. 실천 내용은 절차 6(321행)에 이미 있다. §3.6에 두 문장만 남긴다 | −330 |
| 2 | 방법론(약 1,250단어): 95행 서버 설정 예외 → 부록 표(−80), 107행 상한 경위 → §3.6 한 곳(지금 일곱 번 나옴, −60), 113행 1토큰 규칙 경위 → 부록 D(−60), 120행 제외 런 내역 → 부록 G(−70), 117행 임계값 근거 한 문장(−40), 78행 iperf 세부(−30) | −340 |
| 3 | §7.1(308–312행, 285단어) 삭제. 고유 정보 셋(청크의 TTFT 비용 30·70 ms, 31B는 256, 부하 아래 전송 대기열)은 4·5·6절 끝 한 문장씩으로. 답은 "In short"와 결론이 맡는다 | −230 |
| 4 | 158행 NIXL 디스크립터 산술 → 부록 C, 한 문장 남김(−110). 160행 공유 상한 두 문장(−40) | −150 |
| 5 | 43행 모의 심사 경위 → 한 문장과 부록 E 포인터(−80), 기여 목록 축약(−40) | −120 |
| 6 | 205행 프리필 청크 8,192 문단(판정 불변) → 한 문장 남기고 부록으로 | −95 |
| 7 | §7.3(132단어)을 §6.3 "Link speed"와 한계 절에 합친다 | −80 |

1–4순위만으로 약 1,050단어가 줄어 본문이 약 7,250단어가 되고, 증거는 모두 부록에 남는다.

**기타**
- RQ2(48행)에 "…and what changes when the chunk cannot shrink?"를 더하고, RQ3에는 "(model)"을 붙인다.
- 6절 첫머리에 "Sections 4.2 and 4.4 supply the two terms of the model."을 둔다.
- 319행 "longer prompts favor loading"은 Eq. (1)과 (4)에서 나온 추론이라고 밝힌다.
- 제목 둘째 줄에 "TCP" 한 단어만 남는다.

## 5. 초록 제안 (210단어, `wc -w`)

> Prefill–decode disaggregation usually relies on RDMA or NVLink, which cheap single-GPU instances lack. For a TCP-linked fleet of such instances, we ask whether disaggregation is worth considering once chunked prefill, which attacks the same decode stalls, is tuned, and if so, where. Serving Gemma 4 26B and 31B with stock vLLM and NIXL/UCX on AWS, we judged each request by its time to first token (TTFT) and longest inter-token gap. A replica's longest gap followed the chunk size (26B, 4K inputs: 48 ms at 2,560 tokens, 21 ms at 512), and most of disaggregation's added TTFT was the KV transfer, which a larger UCX TCP segment made 3.4× faster at low load. At 4K inputs and in chat, against tuned chunks, disaggregation served more per GPU under none of the latency targets our measured rates could rank. It won only against replicas held at 2,560 tokens, near vLLM's floor for Gemma 4 with video input (about 3× for 26B). A step-time model calibrated on our runs (out-of-sample TTFT within 8%) predicts that, with a small KV cache as from hybrid attention, disaggregation meets a band of TTFT limits (above 1.5 s at a 50 ms gap limit) that no chunk can beyond roughly 20K input tokens. Tune the chunk first.

현행안과 다른 점: TTFT 한도 띠(M1), "near vLLM's floor", 풀어 쓴 SLO 문장, 앞 문장과 겹치는 끝 권고의 축약.
