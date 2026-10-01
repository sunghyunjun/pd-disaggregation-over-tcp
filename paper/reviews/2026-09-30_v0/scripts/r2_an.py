import json, glob, os, csv, random, statistics as st, sys
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), *(['..']*3)))  # repo root
rows={r['run_id']:r for r in csv.DictReader(open('results/safe_runs.csv'))}
where={os.path.basename(os.path.dirname(p)):p for p in glob.glob('results/*/*/bench.json')}
def runs(stage_set,cfg,wl,rate,inlen=None):
    out=[]
    for rid,r in rows.items():
        if r['safety']=='제외': continue
        if r['stage'] in stage_set and r['config']==cfg and r['workload']==wl and r['rate']==rate and r['network']=='N0':
            if inlen and r['input_len_median']!=inlen: continue
            out.append(rid)
    return sorted(out)
def load(rid): return json.load(open(where[rid]))
def per_req(b,T=1.0,B=0.05):
    res=[]
    for i,(s,t,itl,e) in enumerate(zip(b['start_times'],b['ttfts'],b['itls'],b.get('errors',['']*len(b['ttfts'])))):
        if not itl: res.append(dict(i=i,ok=False,s=s,t=t,mx=None,itl=[])); continue
        srt=sorted(itl,reverse=True)
        mx=srt[0]; mx2=srt[1] if len(srt)>1 else 0
        res.append(dict(i=i,s=s,t=t,mx=mx,mx2=mx2,n=len(itl),itl=itl,err=bool(e),
            ok=(not e) and t<=T and mx<=B, ok_ttft=(t<=T), ok_gap=mx<=B, ok2=(not e) and t<=T and mx2<=B))
    return res
def boot(oks,n=2000,block=None,seed=0):
    rnd=random.Random(seed); N=len(oks); vals=[]
    if block:
        blocks=[oks[i:i+block] for i in range(0,N,block)]
        for _ in range(n):
            s=[];
            while len(s)<N: s+=rnd.choice(blocks)
            vals.append(sum(s[:N])/N)
    else:
        for _ in range(n): vals.append(sum(rnd.choice(oks) for _ in range(N))/N)
    vals.sort(); return vals[int(.025*n)],vals[int(.975*n)]
