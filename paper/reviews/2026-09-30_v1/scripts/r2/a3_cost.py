from lib import *
def gp(rid,T=1.0,B=0.05):
    b=load(rid); R=reqs(rid)
    return sum(r['ol'] for r in R if ok(r,T,B))/b['duration']
def cost(g_per_gpu): return 3.363/(g_per_gpu*3600/1e6)
def seed_of(rid):
    try:
        m=json.load(open(os.path.join(os.path.dirname(WHERE[rid]),'result.json')))
        return m.get('seed') or m.get('meta',{}).get('seed')
    except Exception as e: return None
for lab,st,cfg,wl,rt in [('c1024@4',('E8',),'26_B2_c1024','random',8),('aio@3',('E8',),'26_1P1D_aio','random',6),('aio@4',('E8',),'26_1P1D_aio','random',8),
                         ('toyi@4',('E8',),'26_1P1D_toyi','random',8),('toy E7@3',('E5','E7'),'26_1P1D','random',6),('c2560@1 E5E7',('E5','E7'),'26_B2','random',2),('c2560@1 E8',('E8',),'26_B2_c2560','random',2),
                         ('31 c256@6',('E8',),'31_B2_c256','sharegpt',12),('31 aio@4',('E8',),'31_1P1D_aio','sharegpt',8),('31 toy@2',('E5','E7'),'31_1P1D','sharegpt',4),('31 toy@4',('E5','E7'),'31_1P1D','sharegpt',8)]:
    for rid in runs(st,cfg,wl,rt,'4096' if wl=='random' else None):
        g=gp(rid)/2; b=load(rid)
        print(f"{lab:14} {rid[:17]} seed={seed_of(rid)} att={att(rid):.3f} dur={b['duration']:.0f}s goodput/GPU={g:.0f} tok/s cost=${cost(g):.2f} ttft_p50={q([r['t'] for r in reqs(rid)],.5)*1000:.0f}ms")
