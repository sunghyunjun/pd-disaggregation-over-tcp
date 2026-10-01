#!/usr/bin/env python3
"""영어 원고 v4 그림: v3 그림 전부 + 6절 경계 그림(v4_boundary).

사용:
  uv run --with numpy python3 harness/boundary_model.py --json paper/figures_v4/boundary.json
  uv run --with matplotlib python3 harness/make_figures_v4.py [-o paper/figures_v4]

v4_boundary  저부하 모델(26B FP8, g7e로 보정)이 예측한 첫 토큰 시간: 간격 한도를 지키는 가장 큰 청크의 복제본 대
             TCP 위 1P1D(하이브리드 KV, 모든 레이어가 전역이라고 가정한 KV, 빠른 연결). 두 곡선 사이에서 1P1D만
             두 한도를 함께 지킨다. 16K 너머는 외삽이다.
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_figures as mf  # noqa: E402
import make_figures_v2 as v2  # noqa: E402
import make_figures_v3 as v3  # noqa: E402
import slo_sensitivity as ss  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

INK, INK2 = mf.INK, mf.INK2
S1, S2, S3, S4, S5 = mf.S1, mf.S2, mf.S3, mf.S4, mf.S5


def fig_boundary(out, path):
    """Figure 7: model prediction of the lowest TTFT limit each side can meet together with the gap limit."""
    B = json.load(open(path))
    c = B["curves"]; L = [x / 1024 for x in c["L"]]
    pd15, pd1, pd18 = c["pd_m1.5_s"], c["pd_m1_s"], c["pd_m1.8_s"]
    GRAY = "#8f8f8a"
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.4), sharey=True, gridspec_kw={"wspace": 0.08})
    meta = {}
    meas = {50: (0.194, "replicas, chunk 1,024"), 30: (0.239, "replicas, chunk 512")}
    for ax, G, tag in zip(axes, (50, 30), "ab"):
        rep = c[f"G{G}"]["replica_ttft_s"]; endL = c[f"G{G}"]["end_L"] / 1024
        inside = [x <= endL for x in L]
        top = [r if r is not None else 1e3 for r in rep]
        # regions
        ax.fill_between(L, pd15, top, where=[p < t and ok for p, t, ok in zip(pd15, top, inside)], color=S2, alpha=0.30,
                        lw=0, interpolate=True)
        floor = [min(t, p) if ok else t for t, p, ok in zip(top, pd15, inside)]
        ax.fill_between(L, [0.05] * len(L), [min(f, 1e3) for f in floor], color=mf.NEUTRAL, alpha=0.12, lw=0)
        ax.fill_between([x for x, ok in zip(L, inside) if ok], [p for p, ok in zip(pd18, inside) if ok],
                        [p for p, ok in zip(pd1, inside) if ok], color=S2, alpha=0.13, lw=0)
        # extrapolated range
        ax.axvspan(16, 48, facecolor="none", edgecolor="#e6e6e1", hatch="///", lw=0, zorder=0)
        ax.axvline(16, color=INK2, lw=0.8)
        for x in (4, 16):
            ax.plot([x], [0.1], marker="^", color=INK2, ms=5, clip_on=False, zorder=5)
        ax.text(16.6, 0.105, "extrapolated", fontsize=6.6, color=INK2, va="bottom")
        # reference TTFT limits
        for T in (1, 3):
            ax.axhline(T, color=GRAY, lw=0.7, ls=(0, (1, 2)))
            ax.text(2.1, T * 1.05, f"TTFT {T} s", fontsize=6.4, color=GRAY, va="bottom")
        # curves
        xs = [x for x, r in zip(L, rep) if r is not None]; ys = [r for r in rep if r is not None]
        ax.plot(xs, ys, color=S1, lw=2.2, label="Replicas, largest chunk within the gap limit")
        Lin = [x for x, ok in zip(L, inside) if ok]; Lout = [x for x, ok in zip(L, inside) if not ok]
        ax.plot(Lin, [p for p, ok in zip(pd15, inside) if ok], color=S2, lw=2.2,
                label="1P1D over TCP (this checkpoint's KV, m = 1.5; band m = 1–1.8)")
        if Lout:
            ax.plot(Lout, [p for p, ok in zip(pd15, inside) if not ok], color=GRAY, lw=1.6, ls=(0, (2, 1.6)))
            ax.text(47, 0.3, f"1P1D decode gap\n> {G} ms beyond here", fontsize=6.4, color=GRAY, va="bottom", ha="right")
        ax.plot(Lin, [p for p, ok in zip(c["pd_fast_s"], inside) if ok], color=S3, lw=1.8, ls=(0, (1.2, 1.6)),
                label="1P1D, 95 Gbps link")
        ax.plot(Lin, [p for p, ok in zip(c["pd_kv220_s"], inside) if ok], color=S2, lw=1.0, ls=(0, (6, 2, 1.5, 2)),
                label="1P1D, KV 220 KiB/token (sliding layers keep all)")
        # measured 4K anchors
        ax.plot([4], [meas[G][0]], ls="none", marker="o", mfc="white", mec=S1, mew=1.4, ms=6)
        ax.plot([4], [0.362], ls="none", marker="s", mfc="white", mec=S2, mew=1.4, ms=6)
        ax.set_xscale("log", base=2); ax.set_yscale("log")
        ax.set_xticks([2, 4, 8, 16, 32]); ax.set_xticklabels(["2K", "4K", "8K", "16K", "32K"])
        ax.set_yticks([0.125, 0.25, 0.5, 1, 2, 4, 8, 16]); ax.set_yticklabels(["0.125", "0.25", "0.5", "1", "2", "4", "8", "16"])
        ax.set_xlim(2, 48); ax.set_ylim(0.1, 20)
        ax.set_xlabel("Input length (tokens)")
        ax.set_title(f"({tag}) Model, gap limit {G} ms", fontsize=8.5)
        cr = c[f"G{G}"].get("crossover_m1.5")
        meta[f"G{G}"] = {"crossover_m1.5": cr, "end_L": c[f"G{G}"]["end_L"], "m": 1.5}
    axes[0].set_ylabel("Lowest TTFT limit that can be met (s)")
    hs, ls_ = axes[0].get_legend_handles_labels()
    hs += [Line2D([0], [0], ls="none", marker="o", mfc="white", mec=INK2, ms=6),
           Patch(facecolor=S2, alpha=0.30, edgecolor="none"), Patch(facecolor=mf.NEUTRAL, alpha=0.12, edgecolor="none")]
    ls_ += ["Measured at 4K (circle: replicas, square: 1P1D)", "Only 1P1D meets both limits",
            "Neither replicas nor 1P1D over TCP"]
    fig.legend(hs, ls_, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2, fontsize=7.0)
    fig.suptitle("Model prediction for 26B FP8 on g7e at low load, calibrated at 4K and 16K (triangles). "
                 "Above a curve, that side meets both limits", x=0.01, ha="left", fontsize=7.2, color=INK2, y=1.03)
    v2.save(fig, out, "v4_boundary", meta)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="results/safe_runs.csv")
    ap.add_argument("-o", "--out", default="paper/figures_v4")
    ap.add_argument("--boundary", default="paper/figures_v4/boundary.json")
    ap.add_argument("--rebuild", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    mf.REP_SUFFIX = ", chunk 2,560"
    mf.F08_NOTE = "hollow: caution run\n(client or proxy limit)"
    mf.F06_TITLE = "4K input, 0.5 requests/s per GPU, replicas at a 2,560-token chunk"
    mf.MARK_CAUTION = True
    cache = ss.load_cache(a.csv, rebuild=a.rebuild)
    res = ss.sensitivity(cache, merge_families=True)
    v2.fig_chunk(cache, a.out)
    v3.fig_h2h(cache, a.out)
    v3.fig_transfer(a.out)
    v2.fig_ttft(a.out)
    v2.fig_who_wins(res, a.out)
    v2.fig_proxy_gc(a.out)
    fig_boundary(a.out, a.boundary)
    rows = mf.load(a.csv)
    for f in (mf.f01, mf.f02, mf.f05, mf.f06, mf.f07, mf.f08, mf.f09, mf.f10, mf.f11, mf.f13, mf.f14):
        f(rows, a.out)
    v2.META.update(mf.META)
    json.dump(v2.META, open(os.path.join(a.out, "figures.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print(f"wrote {len(v2.META)} figures to {a.out}")


if __name__ == "__main__":
    main()
