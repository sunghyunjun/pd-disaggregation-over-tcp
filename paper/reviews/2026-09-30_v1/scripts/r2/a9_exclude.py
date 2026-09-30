import sys; sys.path.insert(0,'<scratch>/reviews_v1/r2')
from lib import *
def clusters(rid,thr=0.05,win=0.005):
    b=load(rid); st,T,I=b['start_times'],b['ttfts'],b['itls']
    ev=[];tok={}
    for i,(s,t,l) in enumerate(zip(st,T,I)):
        tt=s+t; ts=[tt]
        for g in l:
            tt+=g; ts.append(tt)
            if g>thr: ev.append((tt,i,g,len(ts)-1))
        tok[i]=ts
    ev.sort(); cl=[]
    for e in ev:
        if cl and e[0]-cl[-1][-1][0]<win: cl[-1].append(e)
        else: cl.append([e])
    out=[]
    for c in cl:
        nxt=[tok[i][k+1]-tok[i][k] for (_,i,_,k) in c if k+1<len(tok[i])]
        burst=sum(1 for x in nxt if x<0.002)/max(1,len(nxt))
        out.append(dict(reqs={x[1] for x in c},glob=len({x[1] for x in c})>=15,burst=burst))
    return out
def att_excl(rid,kind):
    b=load(rid); T,I=b['ttfts'],b['itls']; E=b.get('errors') or ['']*len(T)
    cl=clusters(rid)
    ex=[c for c in cl if c['glob'] and (kind=='all' or (kind=='gc' and c['burst']>=0.5))]
    exreq=set().union(*[c['reqs'] for c in ex]) if ex else set()
    other=set().union(*[c['reqs'] for c in cl if c not in ex]) if cl else set()
    okk=0
    for i,(t,l,e) in enumerate(zip(T,I,E)):
        base=(not e) and t<=1 and ((not l) or max(l)<=0.05)
        if base or ((not e) and t<=1 and l and i in exreq and i not in other): okk+=1
    return okk/len(T), len(ex)
for st,cfg,wl,rate in [(('E8',),'26_1P1D_toyi','random',8),(('E8',),'26_1P1D_aio','random',8),(('E5','E7'),'26_1P1D','random',8),(('E5','E7'),'26_2P1D','random',9),(('E5','E7'),'26_1P2D','random',9),(('E8',),'31_1P1D_aio','sharegpt',8),(('E5','E7'),'31_1P1D','sharegpt',8)]:
    for rid in runs(st,cfg,wl,rate):
        a=att(rid); g,ng=att_excl(rid,'gc'); al,na=att_excl(rid,'all')
        print(f"{rid[:17]} {cfg:13} r{rate}: att={a:.3f}  excl GC-type(burst) events({ng})={g:.3f}  excl all global({na})={al:.3f}")
