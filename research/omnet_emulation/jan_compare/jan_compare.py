#!/usr/bin/env python3
"""Quantitative comparison of base-paper Figs 1-3 (../targets/fig_targets.json) with Jan et al. Figs 5, 7, 8
(jan_targets.json).  Writes compare.json and prints a text report.  Run: python -I jan_compare.py
Pure standard library (no numpy)."""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = json.load(open(os.path.join(HERE, "..", "targets", "fig_targets.json")))
JAN = json.load(open(os.path.join(HERE, "jan_targets.json")))
PAIRS = [("fig1", "fig5"), ("fig2", "fig7"), ("fig3", "fig8"), ("fig1", "fig6")]  # last = negative control
YTOP = {"fig1": 99.9992520126388}


def mean(v): return sum(v) / len(v)
def rms(v): return math.sqrt(sum(x * x for x in v) / len(v)) if v else float("nan")
def std(v):
    if len(v) < 2: return float("nan")
    m = mean(v); return math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))


def ols(xs, ys):
    n = len(xs); mx, my = mean(xs), mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0: return my, 0.0
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    return my - b * mx, b


def cells(b, j):
    """list of (series, g, base, jan, base_censored)"""
    out = []
    for s in b["series"]:
        if s not in j["series"]:
            continue
        for g, (bv, jv) in enumerate(zip(b["series"][s], j["series"][s])):
            out.append((s, g, bv, jv, b["censored"][s][g]))
    return out


def analyse(bk, jk):
    b, j = BASE[bk], JAN[jk]
    C = cells(b, j)
    U = [c for c in C if not c[4]]
    series = list(b["series"])
    res = dict(base=bk, jan=jk, n_cells=len(C), n_uncensored=len(U), n_censored=len(C) - len(U))
    # --- difference table
    res["diff_table"] = {s: [None if c[4] else round(c[2] - c[3], 4) for c in C if c[0] == s] for s in series}
    res["censored_cells_base_ge"] = {s: [(g, round(c[3], 4)) for c in C if c[0] == s and c[4] for g in [c[1]]] for s in series}
    res["x_base"], res["x_jan"] = b["x"], j["x"]
    # --- per-series stats
    st = {}
    for s in series:
        d = [c[2] - c[3] for c in U if c[0] == s]
        st[s] = dict(n=len(d), mean=mean(d), std=std(d), min=min(d), max=max(d), range=max(d) - min(d))
    res["per_series_diff_stats"] = st
    # --- models (fit on uncensored cells)
    d_all = [c[2] - c[3] for c in U]
    models = {}
    c0 = mean(d_all)
    models["M0 uniform constant: base = jan + c"] = dict(params=1, c=c0, rms=rms([x - c0 for x in d_all]),
                                                           max_abs=max(abs(x - c0) for x in d_all))
    cs = {s: st[s]["mean"] for s in series if st[s]["n"]}
    r1 = [c[2] - c[3] - cs[c[0]] for c in U]
    models["M1 per-series constant: base = jan + c_s"] = dict(params=len(cs), c=cs, rms=rms(r1), max_abs=max(abs(x) for x in r1))
    # affine in group index (diff trends with x), global and per-series
    a, bb = ols([c[1] for c in U], d_all)
    r2 = [c[2] - c[3] - (a + bb * c[1]) for c in U]
    models["M2a global affine in group index: base = jan + a + b*g"] = dict(params=2, a=a, b=bb, rms=rms(r2), max_abs=max(abs(x) for x in r2))
    ps = {s: ols([c[1] for c in U if c[0] == s], [c[2] - c[3] for c in U if c[0] == s]) for s in cs if st[s]["n"] > 2}
    if len(ps) == len(cs):
        r3 = [c[2] - c[3] - (ps[c[0]][0] + ps[c[0]][1] * c[1]) for c in U]
        models["M2b per-series affine in group index: base = jan + a_s + b_s*g"] = dict(
            params=2 * len(ps), fits={s: dict(a=v[0], b=v[1]) for s, v in ps.items()}, rms=rms(r3), max_abs=max(abs(x) for x in r3))
    # affine in jan value (rescale): base = a + k*jan
    a4, k4 = ols([c[3] for c in U], [c[2] for c in U])
    r4 = [c[2] - (a4 + k4 * c[3]) for c in U]
    models["M3a global affine in jan value: base = a + k*jan"] = dict(params=2, a=a4, k=k4, rms=rms(r4), max_abs=max(abs(x) for x in r4))
    pk = {}
    for s in cs:
        xs = [c[3] for c in U if c[0] == s]; ys = [c[2] for c in U if c[0] == s]
        if len(xs) > 2 and max(xs) - min(xs) > 0:
            pk[s] = ols(xs, ys)
    if len(pk) == len(cs):
        r5 = [c[2] - (pk[c[0]][0] + pk[c[0]][1] * c[3]) for c in U]
        models["M3b per-series affine in jan value: base = a_s + k_s*jan"] = dict(
            params=2 * len(pk), fits={s: dict(a=v[0], k=v[1]) for s, v in pk.items()}, rms=rms(r5), max_abs=max(abs(x) for x in r5))
    # combined per-series offset + global slope on jan value  (k common, a_s per series)
    res["models"] = models
    # --- noise floor
    nb = BASE[bk]["precision"]["value_resolution"]; nj = JAN[jk]["precision"]["value_resolution"]
    res["quantisation_noise_floor_rms"] = math.sqrt((nb ** 2 + nj ** 2) / 12)
    res["resolution_base_jan"] = (nb, nj)
    # --- censored consistency under M1 (and M0)
    cens = []
    top = YTOP.get(bk)
    for c in C:
        if c[4]:
            cens.append(dict(series=c[0], group=c[1], jan=c[3], pred_M0=c[3] + c0, pred_M1=c[3] + cs.get(c[0], c0),
                             axis_top=top, consistent_M1=(top is not None and c[3] + cs.get(c[0], c0) >= top - 0.05)))
    res["censored_check"] = cens
    # --- identical-height pair structure
    def pairs(r, xkey):
        return sorted(tuple(sorted(v)) for v in r["identical_heights"].values()) if r["identical_heights"] else []
    res["identical_height_groups_base"] = list(BASE[bk]["identical_heights"].values())
    res["identical_height_groups_jan"] = list(JAN[jk]["identical_heights"].values())
    # equalities between cells in base (series_i,g)=(series_j,h) at tol, and the same in jan, by cell index
    def eq_set(vals, tol):
        cl = [(s, g, v) for (s, g, v, *_r) in vals]
        S = set()
        for i in range(len(cl)):
            for k in range(i + 1, len(cl)):
                if abs(cl[i][2] - cl[k][2]) < tol:
                    S.add(((cl[i][0], cl[i][1]), (cl[k][0], cl[k][1])))
        return S
    eb = eq_set([(c[0], c[1], c[2]) for c in U], 0.04)
    ej = eq_set([(c[0], c[1], c[3]) for c in U], 0.04)
    res["equal_cell_pairs"] = dict(base=sorted(map(list, eb)), jan=sorted(map(list, ej)), common=sorted(map(list, eb & ej)),
                                   n_base=len(eb), n_jan=len(ej), n_common=len(eb & ej))
    # --- ordering: ranks of series within each group
    def rank_tuple(sel, g):
        return tuple(sorted(series, key=lambda s: sel[s][g]))
    ordb = [rank_tuple(b["series"], g) for g in range(len(b["x"]))]
    ordj = [rank_tuple(j["series"], g) for g in range(len(j["x"]))]
    res["series_rank_order_same_per_group"] = [x == y for x, y in zip(ordb, ordj)]
    # --- bar order / colours
    res["bar_order_base"], res["bar_order_jan"] = b["in_group_bar_order"], j["in_group_bar_order"]
    res["bar_order_same"] = b["in_group_bar_order"] == j["in_group_bar_order"]
    res["colours_base"], res["colours_jan"] = b["colour_to_series"], j["colour_to_series"]
    inv = lambda m: {v: k for k, v in m.items()}
    cb, cj = inv(b["colour_to_series"]), inv(j["colour_to_series"])
    res["colour_same_per_series"] = {s: cb.get(s) == cj.get(s) for s in series}
    return res


def x_mapping():
    out = {}
    xb = BASE["fig1"]["x"]
    xj = JAN["fig5"]["x"]
    a, k = ols(xj, xb)
    out["fig1_vs_fig5"] = dict(base_x=xb, jan_x=xj, fit_base_eq_a_plus_k_jan=dict(a=a, k=k), exact_ratio_1p5=all(abs(1.5 * x - y) < 1e-9 for x, y in zip(xj, xb)))
    xj7 = JAN["fig7"]["group_centres_axis_units"]
    a7, k7 = ols(xj7, BASE["fig2"]["x"])
    out["fig2_vs_fig7"] = dict(base_x=BASE["fig2"]["x"], jan_group_centres_axis_units=xj7,
                               fit_base_eq_a_plus_k_jan=dict(a=a7, k=k7),
                               ratio_base_over_centre=[b / c for b, c in zip(BASE["fig2"]["x"], xj7)],
                               jan_labelled_ticks="0,200,...,1200 (groups sit between ticks, centres at 100,300,...,1100)")
    # geometry: bar width / group pitch / gap
    geo = {}
    for name, R in (("base_fig1", BASE["fig1"]), ("jan_fig5", JAN["fig5"]), ("jan_fig6", JAN["fig6"]),
                    ("base_fig2", BASE["fig2"]), ("jan_fig7", JAN["fig7"]), ("base_fig3", BASE["fig3"]), ("jan_fig8", JAN["fig8"])):
        s0 = next(iter(R["bar_detail"]))
        w = R["bar_detail"][s0][0]["width"]
        gc = R["group_centres_pt"]
        pitch = (gc[-1] - gc[0]) / (len(gc) - 1) if len(gc) > 1 else None
        nser = len(R["series"])
        geo[name] = dict(bar_width_pt=w, pitch_pt=pitch, nser=nser, bars_fraction_of_pitch=None if pitch is None else nser * w / pitch,
                         axis_span_pt=R["calibration"]["y_axis_top"] - R["calibration"]["baseline_y"] if "baseline_y" in R["calibration"] else None)
    out["geometry"] = geo
    return out


def main():
    out = dict(pairs={}, x_mapping=x_mapping())
    for bk, jk in PAIRS:
        out["pairs"][f"{bk}_vs_{jk}"] = analyse(bk, jk)
    # CMC-2025 Fig 6 (pixel-read values in provenance.md, 1 decimal) vs Jan Fig 5
    cmc = {"Proposed": [43.1, 45.1, 47.6, 50.9, 52.9, 63.9], "Zhanfei 2024": [59.6, 63.9, 68.7, 73.2, 77.8, 79.4],
           "Hassan 2023": [50.1, 54.9, 55.8, 59.7, 63.1, 69.3], "Gupta 2019": [75.8, 77.9, 81.8, 80.9, 84.0, 85.1],
           "Gope 2016": [71.6, 73.3, 75.7, 77.8, 80.6, 81.7], "Hassan 2018": [75.3, 77.9, 74.9, 81.0, 83.9, 86.0]}
    c3 = {}
    for s, v in cmc.items():
        d = [a - b for a, b in zip(v, JAN["fig5"]["series"][s])]
        c3[s] = dict(diff=[round(x, 2) for x in d], mean=mean(d), std=std(d), min=min(d), max=max(d))
    allc = [a - b for s, v in cmc.items() for a, b in zip(v, JAN["fig5"]["series"][s])]
    out["cmc2025_fig6_minus_jan_fig5"] = dict(note="CMC values are 1-decimal pixel reads from provenance.md (+-0.07)", per_series=c3,
                                              pooled_std_about_series_means=rms([a - b - c3[s]["mean"] for s, v in cmc.items() for a, b in zip(v, JAN["fig5"]["series"][s])]))
    json.dump(out, open(os.path.join(HERE, "compare.json"), "w"), indent=1, default=float)
    # ------------------------------------------------------------------ print
    for key, r in out["pairs"].items():
        print("=" * 100)
        print(key, " cells:", r["n_cells"], " uncensored:", r["n_uncensored"], " censored:", r["n_censored"],
              " quantisation noise floor rms: %.4f" % r["quantisation_noise_floor_rms"])
        print(" x base", r["x_base"], " x jan", r["x_jan"])
        print(" diff table (base - jan):")
        for s, d in r["diff_table"].items():
            stt = r["per_series_diff_stats"][s]
            print(f"  {s:13s}", " ".join("  cens " if v is None else f"{v:7.3f}" for v in d),
                  f" | mean {stt['mean']:.4f} std {stt['std']:.4f} min {stt['min']:.4f} max {stt['max']:.4f}")
        for m, v in r["models"].items():
            print(f"  {m:70s} k={v['params']:2d}  rms={v['rms']:.4f}  max|r|={v['max_abs']:.4f}")
        if r["censored_check"]:
            print(" censored cells (base >= axis top):")
            for c in r["censored_check"]:
                print("   ", c["series"], c["group"], "jan=%.3f pred_M0=%.3f pred_M1=%.3f" % (c["jan"], c["pred_M0"], c["pred_M1"]), "consistent" if c["consistent_M1"] else "INCONSISTENT")
        print(" equal-height cell pairs: base", r["equal_cell_pairs"]["n_base"], " jan", r["equal_cell_pairs"]["n_jan"], " common", r["equal_cell_pairs"]["n_common"])
        print("   common:", r["equal_cell_pairs"]["common"])
        print(" same series ranking per group:", r["series_rank_order_same_per_group"])
        print(" bar order same:", r["bar_order_same"], r["bar_order_base"])
        print(" colour same per series:", r["colour_same_per_series"])
    print(json.dumps(out["x_mapping"], indent=1, default=float))
    print(json.dumps(out["cmc2025_fig6_minus_jan_fig5"], indent=1, default=float))


if __name__ == "__main__":
    main()
