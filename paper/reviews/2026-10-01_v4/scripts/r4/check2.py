import json, math, sys
sys.path.insert(0, 'harness')
from boundary_model import chunks, step, kv_mib
B = json.load(open(sys.argv[1]))
par = dict(B["fp8_g7e"]["params"])
# use full-precision params by refitting? use rounded 4g params; small effect
o = par["o"]; CP=8192; CFLOW=9.54; R=28.0
def prefill(p,L,c): return sum(step(p,k,pp) for k,pp in chunks(L,c))
def gap(p,L,c): return max(step(p,k,pp) for k,pp in chunks(L,c))
def rep(p,L,G):
    best=None
    for c in range(128,8193,16):
        if gap(p,L,c)<=G: best=c
    return (best, o+prefill(p,L,best)) if best else (None, math.inf)
kvs={"hybrid":lambda L: kv_mib(L,20,200),"all_global":lambda L: L*220/1024}
def pdt(p,L,kv="hybrid",m=1.0,xs=1.0): return o+prefill(p,L,CP)+xs*kvs[kv](L)*8.388608/(m*CFLOW)+R
def crossing(G,bscale=1.0,**kw):
    p=dict(par); p["b"]=par["b"]*bscale
    for L in range(2048,65537,64):
        c,tr=rep(p,L,G); tp=pdt(p,L,**kw)
        if tp<tr: return L, round(tp/1000,3), (round(tr/1000,3) if tr<math.inf else None)
    return None
for G in (50,30):
    for name,kw in [("base",{}),("b*0.85",{"bscale":0.85}),("m=1.5",{"m":1.5}),("fast",{"xs":0.05}),("allglobal",{"kv":"all_global"})]:
        print(G,name,crossing(G,**kw))
# monotonic check around crossing G50
p=dict(par)
for L in range(17000,23000,500):
    c,tr=rep(p,L,50); print(L,c,round(tr),round(pdt(p,L)))
