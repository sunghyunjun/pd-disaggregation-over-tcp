# list 26B FP8 / NVFP4 1P1D runs with longest-gap stats (read-only)
import sys, statistics as st
sys.path.insert(0,'harness')
import slo_sensitivity as ss
C = ss.load_cache('results/safe_runs.csv')
def q(x,p):
    x=sorted(x); return x[min(len(x)-1,int(p*len(x)))]
keys=set()
for rid,r in C.items():
    keys.add((r['stage'],r['config'],r['workload'],r['model'] if 'model' in r else '', r.get('gpu','')))
print(list(next(iter(C.values())).keys())[:40])
rows=[]
for rid,r in sorted(C.items()):
    if r['workload']!='random': continue
    cfg=r['config']
    if not any(s in cfg for s in ('1P1D','P1','PD','pd')): continue
    mg=[m*1000 for m in r['maxitl'] if m is not None]
    if not mg: continue
    rows.append((r['stage'],cfg,r['rate'],r['input_len_median'],r['safety'],len(mg),q(mg,.5),q(mg,.9),sum(1 for m in mg if m>30)/len(mg),sum(1 for m in mg if m>50)/len(mg),st.median([t*1000 for t in r['ttft']]),rid))
for x in rows: print(x)
