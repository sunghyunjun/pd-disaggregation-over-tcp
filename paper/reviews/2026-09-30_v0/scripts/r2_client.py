from r2_an import *
import bisect
def analyze(rid, B=0.05):
    b=load(rid)
    big=[];  tiny_after=0; nbig=0; all_itl=0; tiny_all=0
    for i,(s,t,l) in enumerate(zip(b['start_times'],b['ttfts'],b['itls'])):
        tt=s+t
        for k,g in enumerate(l):
            all_itl+=1; tiny_all+= g<0.001
            tt+=g
            if g>B:
                nbig+=1
                if k+1<len(l) and l[k+1]<0.002: tiny_after+=1
                big.append((tt-g,tt,i))
    # coincidence: for each big gap, count other requests' big gaps overlapping
    big.sort()
    same=diff=0; ev_with_cross=0
    for a,(s1,e1,i1) in enumerate(big):
        cross=False
        for c in range(a+1,len(big)):
            s2,e2,i2=big[c]
            if s2>e1: break
            if i2==i1: continue
            if (i1-i2)%2==0: same+=1
            else: diff+=1; cross=True
    return dict(nbig=nbig, frac_tiny_after=round(tiny_after/max(1,nbig),3), tiny_all=round(tiny_all/max(1,all_itl),4), overlap_same=same, overlap_diff=diff)
import sys
for stg,cfg,wl,rate,inl in [(('E7',),'26_B2','random','2','4096'),(('E7',),'26_B2','random','4','4096'),(('E7',),'31_B2','sharegpt','2',None),(('E7',),'26_B2','sharegpt','16',None),(('E7',),'26H_B2','sharegpt','16',None),(('E7',),'26H_1P1D','sharegpt','16',None),(('E7',),'31_1P1D','sharegpt','8',None),(('E7',),'26_1P1D','random','8','4096'),(('E7',),'26_2P1D','random','9','4096'),(('E2',),'P1tuned','sharegpt','16',None)]:
    for rid in runs(stg,cfg,wl,rate,inl)[:2]:
        print(cfg,wl[:5],rate,rows[rid]['stage'],analyze(rid))
