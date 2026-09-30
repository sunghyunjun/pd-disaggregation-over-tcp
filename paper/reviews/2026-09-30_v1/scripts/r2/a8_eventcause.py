import sys; sys.path.insert(0,'<scratch>/reviews_v1/r2')
from lib import *
import io,contextlib
with contextlib.redirect_stdout(io.StringIO()):
    from a4_stall import events
for rid in runs(('E8',),'26_1P1D_aio','random',8)[2:]+runs(('E8',),'26_1P1D_toyi','random',8)[2:]+runs(('E8',),'31_1P1D_aio','sharegpt',8):
    b=load(rid); S=b['start_times']; t0=min(S); T=b['ttfts']; I=b['input_lens']
    ev,_,_=events(rid); dur=max(S)-t0
    for e in ev:
        te=e['t']
        arr=[s for s in S if te-3<=s-t0<=te]
        ft=[1 for s,t in zip(S,T) if te-1.0<=s+t-t0<=te]
        # max 1-s count of first tokens anywhere in run, for reference
        fts=sorted(s+t-t0 for s,t in zip(S,T)); import bisect
        mx1=max(bisect.bisect_right(fts,x+1.0)-bisect.bisect_left(fts,x) for x in fts)
        print(f"{rid[:17]} {ROWS[rid]['config']:13} t={te:6.1f}s n={e['n']:3}: arrivals prior 3s={len(arr):2} (run mean {len(S)/dur*3:4.1f}), first tokens prior 1s={len(ft):2} (mean {len(S)/dur:4.1f}, run max {mx1})")
