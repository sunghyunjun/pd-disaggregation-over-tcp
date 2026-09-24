#!/usr/bin/env python3
"""Derive TBT-based metrics and goodput from `vllm bench serve --save-result --save-detailed` JSON.

Why: `--goodput` only accepts ttft/tpot/e2el. We define SLO on TTFT and per-request TBT (ITL)
quantile, following Sarathi-Serve / Splitwise, so goodput must be recomputed from per-request ITLs.

Usage:
  analyze.py RESULT.json [RESULT2.json ...] --slo chat=ttft:1000,tbt:100 --slo doc=ttft:3000,tbt:400 [--tbt-q 0.99] [--csv out.csv]

Per request: meets SLO iff ttft_ms <= T and STAT(itls)*1000 <= B, where STAT is `max` (default) or a quantile
(--tbt-stat p99). Why max: one prefill-induced stall of 300 ms inside a 500-token answer is 0.2% of tokens and
invisible to a per-request p99, but it is exactly the hiccup the user sees. System-level TBT p99 over all tokens
(Sarathi/Splitwise convention) is reported alongside for comparability.
Outputs per file: request_rate, duration, completed, system TBT p50/p90/p99 (over all tokens), per-request
max/median ITL ratio (median over requests), goodput_<slo> (req/s), attain_<slo> (fraction), output tok/s under SLO.
"""
import argparse, json, statistics as st, sys, csv, os

def quantile(xs, q):
    if not xs: return float("nan")
    xs = sorted(xs); k = (len(xs) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)

def parse_slo(s):
    name, _, spec = s.partition("=")
    d = {}
    for kv in spec.split(","):
        k, v = kv.split(":"); d[k.strip()] = float(v)
    return name.strip(), d

def req_stat(l, stat):
    if not l: return float("nan")
    if stat == "max": return max(l)
    return quantile(l, float(stat[1:]) / 100.0)

def analyze(path, slos, tbt_stat):
    with open(path) as f: r = json.load(f)
    ttfts, itls = r.get("ttfts"), r.get("itls")
    if ttfts is None or itls is None:
        raise SystemExit(f"{path}: no per-request ttfts/itls. Re-run bench serve with --save-detailed")
    out_lens = r.get("output_lens", [None]*len(ttfts))
    errors = r.get("errors", [None]*len(ttfts))
    dur = float(r.get("duration") or 0) or float("nan")
    all_itl = [x for l in itls for x in l]
    per_req_q = [req_stat(l, tbt_stat) for l in itls]
    ratios = [ (max(l)/st.median(l)) if len(l) >= 2 and st.median(l) > 0 else float("nan") for l in itls ]
    row = {
        "file": os.path.basename(path),
        "request_rate": r.get("request_rate"), "max_concurrency": r.get("max_concurrency"),
        "duration_s": round(dur, 1), "completed": r.get("completed"), "failed": r.get("failed"),
        "ttft_p50_ms": round(quantile(ttfts, .5)*1000, 1), "ttft_p90_ms": round(quantile(ttfts, .9)*1000, 1), "ttft_p99_ms": round(quantile(ttfts, .99)*1000, 1),
        "tbt_p50_ms": round(quantile(all_itl, .5)*1000, 2), "tbt_p90_ms": round(quantile(all_itl, .9)*1000, 2), "tbt_p99_ms": round(quantile(all_itl, .99)*1000, 2),
        "tpot_mean_ms": r.get("mean_tpot_ms"),
        "itl_max_over_median_p50": round(st.median([x for x in ratios if x == x]), 2) if any(x == x for x in ratios) else None,
        "stall_req_frac": round(sum(1 for x in ratios if x == x and x > 5) / max(1, sum(1 for x in ratios if x == x)), 3),
        "tbt_stat": tbt_stat,
        "output_tok_per_s": r.get("output_throughput"),
    }
    for name, slo in slos.items():
        T, B = slo.get("ttft", float("inf")) / 1000, slo.get("tbt", float("inf")) / 1000
        ok = [ (e is None) and (t <= T) and (pq <= B) for t, pq, e in zip(ttfts, per_req_q, errors) ]
        n_ok = sum(ok)
        row[f"attain_{name}"] = round(n_ok / max(1, len(ok)), 3)
        row[f"goodput_{name}_req_s"] = round(n_ok / dur, 3) if dur == dur else None
        tok_ok = sum((ol or 0) for ol, o in zip(out_lens, ok) if o)
        row[f"goodput_{name}_tok_s"] = round(tok_ok / dur, 1) if dur == dur else None
    return row

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--slo", action="append", default=[], help="name=ttft:MS,tbt:MS (repeatable)")
    ap.add_argument("--tbt-stat", default="max", help="per-request TBT statistic for SLO: max | pNN (e.g. p99)")
    ap.add_argument("--csv", default=None)
    a = ap.parse_args()
    slos = dict(parse_slo(s) for s in a.slo) or {"chat": {"ttft": 1000, "tbt": 100}, "doc": {"ttft": 3000, "tbt": 400}}
    rows = [analyze(p, slos, a.tbt_stat) for p in a.files]
    keys = list(rows[0].keys())
    if a.csv:
        with open(a.csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
    print("\t".join(keys))
    for r in rows: print("\t".join(str(r[k]) for k in keys))

if __name__ == "__main__":
    main()
