import sys, math, itertools
sys.path.insert(0,'harness')
import numpy as np
import boundary_model as bm
from boundary_model import chunks, kv_mib
KIB,MIB=1024,1024*1024
d=7.0
meas=[(4096,2560,62.9),(4096,1024,43.6),(4096,512,27.2),(16384,2560,150.2)]
def fit(points, d=7.0):
    e,a,b=0.0,0.02,1e-6
    for _ in range(60):
        X=[];y=[]
        for L,c,g in points:
            k,p=max(chunks(L,c),key=lambda kp:a*kp[0]+b*kp[0]*(kp[1]+kp[0]/2))
            X.append([1.0,k,k*(p+k/2)]); y.append(g-d)
        e,a,b=np.linalg.lstsq(np.array(X),np.array(y),rcond=None)[0]
    return dict(d=d,e=float(e),a=float(a),b=float(b))
def step(par,c,p): return par['d']+par['e']+par['a']*c+par['b']*c*(p+c/2)
def gap(par,L,c): return max(step(par,k,p) for k,p in chunks(L,c))
def pre(par,L,c): return sum(step(par,k,p) for k,p in chunks(L,c))
Ls=[int(round(2**(11+i/32))) for i in range(0,161)]
def boundary(par, o, G, m=1.0, R=28.0, kv='hybrid', xs=1.0, rep_scale=1.0, pd_scale=1.0, Tmax=None, CP=8192, CF=9.54):
    kvf = (lambda L: kv_mib(L,20,200)) if kv=='hybrid' else (lambda L: L*220*KIB/MIB)
    res=None
    for L in Ls:
        best=None
        for c in range(128,8193,16):
            if gap(par,L,c)<=G: best=c
        tr=(o+pre(par,L,best))*rep_scale if best else math.inf
        tp=(o+pre(par,L,CP)+xs*kvf(L)*8.388608/(m*CF)+R)*pd_scale
        if tp<tr and (Tmax is None or tp<=Tmax):
            return (L, round(tp/1000,2), round(tr/1000,2) if tr<math.inf else None, best)
    return None
base=fit(meas); o=157-pre(base,4096,2560)
print("base",{k:round(v,6) for k,v in base.items()},"o",round(o,1), "d+e", round(base['d']+base['e'],2))
for G in (50,30):
    print(f"G{G} base boundary (L, PD TTFT s, rep TTFT s, rep chunk):", boundary(base,o,G))
# LOO
for i in range(4):
    pts=[m for j,m in enumerate(meas) if j!=i]
    p=fit(pts); oo=157-pre(p,4096,2560) if i!=0 else 157-pre(p,4096,2560)
    print(f"LOO drop {meas[i][:2]}: e={p['e']:.2f} a={p['a']*1000:.2f}us b={p['b']*1e6:.3f}ns  pred dropped gap {gap(p,meas[i][0],meas[i][1]):.1f} vs {meas[i][2]} | G50 {boundary(p,oo,50)} | G30 {boundary(p,oo,30)}")
# median of overlap cluster instead of p90
med=[(4096,2560,62.2),(4096,1024,43.2),(4096,512,26.8),(16384,2560,147.0)]
p=fit(med); oo=157-pre(p,4096,2560)
print("median-ish fit", {k:round(v,6) for k,v in p.items()}, "G50", boundary(p,oo,50), "G30", boundary(p,oo,30))
# residual 87, m=1.8, m=2
for kw in [dict(R=87),dict(m=1.8),dict(m=2.0),dict(m=1.5),dict(xs=0.05)]:
    print(kw, "G50", boundary(base,o,50,**kw), "G30", boundary(base,o,30,**kw))
# apply 16K out-of-sample error ratios
print("16K error-corrected (rep x820/756, PD x1286/1370): G50", boundary(base,o,50,rep_scale=820/756,pd_scale=1286/1370), "G30", boundary(base,o,30,rep_scale=820/756,pd_scale=1286/1370))
print("rep x820/756 only: G50", boundary(base,o,50,rep_scale=820/756), " G30", boundary(base,o,30,rep_scale=820/756))
# strict SLO TTFT<=1s
print("strict T<=1s window? G50", boundary(base,o,50,Tmax=1000), " G30", boundary(base,o,30,Tmax=1000))
# where does T<=1 s window close at G30: PD TTFT crosses 1 s
for L in Ls:
    tp=o+pre(base,L,8192)+kv_mib(L,20,200)*8.388608/9.54+28
    if tp>1000: print("PD TTFT exceeds 1 s at L=",L); break
# 30 ms: L where c=128 fails
for L in Ls:
    if gap(base,L,128)>30: print("G30: c=128 fails from L=",L); break
for L in Ls:
    if gap(base,L,128)>50: print("G50: c=128 fails from L=",L); break
# b scaled 0.85 both sides vs replica-only
p2=dict(base); p2['b']*=0.85
print("b x0.85 both sides G50", boundary(p2,o,50), "G30", boundary(p2,o,30))
# all-global with replica attention also scaled
for bs in (1,2,3,5):
    p3=dict(base); p3['b']*=bs
    print(f"all-global KV, b x{bs} (both sides)", "G50", boundary(p3,o,50,kv='global'), "G30", boundary(p3,o,30,kv='global'))
