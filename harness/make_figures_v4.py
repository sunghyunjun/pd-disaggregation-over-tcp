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
    B = json.load(open(path))
    c = B["curves"]; L = [x / 1024 for x in c["L"]]
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.3), sharey=True, gridspec_kw={"wspace": 0.08})
    meta = {}
    for ax, G in zip(axes, (50, 30)):
        rep = c[f"G{G}"]["replica_ttft_s"]
        pdh = c["pd_hybrid_m1_s"]
        xs = [x for x, r in zip(L, rep) if r is not None]
        ys = [r for r in rep if r is not None]
        # shade: only disaggregation meets both limits (PD below the replica curve, or replicas infeasible)
        top = [r if r is not None else 1e3 for r in rep]
        ax.fill_between(L, pdh, top, where=[p < t for p, t in zip(pdh, top)], color=S2, alpha=0.30, lw=0, interpolate=True)
        ax.fill_between(L, [0.05] * len(L), [min(p, t) for p, t in zip(pdh, top)], color=mf.NEUTRAL, alpha=0.10, lw=0)
        ax.plot(xs, ys, color=S1, lw=2.2, label="Replicas, largest chunk within the gap limit")
        ax.plot(L, pdh, color=S2, lw=2.2, label="1P1D over TCP, hybrid KV (as measured)")
        ax.plot(L, c["pd_all_global_m1_s"], color=S4, lw=1.8, ls=(0, (6, 2.5)), label="1P1D over TCP, KV as if every layer were global")
        ax.plot(L, c["pd_fast_link_s"], color=S3, lw=1.8, ls=(0, (1.5, 1.8)), label="1P1D, fast link (5% of TCP transfer time)")
        ax.axvline(16, color=INK2, lw=0.9, ls=(0, (4, 3)))
        ax.text(15.3, 0.115, "calibrated\n≤16K", ha="right", va="bottom", fontsize=6.8, color=INK2)
        ax.text(17, 0.115, "extrapolated", ha="left", va="bottom", fontsize=6.8, color=INK2)
        if xs and xs[-1] < L[-1]:
            ax.annotate("no chunk ≥128\nmeets the limit", (xs[-1], ys[-1]), xytext=(xs[-1] * 0.62, ys[-1] * 1.9),
                        fontsize=6.6, color=S1, arrowprops=dict(arrowstyle="-", color=S1, lw=0.8))
        ax.set_xscale("log", base=2); ax.set_yscale("log")
        ax.set_xticks([2, 4, 8, 16, 32, 64]); ax.set_xticklabels(["2K", "4K", "8K", "16K", "32K", "64K"])
        ax.set_yticks([0.25, 0.5, 1, 2, 4, 8, 16]); ax.set_yticklabels(["0.25", "0.5", "1", "2", "4", "8", "16"])
        ax.set_xlim(2, 64); ax.set_ylim(0.1, 25)
        ax.set_xlabel("Input length (tokens)")
        ax.set_title(f"({'a' if G == 50 else 'b'}) Gap limit {G} ms", fontsize=8.5)
        meta[f"G{G}"] = {"first_pd_only": B["map"]["grid"][f"G{G}_hybrid_m1"]["first_pd_only"]}
    axes[0].set_ylabel("Lowest TTFT limit that can be met (s)")
    hs, ls_ = axes[0].get_legend_handles_labels()
    hs += [Patch(facecolor=S2, alpha=0.30, edgecolor="none"), Patch(facecolor=mf.NEUTRAL, alpha=0.10, edgecolor="none")]
    ls_ += ["Only 1P1D meets both limits (hybrid KV)", "Neither meets the TTFT limit"]
    fig.legend(hs, ls_, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2, fontsize=7.2)
    fig.suptitle("Model prediction: 26B FP8, g7e, low load, calibrated at 4K and 16K. Above a curve, that side meets both limits",
                 x=0.01, ha="left", fontsize=7.4, color=INK2, y=1.03)
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
