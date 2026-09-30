import json, glob, os, statistics as st
R="<repo>/results/E8"
def conc(starts, lat):
    ev=[]
    for s,l in zip(starts,lat):
        ev.append((s,1)); ev.append((s+l,-1))
    ev.sort(); c=m=0
    for _,d in ev:
        c+=d; m=max(m,c)
    return m
print(f"{'run':44s} n   att  ttF  gapF bothF  ttft50 ttft90 ttft99 gap50 tpot  e2e  maxC  seed")
for d in sorted(glob.glob(R+"/2026-*")):
    b=json.load(open(d+"/bench.json"))
    n=len(b['ttfts']); T=1.0; B=0.050
    tf=gf=bf=ok=0
    mg=[]; tp=[]
    for t,it,e,ol in zip(b['ttfts'],b['itls'],b.get('errors',['']*n),b['output_lens']):
        m=max(it) if it else 0; mg.append(m)
        if it: tp.append(sum(it)/len(it))
        a = t>T; g = m>B
        if e: continue
        if a and g: bf+=1
        elif a: tf+=1
        elif g: gf+=1
        else: ok+=1
    tt=sorted(b['ttfts'])
    q=lambda xs,p: xs[int(p*(len(xs)-1))]
    lab=os.path.basename(d)[18:]
    seed=None
    try:
        log=open(d+"/bench.log").read(); i=log.find("seed="); seed=log[i+5:i+9]
    except: pass
    print(f"{lab:44s}{n:5d} {ok/n:.3f} {tf:4d} {gf:4d} {bf:4d} {q(tt,.5)*1e3:6.0f} {q(tt,.9)*1e3:6.0f} {q(tt,.99)*1e3:6.0f} {st.median(mg)*1e3:5.1f} {st.mean(tp)*1e3:5.1f} {st.mean(b['latencies']):5.1f} {b.get('max_concurrent_requests')!s:>4} {conc(b['start_times'],b['latencies']):4d} {seed}")
