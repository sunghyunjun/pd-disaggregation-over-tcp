# vLLM PR #56874: layer-wise push (local experimental copy)

- Source: https://github.com/vllm-project/vllm/pull/56874 (unmerged; no review as of 2026-09-27)
- PR head: `d64089cb85e0be5a3684ac588b912a4c40cad3ab`, PR base: `668d6c3a778b9ac525f78d39b0c413c8604235d1`
- Scope: the four runtime files of our image `vllm/vllm-openai:v0.30.0`; test-file changes excluded.
- Applied as `pr56874_src.diff` with `patch -p1` on the v0.30.0 sources; 0 rejected hunks; all 809 lines the PR adds verified present. The only differences from the PR's final state are the pre-existing differences between the PR base and v0.30.0 (connector 8 lines, push_worker 4 lines, envs 65 lines).
- Use: mount read-only over the same paths in the container through `EXTRA_MOUNTS` in `harness/serve.sh`, with `ENV_EXTRA="VLLM_NIXL_LAYERWISE_PUSH=1"` and `KV_CONNECTOR_NAME=NixlPushConnector`.
- License: Apache-2.0, as vLLM (SPDX headers kept in each file).

(한국어) vLLM PR #56874의 레이어별 푸시를 v0.30.0 이미지에 적용한 로컬 실험용 사본. 출처·적용 방법·라이선스는 위와 같다.
