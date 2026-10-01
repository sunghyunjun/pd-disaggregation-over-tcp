import json, math, sys
sys.path.insert(0, 'harness')
from boundary_model import chunks, step, kv_mib

B = json.load(open(sys.argv[1])); par = dict(B["fp8_g7e"]["params"]); o=par["o"]; CP=8192; CFLOW=9.54; R=28.0
def prefill(p,L,c): return sum(step(p,k,pp) for k,pp in chunks(L,c))
def gap(p,L,c): return max(step(p,k,pp) for k,pp in chunks(L,c))
def rep(L,G):
    best=None
    for c in range(128,8193,16):
        if gap(par,L,c)<=G: best=c
    return o+prefill(par,L,best) if best else math.inf
def pdt(L,m): return o+prefill(par,L,CP)+kv_mib(L,20,200)*8.388608/(m*CFLOW)+R
for G,m,lo,hi in [(50,1.0,18000,22000),(50,1.5,13000,20000),(30,1.0,8000,11000)]:
    xs=list(range(lo,hi,128)); win=[L for L in xs if pdt(L,m)<rep(L,G)]
    marg=[ (rep(L,G)-pdt(L,m))/rep(L,G) for L in xs]
    print(f"G{G} m{m}: PD better at {len(win)}/{len(xs)} points in [{lo},{hi}); first {win[0] if win else None}; max relative margin {max(marg)*100:.1f}% ; margin at hi-128 {marg[-1]*100:.1f}%")
print("first L where PD advantage >= 8% (and stays for next 2K):")
for G,m in [(50,1.0),(50,1.5),(30,1.0)]:
    for L in range(4096,65537,128):
        r=rep(L,G); 
        if all(((rep(x,G)-pdt(x,m))/rep(x,G) if rep(x,G)<math.inf else 1)>=0.08 for x in range(L,L+2048,256)):
            print(f"  G{G} m{m}: {L}"); break
