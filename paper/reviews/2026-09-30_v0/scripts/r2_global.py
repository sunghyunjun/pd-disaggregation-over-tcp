from r2_an import *
def events(b,B=0.05,win=0.005):
    ev=[]
    for i,(s,t,l) in enumerate(zip(b['start_times'],b['ttfts'],b['itls'])):
        tt=s+t
        for k,g in enumerate(l):
            tt+=g
            if g>B: ev.append((tt,i,g))
    ev.sort(); cl=[]
    for e in ev:
        if cl and e[0]-cl[-1][-1][0]<win: cl[-1].append(e)
        else: cl.append([e])
    return cl
def study(stg,cfg,wl,rate,inl=None,big=15):
    for rid in runs(stg,cfg,wl,rate,inl):
        b=load(rid); N=len(b['ttfts']); s0=b['start_times'][0]
        cl=events(b)
        glob_=[c for c in cl if len({x[1] for x in c})>=big]
        gl_req=set(x[1] for c in glob_ for x in c)
        # attainment if requests failing ONLY due to global-event gaps were counted as pass
        other_gap_fail=set()
        for c in cl:
            if c in glob_: continue
            for x in c: other_gap_fail.add(x[1])
        ok=0; ok_cf=0
        for i,(t,l) in enumerate(zip(b['ttfts'],b['itls'])):
            p = t<=1 and bool(l) and max(l)<=0.05
            ok+=p
            ok_cf+= p or (t<=1 and bool(l) and i in gl_req and i not in other_gap_fail)
        print(f"{cfg:9}{wl[:5]:6}{rate:>5} {rows[rid]['stage']} att={ok/N:.3f}  global events={len(glob_)} at t={[round(c[0][0]-s0) for c in glob_]}s sizes={[len({x[1] for x in c}) for c in glob_]} gap ms={[round(max(x[2] for x in c)*1000) for c in glob_]}  att w/o global={ok_cf/N:.3f}  other stall instants={len(cl)-len(glob_)}")
for a in [(('E5','E7'),'26_1P1D','random','8','4096'),(('E5','E7'),'26_1P1D','random','4','4096'),(('E5','E7'),'26_1P2D','random','9','4096'),(('E5','E7'),'26_1P2D','random','6','4096'),(('E5','E7'),'26_2P1D','random','9','4096'),(('E5','E7'),'31_1P1D','sharegpt','8',None),(('E5','E7'),'31_1P1D','sharegpt','2',None),(('E5','E7'),'26_1P1D','sharegpt','16',None),(('E2',),'P1tuned','sharegpt','16',None),(('E5','E7'),'26_B2','random','2','4096'),(('E5','E7'),'26_B3','random','3','4096'),(('E5','E7'),'26_B2','sharegpt','16',None),(('E5','E7'),'31_B2','sharegpt','2',None)]:
    study(*a)
