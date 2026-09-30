import sys; sys.path.insert(0,'harness')
import slo_sensitivity as ss
cache=ss.load_cache('safe_runs.csv')
res=ss.sensitivity(cache)
rows=[("top",lambda lab:(not lab.startswith("Replicas")) or ("c2560" in lab) or lab=="Replicas (3)"),("bottom",lambda lab:True)]
for key in ("26b_4k_tuned","26f_4k_tuned","31b_chat_tuned"):
    g=res[key]
    print(key, list(g["members"].keys()))
    for rn,keep in rows:
        sub={"members":{k:v for k,v in g["members"].items() if keep(k)}}
        rep,pd=ss.best_of(sub,False),ss.best_of(sub,True)
        both=one=0; cells=[]
        for i,T in enumerate(ss.T_GRID):
            for j,B in enumerate(ss.B_GRID):
                k=ss.classify(rep[i][j],pd[i][j])
                if k=="unknown":
                    (a,ca),(b,cb)=rep[i][j],pd[i][j]
                    if ca and cb: both+=1
                    else: one+=1; cells.append((T,B,round(a,1),ca,round(b,1),cb,round(b/a,2)))
        print(' ',rn,'hatched both-censored',both,'one-side',one, cells[:20])
# strict cell capacities
i1=ss.T_GRID.index(1.0)
for key in ("26b_4k_tuned","26f_4k_tuned","31b_chat_tuned"):
    for lab,m in res[key]["members"].items():
        print(key,lab,'cap@1s/30,40,50:',[round(m["capacity"][i1][j],1) for j in range(3)],[m["censored"][i1][j] for j in range(3)])
