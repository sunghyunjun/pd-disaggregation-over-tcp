import sys, math; sys.path.insert(0,'harness')
from boundary_model import chunks, kv_mib
d,e,a,b,o=7.0,9.027505,0.015107,2.652e-6,40.82
def step(c,p): return d+e+a*c+b*c*(p+c/2)
def pre_fixed(L,c): return sum(step(k,p) for k,p in chunks(L,c))
def best_fixed(L,G):
    best=None
    for c in range(128,8193,16):
        if max(step(k,p) for k,p in chunks(L,c))<=G: best=c
    return best
def pre_adapt(L,G):
    p=0; t=0; n=0
    while p<L:
        # largest c with step(c,p)<=G: solve b/2 c^2 + (a+b p) c + (d+e-G) <= 0
        A=b/2; B=a+b*p; Cc=d+e-G
        c=int((-B+math.sqrt(B*B-4*A*Cc))/(2*A))
        if c<1: return math.inf, n
        c=min(c,L-p); t+=step(c,p); p+=c; n+=1
    return t, n
def pd(L,m=1.0): return o+pre_fixed(L,8192)+kv_mib(L,20,200)*8.388608/(m*9.54)+28
Ls=[int(round(2**(11+i/32))) for i in range(0,161)]
for G in (50,30):
    fx=next(L for L in Ls if (best_fixed(L,G) is None) or pd(L) < o+pre_fixed(L,best_fixed(L,G)))
    ad=next((L for L in Ls if pd(L) < o+pre_adapt(L,G)[0]),None)
    print(f"G{G}: crossing fixed-chunk {fx}, position-adaptive chunk {ad}")
    for L in (16384,32768,65536):
        c=best_fixed(L,G); tf=o+pre_fixed(L,c) if c else math.inf; ta,n=pre_adapt(L,G)
        print(f"   L={L}: fixed c={c} TTFT {tf/1000:.2f}s n={math.ceil(L/c) if c else None} | adaptive TTFT {(o+ta)/1000:.2f}s n={n} | PD {pd(L)/1000:.2f}s")
# 1P1D prefill-GPU capacity vs replicas per GPU at low load (model, GPU-seconds per request)
for L in (16384,32768,65536):
    c=best_fixed(L,50)
    print(f"L={L}: prefill GPU-s per request: replica(c={c}) {pre_fixed(L,c)/1000:.2f}s -> {1000/pre_fixed(L,c):.2f} req/s per GPU; P node (8192) {pre_fixed(L,8192)/1000:.2f}s -> {1000/pre_fixed(L,8192)/2:.2f} req/s per GPU (1P1D pair)")
