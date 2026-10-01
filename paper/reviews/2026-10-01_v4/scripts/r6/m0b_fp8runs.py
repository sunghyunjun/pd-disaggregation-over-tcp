# 26B FP8 replica runs (g7e) with longest-gap p90, TTFT median, ITL p50 (read-only)
import sys, json, glob, os, statistics as st
sys.path.insert(0,'harness')
import slo_sensitivity as ss
C = ss.load_cache('results/safe_runs.csv')
def q(x,p):
    x=sorted(x); return x[min(len(x)-1,int(p*len(x)))]
where = {os.path.basename(os.path.dirname(p)): p for p in glob.glob("results/*/*/bench.json")}
for rid,r in sorted(C.items()):
    if r['workload']!='random': continue
    if not (r['config'].startswith('26F_B2') or (r['stage']=='E2' and r['config'] in ('B2','P1tuned'))): continue
    mg=[m*1000 for m in r['maxitl'] if m is not None]
    itl=[]
    if rid in where:
        b=json.load(open(where[rid]))
        for l in b.get('itls',[]): itl += [x*1000 for x in l]
    print(r['stage'],r['config'],r['rate'],r['input_len_median'],r['safety'],len(mg),'gap p50/p90 %.1f/%.1f'%(q(mg,.5),q(mg,.9)),'ttft p50 %.0f'%st.median([t*1000 for t in r['ttft']]),'itl p50 %.2f'%(st.median(itl) if itl else -1))
