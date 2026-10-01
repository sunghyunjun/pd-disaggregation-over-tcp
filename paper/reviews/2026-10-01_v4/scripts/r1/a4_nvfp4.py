import sys; sys.path.insert(0,'harness')
import numpy as np, statistics as st
import slo_sensitivity as ss
from boundary_model import chunks
C=ss.load_cache('results/safe_runs.csv')
def p90(cfg,rate,stage=None):
    mg=[m*1000 for rid,r in C.items() if r['config']==cfg and float(r['rate'])==rate and r['safety']=='안전' and r['workload']=='random' and int(r['input_len_median'])==4096 and (stage is None or r['stage']==stage) for m in r['maxitl'] if m is not None]
    mg.sort(); return mg[int(0.9*len(mg))], st.median(mg)
pts={}
for c,cfg in [(512,'26_B2_c512'),(1024,'26_B2_c1024'),(1536,'26_B2_c1536'),(2048,'26_B2_c2048'),(2560,'26_B2_c2560')]:
    pts[c]=p90(cfg,2.0); print(c,pts[c])
d=9.0
def fit(cs, use=0):
    e,a,b=0.,0.02,1e-6
    for _ in range(60):
        X=[];y=[]
        for c in cs:
            k,p=max(chunks(4096,c),key=lambda kp:a*kp[0]+b*kp[0]*(kp[1]+kp[0]/2))
            X.append([1,k,k*(p+k/2)]); y.append(pts[c][use]-d)
        e,a,b=np.linalg.lstsq(np.array(X),np.array(y),rcond=None)[0]
    return e,a,b
for use in (0,1):
    e,a,b=fit([512,1024,1536,2560],use)
    st_=lambda c,p: d+e+a*c+b*c*(p+c/2)
    print(['p90','median'][use], f"e={e:.2f} a={a*1e3:.2f}us b={b*1e6:.2f}ns", {c:(round(max(st_(k,p) for k,p in chunks(4096,c)),1), pts[c][use]) for c in (512,1024,1536,2048,2560)})
# Using FP8 g7e params (paper) to show position effect
e,a,b=9.0275,0.015107,2.652e-6
for c in (2560,2048,1536):
    print('FP8 params',c,[(k,p,round(7+e+a*k+b*k*(p+k/2),1)) for k,p in chunks(4096,c)])
