"""R1 v4 review: curve values near the boundary, margin-based boundary, strict-SLO strip, small-chunk d+e sensitivity.
Run from repo root: python3 <this file>"""
import sys, math; sys.path.insert(0,'harness')
from boundary_model import chunks, kv_mib
d,e,a,b,o=7.0,9.027505,0.015107,2.652e-6,40.82
DE=d+e
def step(c,p,x=DE): return x+a*c+b*c*(p+c/2)
def pre(L,c,x=DE): return sum(step(k,p,x) for k,p in chunks(L,c))
def best(L,G,x=DE):
    bb=None
    for c in range(128,8193,16):
        if max(step(k,p,x) for k,p in chunks(L,c))<=G: bb=c
    return bb
def pd(L,m=1.0): return o+pre(L,8192)+kv_mib(L,20,200)*8.388608/(m*9.54)+28
Ls=[int(round(2**(11+i/32))) for i in range(0,161)]
for L in (18000,19000,20000,21000):
    c=best(L,50); print("G50",L,c,round((o+pre(L,c))/1000,3),round(pd(L)/1000,3))
for G in (50,30):
    for thr in (1.0,1.08,1.16):
        for L in Ls:
            c=best(L,G); r=(o+pre(L,c)) if c else math.inf
            if r/pd(L)>=thr: print(f"G{G} rep/PD>={thr}: L={L}"); break
for m in (1.0,1.5):
    for G in (50,30):
        s=[L for L in range(4000,40000,100) if pd(L,m)<=1000 and (best(L,G) is None or o+pre(L,best(L,G))>1000)]
        print(f"strict 1 s, m={m}, G={G}: {s[0] if s else None}..{s[-1] if s else None}")
for L in Ls:
    if pd(L)>1000: print("PD TTFT > 1 s from", L); break
# small-chunk (<=512 tokens) fixed cost lowered; o kept from the eager 4K/2,560 point
for x in (16.03,14.0,12.0,10.0):
    def cross(G):
        for L in Ls:
            bb=None
            for c in range(128,8193,16):
                xx = x if c<=512 else DE
                if max(step(k,p,xx) for k,p in chunks(L,c))<=G: bb=c
            xx = x if (bb and bb<=512) else DE
            tr=o+pre(L,bb,xx) if bb else math.inf
            if pd(L)<tr: return L
    print(f"d+e for <=512-token steps {x}: G50 {cross(50)}, G30 {cross(30)}")
