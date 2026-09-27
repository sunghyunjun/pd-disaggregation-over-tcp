# vLLM PR #56874 · 레이어별 푸시(로컬 실험용 적용본)

- 출처: https://github.com/vllm-project/vllm/pull/56874 (미병합, 2026-09-27 기준 리뷰 없음)
- PR head: `d64089cb85e0be5a3684ac588b912a4c40cad3ab`, PR base: `668d6c3a778b9ac525f78d39b0c413c8604235d1`
- 대상: 우리 이미지 `vllm/vllm-openai:v0.30.0`의 실행 코드 네 파일. 테스트 파일 변경은 제외.
- 적용: `pr56874_src.diff`를 v0.30.0 원본에 `patch -p1`. 거부 조각 0. PR이 추가하는 809줄 전부 존재 확인.
  PR 최종본과의 차이는 PR 기준 커밋과 v0.30.0 사이의 원래 차이뿐(connector 8줄, push_worker 4줄, envs 65줄).
- 사용: `harness/serve.sh`에 `EXTRA_MOUNTS`로 컨테이너의 같은 경로에 읽기 전용으로 덮어 올리고
  `ENV_EXTRA="VLLM_NIXL_LAYERWISE_PUSH=1"`, `KV_CONNECTOR_NAME=NixlPushConnector`.
- 라이선스: vLLM과 같은 Apache-2.0(각 파일의 SPDX 머리글 유지).
