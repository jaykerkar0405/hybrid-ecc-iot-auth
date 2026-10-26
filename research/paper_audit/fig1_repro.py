#!/usr/bin/env python3
"""Time-boxed attempt to reproduce Fig. 1 of the base paper with a deterministic cost model.

Fig. 1 plots an "overhead %" against the number of vehicles (300-1800) for six schemes. The paper's own cost
method (Table V operation counts x Table III constants) gives a per-authentication cost that does not depend on
the number of vehicles, so under that method every curve should be a horizontal line. We test that, then ask how
well the best affine-in-N model per scheme (2 free parameters each, 12 for 36 points) explains the curves, and
whether the curves are even monotone. Values are digitised by eye (+/-0.2 axis units); Gupta 2019 (3 points) and
Hassan 2018 (1 point) are clipped at 100 and are treated as censored (excluded from residual statistics).
We do NOT model Gope/Gupta/Hassan/Zhanfei: they are not cited, so which protocol each one is cannot be established.
"""
import numpy as np
from figures_audit_data import FIG1, N

READ_ERR = 0.2
CENSORED = {("Gupta 2019", 2), ("Gupta 2019", 4), ("Gupta 2019", 5), ("Hassan 2018", 5)}
x = np.array(N, float)

print("=== 1. Flat model (the paper's own cost method: constant in N) ===")
rms_flat = {}
for k, v in FIG1.items():
    idx = [i for i in range(len(v)) if (k, i) not in CENSORED]
    y = np.array([v[i] for i in idx]); r = y - y.mean()
    rms_flat[k] = float(np.sqrt((r**2).mean()))
    print(f"  {k:14s} range {y.min():5.1f}-{y.max():5.1f}  rise {y[-1]-y[0]:+6.1f}  best-flat RMS residual {rms_flat[k]:5.2f}  ({rms_flat[k]/READ_ERR:4.0f}x reading error)")

print("\n=== 2. Best affine model per scheme (2 params each) ===")
for k, v in FIG1.items():
    idx = [i for i in range(len(v)) if (k, i) not in CENSORED]
    xs, y = x[idx], np.array([v[i] for i in idx])
    a, b = np.polyfit(xs, y, 1); r = y - (a * xs + b)
    print(f"  {k:14s} slope {a*100:5.2f} per 100 vehicles  RMS residual {np.sqrt((r**2).mean()):4.2f}  max |res| {abs(r).max():4.2f}"
          f"  ({abs(r).max()/READ_ERR:3.0f}x reading error)")

print("\n=== 3. Monotonicity (point-to-point decreases larger than reading error) ===")
for k, v in FIG1.items():
    dec = [(N[i], N[i+1], v[i+1]-v[i]) for i in range(len(v)-1)
           if (k, i) not in CENSORED and (k, i+1) not in CENSORED and v[i+1]-v[i] < -2*READ_ERR]
    print(f"  {k:14s} {dec if dec else 'none'}")

print("\n=== 4. Step sizes of the proposed curve (a fixed-op-count protocol should not accelerate) ===")
p = FIG1["Proposed"]
print("  increments per 300 vehicles:", [round(p[i+1]-p[i], 1) for i in range(5)])
