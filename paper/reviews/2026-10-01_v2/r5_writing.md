# Reviewer 5 (3차): 영어 문장, 구조, 그림·표

대상: "Chunked Prefill or Disaggregation? Prefill–Decode Serving over TCP on Single-GPU Cloud Instances" (paper/en/main.tex, main.pdf 25쪽, draft v2 2026-10-01)
근거: main.tex 전문, PDF 25쪽 전부, 본문 그림 6개와 부록 그림 2개(A4, A9)는 220 dpi로 따로 렌더링, figures_v2/*.svg 텍스트·글자 크기 추출, figures.json(그림 4 칸 분류 확인), 2차 리뷰 r5_writing.md와 좌장 r6_chair.md(A10, A12, A14, 6절 초록안), main_v1.tex. 저장소는 읽기만 했다.
인쇄 글자 크기는 SVG 폭을 `\includegraphics` 폭(본문 폭 468pt 기준)으로 환산했다.

## 요약

v2의 이야기는 이제 한 줄로 선다. "청크를 줄일 수 없을 때만 TCP 분리가 이긴다." 초록은 201단어·8문장으로 줄었고, 마지막 문장 "Tune the chunk first."가 제목 질문에 답한다. 도입부의 "In short" 문단이 결과를 미리 보여 준다. §4.3의 두 주제문 "Measured against replicas at a 2,560-token chunk, disaggregation looked decisive." / "Measured against replicas at a tuned chunk, the result reverses."가 논문의 뼈대를 이룬다. RQ3 답 "In our measurements, only when the chunk could not be reduced."도 좋다. 2차의 [필수] 다섯 항목 가운데 셋은 반영됐고, 둘(그림 속 요청률, 초록 한정어)은 부분 반영이다.

결론이 두 번 바뀐 흔적은 대부분 지워졌다. 그래도 세 곳이 남아 있다.
1. 그림 A9 제목 "replicas hold only with a fast GPU and light weights"와 §4.8 "Other GPUs … behaved as in the main results"는 새 결론과 어긋난다. §4.2는 같은 g7e에서 FP8을 청크 512·1,024로 살려 냈다.
2. 그림 3은 반복 평균을 선으로 잇는다. 그래서 판정 규칙(모든 반복 ≥0.9)으로는 통과하지 못한 결정적 점 세 개(26B 1P1D aiohttp GPU당 4, 8,192 청크 GPU당 4, 31B 1P1D 시험 프록시 GPU당 4)가 0.9선 위에 그려진다.
3. 결론과 RQ3에 "always … the first token later", "can be estimated before deployment", "is also what chunked prefill provides"가 한정어 없이 남아 있다.

새로 생긴 문제도 있다. 부록 E의 표 번호가 F1이고 부록 F의 표 번호가 G1이다. 표 2는 31B 1P1D "4"에 borderline 표시가 없고 어느 프록시의 값인지도 적지 않았다. 그림 5 부제의 전체 요청률은 2차 [필수]였는데 그대로다. 모두 원고와 그림 라벨만 고치면 된다.

## 2차 지적 반영 점검

| 2차 항목 | 판정 | 근거 |
|---|---|---|
| [필수 1] 그림 속 전체 요청률 | 부분 반영 | 부록 A 머리말에 "Rates printed inside them are totals for two GPUs unless the axis says per GPU"를 넣었고, A3·A7 캡션에도 밝혔다. 부록은 이것으로 충분하다. 그러나 본문 그림 5 부제 "4K input at low load (0.5 and 0.25 requests/s)"는 그대로다. 캡션은 GPU당 0.25와 0.125이고, 부록 머리말 고지는 본문 그림에 적용되지 않는다. |
| [필수 1] 그림 A7 제목 | 반영 | "Disagreement between repeats flips the verdict only near 0.9 (shaded 0.85–0.95)"로 고쳤다. 다만 제목이 길어져 그림 폭이 633pt가 됐고, 행 라벨이 인쇄 4.4pt로 v1(5.1pt)보다 작아졌다. |
| [필수 2] 초록 한정어와 길이 | 대부분 반영 | 201단어·8문장이다. "bounds", 청크 2,560의 제약("near the minimum vLLM allows Gemma 4 with video enabled"), 제목에 대한 답, 전송 연결 문장 삭제가 모두 반영됐다. 남은 것: 3×에 워크로드가 없다(26B 4K에만 해당). "never served more under any SLO we tested"는 판정하지 못한 칸까지 덮는다. "down to 30 ms"는 무엇의 30 ms인지 없다. "held"가 두 문장에서 다른 뜻으로 쓰인다. 문두의 "Its"가 가리키는 대상이 흐리다. |
| [필수 3] §4.4 "similar at 75 ms" | 반영 | 그림 4와 본문을 새로 썼다. 아래 행에 주황 칸이 없고, 본문도 "no cell favors disaggregation"이다. |
| [필수 3] 표 1 캡션 "All main-text results come from g7e" | 반영 | "Used for" 열에 g7의 용도를 적었다. g7 가격 "–"의 이유는 여전히 없다(사소). |
| [필수 3] §3.1 "one of them … accounts for the whole gain" | 부분 반영 | "the TCP segment size accounts for the gain"으로 바뀌었다. §4.5는 송·수신 두 변수라고 쓰므로 복수로 맞춘다. |
| [필수 3] 단위 | 대부분 반영 | 환산식이 "Gbps = 0.008389 × MiB/s"로 맞게 고쳐졌고, §4.5도 MiB가 됐다. §3.2 "28–30 MB" 하나가 남았다. |
| [필수 3] 표 2 31B 1P1D "≥4" | 해소, 새 문제 | GPU당 6에서 측정해(0.765) 4가 실제 한계가 됐다. 그런데 0.903이 포함된 점인데 borderline 표시가 없다. 시험 프록시로는 4에서 탈락(0.885)이라는 사실도 표에 없다(주요 약점 4). |
| [필수 3] 95% 구간 약속 | 반영 | 부록 E 표(현 F1)로 해결했다. 표 번호와 빠진 행은 아래에 적었다. |
| [필수 3] borderline 수치 정의 | 부분 반영 | A7 캡션에는 0.85–0.95가 있다. 정의를 두는 §3.6은 여전히 "points near 0.9"다. |
| [필수 3] 31B 200–400토큰 구간 | 반영 | "43% with 200–400 tokens"가 들어갔다. |
| [필수 4] RQ1 "almost in proportion", 체크리스트 1 "It equals" | 반영 | "roughly the time of a step carrying a full chunk", "approaches … with chat it follows"로 고쳤다. |
| [필수 4] RQ3 "as a default Gemma 4 deployment is" | 반영 | "near the minimum vLLM imposes on Gemma 4 with video input enabled"로 고쳤다. |
| [필수 4] 결론 "exactly what chunked prefill provides by other means" | 부분 반영 | "is also what chunked prefill provides"로 약해졌지만 여전히 동등하다는 뜻으로 읽힌다. "청크 크기만큼"이라는 한정과 디코드 노드의 두 배 배치(§4.3)가 빠졌다. |
| [필수 5] 부록 그림 9개와 부록 B 미참조 | 반영 | A1은 §4.6에서, A2–A9와 부록 B는 §4.8에서 참조된다. 다만 A9를 잇는 문장 "behaved as in the main results"가 틀린 인상을 준다(주요 약점 2). |
| `--limit-mm-per-prompt` 렌더링 | 반영 | pdftotext로 "--limit-mm-per-prompt"를 확인했다. |
| 표 E1(현 G1) 간격 | 반영 | 마지막 열을 ragged-right로 바꿨다. "26B FP8, 31B FP8"(31B FP8은 본문에 없음)과 정의 없는 "KV matching"은 남았다. |
| [권장 6] Results 순서와 RQ 번호 | 미반영 | 여전히 RQ1(§4.2) → RQ3(§4.3–4.4) → RQ2(§4.5–4.6)다. "In short" 문단과 §5.1은 RQ 순서(1, 2, 3)라서 본문 순서와 어긋난다. |
| [권장 7] 도입부 결과 미리보기 | 반영 | "In short: …" 문단이 들어갔다. |
| [권장 8] 용어 통일 | 부분 반영 | "reference proxy"(기여 3), "tuned colocation"(RQ3), "stall limits"(기여 1), "budget"(본문 2곳, 그림 1·A1), "max gap"(그림 2·4), "Rep ×2"(A6)가 남았다. SLO는 34번 쓰지만 한 번도 풀어 쓰지 않았다. |
| [권장 9] 그림 가독성 | 부분 반영 | 그림 7에서 GC와 겹친 스파이크가 보이게 됐다. 그림 3(b)의 가림, 그림 5(b) x 라벨 충돌, A4·A5·A9 범례 겹침은 그대로이고, A7은 더 작아졌다. |
| [권장 10] 참고문헌·형식 | 부분 반영 | [1] SARATHI 추가, 부록 A 제목 단축은 반영됐다. [2] "Amey Agrawal et al."(쪽 누락), [16] TaiChi 이름 없음, [26] "2026. Published June 23.", 접근일 불균형, Acknowledgments는 그대로다. |

## 강점

- 초록이 질문, 방법, 기제, 두 기준선의 결과, 전송 비용, 권고를 201단어에 담았다. 1차의 모순과 2차의 과잉 세부(연결 수, 1.5–1.8×)가 사라졌다.
- 도입부의 모의 심사 서술이 짧고 정직하다. 두 가지 불리함(청크, 연결 상한)을 구체적으로 적고, E9 예측을 먼저 커밋했다고 밝힌다. 부록 D는 다섯 예측 중 빗나간 하나(8,192 청크)까지 수치로 적었다. 프리프린트 독자에게 신뢰를 주는 처리다.
- §4.3의 평행 주제문 두 개와 RQ3의 첫 문장 "only when the chunk could not be reduced"는 논문 전체를 한 번에 요약한다.
- §4.7 "A connection limit in the replicas' proxy" 문단은 증거 제시의 모범이다. 33 of 33, 393 of 393, 상한 해제 뒤 1.000과 0.999–1.000, 그리고 한 문장 결론("lowered … by one step and inflated their TTFT tail")으로 끝난다.
- 그림 4의 두 행 구성이 새 결론을 그림 한 장으로 보여 준다. 위 행은 주황, 아래 행은 파랑뿐이다. 녹색약 독자에게도 명도 차이로 읽힌다.
- §4.2는 청크 512를 넣어 "24 µs per token"과 "shrank more slowly toward the decode-only step"으로 관계를 정량화했다. 1.6 ms 여유("hinged on a small margin")를 스스로 짚은 것도 좋다.
- §5.3 EFA 문단이 "the comparison would change more than the network"로 교란을 정확히 짚는다.
- 부록 그림이 모두 본문에 연결됐고, 부록 A 머리말이 "2,560-token replicas"와 전체 요청률을 한 번에 고지한다.

## 주요 약점

1. **[필수] 그림 3: 선(반복 평균)과 판정(모든 반복 ≥0.9)이 결정적 점에서 어긋난다**
   - 캡션은 "Lines connect the mean of repeats"라고 밝힌다. 그런데 이 그림에서 가장 중요한 x = 4의 점 세 개가 평균으로는 0.9선 위에 있고, 판정으로는 통과하지 못했다.
     - (a) 1P1D aiohttp: 평균 0.944, 최소 0.885 (본문: "borderline at 4")
     - (a) 1P1D, 프리필 청크 8,192: 평균 0.925, 최소 0.874 (부록 D: 예측 실패)
     - (c) 1P1D 시험 프록시: 평균 0.935, 최소 0.885 (본문: 시험 프록시로는 통과 못 함)
   - (a) x = 4에는 네 계열이 겹쳐 aiohttp의 min–max 막대(0.885–0.992)가 보이지 않는다. 독자는 그림에서 "1P1D가 4를 통과했다"고 읽는다.
   - 판정에서 탈락한 점은 속 빈 마커나 ×로 그리고, 캡션에 "hollow: some repeat below 0.9"를 넣는다. 또는 선을 반복의 최솟값으로 잇는다. x를 조금씩 어긋나게(dodge) 두어 막대가 보이게 한다.
   - (b) 26B FP8은 세 계열(청크 512, 1,024, 1P1D 시험 프록시)이 모두 1.0에 겹쳐 주황 사각형 하나만 보인다. 본문의 "512- and 1,024-token replicas and 1P1D all passed"가 그림에서 확인되지 않는다. dodge를 하거나 "all three at 1.00"을 패널에 적는다.

2. **[필수] 새 결론과 어긋나는 잔존 문장: 그림 A9와 §4.8**
   - A9 제목 "4K input at 1 req/s: replicas hold only with a fast GPU and light weights"는 2,560 복제본에만 해당한다. §4.2와 §4.3은 같은 g7e에서 26B FP8이 청크 512·1,024로 통과한다고 쓴다(0.99, 1.00). 제목은 그림만 보는 독자에게 "분리가 이기는 GPU가 있다"는 옛 결론을 전한다. 네 막대가 GPU, 정밀도, 튜닝 여부, 배치 그룹을 한꺼번에 바꾼다는 문제(2차 지적)도 그대로다.
   - §4.8 "Other GPUs and push transfer (Appendix Figures A9 and A8) behaved as in the main results"는 어느 "main results"인지 모호하다. A9가 보여 주는 것은 2,560 복제본 대비 결과(그림 4 위 행)이지 조정한 청크 대비 결과(아래 행)가 아니다.
   - 권고: A9 제목을 "4K input, 2,560-token replicas only"처럼 조건만 적고(1P1D도 g7과 g6e에서는 0.84, 0.83으로 0.9에 못 미쳤다), §4.8은 교정 제안 26번처럼 쓴다. A9를 빼는 것도 방법이다.
   - 같은 이유로 부록 그림 A2, A3, A9의 범례 "Replicas (2)"를 "Replicas (2), chunk 2,560"으로 바꾸기를 권한다. 부록 머리말을 읽지 않고 그림만 보는 독자가 많다.

3. **[필수] 초록·RQ3·결론의 남은 과장과 서로 다른 수치**
   - 초록 "about 3× more requests per GPU than replicas held at 2,560 tokens": 26B 4K에만 해당한다. FP8과 31B 대화에서는 2,560 복제본이 한 점도 통과하지 못했다. "(26B, 4K inputs)"를 넣는다. 도입부 "Disaggregation won by about 3× only when the chunk was held near 2,500 tokens"도 같다. 여기서 "near 2,500"은 "at 2,560"으로 쓴다.
   - 초록 "never served more under any SLO we tested", 도입부 "in every SLO we tested, replicas with a tuned chunk served at least as much", RQ3·결론 "served no more in/under any SLO we tested": 측정한 요청률 안에서는 참이다. 그러나 26B FP8은 TTFT 0.75 s 이상 모든 칸이 "양쪽 모두 최고 측정 부하 통과(판정 불가)"다. 독자는 이 문장을 용량 비교로 읽는다. "no SLO we tested favored disaggregation"으로 쓰고, 본문 한 곳(§4.4)에 "for 26B FP8 both passed our highest load"를 남긴다.
   - RQ3 "always reached the first token later", 결론 "always delivered the first token later": §4.3은 "medians"라고 한정했다. 두 곳에도 "median"을 넣는다.
   - 결론 "a KV transfer that can be estimated before deployment": §4.6이 "Eq. (2) is a low-load estimate, and m falls with load"라고 하고, 사전 추정 오차가 14%였다. "roughly estimated at low load"로 쓴다(2차 과장 목록 그대로).
   - 결론 "Its benefit … is also what chunked prefill provides": "to a degree set by the chunk size"를 붙이고, §4.3의 구조적 비용(디코드 노드 하나가 두 GPU 몫을 싣는다)을 한 구절로 넣는다(교정 제안 29번).
   - RQ1 "at a TTFT cost of about 70 ms and without losing supported load down to 1,024 tokens"와 절차 2 "512–1,024 tokens (26B) … cost at most about 80 ms of median TTFT and no supported load"가 다르다. 70과 80 중 하나로 맞추고(어느 조건의 값인지 적는다), 512는 GPU당 4까지만 쟀으므로 "no supported load"에서 뺀다.

4. **[필수] 표 2와 §4.3의 31B 1P1D 서술**
   - 표 2의 1P1D 열은 어느 프록시의 값인지 적지 않았다. 26B의 "3"은 두 프록시 공통이지만, 31B의 "4"는 aiohttp에서만 성립한다. 시험 프록시로는 네 런 중 하나가 0.885라 4에서 탈락이다.
   - 31B 1P1D GPU당 4는 0.903을 포함한다. §3.6의 정의("points near 0.9 varied by up to ±0.10 … we call them borderline")대로면 borderline이다. 26B에는 "(borderline at 4)"를 붙이고 31B에는 붙이지 않은 것은 비대칭이다. 게다가 이 통과는 E8 뒤에 채택한 1토큰 규칙(§3.5)에 기댄다.
   - §4.3 "1P1D passed 4 (0.903, 0.924, and 1.000 in three runs with our aiohttp proxy; 0.885–0.963 in four runs with the test proxy)"는 두 프록시 모두 통과한 것처럼 읽힌다(교정 제안 19번).
   - 표 2의 26B FP8 행에는 캡션이 약속한 median TTFT가 없다. "none"에는 측정 범위가 없다(예: "none (0.5–1)"). 첫 셀에만 "req/s"가 붙어 있다.
   - 권고: 1P1D 열 머리를 "1P1D (aiohttp proxy)"로 하고, 31B는 "4†"로 쓴 뒤 캡션에 "† borderline (a repeat within 0.85–0.95); with vLLM's test proxy 1P1D failed at 4"를 넣는다.

5. **[필수] 부록 표 번호와 표 F1 캡션**
   - 부록 E "Decisive points"의 표가 "Table F1", 부록 F "Data and code"의 표가 "Table G1"이다. `\renewcommand{\thetable}{F\arabic{table}}`와 `{G…}`를 손으로 넣어서 생긴 한 칸 밀림이다. E1, F1로 고치거나 `\thesection`을 쓴다. 팀장 지시문도 이 번호(F1, G1)를 쓰고 있어 공개 뒤 인용이 어긋날 수 있다.
   - 표 F1 캡션 "Strict-SLO attainment (TTFT ≤1 s)"는 30 ms 행 네 개와 맞지 않는다. "Attainment with TTFT ≤ 1 s and the listed gap limit"으로 쓴다.

6. **[필수(공개 전)] 자리표시자와 "two mock reviews"의 개수**
   - "[contact email]", "[draft v2, 2026-10-01]", "[GitHub URL and Zenodo DOI]"가 주황 글자로 남아 있다.
   - 도입부, 기여 4, Use of AI tools, 부록 F가 모두 "two mock (peer) reviews"라고 쓴다. 이번 3차 심사 기록도 공개 묶음에 넣는다면 개수를 "three rounds"로 바꾸거나 "two mock reviews prompted E8 and E9"처럼 역할로 한정한다.

7. **[권장] 도입부의 모의 심사 서술: 잘 읽히지만 두 틀이 부딪친다**
   - 프리프린트로서 분량과 위치는 적절하다. 결과 미리보기("In short")가 바로 뒤에 와서 독자가 무엇이 바뀌었는지 곧 안다.
   - 다만 틀이 둘이다. 도입부는 청크 2,560 기준선을 "handicapped … its chunk size was untuned"라고 부른다. 초록과 RQ3는 같은 기준선을 "near the minimum vLLM allows Gemma 4 with video enabled", 즉 실제 배포의 제약으로 제시한다. 앞의 틀은 3×를 측정 산물처럼, 뒤의 틀은 정당한 승리처럼 읽히게 한다. 좌장 권고대로 뒤의 틀로 통일한다. "untuned"는 "we had not tried the smaller chunks that disabling every modality allows"로 쓴다.
   - "mock peer reviews"가 누구의 심사인지 도입부만으로는 알 수 없다. Use of AI tools 절이 밝히지만, 도입부 첫 언급에 "AI-assisted"를 넣는 편이 투명하다.
   - "E8 and E9"는 이 시점에 정의되지 않은 세션 이름이다. "(Table G1)"로 연결하거나 이름을 뺀다.
   - "handicapped twice"는 구어적이다. "changed the conclusion"은 "reversed"로 쓰면 무엇이 바뀌었는지가 분명하다.
   - E9 예측은 "committed"로만 쓰고 "pre-registered"라고 부르지 않았다. 원래의 사전 등록 프로토콜과 구분돼 좋다. 그런데 부록 D("Deviations from the pre-registered protocol")의 마지막 항목으로 들어가 있어 이탈 사항처럼 보인다. 다섯 예측과 결과를 작은 표로 따로 두면(예측, 측정값, 적중 여부) 도입부 문장의 신뢰가 커진다.

8. **[권장] Results 순서, RQ 번호, 절 제목**
   - "In short"와 §5.1은 RQ1 → RQ2 → RQ3 순서인데 본문은 RQ1 → RQ3 → RQ2다. §4.4의 "disaggregation's TTFT includes an 80–300 ms transfer"는 아직 나오지 않은 §4.5–4.6에 기댄다.
   - 권고 A(선호): §4.5–4.6(전송, TTFT 비용)을 §4.3 앞으로 옮긴다. 기제(청크 → 전송) 다음에 맞대결과 지도가 온다. 전방 참조가 사라지고, 맞대결이 논문의 절정이 된다.
   - 권고 B(저비용): RQ2와 RQ3의 번호를 바꾸고, "In short"와 §5.1도 그 순서로 쓴다.
   - 절 제목이 주장형(4.1, 4.2, 4.7)과 주제형(4.3–4.6)으로 섞여 있다. 특히 §4.4 "Where each approach wins"는 아래 행에서 분리가 이기는 칸이 없으므로 옛 결론의 흔적처럼 읽힌다. 주장형으로 통일하기를 권한다.
     - 4.3 "Head to head: a tuned chunk reverses the result"
     - 4.4 "No SLO we tested favors disaggregation against a tuned chunk"
     - 4.5 "Segment size, NIXL's splitting, and a shared limit set the transfer rate"
     - 4.6 "The KV transfer is most of disaggregation's TTFT cost"
     - 4.8 "Other observations (before E8, 2,560-token replicas)"
   - §4.3 둘째 문단은 256단어 한 문단에 26B NVFP4, 청크 512, 1P1D 두 프록시, 8,192 청크, 디코드 구조 비용, FP8, 31B, TTFT가 모두 들어 있다. "26B NVFP4" / "why 1P1D's gaps grow (structural)" / "FP8, 31B chat, TTFT" 세 문단으로 나눈다.

9. **[권장] 용어 통일(남은 것)**

   | 개념 | 현재 쓰는 말 | 권고 |
   |---|---|---|
   | 요청별 최대 간격 | 본문 "longest gap"(13회), "longest inter-token gap", "longest token gap"(RQ1). 그림 2 y축 "Per-request max gap", 그림 4 x축 "Max-gap limit"과 범례 "max gap 50 ms" | "longest gap". 그림은 "Longest gap (ms)", "Longest-gap limit (ms)" |
   | 간격 한도 | "gap limit"(10회), "stall limits"(기여 1), "budget"(§4.6 "a 1 s budget", 절차 3 "TTFT budget", 그림 1 "50 ms budget", A1 "TTFT budget 1 s") | "limit" 하나. "multimodal budget check"는 기술 용어라 그대로 둔다 |
   | 전역 정지 | 그림 7 캡션 "Global stalls", §4.7 "events", "paused together", 기여 3 "pauses all streams" | §4.7 첫 문장에서 "global pause"로 정의하고 요청별 "stall"과 구분한다 |
   | 조정한 기준선 | "tuned chunk"(4회), "best measured chunk"(그림 4), "best chunk"(표 2), "smaller chunks"(초록), "256–1,024-token chunk"(RQ3, 결론), "tuned colocation"(RQ3) | §4.3 첫 등장에서 "the best chunk we measured (1,024 or 512 tokens for 26B, 256 for 31B chat)"로 정의하고 "tuned chunk"로 통일 |
   | 시험 프록시 | "reference proxy"(기여 3), "vLLM's test proxy for NIXL", "test proxy"(12회) | "vLLM's test proxy" |
   | SLO | 34회 사용, 풀이 없음 | 초록이나 RQ3 첫 사용에서 "service-level objective (SLO)" |
   | "held" | 초록 "replicas held at 2,560 tokens"(제약)과 바로 다음 문장 "while replicas held 5"(지탱) | 둘째를 "supported 5"로 |
   | 멀티모달 제약 | 초록·RQ3 "with video (input) enabled", §3.3·기여 3·부록 B "unless every modality is disabled / images, audio, and video are all disabled", §3.3 "the budget of one multimodal item" | 시험한 사실에 맞춘다: 2,496은 video 항목 예산, 모든 모달리티를 끄면 통과, 다른 조합은 시험하지 않음(좌장 A10). 교정 제안 12번 |
   | 요청률 | 본문은 GPU당으로 통일됨. 그림 6 "req/s/GPU", 그림 3 "Requests/s per GPU", A4·A5 "Request rate per GPU (req/s)" | 본문 그림은 "Requests/s per GPU"로 맞춘다(사소) |
   | 복제본 표기 | "Replicas (2)", A6 "Rep ×2/×3", A7 "single node, KV matched" | "Replicas (2)/(3)". "KV matched"는 §3.1 첫 등장에서 정의한다 |
   | 숫자 형식 | 본문 "2,560", 그림 2 눈금·그림 4 행 라벨 "2560" | 그림도 천 단위 쉼표 |
   | 부피 | §3.2 "28–30 MB" | "MiB" |

10. **[권장] §4.7 GC 문단의 내용과 제목**
    - 절 제목은 "Pitfalls: proxies that change the verdict"인데, GC 문단은 판정이 어떻게 바뀌었는지 말하지 않는다. 연결 상한 문단은 "lowered the replicas' supported load by one step"으로 답한다. GC 쪽에도 "Removing only the proxy pauses raises the test-proxy runs from 0.77–0.98 to 0.88–0.99; no verdict at 4 changes"처럼 한 문장이 필요하다(좌장 A5 문안). 아니면 제목을 "proxies that distort the measurement"로 바꾼다.
    - 첫 문장 "… paused together for 55–80 ms and then received a burst of tokens"는 모든 사건에 몰림이 있다고 말한다. 같은 문단 뒤쪽의 서버형 사건(113, 110, 316건)에는 몰림이 없었다(좌장 A5). 몰림은 GC형에만 붙인다.
    - "so it is a server-side pause tied to the request sequence"는 같은 시드 두 런의 한 사례에서 나온 추론이다. "most likely"를 붙인다.

11. **[권장] 그림 가독성**(그림·표별 지적 참조): A7 행 라벨 4.4pt, A3 막대 값 5.0pt, A6 x 라벨 5.4pt, 그림 7 GC 라벨 5.6pt, 그림 6 주석 5.8pt. 그림 5(b) x 라벨 충돌, A4·A5·A9 범례 겹침. 그림 3이 8쪽을 혼자 차지하고 위아래 약 60%가 빈다(`[!htbp]`와 `placeins` 조합). 그림 3을 표 2보다 먼저 두거나 `[t]`로 두면 7–8쪽이 붙는다.

12. **[권장] 참고문헌과 형식**: [2] Sarathi-Serve의 저자 절단과 쪽 누락, [16]에 "TaiChi" 표기 없음(본문은 "TaiChi … [16]"), [26] "2026. Published June 23.", 접근일은 [6][7][8]에만 있다. Acknowledgments는 감사 대상 없이 비용만 적었으니 "Funding"으로 바꾼다. 부록 D "One-token outputs pass the gap criterion since session E8"은 시제가 어색하다(교정 제안 30번).

### "Tune the chunk first."에 대하여

제목의 질문에 세 단어로 답한다는 점에서 좋은 마무리다. 다만 이 문장만 남기면 초록만 읽는 독자는 "TCP 분리는 쓰지 말라"로 읽는다. 논문 자신은 RQ3에서 "Disaggregation might still win where no acceptable chunk meets the gap limit"라고 여지를 남겼고, 결론도 "disaggregate over TCP when the chunk cannot be made small enough"로 끝난다. 초록도 조건절 하나를 붙이기를 권한다: "Tune the chunk first; disaggregate only when no workable chunk meets the gap limit." (+10단어)

아래는 위 지적을 모두 반영한 초록안이다(216단어). 200단어 안팎을 지키려면 "(PD)"를 빼고 "its longest gap between output tokens"를 "its longest inter-token gap"으로 줄인다(212단어). 수치는 본문과 대조했지만 저자가 다시 확인해야 한다.

> Prefill–decode (PD) disaggregation usually relies on RDMA or NVLink, which the cheapest single-GPU cloud instances lack. We ask when disaggregation over TCP beats colocated replicas that use chunked prefill. On AWS 2xlarge instances we served Gemma 4 26B (mixture of experts) and 31B (dense) with stock vLLM, disaggregated with NIXL/UCX over TCP, and judged each request by its time to first token (TTFT) and its longest gap between output tokens. A replica stalls whenever another request's prefill shares its scheduler step, so the chunk size bounds that gap: for 26B with 4K-token inputs, the median longest gap fell from 48 ms at a 2,560-token chunk to 21 ms at 512. Under a 1 s TTFT and 50 ms gap limit, disaggregation served about 3× more requests per GPU than replicas held at 2,560 tokens (26B, 4K inputs), near the minimum vLLM allows Gemma 4 with video enabled. Against smaller chunks, no SLO we tested favored it, down to a 30 ms gap limit: for 26B it was borderline at 4 requests/s per GPU while replicas supported 5; for 31B chat, 4 against at least 8. Disaggregation's TTFT cost was mostly the KV transfer, which a larger UCX TCP segment made 3.4× faster. Tune the chunk first; disaggregate only when no workable chunk meets the gap limit.

## 문장 교정 제안

| # | 위치 | 원문 | 제안 |
|---|---|---|---|
| 1 | 초록 | for 26B with 4K-token inputs, the median fell from 48 ms at a 2,560-token chunk to 21 ms at 512. | for 26B with 4K-token inputs, the median longest gap fell from 48 ms at a 2,560-token chunk to 21 ms at 512. |
| 2 | 초록 | disaggregation served about 3× more requests per GPU than replicas held at 2,560 tokens, near the minimum vLLM allows Gemma 4 with video enabled. | disaggregation served about 3× more requests per GPU than replicas held at 2,560 tokens (26B, 4K inputs), near the minimum vLLM allows Gemma 4 with video enabled. |
| 3 | 초록 | Against smaller chunks it never served more under any SLO we tested, down to 30 ms: for 26B it was borderline at 4 requests/s per GPU while replicas held 5; | Against smaller chunks, no SLO we tested favored it, down to a 30 ms gap limit: for 26B it was borderline at 4 requests/s per GPU while replicas supported 5; |
| 4 | 초록 | Its TTFT cost was mostly the KV transfer, | Disaggregation's TTFT cost was mostly the KV transfer, |
| 5 | 초록 끝 | Tune the chunk first. | Tune the chunk first; disaggregate only when no workable chunk meets the gap limit. |
| 6 | 1장 3문단 | Our first comparison pitted disaggregation against replicas at the chunk size our stack first accepted. | Our first comparison used replicas at a 2,560-token chunk, the smallest that vLLM accepted for Gemma 4 with multimodal input enabled. |
| 7 | 1장 3문단 | Two mock peer reviews of our drafts found that this baseline was handicapped twice: its chunk size was untuned, and its request proxy capped concurrent connections at 100. | Two AI-assisted mock peer reviews of our drafts found two handicaps in this baseline: we had not tried the smaller chunks that disabling every modality allows, and its request proxy capped concurrent connections at 100. |
| 8 | 1장 3문단 | We added two sessions (E8 and E9) that swept the chunk size and removed the cap, and we committed our predictions for E9 before running it. These sessions changed the conclusion, and we report both baselines. | We added two measurement sessions (E8 and E9; Table G1) that swept the chunk size and removed the cap, and we committed our predictions for E9 to the repository before running it. These sessions reversed our conclusion; we report both baselines. |
| 9 | 1장 In short | and in every SLO we tested, replicas with a tuned chunk served at least as much as disaggregation over TCP. Disaggregation won by about 3× only when the chunk was held near 2,500 tokens. | and no SLO we tested favored disaggregation over TCP against replicas with a tuned chunk. Disaggregation won only when the replicas' chunk was held at 2,560 tokens (by about 3× for 26B with 4K inputs). |
| 10 | RQ3 | when does disaggregation over TCP serve more SLO-meeting load than tuned colocation? | when does disaggregation over TCP serve more load within a service-level objective (SLO) than replicas with a tuned chunk? |
| 11 | 기여 3 | four pitfalls that changed our conclusions: … the reference proxy's garbage collection pauses all streams; and an HTTP client's default connection limit throttled the replicas | four pitfalls that can change a verdict: … garbage collection in vLLM's test proxy paused all streams in our runs; and an HTTP client's default connection limit throttled the replicas' proxy |
| 12 | 3.3 | vLLM rejects chunks smaller than 2,496 tokens, the budget of one multimodal item, even with images disabled; the check passes only when images, audio, and video are all disabled | vLLM rejects chunks smaller than 2,496 tokens, the budget of one video item, even with images disabled; it accepts smaller chunks with every modality disabled, and we did not test other combinations |
| 13 | 3.5 | we adopted this rule after session E8, when it flipped two borderline 31B runs from 0.899 and 0.878 to 0.924 and 0.903, and it raised other chat runs by at most 0.055. | we adopted this rule after session E8; it moved two borderline 31B runs from 0.899 and 0.878 to 0.924 and 0.903 and raised other chat runs by at most 0.055. |
| 14 | 3.6 | points near 0.9 varied by up to ±0.10 and could flip a verdict, and we call them borderline; low points varied more (0.37–0.64). | points near 0.9 varied by up to ±0.10, enough to flip a verdict; we call a point borderline if any repeat falls between 0.85 and 0.95. Points far below 0.9 varied more (0.37–0.64 at one point). |
| 15 | 4.2 | we could not tell whether … or the different multimodal setting of the 2,560 control causes this. | we could not tell whether … or the different multimodal setting of the 2,560 control caused this. |
| 16 | 4.2 | A 512-token chunk therefore did not help (attainment 0.44, the same as 2,560), | A 512-token chunk still lets one step carry a 400–800-token prompt, so it did not help (attainment 0.44, as at 2,560), |
| 17 | 4.3 ¶2 | 1P1D passed 3 and was borderline at 4: 0.885, 0.954, and 0.992 with our aiohttp proxy (interval 0.873–0.992) and 0.77–0.98 with the test proxy; | 1P1D passed 3 and was borderline at 4: one of three runs fell below 0.9 with our aiohttp proxy (0.885, 0.954, 0.992; interval 0.873–0.992), and two of four with the test proxy (0.77–0.98); |
| 18 | 4.3 ¶2 | Part of 1P1D's gap cost is structural: at equal GPU count its decode node carries the decodes of both GPUs' requests, and its median inter-token latency was 15.5 against 13.2 ms at 3 requests/s per GPU and 20.8 against 15.9 ms at 4. | Part of 1P1D's gap cost is structural. At equal GPU count its single decode node carries the decodes that two replicas would share, so its median inter-token latency was higher: 15.5 against 13.2 ms at 3 requests/s per GPU, and 20.8 against 15.9 ms at 4. |
| 19 | 4.3 ¶2 | while 1P1D passed 4 (0.903, 0.924, and 1.000 in three runs with our aiohttp proxy; 0.885–0.963 in four runs with the test proxy) and failed at 6 (0.765). | while 1P1D passed 4 narrowly with our aiohttp proxy (0.903, 0.924, and 1.000) but not with the test proxy (0.885–0.963 in four runs), and failed at 6 (0.765). |
| 20 | 4.4 항목 2 | For 26B FP8, replicas serve more when TTFT must stay under 0.5 s; | For 26B FP8, replicas serve more at TTFT limits of 0.5 s or less; |
| 21 | 4.4 항목 4 | Replicas are the only option when TTFT must stay under 0.25 s, because disaggregation's TTFT includes an 80–300 ms transfer. | At a 0.25 s TTFT limit only replicas meet the SLO, because disaggregation's TTFT includes an 80–300 ms transfer. |
| 22 | 4.5 ¶1 | it fixes the socket buffers at 8 MB, which disables the kernel's buffer autotuning, and the sender was limited by the receive window for about 40% of its busy time. | it fixed the socket buffers at 8 MB, which disabled the kernel's buffer autotuning, and the sender was limited by the receive window for about 40% of its busy time. |
| 23 | 4.5 ¶2 | Socket samples agree (Figure 5c): four connections each carried 22–27% of the bytes and a fifth, shared one carried the rest; a 26B transfer mostly kept two or three connections busy, | Socket samples agree. Four connections each carried 22–27% of the bytes and a fifth, shared one carried the rest; a 26B transfer mostly kept two or three of the four busy (Figure 5c), |
| 24 | 4.5 ¶4 | Other settings did not help. Staging the KV cache through host memory slowed TTFT 4.7× | No other option changed a verdict. Staging the KV cache through host memory raised TTFT 4.7× |
| 25 | 4.6 | it predicted about 1.5 s against a measured 2.19 s, and an added M/D/1 waiting time is consistent with the difference (about 2.2 s). | it predicted about 1.5 s against a measured 2.19 s; adding an M/D/1 waiting time brings the estimate to about 2.2 s. |
| 26 | 4.8 | Other GPUs and push transfer (Appendix Figures A9 and A8) behaved as in the main results; | Against 2,560-token replicas, 1P1D reached 0.83–1.00 on every GPU we tried, while the replicas held only on g7e with NVFP4 (Appendix Figure A9); we did not test smaller chunks on g6e or g7. Push transfer is in Appendix Figure A8; |
| 27 | 4.7 | one to five times per run, 40–110 in-flight requests paused together for 55–80 ms and then received a burst of tokens. | one to five times per run, 40–110 in-flight requests paused together for 55–80 ms. We call these global pauses; after the pauses caused by the proxy, the streams resumed with a burst of tokens. |
| 28 | 5.1 RQ3 | it served no more in any SLO we tested, down to 30 ms, and always reached the first token later. | no SLO we tested, down to a 30 ms gap limit, favored it, and its median first token always came later. |
| 29 | 7장 | its first-token cost is mostly a KV transfer that can be estimated before deployment. Its benefit, keeping other requests' prefills out of the decode steps, is also what chunked prefill provides. | its first-token cost is mostly a KV transfer that can be roughly estimated at low load. Chunked prefill also keeps other requests' prefills from stalling decodes, to a degree set by the chunk size, and at equal GPU count disaggregation pays for its isolation with a decode node that carries twice the decodes. |
| 30 | 부록 D | One-token outputs pass the gap criterion since session E8. | From the analysis after session E8 on, one-token outputs pass the gap criterion (Section 3.5). |

사소한 것 몇 개를 덧붙인다.
- §3.1 "Section 4.5 shows that the TCP segment size accounts for the gain" → "the two TCP segment sizes (send and receive) account for the gain".
- §3.2 "28–30 MB, as the formula predicts" → "28–30 MiB, close to what the formula predicts".
- §4.5 "Three things set the transfer rate: a software default, how NIXL splits a transfer, and the cloud's caps" → "a UCX default, NIXL's splitting rule, and the cloud's bandwidth limits"(병렬 구조).
- §4.5 "31B chat transfers, which are not split, reached 0.81" → "ran at 0.81"("reached"는 최댓값으로 읽힌다).
- §4.6 "It also shows why long inputs fail: … beyond a 1 s budget" → "Eq. (2) also explains why long inputs fail: … past the 1 s limit".
- 한계 "we excluded the 9 runs that reached the cap, but results from earlier sessions still used 2,560-token replicas" → "we excluded the 9 runs that reached the cap. Results from sessions before E8 (Section 4.8) also used 2,560-token replicas."("but"의 논리 연결이 없다.)
- 절차 2 "cost at most about 80 ms of median TTFT and no supported load" → 주요 약점 3의 마지막 항목대로 RQ1과 숫자·범위를 맞춘다.
- RQ1 "and how far does chunked prefill go?" → "and how far can a smaller chunk shorten them?"(2차 제안, 선택).
- 표 1 캡션 "costs in this paper use them" → "we compute costs from them".

## 그림·표별 지적

인쇄 최소 글자: 그림 1 5.5pt(로그 눈금 지수), 2 6.2pt, 3 6.8pt, 4 6.0pt, 5 6.0pt, 6 5.8pt, 7 5.6pt, A1 5.9pt, A2 6.5pt, A3 5.0pt, A4 6.2pt, A5 6.6pt, A6 5.4pt, **A7 4.4pt**, A8 6.7pt, A9 7.2pt. 본문 그림은 6·7을 빼면 6pt 이상이다.

- **그림 2 (v1_chunk_stall, 512 추가)**
  - 청크 512를 넣어 (a)가 2,560부터 512까지 512 간격 등간격 축이 됐다. 관계가 한눈에 보인다. (b)(c)는 여전히 비등간격 범주 축이다(사소).
  - y축 "Per-request max gap (ms)"는 "Per-request longest gap (ms)"로 바꾼다.
  - 캡션에 "The 512-token points come from E9"를 넣는다. (a)의 1,024와 512는 다른 날의 세션이다.
  - 2,048 점이 멀티모달 설정이 다른 대조군과 비교된다는 교란은 본문에만 있다(2차 지적 그대로).
  - 눈금 "2560"에 천 단위 쉼표를 넣는다.
- **그림 3 (v1_head_to_head, 새 계열과 범례)**
  - 평균선과 판정의 어긋남, (b)의 가림은 주요 약점 1에 적었다.
  - 범례가 열 우선으로 채워져 가운데 열에 "Replicas, chunk 512"와 "1P1D, vLLM test proxy"가 섞인다. 첫 행을 복제본 세 계열, 둘째 행을 1P1D 세 계열로 두면 종류별로 읽힌다.
  - "Replicas, chunk 512 (256 for 31B)"(파랑)와 "1P1D, aiohttp, prefill chunk 8,192"(갈색)가 같은 dash-dot 선이다. 둘 다 짙은 색이라 녹색약 독자에게는 마커(속 빈 마름모, 삼각형)만으로 갈린다. 갈색은 짧은 점선으로 바꾸기를 권한다.
  - 캡션은 색만 말하고 선 모양은 말하지 않는다. 본문이 "(Figure 3, dotted lines)"로 2,560을 가리키므로 캡션에 "dotted: 2,560 tokens; solid: 1,024; dash-dot: 512 (256 for 31B)"를 넣는다.
  - (a)의 시험 프록시 선이 GPU당 4에서 6으로 바로 이어진다. 5를 재지 않았다면 캡션에 적거나 점선 구간으로 표시한다.
  - 그림이 8쪽을 혼자 차지한다(주요 약점 11).
- **그림 4 (v1_who_wins, 아래 행 주황 없음)**
  - 아래 행에 주황이 없어 "no cell favors disaggregation"이 그림에서 바로 읽힌다. 가장 좋은 그림이다.
  - 범례의 "Similar (0.8–1.25×)"는 이제 어느 칸에도 쓰이지 않는다(figures.json의 칸 분류와 삽입 이미지의 색을 모두 확인했다). 빼거나 캡션에 "no cell was similar"라고 적는다. 부록 D의 "Figure 4 uses 0.8–1.25"도 그에 맞춘다.
  - 아래 왼쪽(26B NVFP4) 패널의 (TTFT 0.75 s, 40 ms) 칸 하나만 빗금이다. 더 느슨한 (1 s, 40 ms)와 더 빡빡한 (0.5 s, 40 ms)는 모두 "replicas serve more"다. 규칙상 가능한 경우라도 독자는 오류로 본다. 이유를 캡션에 한 줄 적거나 계산을 확인한다.
  - 캡션에 비율의 방향이 없다(범례의 "≥1.25×", "≤0.8×"가 분리 ÷ 복제본이라는 것은 추측해야 한다). "Ratios are disaggregated ÷ replicas SLO goodput"을 넣는다.
  - 굵은 테두리 칸에 비율을 적으면(위 왼쪽 3×, 아래 왼쪽 0.6×) 초록의 "about 3×"와 "borderline at 4 … replicas supported 5"가 그림에서 바로 읽힌다(2차 권장 그대로).
  - x축 "Max-gap limit (ms)", 범례 "TTFT 1 s, max gap 50 ms", 행 라벨 "Replicas at chunk 2560"은 "Longest-gap limit (ms)", "Strict SLO (1 s, 50 ms)", "Replicas at chunk 2,560"으로 바꾼다.
  - "Neither meets the SLO"(거의 흰색)와 빗금 칸의 바탕색이 같다. 빗금이 있어 구분은 되지만, 인쇄에서 흰 칸이 비어 있는 칸처럼 보인다. 옅은 점무늬를 권한다.
  - §4.4 31B 항목은 40–50 ms만 말하지만, 그림에서는 TTFT 0.5 s에서 75–300 ms, 0.75 s에서 75–100 ms 칸도 "replicas serve more"다. "and at longer gap limits when TTFT must stay within 0.5–0.75 s"를 넣는다.
- **그림 5 (v1_transfer)**
  - 부제 "(0.5 and 0.25 requests/s)"는 전체 요청률이다(2차 [필수], 미반영). "(0.25 and 0.125 requests/s per GPU)"로 고친다. (a)는 iperf라 "low load"가 해당하지 않으니 "(b, c) at low load"로 쓴다.
  - (b) x 라벨 "Segment 256 KB only"와 "Seven UCX variables"가 붙어 "256 KB onlyvariables"로 읽힌다(2차 지적 그대로). "Default / Segments 256 KB / All seven"처럼 줄인다.
  - 캡션 "bars are medians" → "black lines are medians"(2차 지적 그대로).
  - (b)의 "Seven UCX variables" 중앙값 14.2는 21개 창의 값으로, 두 런 가운데 14.16 런으로 보인다(figures.json). 본문은 두 런 "13.5–14.2 Gbps"를 말한다. 어느 런을 그렸는지 캡션에 적는다.
  - (c) 제목 "Four connections per P–D pair"는 본문의 "four connections … and a fifth, shared one"과 어긋난다. x축은 넷까지만 센다. "(c) Busy connections during a transfer"로 바꾸고, 캡션에 "the shared fifth connection is not counted"와 표본 간격(약 0.12 s)이 26B 전송(약 80 ms)보다 길다는 점을 적는다(좌장 A7).
  - (c)의 색이 파랑 = 26B, 주황 = 31B다. 논문 전체의 의미 체계(파랑 = 복제본, 주황 = 분리)와 충돌한다. 둘 다 분리 구성의 전송이므로 주황 두 명도, 또는 회색·주황에 빗금으로 구분한다.
- **그림 6 (v1_ttft)**
  - 주석 "(transfer 85% of added)" → "(transfer: 85% of added TTFT)". 본문도 FP8에만 "(x of y ms)"가 없다.
  - 모형 추정 눈금이 두 행에만 있다. 캡션에 "no prior estimate for 26B FP8"를 넣는다.
  - 행 순서(FP8, NVFP4, 31B)가 본문 서술 순서(NVFP4, 31B, FP8)와 다르다.
  - 주석 글자가 5.8pt다.
- **그림 7 (v1_proxy_gc)**
  - GC와 겹친 두 스파이크(약 90 s, 162 s)가 이제 보인다. 2차 지적이 반영됐다.
  - 13 s의 GC(36 ms)에는 정지가 없다. 독자는 "GC가 항상 정지를 부르지는 않는가"를 묻게 된다. 이유(예: 부하가 쌓이기 전)를 캡션에 한 구절 적는다.
  - 107 s 사건이 두 런에 같은 시각에 나온다는 것이 서버형 정지의 근거인데, 캡션에 없다. "The pause at 107 s appears in both runs (server-side)"를 넣는다.
  - 캡션 "Global stalls" → "Global pauses"(용어 표), "within the same 5 ms" → "in the same 5 ms bin".
  - GC 라벨이 5.6pt다. 회색 부제가 캡션을 되풀이한다.
- **그림 A1 (fig02)**: "TTFT budget 1 s" → "TTFT limit 1 s". x축 1, 2, 3, 5, no limit이 등간격인데 선으로 이어 기울기가 왜곡된다(2차 지적 그대로).
- **그림 A2 (fig05)**: 범례 "Replicas (2)"에 "chunk 2,560"을 넣는다.
- **그림 A3 (fig10)**: 막대 값 5.0pt, "1.00 1.00 / 1.00 0.98"이 붙어 있다. 범례에 "chunk 2,560"을 넣는다.
- **그림 A4 (fig08)**
  - (a) x = 2의 min–max 막대가 범례 "Replicas (2)" 글자를 관통한다(2차 그대로). 범례를 오른쪽 위로 옮긴다.
  - (b) 주석 "hollow marker: client-limited, not used for verdicts"를 2P1D의 속 빈 마름모가 가린다(2차 그대로).
  - (b) 복제본 GPU당 16의 속 빈 점은 이제 §3.3·§3.6이 말하는 연결 상한 런이다(좌장 1.1(e)). "client-limited"는 부정확하다. "caution run (client or proxy limit)"으로 쓴다. 캡션 "hollow markers are client-limited"도 같다.
- **그림 A5 (fig09)**: (b) 0.9 점선이 범례 "Replicas (3)"을 관통하고, Replicas (3)이 Replicas (2) 뒤에 가려진다(2차 그대로).
- **그림 A6 (fig11)**: "Rep ×2/×3" → "Replicas (2)/(3)". x 라벨 5.4pt. §4.8 "(4 and 5.9 requests/s in total)"은 2P1D의 5.8/s를 빠뜨렸다. "4–5.9"로 쓴다.
- **그림 A7 (fig13)**
  - 제목은 고쳐졌다. 대신 제목이 길어져 그림 폭이 633pt가 됐고, 0.85 폭으로 줄이면 행 라벨이 4.4pt다. 인쇄하면 읽을 수 없다. 제목을 캡션으로 옮기거나 두 줄로 나누고, `width=\linewidth`로 넣는다.
  - "KV matched"는 정의가 없다(용어 표).
- **그림 A8 (fig14)**: 부제 "push trims the median, not the SLO" → "not attainment"(2차 그대로).
- **그림 A9 (fig06)**: 제목은 주요 약점 2. 범례 "1P1D"가 "0.84" 라벨에 닿는다(2차 그대로).

- **표 2**
  - 1P1D 열의 프록시, 31B 1P1D borderline, FP8 행의 TTFT 누락, "none"의 범위는 주요 약점 4에 적었다.
  - 한 칸에 부하, 원가, TTFT를 쉼표로 넣어 "5 (1,024), \$0.38, 259–278 ms"가 두 줄로 꺾인다. 세 소열(Load, \$/M tok, TTFT)로 나누거나, 캡션 첫 줄에 "Each cell: supported load (chunk), cost, median TTFT"를 적는다.
  - 첫 열 머리 "Workload"에 정밀도가 섞여 있다. "Model, workload"로 쓴다.
  - 첫 셀에만 "req/s"가 붙어 있다. 빼거나 모든 칸에 붙인다.
- **표 F1 (부록 E)**
  - 번호와 캡션은 주요 약점 5.
  - 마지막 열 "attainment (each run), 95% interval"은 런 값과 구간을 세미콜론으로 이어 한눈에 갈리지 않는다. "Attainment per run"과 "95% interval" 두 열로 나눈다. "per GPU" 열 머리는 "Rate (req/s per GPU)"로 쓴다.
  - 행 이름 "26B 4K"와 "26B FP8 4K"가 섞였다. "26B NVFP4, 4K"로 쓴다.
  - 결정적인데 빠진 점이 있다.
    - 초록의 "about 3×"를 받치는 청크 2,560 복제본 GPU당 1(다섯 런, 0.933–0.958)과 2, 그리고 1P1D GPU당 3.
    - §4.4 "512-token replicas passed 3 requests/s per GPU and 1P1D passed 2" at 30 ms의 판정점인 청크 512 GPU당 3과 1P1D GPU당 3(30 ms). 표에는 GPU당 2만 있다.
  - 한 런짜리 행(구간이 런 안의 시간 블록에서만 나온다)을 캡션이나 표시로 구분한다(좌장 A11).
  - 26B aiohttp 행의 값 순서(0.954, 0.992, 0.885)와 본문 순서(0.885, 0.954, 0.992)가 다르다. 시드 순서라면 캡션에 적는다.
- **표 G1 (부록 F)**
  - 간격 문제는 해결됐다.
  - E1의 "26B FP8, 31B FP8"은 31B FP8이 본문에 없어 중의적이다(2차 그대로). "KV matching"은 정의가 없다.
  - 표 번호는 주요 약점 5.

## 과장 표현

- 초록 "about 3× more requests per GPU than replicas held at 2,560 tokens", 도입부 "Disaggregation won by about 3×": 26B NVFP4 4K에만 해당한다. 도입부의 "near 2,500 tokens"는 "at 2,560"이다.
- 초록 "never served more under any SLO we tested", 도입부 "in every SLO we tested … served at least as much", RQ3·결론 "served no more in/under any SLO we tested": 26B FP8의 대부분 칸은 판정 불가다. "no SLO we tested favored disaggregation"이 정확하다.
- RQ3 "always reached the first token later", 결론 "always delivered the first token later": 중앙값 기준이다.
- 결론 "can be estimated before deployment": 저부하 근사이고, 사전 추정 오차가 14%였다.
- 결론 "is also what chunked prefill provides": 청크 크기만큼만 제공하고, 30 ms 이하는 측정하지 못했다.
- 기여 3 "the reference proxy's garbage collection pauses all streams", 부록 B "vLLM's test proxy for NIXL pauses all streams during garbage collection": 26B, 세션 E8, 다섯 사건 중 넷에서 관찰한 것이다. "in our runs"나 "in vLLM v0.30.0"을 붙인다.
- 기여 3 "four pitfalls that changed our conclusions": GC 함정이 어떤 결론을 바꿨는지 본문에 없다. "that can change a verdict"로 쓴다.
- §3.3 "the check passes only when images, audio, and video are all disabled": 세 조합만 시험했다(좌장 A10).
- §4.7 "and then received a burst of tokens": GC형 사건에만 해당한다.
- §4.7 "so it is a server-side pause tied to the request sequence": 한 쌍의 런에서 나온 추론이다. "most likely".
- §4.7 제목 "proxies that change the verdict": GC 쪽은 판정 변화가 제시되지 않았다.
- §4.2 "A 512-token chunk therefore did not help": "therefore"가 앞 문장에서 바로 따라 나오지 않는다. 기제를 한 구절 넣는다.
- §4.4 제목 "Where each approach wins": 조정한 청크 대비로는 분리가 이기는 칸이 없다.
- 절차 2 "512–1,024 tokens (26B) … cost … no supported load": 512는 GPU당 4까지만 쟀다.
- §4.8 "behaved as in the main results": A9는 2,560 복제본 대비 결과다.
- 그림 A9 제목 "replicas hold only with a fast GPU and light weights": §4.2의 FP8 결과와 모순되고, 네 변수가 함께 바뀐 비교다.
- 그림 5(c) 제목 "Four connections per P–D pair": 다섯째 공유 연결이 있고, 26B는 주로 둘이나 셋이 동시에 움직였다.
- 그림 A8 부제 "not the SLO": "not attainment".

## 점수·확신도

- 표현(presentation): **4/5** (2차 4/5). 초록과 도입부, §4.3의 서술은 4.5 수준이다. 이야기가 한 줄로 서고, 모의 심사와 사전 커밋 예측을 다루는 방식이 프리프린트로서 모범적이다. 점수를 묶어 두는 것은 [필수] 1–6이다: 그림 3의 평균선과 판정의 어긋남, 옛 결론이 남은 A9와 §4.8, 초록·결론의 한정어, 표 2의 31B 1P1D, 부록 표 번호, 자리표시자. 모두 원고, 그림 라벨, 캡션 작업이고 새 측정은 필요 없다. 고치면 4.5다.
- 확신도: **4/5**. main.tex 전문과 PDF 25쪽을 모두 읽었다. 본문 그림 6개와 A4, A9는 220 dpi로 렌더링해 확인했고, 모든 SVG의 텍스트와 글자 크기를 추출해 용어와 요청률 표기를 대조했다. 그림 4의 칸 분류("Similar" 미사용, 빗금 칸 하나)는 figures.json과 삽입 이미지의 픽셀 색으로 확인했다. 그림 3 평균값은 figures.json의 반복값에서 계산했다. `--` 렌더링은 pdftotext로 확인했다. 원자료(per-request 데이터)로 수치를 다시 계산하지는 않았다. 특히 RQ1의 70 ms와 절차 2의 80 ms 중 어느 쪽이 맞는지, (0.75 s, 40 ms) 빗금 칸이 규칙상 옳은지는 저자가 확인해야 한다.
