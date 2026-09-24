#!/usr/bin/env python3
"""Collect every results/**/result.json (+ bench.json) into one flat CSV for sheets/plots.
Usage: aggregate.py results/ -o results/all_runs.csv [--slo chat=ttft:1000,tbt:100 --slo doc=ttft:3000,tbt:400]
One row per run: meta (stage/config/network/workload/rate/model/chunk), env (instance, iperf), bench summary, TBT-derived metrics.
"""
import argparse, csv, glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze import analyze, parse_slo

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("root"); ap.add_argument("-o","--out",required=True)
    ap.add_argument("--slo",action="append",default=[]); ap.add_argument("--tbt-stat",default="max")
    a=ap.parse_args()
    slos=dict(parse_slo(s) for s in a.slo) or {"chat":{"ttft":1000,"tbt":100},"doc":{"ttft":3000,"tbt":400}}
    rows=[]
    for rj in sorted(glob.glob(os.path.join(a.root,"**","result.json"),recursive=True)):
        d=os.path.dirname(rj); bj=os.path.join(d,"bench.json")
        try: r=json.load(open(rj))
        except Exception as e: print("skip",rj,e); continue
        meta=r.get("meta",{}); env=meta.get("env",{}) or {}; b=r.get("bench",{})
        row={"run_id":meta.get("run_id"),"stage":meta.get("stage"),"config":meta.get("config"),"network":meta.get("network"),
             "workload":meta.get("workload"),"rate":meta.get("rate"),"model":b.get("model_id"),"chunk":os.environ.get("CHUNK",""),
             "instance_type":env.get("instance_type"),"az":env.get("az"),"vllm":env.get("vllm_version"),
             "iperf_p1_gbps":env.get("iperf_p1_gbps"),"iperf_p4_gbps":env.get("iperf_p4_gbps"),"ping_ms":env.get("ping_avg_ms"),
             "num_prompts":b.get("num_prompts"),"request_rate":b.get("request_rate"),"max_concurrency":b.get("max_concurrency"),
             "duration_s":b.get("duration"),"completed":b.get("completed"),"failed":b.get("failed"),
             "req_per_s":b.get("request_throughput"),"out_tok_per_s":b.get("output_throughput"),"total_tok_per_s":b.get("total_token_throughput"),
             "ttft_mean_ms":b.get("mean_ttft_ms"),"ttft_p50_ms":b.get("median_ttft_ms"),"ttft_p90_ms":b.get("p90_ttft_ms"),"ttft_p99_ms":b.get("p99_ttft_ms"),
             "tpot_mean_ms":b.get("mean_tpot_ms"),"tpot_p99_ms":b.get("p99_tpot_ms"),"itl_p50_ms":b.get("median_itl_ms"),"itl_p90_ms":b.get("p90_itl_ms"),"itl_p99_ms":b.get("p99_itl_ms"),
             "vllm_goodput_req_s":b.get("request_goodput"),"discarded":meta.get("discarded")}
        if os.path.exists(bj):
            try:
                x=analyze(bj,slos,a.tbt_stat)
                for k in ("tbt_p50_ms","tbt_p90_ms","tbt_p99_ms","itl_max_over_median_p50","stall_req_frac"): row[k]=x.get(k)
                for name in slos: 
                    for k in (f"attain_{name}",f"goodput_{name}_req_s",f"goodput_{name}_tok_s"): row[k]=x.get(k)
            except SystemExit: pass
        rows.append(row)
    if not rows: print("no runs"); return
    keys=list({k:1 for r in rows for k in r}.keys())
    with open(a.out,"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)
    print(f"wrote {a.out}: {len(rows)} runs")
if __name__=="__main__": main()
