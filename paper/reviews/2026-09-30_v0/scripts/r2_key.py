from r2_an import *
pts=[(('E5','E7'),'26_B2','random','1','4096'),(('E5','E7'),'26_B2','random','2','4096'),(('E5','E7'),'26_B2','random','4','4096'),
     (('E5','E7'),'26_B3','random','3','4096'),(('E5','E7'),'26_B3','random','6','4096'),
     (('E5','E7'),'26_1P1D','random','4','4096'),(('E5','E7'),'26_1P1D','random','6','4096'),(('E5','E7'),'26_1P1D','random','8','4096'),
     (('E5','E7'),'26_1P2D','random','6','4096'),(('E5','E7'),'26_1P2D','random','9','4096'),(('E5','E7'),'26_2P1D','random','9','4096'),
     (('E5','E7'),'31_B2','sharegpt','2',None),(('E5','E7'),'31_1P1D','sharegpt','2',None),(('E5','E7'),'31_1P1D','sharegpt','4',None),(('E5','E7'),'31_1P1D','sharegpt','8',None),
     (('E5','E6','E7'),'31_1P1D','random','0.25','4096'),(('E5','E7'),'31_2P1D','random','0.75','4096'),
     (('E5','E7'),'26_B2','sharegpt','16',None),(('E5','E7'),'26_1P1D','sharegpt','16',None),
     (('E2',),'B2','sharegpt','16',None),(('E2',),'P1tuned','sharegpt','16',None),(('E2',),'B2','sharegpt','24',None)]
for stg,cfg,wl,rate,inl in pts:
    for rid in runs(stg,cfg,wl,rate,inl):
        b=load(rid); R=per_req(b)
        oks=[r['ok'] for r in R]; N=len(oks); a=sum(oks)/N
        lo,hi=boot(oks,1000); blo,bhi=boot(oks,1000,block=max(10,N//20))
        f_t=sum(1 for r in R if r['t']>1)/N; f_g=sum(1 for r in R if r.get('ok_gap') is False)/N
        a2=sum(r.get('ok2',False) for r in R)/N
        h=N//2; a1=sum(oks[:h])/h; a2h=sum(oks[h:])/(N-h)
        # attainment at 55ms and 45ms
        a55=sum(1 for r in R if r['mx'] and r['t']<=1 and r['mx']<=0.055)/N; a45=sum(1 for r in R if r['mx'] and r['t']<=1 and r['mx']<=0.045)/N
        print(f"{cfg:8}{wl[:5]:6}{rate:>5} {rows[rid]['stage']} N={N:5} att={a:.3f} iid[{lo:.2f},{hi:.2f}] blk[{blo:.2f},{bhi:.2f}] failTTFT={f_t:.3f} failGap={f_g:.3f} 2ndmax={a2:.3f} 45ms={a45:.3f} 55ms={a55:.3f} halves={a1:.2f}/{a2h:.2f}")
