import sys, csv; sys.path.insert(0,'harness')
import slo_sensitivity as ss
from collections import defaultdict
C=ss.load_cache('safe_runs.csv'); rows={r['run_id']:r for r in csv.DictReader(open('safe_runs.csv'))}
ALIAS={'26_B2_c2560':'26_B2','26_1P1D_toyi':'26_1P1D','31_B2_c2560':'31_B2'}
def grp(cross):
    g=defaultdict(list)
    for rid,r in C.items():
        if r['safety']!='안전': continue
        cfg=ALIAS.get(r['config'],r['config']) if cross else r['config']
        k=(('*' if cross else r['stage']),cfg,r['workload'],r['rate'],r['input_len_median'] if r['workload']=='random' else '',r['network'])
        g[k].append((rid,ss.attain(r,1,50),float(rows[rid]['ttft_p50_ms'])))
    return {k:v for k,v in g.items() if len(v)>=2}
for cross in (False,True):
    G=grp(cross)
    print('==== cross-session' if cross else '==== within session', len(G),'groups')
    res=[]
    for k,v in G.items():
        t=[x[2] for x in v]; a=[x[1] for x in v]
        res.append(((max(t)-min(t))/min(t),k,[round(x) for x in t],[round(x,3) for x in a]))
    res.sort(reverse=True)
    for x in res[:12]: print(f"TTFT var {x[0]*100:5.1f}%",x[1],x[2],x[3])
    # attainment spreads
    hi=[];near=[]
    for k,v in G.items():
        a=[x[1] for x in v]; m=sum(a)/len(a)
        if min(a)>=0.95: hi.append((max(a)-min(a),k,a))
        elif max(a)>=0.8 : near.append(((max(a)-min(a))/2,k,[round(x,3) for x in a]))
    hi.sort(reverse=True); near.sort(reverse=True)
    print('well above 0.9 (min>=0.95) max spread', [(round(x[0],3),x[1]) for x in hi[:3]])
    print('near 0.9 half-range top', [(round(x[0],3),x[1][1],x[1][3],x[2]) for x in near[:5]])
