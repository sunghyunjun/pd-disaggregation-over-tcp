*한국어판. `README.md`가 영어판입니다.*

# configs

각 측정 회차를 구동한 플래그 묶음과 스크립트. 스크립트는 당시 저장소 루트에서 실행한 모습 그대로 둡니다. 스크립트 안의 경로(`configs/lib_E9.sh`, `configs/setup_E8.sh`, `harness/serve.sh` 등)는 회차 당시의 평평한 배치(모든 파일이 `configs/` 바로 아래)를 가리키고, 호스트 변수(`A_PRIV`, `B_PRIV`, `C_PRIV`, `E_PRIV`, `G_PRIV`)는 이미 사라진 노드를 가리킵니다. 따라서 회차 스크립트는 무엇이 실행됐는지의 기록이며, 한 번에 돌리는 실행기가 아닙니다. 한국어 주석과 로그 문구는 뒤에 영어로 옮겼고, 명령·플래그·경로·숫자·줄 순서는 하나도 바꾸지 않았습니다. 명령의 일부인 한국어(`run_E3.sh`의 grep 패턴, `run_D_xfer.sh`의 노브 라벨)는 그대로 두었습니다. 번역의 예외는 E9 회차의 스크립트 두 개로, 바이트 단위로 그대로 두었습니다(마지막 절 참고).

```
configs/
├── README.md, README.ko.md
├── common/     회차들이 공유한 플래그 묶음과 참고 시트(각 .md는 .ko.md 한국어 원본이 있음)
└── rounds/     측정 회차별 폴더: 실행 스크립트, 그리고 P·A′·A·E8은 런북
    ├── P/  Aprime/  A/  B/  C1/  D/
    └── E1/ E2/ E3/ E4/ E5/ E6/ E7/ E8/ E9/
```

## common/

| 파일 | 내용 |
|---|---|
| `b1.env` | 단일 인스턴스 플래그 묶음(B1. B2의 각 복제본도 동일). `MODEL`(기본 `Qwen/Qwen3-8B`), `CHUNK`(기본 2048), `VLLM_FLAGS`를 설정: `--dtype bfloat16 --max-model-len 32768 --gpu-memory-utilization 0.90 --max-num-batched-tokens ${CHUNK} --max-num-seqs 256 --seed 0 --disable-log-requests --port ${PORT:-8000}`. 접두어 캐시는 ShareGPT와 트레이스에서는 켜고, 랜덤 스윕에서는 끕니다(`--no-enable-prefix-caching`). |
| `p1_prefill.env` | `b1.env`를 source 한 뒤 1P1D의 프리필 쪽을 더합니다: `VLLM_NIXL_SIDE_CHANNEL_HOST=${OWN_IP}`(이 노드의 사설 IP), `VLLM_NIXL_SIDE_CHANNEL_PORT=5600`, `UCX_TLS=tcp,cuda_copy,cuda_ipc`, `UCX_NET_DEVICES=all`, `--kv-transfer-config '{"kv_connector":"NixlConnector","kv_role":"kv_producer"}'`. `UCX_TLS` 값은 P 회차에서 나왔습니다. `tcp`만 주면 UCX가 VRAM을 호스트 메모리로 오인해 `registerMem`이 실패했습니다. |
| `p1_decode.env` | `p1_prefill.env`와 같고 `kv_role`만 `kv_consumer`. |
| `models.md` | 모델 후보 매트릭스: 토큰당 KV KB, 가중치 크기, 32K 요청 하나의 KV, 공식 양자화, GPU별 정밀도 지원, 어디에 무엇이 들어가는지, 인스턴스별 테스트 매트릭스. |
| `proxy.md` | 프록시 명령: 1P1D용 vLLM 테스트 프록시(toy proxy), B2용 `harness/rr_proxy.py` 라운드로빈, 프록시 오버헤드 5% 검증 절차. |
| `tc.md` | 송신 측 `tc qdisc ... tbf`로 대역폭을 등화·스윕하는 방법, iperf3로 확인하는 방법, 해제하는 방법. |

뒤쪽 회차(D 이후)는 이 `.env` 파일을 직접 source 하지 않습니다. 실행 스크립트가 같은 플래그를 `harness/serve.sh`에 `CHUNK`, `PREFIX`, `GPU_UTIL`, `CONNECTOR`, `OWN_IP`, `UCX_EXTRA`로 넘깁니다.

## rounds/

| 회차 | 날짜(UTC) | 인스턴스 | 목적 | `rounds/<회차>/`의 스크립트 | RESULTS.md 절 | 릴리즈 자산 |
|---|---|---|---|---|---|---|
| P | 2026-09-24 | g5.xlarge ×2 | 2노드 배관: iperf, NIXL 기동, 첫 종단 요청 | 런북만(`README.md`, `README.ko.md`) | §P | `results-P.tar.gz` |
| A′(폴더 `Aprime/`) | 2026-09-24 | g7e.2xlarge ×1 | 큰 모델 기동 검증 | 런북만(`README.md`, `README.ko.md`) | §A′ | `results-Ap.tar.gz` |
| A | 2026-09-24 | g7.2xlarge ×1 | 청크·워크로드 스윕(접두어 캐시 켬. 보고서에서 제외) | `run_A.sh`, 런북 | §A | `results-A.tar.gz` |
| C1 | 2026-09-25 | g7e.2xlarge ×1 | 양자화와 KV 용량(접두어 캐시 켬. 보고서에서 제외) | `run_C1.sh`, `run_C1_tail.sh`, `prefetch_C1.sh` | §C1 | `results-C1.tar.gz` |
| B | 2026-09-25 | g7.2xlarge ×2 + c6i.xlarge 클라이언트 | 입력 길이 격자와 첫 분리 결과 | `run_B.sh`, `run_B_knee.sh`, `run_B_tail.sh` | §B | `results-B.tar.gz` |
| D | 2026-09-26 | g7.2xlarge ×2 + 클라이언트 | 전송 튜닝(UCX 변수)과 대역폭 제한 스윕 | `run_D_xfer.sh`, `run_D1.sh`, `run_D1b.sh`, `run_D2.sh`, `run_D3.sh` | §D | `results-D.tar.gz` |
| E1 | 2026-09-26 | g6e.2xlarge ×1 + g7e.2xlarge ×1 | FP8 공통 정밀도에서 L40S 대 RTX PRO 6000 교차 GPU, KV 맞춤 | `run_E1.sh`, `run_E1b.sh`, `run_E1c.sh` | §E1 | `results-E1.tar.gz` |
| E2 | 2026-09-26 | g7e.2xlarge ×2 | 분리 대 복제본, 16K 입력 | `run_E2.sh`, `run_E2b.sh` | §E2 | `results-E2.tar.gz` |
| E3 | 2026-09-27 | g6e.2xlarge ×2 | 네트워크 크레딧 | `run_E3.sh` | §E3 | `results-E3.tar.gz` |
| E4 | 2026-09-27 | g7e.2xlarge ×2, 클러스터 배치 그룹 | g7e의 흐름당 상한 | `run_E4.sh`, `run_E4b.sh` | §E4 | `results-E4.tar.gz` |
| E5 | 2026-09-27 | g7e.2xlarge ×2와 ×3, 클러스터 배치 그룹 | 26B·31B NVFP4 스케일링 | `run_E5.sh`, `run_E5b.sh` | §E5 | `results-E5.tar.gz` |
| E6 | 2026-09-27 | g7e.2xlarge ×2, 클러스터 배치 그룹 | 레이어별 푸시(vLLM PR 56874) 시험과 출력 정확성 관문 | `run_E6.sh`, `run_E6b.sh`, `run_E6c.sh` | §E6 | `results-E6.tar.gz` |
| E7 | 2026-09-28 | g7e.2xlarge ×2와 ×3, 클러스터 배치 그룹 | 반복, 실제 트레이스, 26B 4K 상한, 같은 회차 양자화, KV 맞춤 | `lib_E7.sh`, `run_E7a.sh`, `run_E7b.sh`, `run_E7c.sh` | §E7 | `results-E7.tar.gz` |
| E8 | 2026-09-29/30 | g7e.2xlarge ×2, 클러스터 배치 그룹 + c6i.2xlarge 클라이언트 | 복제본 청크 스윕, 전역 정지 원인, P–D 연결 수 | `lib_E8.sh`, `setup_E8.sh`, `step0_E8.sh`, `run_E8.sh`, `run_E8x.sh`, 런북 | §E8 | `results-E8.tar.gz` |
| E9 | 2026-09-30 | g7e.2xlarge ×2, 클러스터 배치 그룹 + c6i.2xlarge 클라이언트 | 측정 전에 커밋한 예측(13:30 UTC), 19런 | `lib_E9.sh`, `run_E9.sh` | §E9(예측, 그다음 결과) | `results-E9.tar.gz` |

표에 대한 메모:

- P·A′·A·C1 회차의 데이터는 공개하지만 보고서에서는 제외했습니다. P는 배관 확인만 했고, A와 C1은 접두어 캐시를 켠 채 돌렸으며, A′는 기동 검증이었습니다. 초기 회차의 같은 시드 반복도 제외했습니다. 감사 라벨은 `results/safe_runs.csv`에 있습니다.
- `lib_*.sh`는 같은 회차의 `run_*.sh`가 source 하는 파일이며 단독으로 실행하지 않습니다. `setup_E8.sh`는 로컬 머신에서, 나머지 스크립트는 모두 클라이언트 노드에서 실행했습니다.
- `rounds/D/run_D_xfer.sh`가 호출하는 `harness/xfer_probe.py`는 NIXL 전송만 따로 재는 독립 프로브였고, 커밋되지 않아 보존되지 않았습니다. 릴리즈 자산과 RESULTS.md §D의 D 회차 대역폭 스윕 런은 vLLM 기반 스크립트(`run_D1.sh`, `run_D1b.sh`, `run_D2.sh`, `run_D3.sh`)에서 나온 것이며 이 프로브에 의존하지 않습니다.
- 릴리즈 자산 이름은 `results/`의 데이터 폴더 이름을 따릅니다. 그래서 A′ 회차는 `results-Ap.tar.gz`이고 스크립트 폴더는 `rounds/Aprime/`입니다.
- 런북(회차별 `README.md`)은 영어 번역이고 `README.ko.md`가 한국어 원본입니다. 런북에 인용된 명령(`bash configs/setup_E8.sh` 등)도 스크립트와 같은 이유로 당시의 평평한 배치를 씁니다.

## E9 스크립트

`rounds/E9/run_E9.sh`와 `rounds/E9/lib_E9.sh`는 사전 등록 커밋(공개 해시 `b220463`)과 바이트 단위로 같습니다. 그 커밋은 마지막 회차의 런이 하나도 시작되기 전에 예측을 기록한 것입니다. 그래서 두 파일의 주석은 아직 한국어입니다. 다른 모든 회차의 스크립트는 뒤에 주석과 로그 문구를 번역했으며, 각 파일의 `git log`에서 번역 커밋이 측정 당시 커밋과 분리되어 보입니다.
