import sys, os, glob, json, statistics as st
sys.path.insert(0,'harness')
import slo_sensitivity as ss
import boundary_model as bm
C = ss.load_cache('results/safe_runs.csv')
def pct(x,p):
    x=sorted(x); return x[min(len(x)-1,int(p*len(x)))]
pts = [(4096,2560,"E7","26F_B2",1.0),(4096,1024,"E8","26F_B2_c1024",1.0),(4096,512,"E9","26F_B2_c512",1.0),(16384,2560,"E2","B2",0.25),
       (4096,2560,"B","B2",0.25),(16384,2560,"B","B2",0.25),(32000,2560,"B","B2",0.25)]
where = {os.path.basename(os.path.dirname(p)): p for p in glob.glob("results/*/*/bench.json")}
for L,c,stg,cfg,rate in pts:
    rs=[(rid,r) for rid,r in sorted(C.items()) if r["stage"]==stg and r["config"]==cfg and r["workload"]=="random" and float(r["rate"])==rate and r["safety"]=="안전" and int(r["input_len_median"])==L]
    mg=[m*1000 for _,r in rs for m in r["maxitl"] if m is not None]
    tt=[t*1000 for _,r in rs for t in r["ttft"]]
    # median ITL from bench
    itl=[]
    for rid,_ in rs:
        b=json.load(open(where[rid]))
        for l in b["itls"]: itl+= [x*1000 for x in l]
    print(f"{stg} {cfg} L={L} c={c} rate={rate} runs={len(rs)} n={len(mg)} | maxgap p25 {pct(mg,.25):.1f} p50 {pct(mg,.5):.1f} p75 {pct(mg,.75):.1f} p90 {pct(mg,.9):.1f} max {max(mg):.1f} | ttft p25 {pct(tt,.25):.0f} p50 {st.median(tt):.0f} p75 {pct(tt,.75):.0f} p90 {pct(tt,.9):.0f} | ITL p50 {st.median(itl):.2f} | frac maxgap>2*ITLp50 {sum(1 for m in mg if m>2*st.median(itl))/len(mg):.2f}  ids={[x for x,_ in rs]}")
