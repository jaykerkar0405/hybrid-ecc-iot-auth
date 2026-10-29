#!/usr/bin/env python3
"""Extract exact bar heights of Figs. 5-8 of Jan et al. (IEEE IoT J. 12(5), 4721-4734, 2025,
"ML-based authentication for privacy preservation in distributed edge-enabled IoV") from the vector graphics
in the PDF.  Adapted from research/omnet_emulation/targets/extract_figs.py (base-paper extractor).

Differences from the base-paper script:
  * the Jan charts are NOT Form XObjects: they are drawn inline in the page content stream (PDF p.8 = journal
    p.4722: Figs 5,6; PDF p.9 = p.4723: Figs 7,8; Producer Acrobat Distiller 23.0, Origin-style charts), with all
    chart text outlined (no fonts for the labels).  The content stream is interpreted at page level and the
    paths are filtered by a page-coordinate region box per figure;
  * tick label values (outlined glyphs) were read off 300-dpi renders (Fig5 y 20..100, Fig6 y 20..90,
    Fig7 y 16..38, Fig8 y 0.50..0.70; x ticks Fig5 200..1200, Fig6 2..12, Fig7 0..1200); the script verifies that a
    glyph cluster sits at every major tick and that the tick positions are exactly linear (residuals reported);
  * the legend order differs per figure (read off the renders, see FIGS[...]['legend']) and is mapped to colours
    through the legend swatches;
  * the x axis is calibrated from the labelled x ticks (so group centres are reported in axis units), except Fig 8
    whose x ticks are unlabelled.

Usage: python -I jan_extract.py [path/to/jan.pdf] [out.json]
"""
import json
import math
import os
import sys
from collections import defaultdict

import pikepdf

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PDF = os.path.join(HERE, "..", "..", "..", "docs", "references", "jan_2025_ml_auth_edge_iov.pdf")

FIGS = {
    "fig5": dict(page=8, region=(335, 560, 570, 745),
                 title="Average processing time at the vehicular devices",
                 y_label="Average Processing Time (ns)", x_label="Number of Vehicles in the IoV",
                 y_major=[20, 30, 40, 50, 60, 70, 80, 90, 100],
                 x_major=[200, 400, 600, 800, 1000, 1200], x_groups=[200, 400, 600, 800, 1000, 1200],
                 legend=["Proposed", "Zhanfei 2024", "Hassan 2023", "Gupta 2019", "Gope 2016", "Hassan 2018"],
                 grids=(1.0, 0.5, 0.25, 0.1, 0.05, 0.01)),
    "fig6": dict(page=8, region=(320, 330, 570, 550),
                 title="Average processing time at the edge servers",
                 y_label="Average Processing Time (ns)", x_label="Number of Active Edge Servers in the IoV",
                 y_major=[20, 30, 40, 50, 60, 70, 80, 90],
                 x_major=[2, 4, 6, 8, 10, 12], x_groups=[2, 4, 6, 8, 10, 12],
                 legend=["Proposed", "Zhanfei 2024", "Hassan 2023", "Gupta 2019", "Gope 2016", "Hassan 2018"],
                 grids=(1.0, 0.5, 0.25, 0.1, 0.05, 0.01)),
    "fig7": dict(page=9, region=(40, 255, 300, 460),
                 title="Average communication overhead in a multihop infrastructure (y axis: Average End-to-End Delay)",
                 y_label="Average End-to-End Delay (ms)", x_label="Number of Vehicles in the IoV",
                 y_major=[16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38],
                 x_major=[0, 200, 400, 600, 800, 1000, 1200], x_groups=None,
                 legend=["Gope 2016", "Gupta 2019", "Hassan 2023", "Zhanfei 2024", "Proposed"],
                 grids=(1.0, 0.5, 0.25, 0.1, 0.05, 0.01)),
    "fig8": dict(page=9, region=(320, 150, 570, 375),
                 title="Average storage overhead",
                 y_label="Storage Overhead (%)", x_label="Proposed and Existing Schemes",
                 y_major=[0.50, 0.55, 0.60, 0.65, 0.70],
                 x_major=None, x_groups=["single group"],
                 legend=["Proposed", "Zhanfei 2024", "Hassan 2023", "Gupta 2019", "Hassan 2018", "Gope 2016"],
                 grids=(0.01, 0.005, 0.001, 0.0005)),
}


# ----------------------------------------------------------------------------------------------- parsing
def mat_mul(m1, m2):
    a, b, c, d, e, f = m1
    A, B, C, D, E, F = m2
    return (a * A + b * C, a * B + b * D, c * A + d * C, c * B + d * D, e * A + f * C + E, e * B + f * D + F)


def apply(m, x, y):
    a, b, c, d, e, f = m
    return (a * x + c * y + e, b * x + d * y + f)


def parse(xobj):
    """Return list of painted paths: dict(op, fill, stroke, lw, bbox, rects, segs, clip, ncurves)."""
    ctm = (1, 0, 0, 1, 0, 0)
    st = dict(ctm=ctm, fill=(0, 0, 0), stroke=(0, 0, 0), lw=1.0, clip=None)
    stack = []
    path_pts, rects, segs, ncurves = [], [], [], 0
    cur = None
    pending_clip = False
    out = []
    for operands, op in pikepdf.parse_content_stream(xobj):
        op = str(op)
        v = [float(o) for o in operands if _isnum(o)]
        if op == "q":
            stack.append(dict(st))
        elif op == "Q":
            st = stack.pop()
        elif op == "cm":
            st["ctm"] = mat_mul(tuple(v), st["ctm"])
        elif op == "rg":
            st["fill"] = tuple(v)
        elif op == "RG":
            st["stroke"] = tuple(v)
        elif op == "g":
            st["fill"] = (v[0],) * 3
        elif op == "G":
            st["stroke"] = (v[0],) * 3
        elif op == "w":
            st["lw"] = v[0]
        elif op == "re":
            x, y, w, h = v
            p = [apply(st["ctm"], *q) for q in ((x, y), (x + w, y), (x + w, y + h), (x, y + h))]
            path_pts += p
            xs, ys = [q[0] for q in p], [q[1] for q in p]
            rects.append((min(xs), min(ys), max(xs), max(ys)))
        elif op == "m":
            cur = apply(st["ctm"], *v)
            path_pts.append(cur)
        elif op == "l":
            nxt = apply(st["ctm"], *v)
            segs.append((cur, nxt))
            path_pts.append(nxt)
            cur = nxt
        elif op in ("c", "v", "y"):
            pts = [apply(st["ctm"], v[i], v[i + 1]) for i in range(0, len(v), 2)]
            path_pts += pts
            cur = pts[-1]
            ncurves += 1
        elif op in ("W", "W*"):
            pending_clip = True
        elif op in ("f", "F", "f*", "S", "s", "B", "B*", "b", "b*", "n"):
            if path_pts:
                xs, ys = [q[0] for q in path_pts], [q[1] for q in path_pts]
                bbox = (min(xs), min(ys), max(xs), max(ys))
            else:
                bbox = None
            if op != "n":
                out.append(dict(op=op, fill=st["fill"] if op not in ("S", "s") else None,
                                stroke=st["stroke"] if op in ("S", "s", "B", "B*", "b", "b*") else None,
                                lw=st["lw"], bbox=bbox, rects=rects, segs=segs, ncurves=ncurves,
                                clip=st["clip"]))
            if pending_clip and bbox:
                st["clip"] = bbox if st["clip"] is None else (
                    max(bbox[0], st["clip"][0]), max(bbox[1], st["clip"][1]),
                    min(bbox[2], st["clip"][2]), min(bbox[3], st["clip"][3]))
                pending_clip = False
            path_pts, rects, segs, ncurves = [], [], [], 0
    return out


def _isnum(o):
    try:
        float(o)
        return True
    except Exception:
        return False


# ----------------------------------------------------------------------------------------------- analysis
def linfit(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    a = my - b * mx
    return a, b



def cluster_glyphs(glyphs, gap=1.2):
    """Union glyph bboxes that are within `gap` pt of each other into text clusters."""
    boxes = [list(g) for g in glyphs]
    merged = True
    while merged:
        merged = False
        out = []
        while boxes:
            b = boxes.pop()
            changed = True
            while changed:
                changed = False
                rest = []
                for o in boxes:
                    if (o[0] <= b[2] + gap and b[0] <= o[2] + gap and o[1] <= b[3] + gap and b[1] <= o[3] + gap):
                        b = [min(b[0], o[0]), min(b[1], o[1]), max(b[2], o[2]), max(b[3], o[3])]
                        changed = merged = True
                    else:
                        rest.append(o)
                boxes = rest
            out.append(b)
        boxes = out
        if not merged:
            break
        merged = False
    return boxes



# ----------------------------------------------------------------------------------------------- analysis
def in_region(bb, reg):
    return bb is not None and bb[0] >= reg[0] and bb[2] <= reg[2] and bb[1] >= reg[1] and bb[3] <= reg[3]


def extract(pdf, key, cfg, all_paths):
    reg = cfg["region"]
    paths = [p for p in all_paths[cfg["page"]] if in_region(p["bbox"], reg)]
    eps = 0.02

    lines = [(p, s) for p in paths if p["op"] == "S" for s in p["segs"]]
    hlines = [(p, s) for p, s in lines if abs(s[0][1] - s[1][1]) < 1e-6 and abs(s[0][0] - s[1][0]) > 0
              and p["stroke"] == (0, 0, 0)]
    vlines = [(p, s) for p, s in lines if abs(s[0][0] - s[1][0]) < 1e-6 and abs(s[0][1] - s[1][1]) > 0
              and p["stroke"] == (0, 0, 0)]
    hlen = lambda s: abs(s[0][0] - s[1][0])
    vlen = lambda s: abs(s[0][1] - s[1][1])
    hmax = max(hlen(s) for _, s in hlines)
    vmax = max(vlen(s) for _, s in vlines)
    xaxis = min((s for _, s in hlines if hlen(s) > 0.95 * hmax), key=lambda s: s[0][1])
    yaxis = min((s for _, s in vlines if vlen(s) > 0.9 * vmax), key=lambda s: s[0][0])
    base_y = xaxis[0][1]
    axis_x = yaxis[0][0]
    y_top_axis = max(yaxis[0][1], yaxis[1][1])
    y_bot_axis = min(yaxis[0][1], yaxis[1][1])

    # --- y ticks
    ticks = []
    for p, s in hlines:
        x0, x1 = sorted((s[0][0], s[1][0]))
        if abs(x1 - axis_x) < 0.01 and (x1 - x0) < 5:
            ticks.append((s[0][1], x1 - x0))
    ticks = sorted(set((round(y, 4), round(L, 3)) for y, L in ticks))
    Lmax = max(L for _, L in ticks)
    major = [y for y, L in ticks if L > 0.75 * Lmax]
    minor = [y for y, L in ticks if L <= 0.75 * Lmax]
    assert len(major) == len(cfg["y_major"]), (key, major)

    glyphs = [p["bbox"] for p in paths if p["op"] in ("f", "f*") and p["ncurves"] > 0 and p["fill"] == (0, 0, 0)
              and p["bbox"][2] < axis_x - 0.5 and p["bbox"][2] > axis_x - 25]
    clusters = cluster_glyphs(glyphs, gap=0.9)
    label_check = []
    for y in major:
        cands = [c for c in clusters if c[1] - 1 < y < c[3] + 1 and (c[3] - c[1]) < 8]
        c = min(cands, key=lambda c: abs((c[1] + c[3]) / 2 - y)) if cands else None
        label_check.append(None if c is None else round((c[1] + c[3]) / 2 - y, 4))

    a, b = linfit(major, cfg["y_major"])
    to_val = lambda y: a + b * y
    resid = [cfg["y_major"][i] - to_val(y) for i, y in enumerate(major)]
    step = cfg["y_major"][1] - cfg["y_major"][0]
    minor_vals = [to_val(y) for y in minor]
    minor_resid = [v - (round(v / (step / 2)) * (step / 2)) for v in minor_vals]

    # --- x ticks (vertical strokes whose top end is on the x axis line)
    xt = []
    for p, s in vlines:
        y0, y1 = sorted((s[0][1], s[1][1]))
        if abs(y1 - base_y) < 0.01 and (y1 - y0) < 5:
            xt.append((s[0][0], y1 - y0))
    xt = sorted(set((round(x, 4), round(L, 3)) for x, L in xt))
    xLmax = max(L for _, L in xt) if xt else 0
    xmajor_pos = [x for x, L in xt if L > 0.75 * xLmax]
    xminor_pos = [x for x, L in xt if L <= 0.75 * xLmax]
    xcal = None
    if cfg["x_major"]:
        # take the labelled majors that lie within the x axis (drop a possible unlabelled leading major)
        mp = xmajor_pos
        if len(mp) != len(cfg["x_major"]):
            mp = [x for x in mp if x >= min(cfg["x_major"]) * 0 + axis_x - 0.01]
        assert len(mp) == len(cfg["x_major"]), (key, xmajor_pos)
        xa, xb = linfit(mp, cfg["x_major"])
        xcal = dict(a=xa, b=xb, major_pos=mp, major_values=cfg["x_major"],
                    residuals=[v - (xa + xb * x) for x, v in zip(mp, cfg["x_major"])])

    # --- bars and legend swatches
    fills = [p for p in paths if p["op"] in ("f", "f*", "F") and p["rects"] and p["ncurves"] == 0 and len(p["rects"]) == 1]
    bars, swatches = [], []
    for p in fills:
        r = p["rects"][0]
        w, h = r[2] - r[0], r[3] - r[1]
        if abs(r[1] - base_y) < eps and w > 3:
            bars.append(dict(rect=r, fill=p["fill"], clip=p["clip"]))
        elif r[1] > base_y + 5 and 8 < w < 20 and 3 < h < 8 and p["fill"] != (1, 1, 1):
            swatches.append(dict(rect=r, fill=p["fill"]))
    sw = {}
    for s in sorted(swatches, key=lambda s: -s["rect"][3]):
        sw.setdefault(s["fill"], s)
    sw_order = sorted(sw.values(), key=lambda s: -s["rect"][3])
    assert len(sw_order) == len(cfg["legend"]), (key, [s["fill"] for s in sw_order])
    colour2name = {s["fill"]: name for s, name in zip(sw_order, cfg["legend"])}

    top_edges = [(s[0][1], min(s[0][0], s[1][0]), max(s[0][0], s[1][0])) for p, s in hlines]
    for bar in bars:
        r = bar["rect"]
        edge = [y for y, x0, x1 in top_edges if abs(x0 - r[0]) < 0.01 and abs(x1 - r[2]) < 0.01 and abs(y - r[3]) < 0.01]
        bar["fill_top"] = r[3]
        bar["edge_top"] = edge[0] if edge else None
        # strokes of this bar's outline top edge (any colour) as an independent check
        bar["top"] = r[3]
        bar["height_pt"] = r[3] - base_y
        bar["value"] = to_val(r[3])
        bar["clipped"] = r[3] >= y_top_axis - 0.01

    bars.sort(key=lambda b: b["rect"][0])
    nser = len(cfg["legend"])
    # group by gaps
    groups, cur = [], [bars[0]]
    for bb in bars[1:]:
        if bb["rect"][0] - cur[-1]["rect"][2] > 2.0:
            groups.append(cur)
            cur = [bb]
        else:
            cur.append(bb)
    groups.append(cur)
    assert all(len(g) == nser for g in groups), (key, [len(g) for g in groups])
    ngroups = len(groups)
    group_centres = [(g[0]["rect"][0] + g[-1]["rect"][2]) / 2 for g in groups]
    if xcal:
        gx = [xcal["a"] + xcal["b"] * c for c in group_centres]
    else:
        gx = None
    x_vals = cfg["x_groups"] if cfg["x_groups"] and len(cfg["x_groups"]) == ngroups else (
        [round(v, 2) for v in gx] if gx else list(range(1, ngroups + 1)))

    series = {n: [] for n in cfg["legend"]}
    detail = {n: [] for n in cfg["legend"]}
    for g in groups:
        for bar in g:
            n = colour2name[bar["fill"]]
            series[n].append(bar["value"])
            detail[n].append(dict(value=bar["value"], top_y=bar["top"], top_edge_stroke_matches=bar["edge_top"] is not None,
                                  height_pt=bar["height_pt"], clipped_at_axis_top=bar["clipped"],
                                  x_left=bar["rect"][0], width=bar["rect"][2] - bar["rect"][0]))
    order = [[colour2name[b["fill"]] for b in g] for g in groups]
    censored = {n: [d["clipped_at_axis_top"] for d in detail[n]] for n in detail}
    rms = math.sqrt(sum(r * r for r in resid) / len(resid))

    hs = sorted(set(round(y - base_y, 4) for y in major + minor + [bb["top"] for bb in bars] if y - base_y > 0.5))
    q_err, q = min((math.sqrt(sum((h / u - round(h / u)) ** 2 for h in hs) / len(hs)), u)
                   for u in (i / 100000.0 for i in range(3000, 12001)))
    resolution = q * b
    tol = 0.5 * resolution + max(abs(r) for r in resid)

    vals = [v for n in series for v, c in zip(series[n], censored[n]) if not c]
    grids = {}
    for g in cfg["grids"]:
        if 2 * tol >= g:
            grids[str(g)] = dict(testable=False, note="grid finer than 2*tolerance")
            continue
        dev = [abs(v - round(v / g) * g) for v in vals]
        k = sum(d <= tol for d in dev)
        grids[str(g)] = dict(testable=True, n_within_tol=k, n=len(vals), chance_rate=min(1.0, 2 * tol / g),
                             expected_by_chance=len(vals) * min(1.0, 2 * tol / g))
    same = defaultdict(list)
    for n in detail:
        for i, d in enumerate(detail[n]):
            if not d["clipped_at_axis_top"]:
                same[round(d["height_pt"], 4)].append(f"{n}@{x_vals[i]}")
    repeats = {f"{h:.4f}pt -> {to_val(base_y + h):.4f}": v for h, v in same.items() if len(v) > 1}

    return dict(
        x=x_vals, x_label=cfg["x_label"], y_label=cfg["y_label"], title=cfg["title"],
        series=series,
        series_3dp={n: [round(v, 3) for v in vs] for n, vs in series.items()},
        censored=censored,
        censoring_note="no bar reaches the axis top" if not any(any(c) for c in censored.values()) else
        "censored=True: bar reaches the axis top",
        precision=dict(grid_quantum_pt=q, grid_fit_rms_in_quanta=q_err, value_resolution=resolution,
                       tolerance_used=tol, tolerance_def="0.5*value_resolution + max|tick residual|"),
        round_number_test=grids,
        identical_heights=repeats,
        bar_detail=detail,
        colour_to_series={",".join(f"{c:.3f}" for c in k): v for k, v in colour2name.items()},
        legend_order_top_to_bottom=cfg["legend"],
        in_group_bar_order=order[0], in_group_order_consistent=all(o == order[0] for o in order),
        group_centres_pt=group_centres,
        group_centres_axis_units=gx,
        x_calibration=xcal,
        x_minor_tick_pos=xminor_pos,
        calibration=dict(
            pdf_page=cfg["page"], coord_space="PDF page user space (pt, y up)",
            baseline_y=base_y, y_axis_x=axis_x, y_axis_top=y_top_axis, y_axis_bottom=y_bot_axis,
            major_tick_y=major, major_tick_values=cfg["y_major"], minor_tick_y=minor,
            fit="value = a + b*y", a=a, b=b, units_per_pt=b,
            major_residuals=resid, max_abs_residual=max(abs(r) for r in resid), rms_residual=rms,
            minor_tick_values=minor_vals, minor_tick_residual_vs_half_step=minor_resid,
            label_centre_minus_tick_y=label_check,
            baseline_value=to_val(base_y), axis_top_value=to_val(y_top_axis),
        ),
    )


def main():
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PDF
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "jan_targets.json")
    pdf = pikepdf.open(pdf_path)
    all_paths = {pn: parse(pdf.pages[pn - 1]) for pn in sorted({c["page"] for c in FIGS.values()})}
    res = {}
    for key, cfg in FIGS.items():
        res[key] = extract(pdf, key, cfg, all_paths)
    res["meta"] = dict(pdf_info={str(k): str(v) for k, v in pdf.docinfo.items()},
                       note="charts drawn inline in the page content stream (no Form XObjects, no raster images); "
                            "chart text outlined; pdf pages 8 (Figs 5,6) and 9 (Figs 7,8)")
    with open(out_path, "w") as f:
        json.dump(res, f, indent=1)
    for key, r in res.items():
        if not key.startswith("fig"):
            continue
        c = r["calibration"]
        print(f"\n{key}: {r['y_label']}  fit b={c['b']:.6f} units/pt  max|resid|={c['max_abs_residual']:.5f}  "
              f"rms={c['rms_residual']:.5f}  baseline={c['baseline_value']:.4f} top={c['axis_top_value']:.4f}")
        print("  label centre - tick y:", c["label_centre_minus_tick_y"])
        print("  x:", r["x"], " centres(axis units):", None if r["group_centres_axis_units"] is None else
              [round(v, 2) for v in r["group_centres_axis_units"]])
        for n, vs in r["series"].items():
            flags = ["*" if d["clipped_at_axis_top"] else "" for d in r["bar_detail"][n]]
            print(f"  {n:14s}", "  ".join(f"{v:9.4f}{f:1s}" for v, f in zip(vs, flags)))
        print("  bar order:", r["in_group_bar_order"], "consistent:", r["in_group_order_consistent"])
    print("\nwrote", out_path)


if __name__ == "__main__":
    main()
