import json, glob, os, csv, random
REPO='<repo>'
os.chdir(REPO)
ROWS={r['run_id']:r for r in csv.DictReader(open('results/safe_runs.csv'))}
WHERE={os.path.basename(os.path.dirname(p)):p for p in glob.glob('results/*/*/bench.json')}
_cache={}
def runs(stages,cfg,wl,rate=None,inlen=None,safe=('안전',)):
    out=[]
    for rid,r in ROWS.items():
        if r['safety'] not in safe: continue
        if r['stage'] in stages and r['config']==cfg and r['workload']==wl and r['network']=='N0':
            if rate is not None and float(r['rate'])!=float(rate): continue
            if inlen and r['input_len_median']!=inlen: continue
            out.append(rid)
    return sorted(out)
def load(rid):
    if rid not in _cache: _cache[rid]=json.load(open(WHERE[rid]))
    return _cache[rid]
def reqs(rid):
    b=load(rid); E=b.get('errors') or ['']*len(b['ttfts'])
    out=[]
    for i,(s,t,l,e,ol,il) in enumerate(zip(b['start_times'],b['ttfts'],b['itls'],E,b['output_lens'],b['input_lens'])):
        out.append(dict(i=i,s=s,t=t,itl=l,mx=(max(l) if l else None),err=bool(e),ol=ol,il=il))
    return out
def ok(r,T=1.0,B=0.05,fix=True):
    if r['err'] or r['t']>T: return False
    if r['mx'] is None: return fix
    return r['mx']<=B
def att(rid,T=1.0,B=0.05,fix=True):
    R=reqs(rid); return sum(ok(r,T,B,fix) for r in R)/len(R)
def blocks_by_time(R,nb=20):
    R=sorted(R,key=lambda r:r['s']); N=len(R); 
    return [R[k*N//nb:(k+1)*N//nb] for k in range(nb)]
def block_boot(rid,T=1.0,B=0.05,nb=20,n=4000,seed=1):
    R=reqs(rid); bl=blocks_by_time(R,nb); rnd=random.Random(seed)
    bo=[(sum(ok(r,T,B) for r in b),len(b)) for b in bl]
    vals=[]
    for _ in range(n):
        s=[rnd.choice(bo) for _ in range(nb)]
        vals.append(sum(x for x,_ in s)/sum(y for _,y in s))
    vals.sort(); return vals[int(.025*n)], vals[int(.975*n)-1]
def hier_boot(rids,T=1.0,B=0.05,nb=20,n=4000,seed=2):
    """resample runs, then time blocks within each run: mean attainment over repeats"""
    rnd=random.Random(seed)
    per=[[(sum(ok(r,T,B) for r in b),len(b)) for b in blocks_by_time(reqs(x),nb)] for x in rids]
    vals=[]
    for _ in range(n):
        tot=0;cnt=0
        for _ in rids:
            bo=rnd.choice(per)
            s=[rnd.choice(bo) for _ in range(nb)]
            tot+=sum(x for x,_ in s); cnt+=sum(y for _,y in s)
        vals.append(tot/cnt)
    vals.sort(); return vals[int(.025*n)], vals[int(.975*n)-1]
def q(a,p):
    a=sorted(a); k=(len(a)-1)*p; lo=int(k); hi=min(lo+1,len(a)-1); return a[lo]+(a[hi]-a[lo])*(k-lo)
