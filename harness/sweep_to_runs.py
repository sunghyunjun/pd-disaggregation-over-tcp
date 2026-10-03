#!/usr/bin/env python3
"""Convert `vllm bench sweep serve` output into the existing result layout (results/<RUN_ID>/{result,bench}.json).
An adapter so the aggregation path (analysis/aggregate.py -> analysis/analyze.py -> analysis/table.py) can be used unchanged.
Usage: sweep_to_runs.py SWEEP_EXP_DIR --stage E5 --config P1tuned --workload sharegpt [--network N0] [--out results]
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
            # sweep does not record the run time, so the file mtime in UTC is used instead
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
        print("no run=*.json to convert under:", a.exp_dir, file=sys.stderr); sys.exit(1)
    print(f"converted {made} runs")

if __name__ == "__main__":
    main()
