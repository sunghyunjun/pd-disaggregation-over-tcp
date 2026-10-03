# 영어 원고 v4 모의 심사 4차 (2026-10-01)

## English summary

Round 4, on English draft v4 (private commit d0f4c12, 33 pages), the "Chunk First" reframing with the calibrated step-time model of Section 6 (`harness/boundary_model.py`). Same five roles plus a meta-reviewer; the author ruled out new measurements. Scores: systems 3.5, methods 3.5, network 4.0, reproducibility 3.5 (numbers 4.0, packaging 2.5), writing 4.0; meta verdict: major revision limited to Section 6 and the places that quote it, no new measurements, keep the reframing. The draft's "beyond roughly 20K tokens only disaggregation meets both limits" was found wrong as stated: the number came from a TTFT grid rather than the curve crossing, the TTFT-limit and low-load conditions were missing, the 1P1D decode node's gap was held at 7 ms against its measured growth with input length, and a point estimate hid a factor-of-two uncertainty. The corrected prediction, now in the report: at a 50 ms gap limit and low load the crossover is near 14K tokens (11K–34K within the model's uncertainty) and 1P1D's advantage ends near 37K where the decode node's own gap reaches the limit; at 30 ms, about 6K (4K–17K) to 18K; essentially no such region under the strict 1 s / 50 ms SLO; per-GPU capacity at 50 ms favors replicas at every length. Reviews and scripts are in Korean.

대상: `paper/en/main.tex` v4 초안(커밋 d0f4c12, 33쪽). "Chunk First" 틀로 재구성하고 6절에 보정 모델(harness/boundary_model.py)을 더한 판.
방식: 심사 에이전트 5명 + 종합 심사자(메타리뷰어) 1명. 저장소는 읽기만 했다. 이 폴더에는 심사평과 분석 스크립트·출력만 옮겼다(재생성 그림 등 산출물 제외).
조건: 저자는 새 측정을 하지 않는다(추가 클라우드 비용 없음).

| 파일 | 역할 | 점수 |
|---|---|---|
| r1_systems.md | 서빙 시스템 | 3.5 |
| r2_methods.md | 측정·통계 | 3.5 |
| r3_network.md | 네트워크·클라우드 | 4.0 |
| r4_repro.md | 재현성 | 3.5 (수치 4.0, 공개용 정리 2.5) |
| r5_writing.md | 글쓰기·구조 | 4.0 |
| r6_meta.md | 종합 심사자 | 주요 수정(6절과 그 수치를 옮긴 곳만), 새 측정 불필요, 재구성 유지 |

## 종합 판정 요지
- v4 초안의 "약 20K부터 분리만 두 한도를 지킨다"는 격자에서 나온 수치, TTFT 한도·저부하 조건 누락, 1P1D 디코드 노드 간격 7 ms 고정, 점 추정 때문에 틀렸다.
- 고친 결론(모델 예측): 50 ms 간격 한도에서 교차 길이 약 14K(불확실성 11K–34K), 디코드 노드 간격이 한도에 닿는 약 37K까지; 30 ms는 약 6K(4K–17K)부터 18K까지. TTFT 한도 1 s 이상, 저부하, 작은 KV가 조건이며, 엄격 SLO(1 s, 50 ms)에서는 그런 구간이 사실상 없다. GPU당 용량은 50 ms에서 복제본이 모든 길이에서 높다.
- 반영 결과는 원고 v4 최종본(이 커밋)과 harness/boundary_model.py, harness/make_figures_v4.py.
