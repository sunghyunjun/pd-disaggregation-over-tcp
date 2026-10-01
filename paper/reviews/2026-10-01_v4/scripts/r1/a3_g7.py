import sys; sys.path.insert(0,'harness')
import numpy as np
from boundary_model import chunks
d7=12.0
pts=[(4096,131.2),(16384,254.5)]
k0,b7=90.0,4e-6
for _ in range(50):
    X=[];y=[]
    for L,g in pts:
        k,p=max(chunks(L,2560),key=lambda kp:k0*kp[0]/2560+b7*kp[0]*(kp[1]+kp[0]/2))
        X.append([k/2560, k*(p+k/2)]); y.append(g-d7)
    k0,b7=np.linalg.solve(np.array(X),np.array(y))
def st(c,p): return d7+k0*c/2560+b7*c*(p+c/2)
def gap(L): return max(st(k,p) for k,p in chunks(L,2560))
def pre(L): return sum(st(k,p) for k,p in chunks(L,2560))
o=278-pre(4096)
print(f"consistent g7 fit: k0={k0:.2f} b={b7*1e6:.3f} ns o={o:.0f}")
for L,g,t in [(4096,131.2,278),(16384,254.5,1430),(32000,375.7,3507)]:
    print(L, f"gap meas/model {g}/{gap(L):.1f} ({(gap(L)/g-1)*100:+.1f}%)  TTFT {t}/{o+pre(L):.0f} ({((o+pre(L))/t-1)*100:+.1f}%)")
# which chunk is longest at 4K for g7e FP8 base params
d,e,a,b=7.0,9.0275,0.015107,2.652e-6
for c in (2560,1024,512):
    print("g7e 4K c",c,[(k,p,round(d+e+a*k+b*k*(p+k/2),1)) for k,p in chunks(4096,c)])
