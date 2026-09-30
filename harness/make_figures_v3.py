#!/usr/bin/env python3
"""영어 원고 v3 그림(3차 모의 심사 반영). v2 스크립트의 함수를 그대로 쓰고 바뀐 그림만 다시 정의한다.

사용:
  uv run --with matplotlib python3 harness/make_figures_v3.py [-o paper/figures_v3]

v2와 다른 점
  v1_head_to_head  판정(모든 반복 ≥0.9)을 통과하지 못한 점은 속 빈 마커, 같은 x의 계열을 조금씩 어긋나게,
                   P 청크 8,192 계열은 다른 선 모양과 "UCX segment sizes only" 라벨, FP8 패널에 겹침 표기(A11, B15)
  v1_transfer      (c) 제목·축 이름을 실제 지표(표본마다 64 KiB 넘게 움직인 연결 수)에 맞추고, 두 계열 모두 분리 전송이라
                   주황 두 명도 + 빗금으로 구분, 윗제목의 요청률을 GPU당으로(A9)
  v1_who_wins      절단 판정만 같은 서빙 구성의 프록시·세션 변형을 합친다(slo_sensitivity.FAMILIES, B6). 26B 동률 8칸이 나온다
  부록             복제본 범례에 ", chunk 2,560", 주의 런 표시, 그림 A9 제목을 조건만(A12, A13-17)
"""
import argparse, json, os, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_figures as mf  # noqa: E402
import make_figures_v2 as v2  # noqa: E402
import slo_sensitivity as ss  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

INK, INK2 = mf.INK, mf.INK2
S1, S2, S3, S4, S5 = mf.S1, mf.S2, mf.S3, mf.S4, mf.S5
META = v2.META


# ---------------------------------------------------------------- head to head
def series(ax, cache, stages, cfgs, wl, inl, gpus, color, marker, ls, label, dx=0.0):
    by = defaultdict(list)
    for c in cfgs:
        for rid, r in v2.runs(cache, stages, c, wl, None, inl):
            by[float(r["rate"])].append(ss.attain(r, 1.0, 50))
    xs = sorted(by)
    if not xs:
        return None
    X = [x / gpus + dx for x in xs]
    ys = [sum(by[x]) / len(by[x]) for x in xs]
    ax.plot(X, ys, color=color, ls=ls, lw=1.8, label=label, marker=marker, mfc=color, mec=color, ms=5.5)
    ax.vlines(X, [min(by[x]) for x in xs], [max(by[x]) for x in xs], color=color, lw=1.1)
    fail = [(xx, y) for xx, y, x in zip(X, ys, xs) if min(by[x]) < 0.9]   # 판정 탈락: 속 빈 마커
    if fail:
        ax.plot([f[0] for f in fail], [f[1] for f in fail], ls="none", marker=marker, mfc="white", mec=color, mew=1.4, ms=5.5)
    return {f"{x / gpus:g}": [round(v, 3) for v in by[x]] for x in xs}


def fig_h2h(cache, out):
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 3.0), sharey=True, gridspec_kw={"wspace": 0.12})
    meta = {}
    DASH, DOT, DD, DDD = (0, (5, 2.5)), (0, (1.5, 1.8)), (0, (6, 2, 1.5, 2)), (0, (9, 2.5))
    a, b, c = axes
    L = {"c2560": "Replicas, chunk 2,560", "c1024": "Replicas, chunk 1,024", "small": "Replicas, chunk 512 (256 for 31B)",
         "toy": "1P1D, vLLM test proxy", "aio": "1P1D, aiohttp proxy",
         "p8192": "1P1D, aiohttp, prefill chunk 8,192\n(UCX segment sizes only)"}
    meta["26b_4k"] = {
        "Replicas chunk 2560": series(a, cache, ("E5", "E7", "E8"), ["26_B2", "26_B2_c2560"], "random", "4096", 2, S5, "o", DOT, L["c2560"], -0.10),
        "Replicas chunk 1024": series(a, cache, ("E8", "E9"), ["26_B2_c1024"], "random", "4096", 2, S1, "o", "-", L["c1024"], -0.06),
        "Replicas chunk 512": series(a, cache, ("E9",), ["26_B2_c512"], "random", "4096", 2, S1, "D", DD, L["small"], -0.02),
        "1P1D test proxy": series(a, cache, ("E5", "E7", "E8"), ["26_1P1D", "26_1P1D_toyi"], "random", "4096", 2, S3, "s", DASH, L["toy"], 0.02),
        "1P1D aiohttp proxy": series(a, cache, ("E8",), ["26_1P1D_aio"], "random", "4096", 2, S2, "s", "-", L["aio"], 0.06),
        "1P1D aiohttp, prefill chunk 8192 (UCX segment only)": series(a, cache, ("E9",), ["26_1P1D_aio_p8192"], "random", "4096", 2, S4, "^", DDD, L["p8192"], 0.10),
    }
    meta["26f_4k"] = {
        "Replicas chunk 2560": series(b, cache, ("E7",), ["26F_B2"], "random", "4096", 2, S5, "o", DOT, L["c2560"], -0.03),
        "Replicas chunk 1024": series(b, cache, ("E8",), ["26F_B2_c1024"], "random", "4096", 2, S1, "o", "-", L["c1024"], -0.01),
        "Replicas chunk 512": series(b, cache, ("E9",), ["26F_B2_c512"], "random", "4096", 2, S1, "D", DD, L["small"], 0.01),
        "1P1D test proxy": series(b, cache, ("E7",), ["26F_1P1D"], "random", "4096", 2, S3, "s", DASH, L["toy"], 0.03),
    }
    b.text(0.96, 0.84, "chunk 1,024, chunk 512\nand 1P1D all at 1.00", transform=b.transAxes, ha="right", va="top",
           fontsize=6.8, color=INK2)
    meta["31b_chat"] = {
        "Replicas chunk 2560": series(c, cache, ("E5", "E7", "E8"), ["31_B2", "31_B2_c2560"], "sharegpt", None, 2, S5, "o", DOT, L["c2560"], -0.12),
        "Replicas chunk 256": series(c, cache, ("E8", "E9"), ["31_B2_c256"], "sharegpt", None, 2, S1, "D", DD, L["small"], -0.04),
        "1P1D test proxy": series(c, cache, ("E5", "E7"), ["31_1P1D"], "sharegpt", None, 2, S3, "s", DASH, L["toy"], 0.04),
        "1P1D aiohttp proxy": series(c, cache, ("E8", "E9"), ["31_1P1D_aio"], "sharegpt", None, 2, S2, "s", "-", L["aio"], 0.12),
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
    order = [L[k] for k in ("c2560", "c1024", "small", "toy", "aio", "p8192")]
    idx = [ls_.index(o) for o in order if o in ls_]
    fig.legend([hs[i] for i in idx], [ls_[i] for i in idx], loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=3, fontsize=7.3)
    fig.suptitle("Two g7e nodes in a placement group. Line: mean of repeats; bar: min–max; hollow marker: some repeat below 0.9",
                 x=0.01, ha="left", fontsize=7.8, color=INK2, y=1.03)
    v2.save(fig, out, "v1_head_to_head", meta)


# ---------------------------------------------------------------- transfer path
def fig_transfer(out, root="results/E8"):
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.8), gridspec_kw={"width_ratios": [1, 1.2, 1.3], "wspace": 0.45})
    a, b, c = axes
    flows = [1, 2, 4, 8]; gb = [9.54, 19.06, 38.11, 49.72]
    a.plot(flows, gb, color=S1, marker="o")
    a.axhline(50, color=INK2, lw=1, ls=(0, (4, 3)))
    a.text(1, 51.5, "instance 50 Gbps", fontsize=7, color=INK2)
    a.set_xticks(flows); a.set_ylim(0, 58); a.set_xlabel("Parallel TCP flows (iperf)"); a.set_ylabel("Gbps")
    a.set_title("(a) Bandwidth vs flows", fontsize=8.3)
    sets = [("UCX\ndefault", f"{root}/xfer_E8/26_1P1D_def_random_r0.5_n0_*.log"),
            ("Segment\n256 KB\nonly", f"{root}/xfer_E8/26_1P1D_seg_random_r0.5_n0_*.log"),
            ("Seven\nUCX\nvariables", f"{root}/xfer_E8/26_1P1D_aio_random_r0.5_n0_*.log")]
    meta = {"iperf_flows_gbps": dict(zip(flows, gb)), "quoted_iperf": "RESULTS.md E4-0"}
    for i, (lab, pat) in enumerate(sets):
        v = v2.xfer_stats(pat)
        b.scatter([i] * len(v), v, s=11, color=S2, alpha=0.6, edgecolors="none")
        if v:
            med = v2.q(v, .5)
            b.plot([i - 0.25, i + 0.25], [med, med], color=INK, lw=1.6)
            b.text(i + 0.28, med, f"{med:.1f}", va="center", fontsize=7)
        meta["transfer_gbps|" + lab.replace("\n", " ")] = {"n_windows": len(v), "median": round(v2.q(v, .5), 2),
                                                           "min": round(min(v), 2) if v else None, "max": round(max(v), 2) if v else None}
    b.axhline(9.54, color=S1, lw=1.2, ls=(0, (4, 3)))
    b.text(2.45, 9.9, "one flow\n9.54", fontsize=6.8, color=S1, ha="right", va="bottom")
    b.set_xticks(range(3)); b.set_xticklabels([s[0] for s in sets], fontsize=6.6); b.set_xlim(-0.5, 2.6)
    b.set_ylim(0, 19); b.set_ylabel("KV transfer rate (Gbps)")
    b.set_title("(b) 26B, 140 MiB per request", fontsize=8.3)
    d26 = v2.ss_active(f"{root}/ss/ss_E8_26_1P1D_aio_random_r0.5_n0_P.txt")
    d31 = v2.ss_active(f"{root}/ss/ss_E8_31_1P1D_ss_random_r0.25_n0_P.txt")
    w = 0.38
    c.bar([k - w / 2 for k in range(1, 5)], [d26[k] for k in range(1, 5)], w, color=S3, label="26B, 140 MiB")
    c.bar([k + w / 2 for k in range(1, 5)], [d31[k] for k in range(1, 5)], w, color=S2, hatch="////", edgecolor="white", lw=0,
          label="31B, 560 MiB")
    c.set_xticks(range(1, 5)); c.set_xlabel("Worker connections moving data"); c.set_ylabel("Share of socket samples")
    c.set_title("(c) Connections moving data", fontsize=8.3); c.legend(loc="upper left", fontsize=7)
    meta["active_connections_share"] = {"26B": d26, "31B": d31,
                                        "definition": "socket samples ~0.12 s apart; connections that moved >64 KiB; samples with any movement; shared fifth connection not counted"}
    fig.suptitle("Two g7e nodes in a placement group, 4K input; (b) and (c) at 0.25 (26B) and 0.125 (31B) requests/s per GPU",
                 x=0.01, ha="left", fontsize=7.8, color=INK2, y=1.03)
    v2.save(fig, out, "v1_transfer", meta)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="results/safe_runs.csv")
    ap.add_argument("--rebuild", action="store_true", help="요청별 캐시를 항상 다시 만든다")
    ap.add_argument("-o", "--out", default="paper/figures_v3")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    mf.REP_SUFFIX = ", chunk 2,560"
    mf.F08_NOTE = "hollow: caution run\n(client or proxy limit)"
    mf.F06_TITLE = "4K input, 0.5 requests/s per GPU, replicas at a 2,560-token chunk"
    mf.MARK_CAUTION = True
    cache = ss.load_cache(a.csv, rebuild=a.rebuild)
    res = ss.sensitivity(cache, merge_families=True)
    v2.fig_chunk(cache, a.out)
    fig_h2h(cache, a.out)
    fig_transfer(a.out)
    v2.fig_ttft(a.out)
    v2.fig_who_wins(res, a.out)
    v2.fig_proxy_gc(a.out)
    rows = mf.load(a.csv)
    for f in (mf.f01, mf.f02, mf.f05, mf.f06, mf.f07, mf.f08, mf.f09, mf.f10, mf.f11, mf.f13, mf.f14):
        f(rows, a.out)
    META.update(mf.META)
    json.dump(META, open(os.path.join(a.out, "figures.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print(f"wrote {len(META)} figures to {a.out}")


if __name__ == "__main__":
    main()
