#!/usr/bin/env python3
"""R3 round-2: classify single-transfer bursts by number of pieces (connections >1 MiB) and which connection."""
import sys, collections
sys.path.insert(0, "<scratch>/reviews_v1")
import importlib.util
spec = importlib.util.spec_from_file_location("b", sys.path[0] + "/r3_ss_bursts.py"); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
import io, contextlib
for p, unit in [(a, float(u)) for a, u in zip(sys.argv[1::2], sys.argv[2::2])]:
    with contextlib.redirect_stdout(io.StringIO()):
        bursts, S = b.analyze(p)
    tot = collections.Counter(); keyrank = collections.Counter()
    for x in bursts:
        for k, v in x["bytes"].items(): keyrank[k] += v
    order = [k for k, _ in keyrank.most_common()]
    fifth = order[4] if len(order) > 4 else None
    single = [x for x in bursts if abs(sum(x["bytes"].values()) / 2**20 - unit) < 0.05 * unit]
    multi = [x for x in bursts if sum(x["bytes"].values()) / 2**20 > 1.5 * unit]
    pieces = collections.Counter(); on5 = 0; biggest = []
    for x in single:
        used = [k for k, v in x["bytes"].items() if v > 2**20]
        pieces[len(used)] += 1
        if fifth in used: on5 += 1
        biggest.append(max(x["bytes"].values()) / 2**20)
    import statistics as st
    print(f"{p.split('/')[-1]}: bursts {len(bursts)}, single-transfer {len(single)}, multi-transfer {len(multi)}")
    print(f"   pieces per single transfer: {dict(sorted(pieces.items()))}; single transfers touching 5th conn: {on5}")
    print(f"   largest piece MiB: median {st.median(biggest):.1f}, p10 {sorted(biggest)[len(biggest)//10]:.1f}, p90 {sorted(biggest)[9*len(biggest)//10]:.1f}; share of volume in largest piece median {100*st.median(biggest)/unit:.0f}%")
