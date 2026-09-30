from a4_stall import events
from lib import *
for st,cfg,wl,rate in [(('E8',),'26_B2_c1536','random',8),(('E8',),'26_B2_c2560','random',4),(('E8',),'26_B2_c1024','random',10),(('E8',),'26_B2_c1024','random',12),(('E8',),'26_B2_c1024','random',8),(('E5','E7'),'26_B2','random',4),(('E5','E7'),'26_B2','random',2),(('E5','E7'),'31_1P1D','sharegpt',8),(('E5','E7'),'31_B2','sharegpt',2)]:
    for rid in runs(st,cfg,wl,rate):
        ev,t0,t1=events(rid)
        if not ev: print(f"{rid[:17]} {cfg} r{rate} att={att(rid):.3f} events=0"); continue
        ns=[e['n'] for e in ev]; gm=[e['gmed'] for e in ev]; bu=[e['sub2'] for e in ev]
        print(f"{rid[:17]} {cfg} r{rate} att={att(rid):.3f} events={len(ev)} n med={q(ns,.5):.0f} range={min(ns)}-{max(ns)} gapmed range={min(gm):.0f}-{max(gm):.0f} burst mean={sum(bu)/len(bu):.2f}")
