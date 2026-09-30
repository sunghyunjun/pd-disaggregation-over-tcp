#!/usr/bin/env python3
"""R3 round-3: Eq.(1) check on chat runs from logged input lengths.
Coefficients from HF config.json (FP8 KV): 26B sliding 25x8x256x2 B = 100 KiB, global 5x2x512x2 B = 10 KiB, W = 1024;
31B sliding 50x16x256x2 = 400 KiB, global 10x4x512x2 = 40 KiB. Block rounding: 16-token sliding blocks, 32-token global blocks
(inferred from 2,240 = 5*128 + 25*64 descriptors at 4K). Predicts mean volume, unmerged descriptor count, NIXL split share (>=1024 desc)."""
import json, glob, math, statistics as st
R = "<repo>/results/"
cases = [("E7/*_E7_26_1P1D_N0_sharegpt_r16", 10, 100, 5, 25), ("E5/*_E5_26_1P1D_N0_sharegpt_r*", 10, 100, 5, 25),
         ("E7/*_E7_26F_1P1D_N0_sharegpt_r16", 20, 200, 5, 25),
         ("E8/*31_1P1D_aio_N0_sharegpt_r8", 40, 400, 10, 50), ("E9/*31_1P1D_aio_N0_sharegpt_r*", 40, 400, 10, 50)]
for pat, bg, bw, ng, nw in cases:
    for f in sorted(glob.glob(R + pat + "/result.json")):
        L = json.load(open(f))["bench"]["input_lens"]
        V = [(bg * 32 * math.ceil(l / 32) + bw * 16 * math.ceil(min(l, 1024) / 16)) / 1024 for l in L]
        D = [ng * math.ceil(l / 32) + nw * math.ceil(min(l, 1024) / 16) for l in L]
        sp = [v for v, d in zip(V, D) if d >= 1024]
        lmin = min([l for l, d in zip(L, D) if d >= 1024], default=None)
        print(f"{f.split('/')[-2][:52]:52s} n {len(L)} L mean {st.mean(L):.0f} med {st.median(L):.0f} max {max(L)} | "
              f"pred MiB {st.mean(V):.1f} desc {st.mean(D):.0f} | split(>=1024 desc) {100*len(sp)/len(V):.1f}% of xfers, {100*sum(sp)/sum(V):.1f}% of bytes, from L={lmin}")
