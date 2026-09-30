import io,contextlib
with contextlib.redirect_stdout(io.StringIO()):
    from a4_stall import events
from lib import *
for st,cfg,wl,rate in [(('E5','E7'),'26_1P1D','random',8),(('E5','E7'),'26_1P1D','random',6),(('E5','E7'),'26_2P1D','random',9),(('E5','E7'),'26_1P2D','random',9),(('E5','E7'),'26_1P2D','random',6)]:
    for rid in runs(st,cfg,wl,rate):
        ev,t0,t1=events(rid)
        a=att(rid)
        print(f"{rid[:17]} {cfg} r{rate} att={a:.3f} events={len(ev)} "+'; '.join(f"t={e['t']:.0f} n={e['n']} g={e['gmed']:.0f} burst={e['sub2']:.2f}" for e in ev))
