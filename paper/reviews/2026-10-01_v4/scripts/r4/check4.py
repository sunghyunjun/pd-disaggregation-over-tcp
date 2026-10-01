import json, sys
import numpy as np
sys.path.insert(0,'harness')
from boundary_model import chunks
B=json.load(open(sys.argv[1])); g=B["nvfp4_g7_check"]; pts=g["points"]; d7=12.0
def st(k0,b,c,p): return d7+k0*c/2560+b*c*(p+c/2)
k0,b=98.8,4e-6
for it in range(50):
    X=[];y=[]
    for m in pts[:2]:
        k,p=max(chunks(m["L"],2560),key=lambda kp: st(k0,b,*kp))
        X.append([k/2560,k*(p+k/2)]); y.append(m["gap_ms"]-d7)
    k0,b=np.linalg.solve(np.array(X),np.array(y))
print("consistent fit k0",round(k0,2),"b",b)
o7=pts[0]["ttft_ms"]-sum(st(k0,b,k,p) for k,p in chunks(4096,2560))
for m in pts:
    gp=max(st(k0,b,k,p) for k,p in chunks(m["L"],2560)); tt=o7+sum(st(k0,b,k,p) for k,p in chunks(m["L"],2560))
    print(m["L"],"gap meas/model",m["gap_ms"],round(gp,1),f"{(gp/m['gap_ms']-1)*100:+.1f}%","TTFT meas/model",m["ttft_ms"],round(tt),f"{(tt/m['ttft_ms']-1)*100:+.1f}%")
print("original script:")
for m in pts: print(m["L"],m["gap_ms"],m["gap_model_ms"],f"{(m['gap_model_ms']/m['gap_ms']-1)*100:+.1f}%",m["ttft_ms"],m["ttft_model_ms"],f"{(m['ttft_model_ms']/m['ttft_ms']-1)*100:+.1f}%")
