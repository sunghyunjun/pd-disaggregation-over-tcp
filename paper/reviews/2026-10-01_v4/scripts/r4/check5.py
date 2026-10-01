import sys, statistics as st
sys.path.insert(0,'harness')
import slo_sensitivity as ss
C=ss.load_cache("results/safe_runs.csv")
def nr(x,p): x=sorted(x); return x[min(len(x)-1,int(p*len(x)))]
def li(x,p): return ss.q(x,p)
def show(stage,cfg,rate,L="4096"):
    rs=[(k,r) for k,r in sorted(C.items()) if r["stage"]==stage and r["config"]==cfg and r["workload"]=="random" and float(r["rate"])==float(rate) and r["input_len_median"]==L and r["safety"]=="안전"]
    for k,r in rs:
        mg=[m*1000 for m in r["maxitl"] if m is not None]
        print(f"{stage} {cfg} rate {rate} L {L} net {r['network']}: n={len(mg)} median longest gap {st.median(mg):.1f}  p90 nearest {nr(mg,.9):.1f} p90 interp {li(mg,.9):.1f}  TTFT p50 {st.median(r['ttft'])*1000:.0f}")
for a in [("E7","26_B2",1),("E7","26_B2",2),("E5","26_B2",2),("E8","26_B2_c2560",2),("E8","26_B2_c1024",2),("E9","26_B2_c512",2),
          ("E7","26F_B2",1),("E7","26F_B2",2),("E8","26F_B2_c1024",1),("E8","26F_B2_c1024",2),("E9","26F_B2_c512",1),("E9","26F_B2_c512",2),("E2","B2",0.5),("E2","B2",1)]:
    show(*a)
show("E2","B2",0.25,"16384"); show("E2","B2",0.5,"16384")
for L in ("4096","16384","32000"): show("B","B2",0.25,L)
