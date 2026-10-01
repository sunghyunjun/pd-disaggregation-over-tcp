import sys, statistics as st
sys.path.insert(0,'harness')
import slo_sensitivity as ss
C=ss.load_cache("results/safe_runs.csv")
for stage,cfg,rates in [("E9","26_B2_c1024",(8,10)),("E8","26_B2_c1024",(2,4)),("E9","26_B2_c512",(2,4,8)),("E8","26_B2_c2560",(2,4)),("E7","26_B2",(2,4))]:
    for rate in rates:
        for k,r in sorted(C.items()):
            if r["stage"]==stage and r["config"]==cfg and r["workload"]=="random" and float(r["rate"])==rate and r["safety"]=="안전":
                mg=[m*1000 for m in r["maxitl"] if m is not None]
                print(stage,cfg,"rate",rate,f"median longest gap {st.median(mg):.1f}",f"TTFT p50 {st.median(r['ttft'])*1000:.0f}", k[-30:])
