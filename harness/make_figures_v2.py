#!/usr/bin/env python3
"""영어 원고 v2 그림(v1 스크립트 복사 + 세션 E9: 청크 512, 프록시 상한 해제 재측정, P 청크 8,192).
원래 설명:
영어 원고 v1(청크 프리필 × 분리) 그림. 기존 make_figures.py의 스타일과 함수를 재사용하고 새 그림을 더한다.

사용:
  uv run --with matplotlib python3 harness/make_figures_v2.py [-o paper/figures_v2]

새 그림
  v1_chunk_stall   청크 크기별 요청별 최대 토큰 간격(26B 4K, 31B 대화, 26B FP8 4K; GPU당 1건 이하)
  v1_head_to_head  같은 GPU 수에서 청크 변형 복제본 대 1P1D의 달성률 곡선
  v1_transfer      (a) iperf 흐름 수, (b) UCX 설정별 KV 전송률, (c) 전송 중 동시에 움직인 TCP 연결 수
  v1_ttft          분리의 첫 토큰 추가 지연 분해
  v1_who_wins      SLO 격자별 우열: 청크 2560 복제본 대비(위) / 청크를 조정한 복제본 대비(아래)
  v1_proxy_gc      분리 구성의 전역 정지와 프록시 GC(toy 대 aiohttp)
나머지(부록)는 make_figures.py의 함수를 같은 CSV로 다시 그린다.
"""
import argparse, glob, json, os, re, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_figures as mf  # noqa: E402  (스타일·공통 함수)
import slo_sensitivity as ss  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

INK, INK2, GRID = mf.INK, mf.INK2, mf.GRID
S1, S2, S3, S4, S5 = mf.S1, mf.S2, mf.S3, mf.S4, mf.S5
META = {}
MIB = 1.048576  # vLLM의 "MB" = MiB


def save(fig, out, name, meta):
    fig.savefig(os.path.join(out, name + ".pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(out, name + ".svg"), bbox_inches="tight", transparent=True)
    plt.close(fig)
    META[name] = meta


def q(a, p):
    a = sorted(a)
    if not a:
        return float("nan")
    k = (len(a) - 1) * p; lo = int(k); hi = min(lo + 1, len(a) - 1)
    return a[lo] + (a[hi] - a[lo]) * (k - lo)


def runs(cache, stages, cfg, wl, rate=None, inlen=None):
    out = []
    for rid, r in cache.items():
        if r["stage"] in stages and r["config"] == cfg and r["workload"] == wl and r["network"] == "N0" and r["safety"] == "안전":
            if inlen and r["input_len_median"] != inlen:
                continue
            if rate is not None and float(r["rate"]) != float(rate):
                continue
            out.append((rid, r))
    return sorted(out)


# ---------------------------------------------------------------- chunk sets the stall
def fig_chunk(cache, out):
    panels = [
        ("(a) 26B NVFP4, 4K input", "random", "4096", 2.0,
         [("2560", ("E5", "E7", "E8"), ["26_B2", "26_B2_c2560"]), ("2048", ("E8",), ["26_B2_c2048"]),
          ("1536", ("E8",), ["26_B2_c1536"]), ("1024", ("E8",), ["26_B2_c1024"]), ("512", ("E9",), ["26_B2_c512"])]),
        ("(b) 26B FP8, 4K input", "random", "4096", 1.0,
         [("2560", ("E7",), ["26F_B2"]), ("1024", ("E8",), ["26F_B2_c1024"]), ("512", ("E9",), ["26F_B2_c512"])]),
        ("(c) 31B NVFP4, ShareGPT chat", "sharegpt", None, 2.0,
         [("2560", ("E5", "E7", "E8"), ["31_B2", "31_B2_c2560"]), ("512", ("E8",), ["31_B2_c512"]),
          ("256", ("E8",), ["31_B2_c256"])]),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.9), gridspec_kw={"width_ratios": [5, 3.1, 3.1], "wspace": 0.35})
    meta = {}
    for ax, (title, wl, inl, rate, items) in zip(axes, panels):
        for x, (lab, stages, cfgs) in enumerate(items):
            mx, tt, att = [], [], []
            for c in cfgs:
                for rid, r in runs(cache, stages, c, wl, rate, inl):
                    m = [v * 1000 for v in r["maxitl"] if v is not None]
                    mx += m; tt += [v * 1000 for v in r["ttft"]]
                    att.append(ss.attain(r, 1.0, 50))
            lo, p50, hi = q(mx, .1), q(mx, .5), q(mx, .9)
            col = S1 if p50 <= 50 else S5
            ax.vlines(x, lo, hi, color=col, lw=5, alpha=0.55)
            ax.plot([x], [p50], marker="o", color=col, ms=7, mec="white", mew=0.8)
            ax.text(x + 0.12, p50, f"{p50:.0f}", va="center", fontsize=7.3, color=INK)
            meta[f"{title}|{lab}"] = {"runs": len(att), "maxgap_p10_p50_p90_ms": [round(lo, 1), round(p50, 1), round(hi, 1)],
                                     "ttft_p50_ms": round(q(tt, .5)), "attain_1s_50ms": [round(a, 3) for a in att]}
        ax.axhline(50, color=INK2, lw=1, ls=(0, (4, 3))); ax.axhline(30, color=INK2, lw=0.8, ls=(0, (1, 2)))
        ax.set_xticks(range(len(items))); ax.set_xticklabels([i[0] for i in items])
        ax.set_xlim(-0.5, len(items) - 0.4); ax.set_ylim(0, 80)
        ax.set_title(title, fontsize=8.3)
    axes[0].set_ylabel("Per-request max gap (ms)")
    fig.supxlabel("Prefill chunk size (max tokens per step)", fontsize=8.5, y=-0.04)
    axes[0].text(-0.4, 51.5, "50 ms", fontsize=7, color=INK2); axes[0].text(-0.4, 31.5, "30 ms", fontsize=7, color=INK2)
    fig.suptitle("Replicas, 1 request/s per GPU (26B FP8: 0.5). Dot: median over requests; bar: 10th–90th percentile",
                 x=0.01, ha="left", fontsize=7.8, color=INK2, y=1.03)
    save(fig, out, "v1_chunk_stall", meta)


# ---------------------------------------------------------------- head to head
def series(ax, cache, stages, cfgs, wl, inl, gpus, color, marker, ls, label, lw=2.0, mfc=None):
    by = defaultdict(list)
    for c in cfgs:
        for rid, r in runs(cache, stages, c, wl, None, inl):
            by[float(r["rate"])].append(ss.attain(r, 1.0, 50))
    xs = sorted(by)
    if not xs:
        return None
    ys = [sum(by[x]) / len(by[x]) for x in xs]
    ax.plot([x / gpus for x in xs], ys, color=color, marker=marker, ls=ls, lw=lw, label=label,
            mfc=mfc or color, mec=color)
    ax.vlines([x / gpus for x in xs], [min(by[x]) for x in xs], [max(by[x]) for x in xs], color=color, lw=1.1)
    return {f"{x / gpus:g}": [round(v, 3) for v in by[x]] for x in xs}


def fig_h2h(cache, out):
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 3.0), sharey=True, gridspec_kw={"wspace": 0.12})
    meta = {}
    DASH, DOT, DD = (0, (5, 2.5)), (0, (1.5, 1.8)), (0, (6, 2, 1.5, 2))
    a, b, c = axes
    meta["26b_4k"] = {
        "Replicas chunk 2560": series(a, cache, ("E5", "E7", "E8"), ["26_B2", "26_B2_c2560"], "random", "4096", 2, S5, "o", DOT, "Replicas, chunk 2,560"),
        "Replicas chunk 1024": series(a, cache, ("E8", "E9"), ["26_B2_c1024"], "random", "4096", 2, S1, "o", "-", "Replicas, chunk 1,024"),
        "Replicas chunk 512": series(a, cache, ("E9",), ["26_B2_c512"], "random", "4096", 2, S1, "D", DD, "Replicas, chunk 512 (256 for 31B)", mfc="white"),
        "1P1D test proxy": series(a, cache, ("E5", "E7", "E8"), ["26_1P1D", "26_1P1D_toyi"], "random", "4096", 2, S3, "s", DASH, "1P1D, vLLM test proxy"),
        "1P1D aiohttp proxy": series(a, cache, ("E8",), ["26_1P1D_aio"], "random", "4096", 2, S2, "s", "-", "1P1D, aiohttp proxy"),
        "1P1D aiohttp, prefill chunk 8192": series(a, cache, ("E9",), ["26_1P1D_aio_p8192"], "random", "4096", 2, S4, "^", DD, "1P1D, aiohttp, prefill chunk 8,192"),
    }
    meta["26f_4k"] = {
        "Replicas chunk 2560": series(b, cache, ("E7",), ["26F_B2"], "random", "4096", 2, S5, "o", DOT, "Replicas, chunk 2,560"),
        "Replicas chunk 1024": series(b, cache, ("E8",), ["26F_B2_c1024"], "random", "4096", 2, S1, "o", "-", "Replicas, chunk 1,024"),
        "Replicas chunk 512": series(b, cache, ("E9",), ["26F_B2_c512"], "random", "4096", 2, S1, "D", DD, "Replicas, chunk 512 (256 for 31B)", mfc="white"),
        "1P1D test proxy": series(b, cache, ("E7",), ["26F_1P1D"], "random", "4096", 2, S3, "s", DASH, "1P1D, vLLM test proxy"),
    }
    meta["31b_chat"] = {
        "Replicas chunk 2560": series(c, cache, ("E5", "E7", "E8"), ["31_B2", "31_B2_c2560"], "sharegpt", None, 2, S5, "o", DOT, "Replicas, chunk 2,560"),
        "Replicas chunk 256": series(c, cache, ("E8", "E9"), ["31_B2_c256"], "sharegpt", None, 2, S1, "D", DD, "Replicas, chunk 512 (256 for 31B)", mfc="white"),
        "1P1D test proxy": series(c, cache, ("E5", "E7"), ["31_1P1D"], "sharegpt", None, 2, S3, "s", DASH, "1P1D, vLLM test proxy"),
        "1P1D aiohttp proxy": series(c, cache, ("E8", "E9"), ["31_1P1D_aio"], "sharegpt", None, 2, S2, "s", "-", "1P1D, aiohttp proxy"),
    }
    a.set_title("(a) 26B NVFP4, 4K input", fontsize=8.3); b.set_title("(b) 26B FP8, 4K input", fontsize=8.3)
    c.set_title("(c) 31B NVFP4, ShareGPT chat", fontsize=8.3)
    for ax in axes:
        mf.slo_line(ax); ax.set_ylim(-0.03, 1.05); ax.set_xlabel("Requests/s per GPU")
    a.set_ylabel("Strict-SLO attainment")
    b.set_xlim(0, 1.6)
    hs, ls_ = [], []
    for ax in axes:
        h, l = ax.get_legend_handles_labels()
        for hh, ll in zip(h, l):
            if ll not in ls_:
                hs.append(hh); ls_.append(ll)
    order = ["Replicas, chunk 2,560", "Replicas, chunk 1,024", "Replicas, chunk 512 (256 for 31B)",
             "1P1D, vLLM test proxy", "1P1D, aiohttp proxy", "1P1D, aiohttp, prefill chunk 8,192"]
    idx = [ls_.index(o) for o in order if o in ls_]
    fig.legend([hs[i] for i in idx], [ls_[i] for i in idx], loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=3, fontsize=7.3)
    fig.suptitle("Two g7e nodes in a placement group. Line: mean of repeats; vertical bar: min–max over repeats",
                 x=0.01, ha="left", fontsize=7.8, color=INK2, y=1.03)
    save(fig, out, "v1_head_to_head", meta)


# ---------------------------------------------------------------- transfer path
def xfer_stats(pattern):
    vals = []
    for f in glob.glob(pattern):
        for line in open(f, errors="replace"):
            m = re.search(r"Avg xfer time \(ms\)=([0-9.]+).*Avg MB per transfer=([0-9.]+)", line)
            if m and float(m.group(2)) > 100:
                t, mb = float(m.group(1)), float(m.group(2))
                vals.append(mb * MIB * 8 / t)   # Gbps (10^9 bit/s)
    return vals


def ss_active(path, thresh=64 * 1024):
    """ss_sample 출력에서 전송 중(한 연결이라도 움직인 샘플) 동시에 움직인 연결 수의 분포"""
    samples, cur, ts, key = [], {}, None, None
    rx = re.compile(r"^\S+\s+\d+\s+\d+\s+(\S+):(\d+)\s+(\S+):(\d+)")
    for line in open(path, errors="replace"):
        line = line.rstrip("\n")
        if line.startswith("# "):
            if ts is not None:
                samples.append(cur)
            ts, cur, key = float(line[2:]), {}, None
            continue
        m = rx.match(line.strip())
        if m:
            lp, rp = int(m.group(2)), int(m.group(4))
            key = None if (lp in (22, 5201, 5600) or rp in (22, 5201, 5600)) else (lp, rp)
            continue
        if key is not None:
            a = re.search(r"bytes_acked:(\d+)", line); r = re.search(r"bytes_received:(\d+)", line)
            cur[key] = (int(a.group(1)) if a else 0) + (int(r.group(1)) if r else 0)
    cnt = defaultdict(int)
    for s0, s1 in zip(samples, samples[1:]):
        n = sum(1 for k, v in s1.items() if v - s0.get(k, v) > thresh)
        if n:
            cnt[n] += 1
    tot = sum(cnt.values()) or 1
    return {k: cnt[k] / tot for k in range(1, 5)}


def fig_transfer(out, root="results/E8"):
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.7), gridspec_kw={"width_ratios": [1, 1.25, 1.2], "wspace": 0.42})
    a, b, c = axes
    flows = [1, 2, 4, 8]; gb = [9.54, 19.06, 38.11, 49.72]
    a.plot(flows, gb, color=S1, marker="o")
    a.axhline(50, color=INK2, lw=1, ls=(0, (4, 3)))
    a.text(1, 51.5, "instance 50 Gbps", fontsize=7, color=INK2)
    a.set_xticks(flows); a.set_ylim(0, 58); a.set_xlabel("Parallel TCP flows (iperf)"); a.set_ylabel("Gbps")
    a.set_title("(a) Bandwidth vs flows", fontsize=8.3)
    sets = [("UCX\ndefault", f"{root}/xfer_E8/26_1P1D_def_random_r0.5_n0_*.log"),
            ("Segment\n256 KB only", f"{root}/xfer_E8/26_1P1D_seg_random_r0.5_n0_*.log"),
            ("Seven UCX\nvariables", f"{root}/xfer_E8/26_1P1D_aio_random_r0.5_n0_*.log")]
    meta = {"iperf_flows_gbps": dict(zip(flows, gb)), "quoted_iperf": "RESULTS.md E4-0"}
    for i, (lab, pat) in enumerate(sets):
        v = xfer_stats(pat)
        b.scatter([i] * len(v), v, s=11, color=S2, alpha=0.6, edgecolors="none")
        if v:
            med = q(v, .5)
            b.plot([i - 0.25, i + 0.25], [med, med], color=INK, lw=1.6)
            b.text(i + 0.28, med, f"{med:.1f}", va="center", fontsize=7)
        meta["transfer_gbps|" + lab.replace("\n", " ")] = {"n_windows": len(v), "median": round(q(v, .5), 2),
                                                           "min": round(min(v), 2) if v else None, "max": round(max(v), 2) if v else None}
    b.axhline(9.54, color=S1, lw=1.2, ls=(0, (4, 3)))
    b.text(2.45, 9.9, "one flow\n9.54", fontsize=6.8, color=S1, ha="right", va="bottom")
    b.set_xticks(range(3)); b.set_xticklabels([s[0] for s in sets], fontsize=7); b.set_xlim(-0.5, 2.6)
    b.set_ylim(0, 19); b.set_ylabel("KV transfer rate (Gbps)")
    b.set_title("(b) 26B, 140 MiB per request", fontsize=8.3)
    d26 = ss_active(f"{root}/ss/ss_E8_26_1P1D_aio_random_r0.5_n0_P.txt")
    d31 = ss_active(f"{root}/ss/ss_E8_31_1P1D_ss_random_r0.25_n0_P.txt")
    w = 0.38
    c.bar([k - w / 2 for k in range(1, 5)], [d26[k] for k in range(1, 5)], w, color=S5, label="26B, 140 MiB")
    c.bar([k + w / 2 for k in range(1, 5)], [d31[k] for k in range(1, 5)], w, color=S2, label="31B, 560 MiB")
    c.set_xticks(range(1, 5)); c.set_xlabel("TCP connections moving data"); c.set_ylabel("Share of transfer time")
    c.set_title("(c) Four connections per P–D pair", fontsize=8.3); c.legend(loc="upper left", fontsize=7)
    meta["active_connections_share"] = {"26B": d26, "31B": d31}
    fig.suptitle("Two g7e nodes in a placement group, 4K input at low load (0.5 and 0.25 requests/s)", x=0.01, ha="left",
                 fontsize=7.8, color=INK2, y=1.03)
    save(fig, out, "v1_transfer", meta)


# ---------------------------------------------------------------- TTFT decomposition
def fig_ttft(out):
    items = [  # label, single, transfer, residual, predicted
        ("26B FP8 · 4K · 0.25 req/s/GPU", 158, 165, 28, None),
        ("26B NVFP4 · 4K · 0.5 req/s/GPU", 130, 84, 53, 235),
        ("31B NVFP4 · 4K · 0.125 req/s/GPU", 483, 283, 87, 820),
    ]
    fig, ax = plt.subplots(figsize=(6.2, 2.1))
    ys = list(range(len(items)))[::-1]
    for y, (lab, s, t, r, p) in zip(ys, items):
        ax.barh(y, s, color=mf.NEUTRAL, height=0.55)
        ax.barh(y, t, left=s, color=S2, height=0.55)
        ax.barh(y, r, left=s + t, color="#f4b79c", height=0.55)
        ax.text(s + t + r + 12, y, f"{s + t + r} ms  (transfer {100 * t / (t + r):.0f}% of added)", va="center", fontsize=7.2)
        if p:
            ax.plot([p, p], [y - 0.34, y + 0.34], color=INK, lw=1.6)
    ax.set_yticks(ys); ax.set_yticklabels([i[0] for i in items]); ax.set_xlim(0, 1150)
    ax.set_xlabel("TTFT p50 (ms)"); ax.grid(axis="y", visible=False)
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=mf.NEUTRAL), plt.Rectangle((0, 0), 1, 1, color=S2),
                       plt.Rectangle((0, 0), 1, 1, color="#f4b79c"), Line2D([0], [0], color=INK, lw=1.6)],
              labels=["Colocated TTFT", "KV transfer", "Residual", "Model estimate"],
              loc="upper left", bbox_to_anchor=(0, -0.3), ncol=4, fontsize=7.3)
    save(fig, out, "v1_ttft", {"quoted": "RESULTS.md E4-1 (row 1, two days joined), E5 formula check (rows 2-3)", "items": items})


# ---------------------------------------------------------------- who wins
def fig_who_wins(res, out):
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch
    cats = ["neither", "r_only", "r_better", "similar", "d_better", "d_only"]
    ccol = ["#f6f6f3", "#1d4f91", "#9dbde3", "#dddbd4", "#f0b48f", "#c8501e"]
    labels = {"d_only": "Only disaggregated meets the SLO", "d_better": "Disaggregated serves more (≥1.25×)",
              "similar": "Similar (0.8–1.25×)", "r_better": "Replicas serve more (≤0.8×)",
              "r_only": "Only replicas meet the SLO", "neither": "Neither meets the SLO",
              "unknown": "Cannot tell within measured rates"}
    cols = [("26b_4k_tuned", "26B NVFP4 · 4K"), ("26f_4k_tuned", "26B FP8 · 4K"), ("31b_chat_tuned", "31B NVFP4 · chat")]
    rows = [("Replicas at chunk 2560", lambda lab: (not lab.startswith("Replicas")) or ("c2560" in lab) or lab == "Replicas (3)"),
            ("Replicas at the best\nmeasured chunk", lambda lab: True)]
    fig, axes = plt.subplots(2, 3, figsize=(7.6, 5.6))
    j50, i1 = ss.B_GRID.index(50), ss.T_GRID.index(1.0)
    meta = {}
    for r, (rowname, keep) in enumerate(rows):
        for c, (key, title) in enumerate(cols):
            ax = axes[r][c]
            g = res[key]
            sub = {"members": {k: v for k, v in g["members"].items() if keep(k)}}
            rep, pd = ss.best_of(sub, False), ss.best_of(sub, True)
            K = [[ss.classify(rep[i][j], pd[i][j]) for j in range(len(ss.B_GRID))] for i in range(len(ss.T_GRID))]
            meta[f"{rowname}|{key}"] = K
            img = [[cats.index(k) if k in cats else 0 for k in rr] for rr in K]
            ax.imshow(img, origin="lower", aspect="auto", cmap=ListedColormap(ccol), vmin=-0.5, vmax=len(cats) - 0.5)
            for i in range(len(ss.T_GRID)):
                for j in range(len(ss.B_GRID)):
                    if K[i][j] == "unknown":
                        ax.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, facecolor="#ffffff", edgecolor="#b9b7ae", hatch="////", lw=0))
            for x in range(len(ss.B_GRID) + 1):
                ax.axvline(x - .5, color="#ffffff", lw=0.6)
            for y in range(len(ss.T_GRID) + 1):
                ax.axhline(y - .5, color="#ffffff", lw=0.6)
            ax.add_patch(plt.Rectangle((j50 - .5, i1 - .5), 1, 1, fill=False, ec=INK, lw=1.6))
            ax.grid(False)
            ax.set_xticks(range(len(ss.B_GRID))); ax.set_xticklabels(ss.B_GRID, fontsize=7, rotation=90)
            ax.set_yticks(range(len(ss.T_GRID))); ax.set_yticklabels([f"{t:g}" for t in ss.T_GRID], fontsize=7)
            if r == 0:
                ax.set_title(title, fontsize=8.5)
            if c == 0:
                ax.set_ylabel(f"{rowname}\n\nTTFT limit (s)", fontsize=8)
            if r == 1:
                ax.set_xlabel("Max-gap limit (ms)", fontsize=8)
    handles = [Patch(facecolor=ccol[cats.index(k)], edgecolor="#b9b7ae", label=labels[k])
               for k in ["d_only", "d_better", "similar", "r_better", "r_only", "neither"]]
    handles.append(Patch(facecolor="#ffffff", edgecolor="#b9b7ae", hatch="////", label=labels["unknown"]))
    handles.append(Patch(facecolor="none", edgecolor=INK, lw=1.6, label="TTFT 1 s, max gap 50 ms"))
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.02), ncol=3, fontsize=7.4, handlelength=1.6, handleheight=1.2)
    fig.suptitle("Per GPU, which side serves more SLO-meeting tokens? Each cell is one SLO; best configuration of each kind",
                 x=0.01, ha="left", fontsize=7.8, color=INK2)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    save(fig, out, "v1_who_wins", meta)


# ---------------------------------------------------------------- proxy GC stalls
def stall_timeline(bench, trace):
    b = json.load(open(bench)); st_ = b["start_times"]; t0 = min(st_)
    ev = []
    for i, (s, t, l) in enumerate(zip(st_, b["ttfts"], b["itls"])):
        tt = s + t
        for g in l:
            tt += g
            if g > 0.05:
                ev.append((tt, i))
    ev.sort(); cl = []
    for e in ev:
        if cl and e[0] - cl[-1][-1][0] < 0.005:
            cl[-1].append(e)
        else:
            cl.append([e])
    pts = [(c[0][0] - t0, len({x[1] for x in c})) for c in cl]
    tr = [json.loads(l) for l in open(trace)]
    t1 = max(st_) + 60
    gc2 = [(x["t"] - t0, x["ms"]) for x in tr if x["k"] == "gc" and x.get("gen") == 2 and t0 <= x["t"] <= t1]
    return pts, gc2, max(st_) - t0 + 30


def fig_proxy_gc(out, root="results/E8"):
    runs_ = [("(a) vLLM test proxy (FastAPI + httpx)", "26_1P1D_toyi", 2), ("(b) aiohttp proxy", "26_1P1D_aio", 2)]
    fig, axes = plt.subplots(2, 1, figsize=(6.6, 3.4), sharex=True)
    meta = {}
    for ax, (title, cfg, pick) in zip(axes, runs_):
        dirs = sorted(glob.glob(f"{root}/*_E8_{cfg}_N0_random_r8"))
        d = dirs[pick]
        pts, gc2, T = stall_timeline(d + "/bench.json", f"{root}/proxy_trace_E8_{cfg}.jsonl")
        ax.vlines([p[0] for p in pts], 0, [p[1] for p in pts], color=S2, lw=1.2)
        for t, ms in gc2:
            ax.axvline(t, color=S1, lw=1.0, ls=(0, (2, 2)))
            ax.text(t + 1, 118, f"GC {ms:.0f} ms", fontsize=6.5, color=S1, rotation=90, va="top")
        ax.set_ylim(0, 125); ax.set_xlim(0, T); ax.set_ylabel("Requests\nstalled >50 ms", fontsize=7.8)
        ax.set_title(title, fontsize=8.3)
        meta[cfg] = {"run": os.path.basename(d), "events_ge15": [(round(t, 1), n) for t, n in pts if n >= 15],
                     "gen2_gc": [(round(t, 1), round(ms, 1)) for t, ms in gc2]}
    axes[1].set_xlabel("Time into the run (s)")
    fig.suptitle("26B NVFP4 1P1D, 4K input at 4 requests/s per GPU. Orange: requests stalled together within 5 ms; "
                 "blue dashed: proxy gen-2 GC", x=0.01, ha="left", fontsize=7.4, color=INK2, y=1.02)
    fig.tight_layout()
    save(fig, out, "v1_proxy_gc", meta)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="results/safe_runs.csv")
    ap.add_argument("--rebuild", action="store_true", help="요청별 캐시를 항상 다시 만든다")
    ap.add_argument("-o", "--out", default="paper/figures_v2")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    cache = ss.load_cache(a.csv, rebuild=a.rebuild)
    res = ss.sensitivity(cache)
    fig_chunk(cache, a.out)
    fig_h2h(cache, a.out)
    fig_transfer(a.out)
    fig_ttft(a.out)
    fig_who_wins(res, a.out)
    fig_proxy_gc(a.out)
    # 부록: 기존 그림을 고친 CSV로 다시
    rows = mf.load(a.csv)
    for f in (mf.f01, mf.f02, mf.f05, mf.f06, mf.f07, mf.f08, mf.f09, mf.f10, mf.f11, mf.f13, mf.f14):
        f(rows, a.out)
    META.update(mf.META)
    json.dump(META, open(os.path.join(a.out, "figures.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print(f"wrote {len(META)} figures to {a.out}")


if __name__ == "__main__":
    main()
