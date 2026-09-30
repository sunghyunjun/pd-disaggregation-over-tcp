# 세션 E8 실행 순서 (심사 대응 B1·B2·B3)

배경: `paper/reviews/2026-09-30_v0/` 좌장 권고. 유저 승인 2026-09-30(B1+B2+B3 묶음, B4 제외). 업무시간(평일 10~19시 KST) 밖에서 실행.
예상: 약 5시간, g7e.2xlarge 두 대(배치 그룹) + c6i.2xlarge, 약 $37~40.

1. 자격 확인: `AWS_PROFILE=default aws sts get-caller-identity`, 떠 있는 인스턴스 확인(다른 프로젝트 인스턴스는 건드리지 않는다).
2. 인프라(E7과 같은 방식)
   - 클라이언트: `CLIENT_TYPE=c6i.2xlarge bash infra/up.sh g7e_2x 0 --client --hours 8`
   - GPU: `bash infra/up.sh g7e_2x 2 --pg --hours 8 --ws e8` (DescribeInstanceAttribute 권한 오류로 끝나도 생성은 된다. IP는 AWS CLI로 읽는다)
3. 준비: `C=<클라이언트 공인> NODES="<GPU 공인 둘>" bash configs/setup_E8.sh` (모델 셋: 26B NVFP4, 31B NVFP4, 26B FP8)
4. 0단계(클라이언트에서): `A_PRIV=.. B_PRIV=.. bash configs/step0_E8.sh` → 26B 1024/1536/2048, 31B 256/512가 어떤 MM_LIMIT·추가 인자로 뜨는지 확인
   - 26B가 전부 거부되면: CHUNKS26 비우고 PHASES에서 1의 스윕을 빼되 2560 대조는 유지(스택 제약 자체가 결과)
   - 31B가 전부 거부되면 5단계의 청크 팔을 빼고 1P1D 연결 수 측정만
5. 본 측정(클라이언트에서, setsid): `A_PRIV=.. B_PRIV=.. CHUNKS26=".." CHUNK31=.. [CHUNK31B=..] MM_LIMIT='..' SERVE_EXTRA='..' bash configs/run_E8.sh > results/run_E8.log 2>&1`
6. 감시: run_E8.log의 단계·달성률·오류. 한 지점 제한 25분.
7. 회수: 클라이언트 `results/*_E8_*`, `rr_proxy_E8_*`, `proxy_E8_*`, `proxy_trace_E8_*`, `xfer_E8/`, `metrics_E8/`, `client_cpu_E8_*`, `step0_E8_*`, `run_E8.log` → `results/E8/`. GPU 노드 `collect_*`, `ss_E8_*` → `results/E8/collect/<host>/`, `results/E8/ss/`.
8. 삭제: `bash infra/down.sh --ws e8` 다음 `bash infra/down.sh --ws default`(주의: up.sh --ws e8 뒤에는 현재 작업 공간이 e8이라, 인자 없는 down.sh는 클라이언트를 지우지 않는다). 인스턴스 0 확인(다른 프로젝트 제외).
   - 2단계도 순서대로(클라이언트 먼저, GPU 나중). 같은 terraform 폴더라 동시에 돌리면 작업 공간이 엉킨다.
9. 기록: RESULTS.md에 E8 절, 마찰, 비용. 메모리 갱신.
