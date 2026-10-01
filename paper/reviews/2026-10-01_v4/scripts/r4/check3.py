import json, sys
sys.path.insert(0,'harness')
from boundary_model import chunks
B=json.load(open(sys.argv[1])); g=B["nvfp4_g7_check"]; print({k:v for k,v in g.items() if k!='points'})
d7=g["d"]; k0=g["k0"]; b7=g["b"]
for m in g["points"]:
    L=m["L"]; ch=chunks(L,2560)
    sel=max(ch,key=lambda kp: kp[0]*(kp[1]+kp[0]/2))
    fitrow=d7+k0+b7*sel[0]*(sel[1]+sel[0]/2)
    evals=[(k,p,d7+k0*k/2560+b7*k*(p+k/2)) for k,p in ch]
    best=max(evals,key=lambda x:x[2])
    print(L,"meas",m["gap_ms"],"fit-row value (k0 unscaled, chunk",sel,")",round(fitrow,1),"| eval max",best[:2],round(best[2],1))
# b-scale needed at 32K
L=32000; ch=chunks(L,2560)
for s in (1.0,0.9,0.85,0.8):
    v=max(d7+k0*k/2560+b7*s*k*(p+k/2) for k,p in ch); print("b scale",s,"32K gap",round(v,1))
# g7e model: 16K gap with b*0.85 and how fit points move
P=B["fp8_g7e"]["params"]
def gap(L,c,s=1.0): return max(P["d"]+P["e"]+P["a"]*k+P["b"]*s*k*(p+k/2) for k,p in chunks(L,c))
for L,c in ((4096,2560),(4096,1024),(4096,512),(16384,2560)):
    print("g7e",L,c,round(gap(L,c),1),"b*0.85:",round(gap(L,c,0.85),1))
