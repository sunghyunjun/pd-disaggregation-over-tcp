#!/usr/bin/env python3
"""Label every run in all_runs.csv by whether it may support a conclusion (audit criteria of 2026-09-28).
  safe (안전):     prefix caching off, not discarded, not a failed start, not in a client-limited range
  caution (주의):  the measurement is valid but needs a qualifier (E5 ShareGPT at 32 req/s and above = client
                   proxy CPU limit; replica runs before E9 in which 100 requests were in flight = rr_proxy
                   connection cap)
  excluded (제외): prefix caching on or not recorded (rounds A, A', C1, P; ShareGPT and Azure in B; the D3
                   ladder; Azure in E2), discarded, or a failed start
The label and reason strings are written to the CSV in Korean and are read back by the other scripts, so they
stay as they are. Usage: safe_runs.py results/all_runs.csv -o results/safe_runs.csv
"""
import argparse, bisect, csv, collections, glob, json, os

def f(v):
    try: return float(v)
    except (TypeError, ValueError): return 0.0

_BENCH = None
def max_inflight(run_id):
    """Largest number of requests in flight, as seen by the client, at the moment a request arrived
    (the same computation as the second mock review's meta-reviewer script r6_proxycap.py)."""
    global _BENCH
    if _BENCH is None:
        _BENCH = {os.path.basename(os.path.dirname(p)): p for p in glob.glob("results/*/*/bench.json")}
    p = _BENCH.get(run_id)
    if not p:
        return 0
    b = json.load(open(p))
    st, lat = b["start_times"], b["latencies"]
    se = sorted(s + l for s, l in zip(st, lat))
    return max((i - bisect.bisect_right(se, s) for i, s in enumerate(sorted(st))), default=0)

def classify(r):
    s, w, p = r["stage"], r["workload"], r["prefix_caching"]
    if r.get("discarded") == "True": return "제외", "폐기 런"
    if s in ("A", "Ap", "C1", "P"): return "제외", "접두어 캐시 켬 또는 미기록, 같은 시드 반복"
    if p == "on": return "제외", "접두어 캐시 켬"
    if f(r["ttft_p50_ms"]) == 0: return "제외", "기동 실패 런"
    if s == "E5" and w == "sharegpt" and f(r["rate"]) >= 32: return "주의", "클라이언트 프록시 한계 구간"
    # Second mock review (2026-09-30): before E9 the replica proxy (rr_proxy.py) used aiohttp's default connector,
    # which caps concurrent connections at 100. In a replica run that reached 100 requests in flight, the first
    # token of every later request was delayed inside the proxy, so such runs are not used for verdicts.
    cfg = r["config"]
    if s != "E9" and ("B2" in cfg or "B3" in cfg) and r["rate"] not in ("self", "inf") and max_inflight(r["run_id"]) >= 100:
        return "주의", "복제본 프록시 연결 상한 100 도달(E9 이전 rr_proxy)"
    return "안전", ""

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("csv"); ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    rows = list(csv.DictReader(open(a.csv)))
    for r in rows:
        r["safety"], r["safety_reason"] = classify(r)
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    c = collections.Counter(r["safety"] for r in rows)
    print(f"wrote {a.out}: safe {c['안전']}, caution {c['주의']}, excluded {c['제외']} (total {len(rows)})")

if __name__ == "__main__":
    main()
