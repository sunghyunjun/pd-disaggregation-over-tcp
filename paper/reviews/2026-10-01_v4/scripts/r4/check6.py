import sys
sys.path.insert(0,'harness')
import slo_sensitivity as ss
C=ss.load_cache("results/safe_runs.csv")
for stage,cfg,rate,L,thr in [("E2","B2",0.25,"16384",30),("B","B2",0.25,"4096",40),("B","B2",0.25,"16384",40),("B","B2",0.25,"32000",40),("E7","26F_B2",1,"4096",30),("E9","26F_B2_c512",1,"4096",15),("E8","26F_B2_c1024",1,"4096",20)]:
    for k,r in sorted(C.items()):
        if r["stage"]==stage and r["config"]==cfg and r["workload"]=="random" and float(r["rate"])==rate and r["input_len_median"]==L and r["safety"]=="안전":
            mg=sorted(m*1000 for m in r["maxitl"] if m is not None)
            frac=sum(1 for m in mg if m>thr)/len(mg)
            print(stage,cfg,rate,L,"n",len(mg),f"frac>{thr}ms {frac:.2f}","top 15%:",[round(x) for x in mg[int(len(mg)*0.85):]])
