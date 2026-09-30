"""R2 3차: 연결 상한의 양면 효과(대기열로 첫 토큰 악화, 서버 동시 수 제한으로 간격 개선?). E8 상한 런 vs E9 무상한 런, 같은 요청률·시드. 읽기 전용."""
import gzip, json, statistics as st
C = json.load(gzip.open("results/per_request.json.gz", "rt"))
def q(xs, p):
    xs = sorted(xs); k = (len(xs)-1)*p; lo = int(k); hi = min(lo+1, len(xs)-1); return xs[lo] + (xs[hi]-xs[lo])*(k-lo)
sel = [(rid, r) for rid, r in C.items() if r["config"] in ("26_B2_c1024", "31_B2_c256", "26_B2_c1536") and r["stage"] in ("E8", "E9")]
for rid, r in sorted(sel, key=lambda x: (x[1]["config"], float(x[1]["rate"]), x[0])):
    mi = [m*1000 for m in r["maxitl"] if m is not None]
    gapfail = sum(1 for m in r["maxitl"] if m is not None and m*1000 > 50) / len(r["ttft"])
    ttfail = sum(1 for t in r["ttft"] if t > 1.0) / len(r["ttft"])
    tt = [t*1000 for t in r["ttft"]]
    print(f"{r['stage']} {r['config']:12s} r{r['rate']:>3} {r['safety']}  n={len(tt)}  maxgap p50 {q(mi,.5):5.1f} p90 {q(mi,.9):5.1f}  gap>50 {gapfail:.3f}  TTFT>1s {ttfail:.3f}  TTFT p50 {q(tt,.5):6.0f} p99 {q(tt,.99):6.0f}")
