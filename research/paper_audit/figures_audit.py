#!/usr/bin/env python3
"""Do Figs. 1-3 of the paper yield the abstract's 17% (communication), 21% (processing), 12% (storage)?
Bar heights were READ BY EYE from 600-DPI renders of the figures (axis tick spacing 2 units for Figs 1-2,
0.05 for Fig 3), so values carry roughly +/-0.2 (Figs 1-2) and +/-0.003 (Fig 3) of reading error. Bars that run
past the axis top in Fig. 1 are clipped at 100 and are therefore censored (marked * below)."""
import itertools, statistics as st

N = [300, 600, 900, 1200, 1500, 1800]  # "Vehicles in VANET"

# Fig. 1 (journal p.4488) captioned "Processing requirements" but y-axis reads "Communication Overhead (%)", axis 30-100
FIG1 = {
    "Proposed":       [42.7, 44.8, 47.3, 50.5, 52.5, 63.5],
    "Zhanfei 2024":   [72.7, 76.9, 81.8, 86.2, 90.8, 92.5],
    "Hassan 2023":    [65.0, 69.7, 70.5, 74.5, 77.9, 84.1],
    "Gupta 2019":     [94.8, 96.8, 100.0, 99.9, 100.0, 100.0],   # 900, 1500, 1800 clipped (*)
    "Gope 2016":      [86.2, 88.0, 90.3, 92.5, 95.2, 96.4],
    "Hassan 2018":    [89.3, 91.8, 89.0, 94.9, 97.9, 100.0],     # 1800 clipped (*)
}
# Fig. 2 (p.4489) captioned "Communication requirements", y-axis "Communication Cost (bits)", axis 20-44
FIG2 = {
    "Proposed":     [22.4, 23.35, 24.75, 25.85, 27.1, 28.6],
    "Gope 2016":    [29.95, 31.5, 34.5, 37.15, 38.5, 40.75],
    "Gupta 2019":   [27.7, 30.5, 32.5, 35.2, 34.5, 37.75],
    "Hassan 2023":  [28.5, 31.5, 33.5, 35.5, 36.0, 39.0],
    "Zhanfei 2024": [29.0, 33.5, 36.0, 38.5, 40.35, 41.5],
}
# Fig. 3 (p.4490) "Storage Overhead (%)", axis 0.50-0.75, single group of bars
FIG3 = {"Proposed": [0.53], "Zhanfei 2024": [0.57], "Hassan 2023": [0.63], "Gupta 2019": [0.615],
        "Hassan 2018": [0.66], "Gope 2016": [0.71]}

def stats(fig):
    prop = fig["Proposed"]; others = {k: v for k, v in fig.items() if k != "Proposed"}
    n = len(prop); out = {}
    red = lambda ref, p: 100 * (1 - p / ref)
    per_n = lambda f: [f([v[i] for v in others.values()]) for i in range(n)]
    out["vs best, mean over x"] = st.mean(red(b, p) for b, p in zip(per_n(min), prop))
    out["vs mean-of-others, mean over x"] = st.mean(red(m, p) for m, p in zip(per_n(st.mean), prop))
    out["vs median-of-others, mean over x"] = st.mean(red(m, p) for m, p in zip(per_n(st.median), prop))
    out["vs worst, mean over x"] = st.mean(red(w, p) for w, p in zip(per_n(max), prop))
    out["mean over every (scheme, x) pair"] = st.mean(red(v[i], prop[i]) for v in others.values() for i in range(n))
    out["first x only, vs best"] = red(per_n(min)[0], prop[0])
    out["last x only, vs best"] = red(per_n(min)[-1], prop[-1])
    out["ratio of sums vs sum-of-means"] = 100 * (1 - sum(prop) / sum(per_n(st.mean)))
    out["abs. difference vs mean, mean over x (same units)"] = st.mean(m - p for m, p in zip(per_n(st.mean), prop))
    return out

targets = {"Fig 1 (caption: processing; axis: communication %)": (FIG1, 21), "Fig 2 (communication, bits)": (FIG2, 17), "Fig 3 (storage %)": (FIG3, 12)}
for name, (fig, claim) in targets.items():
    print(f"\n=== {name}  -- abstract claims ~{claim}% for the matching metric ===")
    for k, v in stats(fig).items():
        flag = "  <-- within 1 of the claim" if abs(v - claim) <= 1 else ""
        print(f"  {k:52s} {v:7.2f}{flag}")
print("\nOther inconsistencies visible in the figures:")
print("  * Fig. 1/2 x-axis is 'Vehicles in VANET' (300-1800); Table II and the paper's scope are IoT devices (100-1000), static only (conclusion).")
print("  * Fig. 2 shows the proposed scheme's per-authentication bit cost rising from 22.4 to 28.6 with the number of vehicles;")
print("    a fixed two-message protocol has a fixed bit count, independent of network size.")
print("  * Fig. 2 plots 22-41 'bits' while the text says 264 bits and Table IV says 1024 bits for the proposed scheme.")
print("  * Fig. 1 bars for Gupta 2019 and Hassan 2018 exceed the 100% axis limit and are clipped.")
