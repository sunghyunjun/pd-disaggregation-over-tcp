#!/usr/bin/env bash
# 런 사이 서버 캐시 리셋. vllm bench sweep serve의 clear_cache()와 같은 엔드포인트를 쓴다.
# 서버가 VLLM_SERVER_DEV_MODE=1로 떠 있어야 한다(serve.sh가 설정).
# 사용: reset_caches.sh http://10.0.0.1:8100 [http://10.0.0.2:8200 ...]
set -u
rc=0
for base in "$@"; do
  for ep in /reset_prefix_cache /reset_mm_cache /reset_encoder_cache; do
    code=$(curl -s -o /dev/null -w "%{http_code}" -X POST --max-time 15 "${base}${ep}" 2>/dev/null)
    case "$code" in
      200|204) ;;                      # 정상
      404) ;;                          # 해당 캐시 없는 구성(멀티모달 미사용 등) — 무시
      *) echo "    캐시 리셋 실패 ${base}${ep} -> ${code:-no-response}"; rc=1;;
    esac
  done
done
exit $rc
