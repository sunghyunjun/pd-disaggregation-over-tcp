import sys, os, json, gzip
sys.path.insert(0,'harness')
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), *(['..']*3)))  # repo root
import slo_sensitivity as ss
cache=ss.load_cache('results/safe_runs.csv')
def seedidx(r):  # not available in cache; use run id order within rate
    return None
RULES={}
def cap_paper(br,n,T,B): return ss.capacity(br,n,T,B)
def cap_mean(br,n,T,B):
    best,br_=0.0,None
    for rate,rs in br.items():
        if sum(ss.attain(r,T,B) for r in rs)/len(rs)>=0.9:
            g=sum(ss.goodput(r,T,B) for r in rs)/len(rs)/n
            if g>best: best,br_=g,rate
    return best,(br_ is not None and br_==max(br))
def run(capf,label,keys=('26b_4k_tuned','26f_4k_tuned','31b_chat_tuned'),cells=None):
    print('==',label)
    for key in keys:
        g=[x for x in ss.GROUPS if x[0]==key][0]
        mem={}
        for lab,st,cfg,wl,inl,n in g[2]:
            br=ss.runs_for(cache,st,cfg,wl,inl)
            if br: mem[lab]=(br,n)
        for T in [1.0,0.25,3.0]:
            row=[]
            for B in ss.B_GRID:
                caps={lab:capf(br,n,T,B) for lab,(br,n) in mem.items()}
                rep=[(v,lab) for lab,v in caps.items() if lab.startswith('Replicas')]
                pd=[(v,lab) for lab,v in caps.items() if not lab.startswith('Replicas')]
                (rv,rl)=max(rep,key=lambda x:x[0][0]); (pv,pl)=max(pd,key=lambda x:x[0][0])
                a=(rv[0],rv[0]>0 and any(v[1] for v,l in rep if v[0]==rv[0]))
                b=(pv[0],pv[0]>0 and any(v[1] for v,l in pd if v[0]==pv[0]))
                k=ss.classify(a,b)
                ratio=(b[0]/a[0]) if a[0]>0 else float('inf')
                row.append(f"{B}:{k}({ratio:.2f};R={rl.replace('Replicas ','')[:10]}{'*' if a[1] else ''}={rv[0]:.0f};P={pl[:10]}{'*' if b[1] else ''}={pv[0]:.0f})")
            print(key,'T=',T); print('   '+'\n   '.join(row))
run(cap_paper,'paper rule: every repeat >=0.9, min goodput')

print()
run(cap_mean,'mean-attainment rule (mean over repeats >=0.9, mean goodput)',keys=('26b_4k_tuned','31b_chat_tuned'))
