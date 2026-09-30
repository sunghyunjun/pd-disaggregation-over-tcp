from lib import *
def events(rid, thr=0.05, win=0.005, minreq=15):
    b=load(rid); st,T,I=b['start_times'],b['ttfts'],b['itls']
    ev=[]; tok={}
    for i,(s,t,l) in enumerate(zip(st,T,I)):
        tt=s+t; ts=[tt]
        for g in l:
            tt+=g; ts.append(tt)
            if g>thr: ev.append((tt,i,g))
        tok[i]=ts
    ev.sort(); cl=[]
    for e in ev:
        if cl and e[0]-cl[-1][-1][0]<win: cl[-1].append(e)
        else: cl.append([e])
    glob=[c for c in cl if len({x[1] for x in c})>=minreq]
    out=[]
    for c in glob:
        reqs_={x[1] for x in c}; t0=c[0][0]
        # burst after: for each stalled request, the next gap after the stall
        nxt=[]
        for (tt,i,g) in c:
            ts=tok[i]; k=[j for j in range(len(ts)) if abs(ts[j]-tt)<1e-9]
            if k and k[0]+1<len(ts): nxt.append(ts[k[0]+1]-ts[k[0]])
        sub2=sum(1 for x in nxt if x<0.002)/max(1,len(nxt))
        out.append(dict(t=t0-min(st),tabs=t0,n=len(reqs_),gmax=max(x[2] for x in c)*1000,gmed=q([x[2] for x in c],.5)*1000,sub2=sub2))
    return out, min(st), max(st)
def trace(path):
    return [json.loads(l) for l in open(path)]
import sys
TR={k:trace(f'results/E8/proxy_trace_E8_{k}.jsonl') for k in ['26_1P1D_toyi','26_1P1D_aio','31_1P1D_aio']}
def near(tr,t,kinds,w=0.1):
    return [(x['k'],x.get('gen'),round(x['ms'],1),round(x['t']-t,3)) for x in tr if x['k'] in kinds and abs(x['t']-t)<w and (x['k']!='gc' or x.get('gen')==2)]
def upstream(tr,t,w=0.15):
    g=[x for x in tr if x['k']=='gap' and abs(x['t']-t)<w and x['ms']>50]
    return len({x['rid'] for x in g}), (max(x['ms'] for x in g) if g else None)
for key,cfg,wl,rate in [('26_1P1D_toyi','26_1P1D_toyi','random',8),('26_1P1D_toyi','26_1P1D_toyi','random',6),('26_1P1D_aio','26_1P1D_aio','random',8),('26_1P1D_aio','26_1P1D_aio','random',6),('31_1P1D_aio','31_1P1D_aio','sharegpt',8)]:
    tr=TR[key]
    for rid in runs(('E8',),cfg,wl,rate):
        ev,t0,t1=events(rid)
        gc2=[x for x in tr if x['k']=='gc' and x.get('gen')==2 and t0<=x['t']<=t1+60]
        lags=[x for x in tr if x['k']=='lag' and t0<=x['t']<=t1+60]
        print(f"{rid[:17]} {cfg} r{rate} seed? att={att(rid):.3f} events={len(ev)} gen2GC={[(round(x['t']-t0,1),x['ms']) for x in gc2]} lags={[(round(x['t']-t0,1),x['ms']) for x in lags]}")
        for e in ev:
            print(f"    t={e['t']:.2f}s n={e['n']} gap max/med={e['gmax']:.0f}/{e['gmed']:.0f}ms burst<2ms={e['sub2']:.2f} proxy={near(tr,e['tabs'],('gc','lag'))} upstream>50ms(reqs,max)={upstream(tr,e['tabs'])}")
