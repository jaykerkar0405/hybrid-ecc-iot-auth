#!/usr/bin/env python3
"""Extract exact bar heights of Figs. 1-3 of the base paper (Al-Rasheed et al., IEEE TCE 2026)
from the vector graphics in the PDF.

The three charts are embedded as pdfTeX Form XObjects (Im5 on PDF p.6, Im7 on p.7, Im9 on p.8), each an
Adobe Illustrator 26.5 re-save of the original chart with all text converted to outlines (no fonts).
This script interprets each XObject content stream directly (q/Q/cm/re/m/l/c/W/f/S/rg/RG ...), so all
coordinates are in XObject space (the page placement is a pure translation + ~1.0001 scale, which a
linear calibration absorbs anyway).

Pipeline per figure:
  1. collect painted paths with their fill/stroke colour, CTM-transformed bbox and active clip rect;
  2. y-axis calibration: the short horizontal stroked tick marks that end on the y-axis line; long ones
     are major (labelled) ticks.  Tick label values are taken from the rendered figure (labels are
     outlined glyphs) and assigned bottom-to-top; the script checks each major tick has a glyph cluster
     immediately to its left whose vertical centre matches the tick.  value = a + b*y by least squares
     over all major ticks; residuals reported;
  3. bars: filled rectangles whose bottom sits on the x-axis baseline; the top is taken from the separate
     black top-edge stroke (4-dp cm translation) where present, else the fill rect top;
  4. series: legend swatches (filled rects not on the baseline) sorted top-to-bottom, matched by exact
     fill colour; legend label order read off the render (hard-coded below, checked by colour count);
  5. clipping: a bar whose fill top equals the plot clip/axis top and which has no top-edge stroke is
     flagged as clipped (the raw unclipped height is not present in the file).

Usage: python -I extract_figs.py [path/to/base_paper.pdf] [out.json]
"""
import json
import math
import os
import sys

import pikepdf

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PDF = os.path.join(HERE, "..", "..", "..", "docs", "references", "base_paper.pdf")

FIGS = {
    "fig1": dict(page=6, xobj="/Im5",
                 y_label="Communication Overhead (%)", x_label="Vehicles in VANET",
                 y_major=[30, 40, 50, 60, 70, 80, 90, 100],
                 x=[300, 600, 900, 1200, 1500, 1800],
                 legend=["Proposed", "Zhanfei 2024", "Hassan 2023", "Gupta 2019", "Gope 2016", "Hassan 2018"]),
    "fig2": dict(page=7, xobj="/Im7",
                 y_label="Communication Cost (bits)", x_label="Vehicles in VANET",
                 y_major=[20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44],
                 x=[300, 600, 900, 1200, 1500, 1800],
                 legend=["Gope 2016", "Gupta 2019", "Hassan 2023", "Zhanfei 2024", "Proposed"]),
    "fig3": dict(page=8, xobj="/Im9",
                 y_label="Storage Overhead (%)", x_label="Proposed and Existing Schemes",
                 y_major=[0.50, 0.55, 0.60, 0.65, 0.70, 0.75],
                 x=["single group"],
                 legend=["Proposed", "Zhanfei 2024", "Hassan 2023", "Gupta 2019", "Hassan 2018", "Gope 2016"]),
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


# Earlier eyeball digitisation (research/paper_audit/figures_audit.py), for deltas.
EYEBALL = {
    "fig1": {"Proposed": [42.7, 44.8, 47.3, 50.5, 52.5, 63.5],
             "Zhanfei 2024": [72.7, 76.9, 81.8, 86.2, 90.8, 92.5],
             "Hassan 2023": [65.0, 69.7, 70.5, 74.5, 77.9, 84.1],
             "Gupta 2019": [94.8, 96.8, 100.0, 99.9, 100.0, 100.0],
             "Gope 2016": [86.2, 88.0, 90.3, 92.5, 95.2, 96.4],
             "Hassan 2018": [89.3, 91.8, 89.0, 94.9, 97.9, 100.0]},
    "fig2": {"Proposed": [22.4, 23.35, 24.75, 25.85, 27.1, 28.6],
             "Gope 2016": [29.95, 31.5, 34.5, 37.15, 38.5, 40.75],
             "Gupta 2019": [27.7, 30.5, 32.5, 35.2, 34.5, 37.75],
             "Hassan 2023": [28.5, 31.5, 33.5, 35.5, 36.0, 39.0],
             "Zhanfei 2024": [29.0, 33.5, 36.0, 38.5, 40.35, 41.5]},
    "fig3": {"Proposed": [0.53], "Zhanfei 2024": [0.57], "Hassan 2023": [0.63], "Gupta 2019": [0.615],
             "Hassan 2018": [0.66], "Gope 2016": [0.71]},
}

MARKERS = [b"Origin", b"OriginLab", b"MATLAB", b"Matlab", b"Excel", b"matplotlib", b"gnuplot", b"SigmaPlot",
           b"GraphPad", b"Prism", b"/PieceInfo", b"/Metadata", b"AIPrivateData", b"Illustrator"]


def scan_markers(pdf):
    """Count software marker strings across all (decompressed) streams and object dicts."""
    hits = {m.decode(): 0 for m in MARKERS}
    where = {m.decode(): set() for m in MARKERS}
    for obj in pdf.objects:
        blobs = []
        try:
            blobs.append(repr(obj).encode("latin1", "replace"))
        except Exception:
            pass
        if isinstance(obj, pikepdf.Stream):
            try:
                blobs.append(obj.read_bytes())
            except Exception:
                pass
        for blob in blobs:
            for m in MARKERS:
                c = blob.count(m)
                if c:
                    hits[m.decode()] += c
                    where[m.decode()].add(obj.objgen[0])
    return {k: dict(count=v, objects=sorted(where[k])[:20]) for k, v in hits.items()}


def extract(pdf, key, cfg):
    xobj = pdf.pages[cfg["page"] - 1].Resources.XObject[cfg["xobj"]]
    paths = parse(xobj)
    eps = 0.02

    # --- axes: long black stroked horizontal line = x-axis, long vertical = y-axis
    lines = [(p, s) for p in paths if p["op"] == "S" for s in p["segs"]]
    hlines = [(p, s) for p, s in lines if abs(s[0][1] - s[1][1]) < 1e-6 and abs(s[0][0] - s[1][0]) > 0]
    vlines = [(p, s) for p, s in lines if abs(s[0][0] - s[1][0]) < 1e-6 and abs(s[0][1] - s[1][1]) > 0]
    hlen = lambda s: abs(s[0][0] - s[1][0])
    vlen = lambda s: abs(s[0][1] - s[1][1])
    hmax = max(hlen(s) for _, s in hlines)
    vmax = max(vlen(s) for _, s in vlines)
    # x-axis: lowest of the longest horizontal lines; y-axis: leftmost of the longest vertical lines
    # (bar side edges of clipped bars are as long as the y-axis, so take the leftmost)
    xaxis = min((s for _, s in hlines if hlen(s) > 0.95 * hmax), key=lambda s: s[0][1])
    yaxis = min((s for _, s in vlines if vlen(s) > 0.95 * vmax), key=lambda s: s[0][0])
    base_y = xaxis[0][1]
    axis_x = yaxis[0][0]
    y_top_axis = max(yaxis[0][1], yaxis[1][1])

    # --- y ticks: short horizontal black strokes whose right end touches the y-axis line
    ticks = []
    for p, s in hlines:
        x0, x1 = sorted((s[0][0], s[1][0]))
        if abs(x1 - axis_x) < 0.01 and (x1 - x0) < 5 and p["stroke"] == (0, 0, 0):
            ticks.append((s[0][1], x1 - x0))
    ticks = sorted(set((round(y, 4), round(L, 3)) for y, L in ticks))
    Lmax = max(L for _, L in ticks)
    major = [y for y, L in ticks if L > 0.75 * Lmax]
    minor = [y for y, L in ticks if L <= 0.75 * Lmax]
    assert len(major) == len(cfg["y_major"]), (key, major)

    # --- check each major tick has a label cluster just left of it, vertically centred
    glyphs = [p["bbox"] for p in paths if p["op"] in ("f", "f*") and (p["ncurves"] > 0 or p["segs"]) and p["fill"] == (0, 0, 0)
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
    step = (cfg["y_major"][1] - cfg["y_major"][0])
    minor_vals = [to_val(y) for y in minor]
    minor_resid = [v - (round(v / (step / 2)) * (step / 2)) for v in minor_vals]

    # --- bars and legend swatches
    fills = [p for p in paths if p["op"] in ("f", "f*", "F", "B", "B*", "b", "b*") and p["rects"] and p["ncurves"] == 0
             and len(p["rects"]) == 1]
    bars, swatches = [], []
    for p in fills:
        r = p["rects"][0]
        w, h = r[2] - r[0], r[3] - r[1]
        if w > 150 or h > 150:
            continue
        if abs(r[1] - base_y) < eps:
            bars.append(dict(rect=r, fill=p["fill"], clip=p["clip"]))
        elif r[1] > base_y + 5 and 3 < w < 15 and 1.5 < h < 7 and p["fill"] != (1, 1, 1):  # legend swatch (not glyph strokes)
            swatches.append(dict(rect=r, fill=p["fill"]))
    # legend: dedupe by colour, order top->bottom
    sw = {}
    for s in sorted(swatches, key=lambda s: -s["rect"][3]):
        sw.setdefault(s["fill"], s)
    sw_order = sorted(sw.values(), key=lambda s: -s["rect"][3])
    assert len(sw_order) == len(cfg["legend"]), (key, [s["fill"] for s in sw_order])
    colour2name = {s["fill"]: name for s, name in zip(sw_order, cfg["legend"])}

    # --- top edges: black (or same-colour) horizontal strokes at the top of each bar
    top_edges = [(s[0][1], min(s[0][0], s[1][0]), max(s[0][0], s[1][0])) for p, s in hlines]

    clip_top = None
    for bar in bars:
        r = bar["rect"]
        edge = [y for y, x0, x1 in top_edges if abs(x0 - r[0]) < 0.01 and abs(x1 - r[2]) < 0.01 and abs(y - r[3]) < 0.01]
        bar["fill_top"] = r[3]
        bar["edge_top"] = edge[0] if edge else None
        bar["top"] = edge[0] if edge else r[3]
        bar["height_pt"] = bar["top"] - base_y
        bar["value"] = to_val(bar["top"])
        bar["value_fill"] = to_val(r[3])
        bar["clipped"] = bar["edge_top"] is None and abs(r[3] - y_top_axis) < 0.01
        # clip state of the bar's stroked outline / side edges (the fill itself may be unclipped)
        oc = set()
        for p in paths:
            if p["op"] not in ("S", "s") or p["bbox"] is None or p["clip"] is None:
                continue
            bb = p["bbox"]
            if bb[0] > r[0] - 0.01 and bb[2] < r[2] + 0.01 and bb[1] > r[1] - 0.01 and bb[3] < r[3] + 0.01:
                if p["clip"][2] - p["clip"][0] < 170:  # ignore the whole-artboard clip
                    oc.add(tuple(round(c, 4) for c in p["clip"]))
        bar["outline_clip"] = sorted(oc)
        if bar["clip"]:
            clip_top = bar["clip"][3]

    # group bars into x groups by centre
    bars.sort(key=lambda b: b["rect"][0])
    ngroups = len(cfg["x"])
    nser = len(cfg["legend"])
    assert len(bars) == ngroups * nser, (key, len(bars))
    series = {n: [] for n in cfg["legend"]}
    detail = {n: [] for n in cfg["legend"]}
    group_centres = []
    for g in range(ngroups):
        grp = bars[g * nser:(g + 1) * nser]
        group_centres.append((grp[0]["rect"][0] + grp[-1]["rect"][2]) / 2)
        for bar in grp:
            n = colour2name[bar["fill"]]
            series[n].append(bar["value"])
            detail[n].append(dict(value=bar["value"], value_from_fill_rect=bar["value_fill"],
                                  top_y=bar["top"], fill_top_y=bar["fill_top"], top_edge_stroke=bar["edge_top"] is not None,
                                  height_pt=bar["height_pt"], clipped_at_axis_top=bar["clipped"],
                                  fill_drawn_inside_clip=bar["clip"] is not None,
                                  outline_clip_rects=bar["outline_clip"],
                                  bottom_on_baseline=abs(bar["rect"][1] - base_y) < 1e-3,
                                  x_left=bar["rect"][0], width=bar["rect"][2] - bar["rect"][0]))
    # in-group order check
    order = [[colour2name[b["fill"]] for b in bars[g * nser:(g + 1) * nser]] for g in range(ngroups)]

    censored = {n: [d["clipped_at_axis_top"] for d in detail[n]] for n in detail}
    rms = math.sqrt(sum(r * r for r in resid) / len(resid))

    # device-grid quantum of the source renderer: all heights (ticks + bar tops) are ~integer multiples of q pt
    hs = sorted(set(round(y - base_y, 4) for y in major + minor + [bb["top"] for bb in bars] if y - base_y > 0.5))
    q_err, q = min((math.sqrt(sum((h / u - round(h / u)) ** 2 for h in hs) / len(hs)), u)
                   for u in (i / 100000.0 for i in range(3000, 12001)))
    resolution = q * b
    tol = 0.5 * resolution + max(abs(r) for r in resid)

    # round-number test over uncensored bars
    vals = [v for n in series for v, c in zip(series[n], censored[n]) if not c]
    grids = {}
    for g in (1.0, 0.5, 0.25, 0.1, 0.05, 0.01, 0.005):
        if 2 * tol >= g:
            grids[str(g)] = dict(testable=False, note="grid finer than 2*tolerance")
            continue
        dev = [abs(v - round(v / g) * g) for v in vals]
        k = sum(d <= tol for d in dev)
        grids[str(g)] = dict(testable=True, n_within_tol=k, n=len(vals), chance_rate=min(1.0, 2 * tol / g),
                             expected_by_chance=len(vals) * min(1.0, 2 * tol / g))
    # identical heights across different bars
    from collections import defaultdict
    same = defaultdict(list)
    for n in detail:
        for i, d in enumerate(detail[n]):
            if not d["clipped_at_axis_top"]:
                same[round(d["height_pt"], 4)].append(f"{n}@{cfg['x'][i]}")
    repeats = {f"{h:.4f}pt -> {to_val(base_y + h):.4f}": v for h, v in same.items() if len(v) > 1}

    clip_rects = sorted({tuple(c) for bb in bars for c in bb["outline_clip"]})

    return dict(
        x=cfg["x"], x_label=cfg["x_label"], y_label=cfg["y_label"],
        series=series,
        series_3dp={n: [round(v, 3) for v in vs] for n, vs in series.items()},
        censored=censored,
        censoring_note=("censored=True: bar reaches the axis top (fill rect truncated to the axis limit by the source "
                        "software, no top-edge stroke); true value >= axis max, raw height NOT recoverable from the file")
        if any(any(c) for c in censored.values()) else "no bar reaches the axis top",
        outline_clip_rects=[dict(x0=c[0], y0=c[1], x1=c[2], y1=c[3], top_value=to_val(c[3])) for c in clip_rects],
        precision=dict(grid_quantum_pt=q, grid_fit_rms_in_quanta=q_err, value_resolution=resolution,
                       tolerance_used=tol, tolerance_def="0.5*value_resolution + max|tick residual|"),
        round_number_test=grids,
        identical_heights=repeats,
        bar_detail=detail,
        colour_to_series={",".join(f"{c:.3f}" for c in k): v for k, v in colour2name.items()},
        in_group_bar_order=order[0], in_group_order_consistent=all(o == order[0] for o in order),
        group_centres_pt=group_centres,
        calibration=dict(
            pdf_page=cfg["page"], xobject=cfg["xobj"][1:], coord_space="XObject user space (pt, y up)",
            baseline_y=base_y, y_axis_x=axis_x, y_axis_top=y_top_axis, plot_clip_top=clip_top,
            major_tick_y=major, major_tick_values=cfg["y_major"], minor_tick_y=minor,
            fit="value = a + b*y", a=a, b=b, units_per_pt=b,
            major_residuals=resid, max_abs_residual=max(abs(r) for r in resid),
            rms_residual=rms,
            minor_tick_values=minor_vals, minor_tick_residual_vs_half_step=minor_resid,
            label_centre_minus_tick_y=label_check,
            baseline_value=to_val(base_y),
        ),
    )


def main():
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PDF
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "fig_targets.json")
    pdf = pikepdf.open(pdf_path)
    res = {}
    for key, cfg in FIGS.items():
        res[key] = extract(pdf, key, cfg)
        xo = pdf.pages[cfg["page"] - 1].Resources.XObject[cfg["xobj"]]
        info = xo.get("/PTEX.InfoDict")
        res[key]["provenance"] = dict(
            ptex_filename=str(xo.get("/PTEX.FileName")),
            info={str(k): str(v) for k, v in info.items()} if info is not None else None,
            fonts_in_xobject=list(map(str, xo.Resources.get("/Font", {}).keys())),
            note="text is outlined (no fonts); file is an Adobe Illustrator 26.5 re-save of the chart",
        )
        eb = EYEBALL[key]
        res[key]["delta_vs_eyeball"] = {
            n: [None if (c or eb[n][i] is None) else round(v - eb[n][i], 4)
                for i, (v, c) in enumerate(zip(vs, res[key]["censored"][n]))]
            for n, vs in res[key]["series"].items()}
    res["meta"] = dict(pdf_info={str(k): str(v) for k, v in pdf.docinfo.items()}, software_marker_scan=scan_markers(pdf),
                       eyeball_source="research/paper_audit/figures_audit.py (FIG1-3)")
    with open(out_path, "w") as f:
        json.dump(res, f, indent=1)
    for key, r in res.items():
        if not key.startswith("fig"):
            continue
        c = r["calibration"]
        print(f"\n{key}: {r['y_label']}  fit b={c['b']:.6f} units/pt  max|resid|={c['max_abs_residual']:.4f}  "
              f"rms={c['rms_residual']:.4f}  baseline={c['baseline_value']:.4f}")
        print("  label centre - tick y:", c["label_centre_minus_tick_y"])
        print("  x:", r["x"])
        for n, vs in r["series"].items():
            flags = ["*" if d["clipped_at_axis_top"] else "" for d in r["bar_detail"][n]]
            print(f"  {n:14s}", "  ".join(f"{v:9.4f}{f:1s}" for v, f in zip(vs, flags)))
    print("\nwrote", out_path)


if __name__ == "__main__":
    main()
