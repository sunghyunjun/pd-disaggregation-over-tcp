# Per-run server-side view for E9: running/waiting/steps/tokens-per-step/ITL per node+port
import json, glob, datetime, collections, sys
R='results/E9'
series=collections.defaultdict(list)  # (node,port,metric)->[(t,v)]
for f in glob.glob(R+'/collect/*/*prom.tsv'):
    node=f.split('/')[-2].split('-')[-1]
    for line in open(f):
        p=line.rstrip('\n').split('\t')
        if len(p)<4: continue
        t,port,m,v=int(p[0]),p[1],p[2],p[3]
        if m in ('vllm:num_requests_running','vllm:num_requests_waiting','vllm:iteration_tokens_total_sum','vllm:iteration_tokens_total_count','vllm:inter_token_latency_seconds_sum','vllm:inter_token_latency_seconds_count','vllm:kv_cache_usage_perc','vllm:num_preemptions_total','vllm:prompt_tokens_total','vllm:generation_tokens_total'):
            try: series[(node,port,m)].append((t,float(v)))
            except: pass
def win(key,t0,t1):
    return [(t,v) for t,v in series.get(key,[]) if t0<=t<=t1]
for f in sorted(glob.glob(R+'/2026-*/result.json')):
    d=json.load(open(f)); b=d['bench']; meta=d['meta']
    end=datetime.datetime.strptime(b['date'],'%Y%m%d-%H%M%S').replace(tzinfo=datetime.timezone.utc).timestamp()
    t0=end-b['duration']+20; t1=end-10
    print(f"== {meta['config']} r{meta['rate']} seed {meta['seed']}")
    for node in ('93','188'):
        for port in ('8100','8200'):
            run=win((node,port,'vllm:num_requests_running'),t0,t1)
            if not run or max(v for _,v in run)==0: continue
            wt=win((node,port,'vllm:num_requests_waiting'),t0,t1)
            def delta(m):
                s=win((node,port,m),t0,t1)
                return (s[-1][1]-s[0][1], s[-1][0]-s[0][0]) if len(s)>1 else (0,1)
            ts,dt=delta('vllm:iteration_tokens_total_sum'); tc,_=delta('vllm:iteration_tokens_total_count')
            isum,_=delta('vllm:inter_token_latency_seconds_sum'); icnt,_=delta('vllm:inter_token_latency_seconds_count')
            pt,_=delta('vllm:prompt_tokens_total'); gt,_=delta('vllm:generation_tokens_total')
            pre,_=delta('vllm:num_preemptions_total')
            kv=win((node,port,'vllm:kv_cache_usage_perc'),t0,t1)
            rv=[v for _,v in run]; wv=[v for _,v in wt]
            print(f"  {node}:{port} running mean {sum(rv)/len(rv):.0f} max {max(rv):.0f} | waiting mean {sum(wv)/len(wv):.1f} max {max(wv):.0f} | steps/s {tc/dt:.1f} tok/step {ts/max(tc,1):.0f} step_ms {1000*dt/max(tc,1):.1f} | ITL mean {1000*isum/max(icnt,1):.1f} ms | prompt tok/s {pt/dt:.0f} gen tok/s {gt/dt:.0f} | kv max {max(v for _,v in kv) if kv else 0:.2f} preempt {pre:.0f}")
