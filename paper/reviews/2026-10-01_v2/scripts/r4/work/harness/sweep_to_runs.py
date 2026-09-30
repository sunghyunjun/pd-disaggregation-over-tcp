#!/usr/bin/env python3
"""`vllm bench sweep serve` 출력을 기존 결과 배치(results/<RUN_ID>/{result,bench}.json)로 변환한다.
집계 경로(aggregate.py → analyze.py → table.py)를 그대로 쓰기 위한 어댑터다.
사용법: sweep_to_runs.py SWEEP_EXP_DIR --stage E5 --config P1tuned --workload sharegpt [--network N0] [--out results]
"""
import argparse, json, os, re, shutil, sys
from datetime import datetime, timezone

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exp_dir"); ap.add_argument("--stage", required=True); ap.add_argument("--config", required=True)
    ap.add_argument("--workload", required=True); ap.add_argument("--network", default="N0")
    ap.add_argument("--out", default="results"); ap.add_argument("--env-json", default=os.environ.get("ENV_JSON"))
    a = ap.parse_args()
    env = {}
    if a.env_json and os.path.exists(a.env_json):
        env = json.load(open(a.env_json))
    made = 0
    for root, _dirs, files in os.walk(a.exp_dir):
        for fn in sorted(files):
            if not re.fullmatch(r"run=\d+\.json", fn):
                continue
            src = os.path.join(root, fn)
            b = json.load(open(src))
            rate = b.get("request_rate")
            rate_s = "inf" if rate in (None, float("inf")) else (f"{rate:g}")
            # 실행 시각은 sweep이 남기지 않으므로 파일 mtime을 UTC로 쓴다
            ts = datetime.fromtimestamp(os.path.getmtime(src), timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
            run_no = fn[len("run="):-len(".json")]
            run_id = f"{ts}_{a.stage}_{a.config}_{a.network}_{a.workload}_r{rate_s}_n{run_no}"
            d = os.path.join(a.out, run_id); os.makedirs(d, exist_ok=True)
            shutil.copyfile(src, os.path.join(d, "bench.json"))
            meta = {"run_id": run_id, "stage": a.stage, "config": a.config, "network": a.network,
                    "workload": a.workload, "rate": rate_s, "seed": str(b.get("seed", "")),
                    "point_sec": "", "vllm_flags": "", "chunk": os.environ.get("CHUNK", ""),
                    "prefix_caching": os.environ.get("PREFIX", ""), "model": b.get("model_id", ""),
                    "env": env, "discarded": False, "discard_reason": "",
                    "source": "vllm bench sweep serve", "sweep_path": src, "run_number": b.get("run_number")}
            json.dump({"meta": meta, "bench": b}, open(os.path.join(d, "result.json"), "w"))
            made += 1
            print("wrote", os.path.join(d, "result.json"))
    if made == 0:
        print("변환할 run=*.json 이 없습니다:", a.exp_dir, file=sys.stderr); sys.exit(1)
    print(f"{made}개 런 변환 완료")

if __name__ == "__main__":
    main()
