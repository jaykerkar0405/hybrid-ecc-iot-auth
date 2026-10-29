#!/usr/bin/env python3
"""Shape checks on Jan et al. Figs 5-7 values (jan_targets.json): linear-in-N fits, and consistency with Tables III/IV
(ops x per-op time; bits).  Standard library only.  python -I jan_shape.py"""
import json, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
J = json.load(open(os.path.join(HERE, "jan_targets.json")))
def ols(x, y):
    n = len(x); mx = sum(x)/n; my = sum(y)/n
    sxx = sum((a-mx)**2 for a in x); b = sum((a-mx)*(c-my) for a, c in zip(x, y))/sxx; a0 = my-b*mx
    ss = sum((c-my)**2 for c in y); sr = sum((c-(a0+b*a))**2 for a, c in zip(x, y))
    return a0, b, 1-sr/ss, math.sqrt(sr/n)
out = {}
for k, xs in (("fig5", [200,400,600,800,1000,1200]), ("fig6", [2,4,6,8,10,12]), ("fig7", [100,300,500,700,900,1100])):
    out[k] = {}
    for s, v in J[k]["series"].items():
        a, b, r2, rm = ols(xs, v)
        qa = ols([x*x for x in xs], v)
        out[k][s] = dict(intercept=a, slope_per_unit=b, R2=r2, rms=rm, total_rise=v[-1]-v[0], rise_pct=100*(v[-1]/v[0]-1),
                         steps=[round(v[i+1]-v[i], 3) for i in range(5)], R2_quadratic_in_x=qa[2])
    print(k, J[k]["y_label"])
    for s, d in out[k].items():
        print(f"  {s:13s} a={d['intercept']:7.3f} slope={d['slope_per_unit']:.5f} R2={d['R2']:.4f} rise={d['total_rise']:.2f} ({d['rise_pct']:.0f}%) steps={d['steps']}")
# ops x per-op: Table III totals (Th, XOR) and Fig 5 at each group
tot = {"Proposed": (4, 6), "Gupta 2019": (16, 11), "Gope 2016": (12, 5), "Hassan 2018": (7, 14)}
dev = {"Proposed": (2, 3), "Gupta 2019": (4, 4), "Hassan 2018": (2, 5)}
def solve2(p, q, tp, tq):  # a*h + b*x = t
    d = p[0]*q[1]-p[1]*q[0]
    return ((tp*q[1]-tq*p[1])/d, (p[0]*tq-q[0]*tp)/d)
rep = {}
for g in range(6):
    t = {s: J["fig5"]["series"][s][g] for s in tot}
    # least squares on 4 totals
    A = [[tot[s][0], tot[s][1]] for s in tot]; y = [t[s] for s in tot]
    ata = [[sum(r[i]*r[j] for r in A) for j in range(2)] for i in range(2)]
    aty = [sum(r[i]*yy for r, yy in zip(A, y)) for i in range(2)]
    d = ata[0][0]*ata[1][1]-ata[0][1]*ata[1][0]
    h = (aty[0]*ata[1][1]-aty[1]*ata[0][1])/d; x = (ata[0][0]*aty[1]-ata[1][0]*aty[0])/d
    res = {s: t[s]-(h*tot[s][0]+x*tot[s][1]) for s in tot}
    dh, dx = solve2(dev["Proposed"], dev["Hassan 2018"], J["fig5"]["series"]["Proposed"][g], J["fig5"]["series"]["Hassan 2018"][g])
    rep[g] = dict(total_cost_LS_Th=h, total_cost_LS_Txor=x, resid=res,
                  device_col_Proposed_Hassan18_exact_solve=(dh, dx),
                  device_col_pred_Gupta=dh*4+dx*4, gupta_actual=J["fig5"]["series"]["Gupta 2019"][g])
out["ops_vs_fig5"] = rep
print("ops fit at 200 veh:", rep[0])
print("ops fit at 1200 veh:", rep[5])
# bits vs delay (Fig 7)
bits = {"Proposed": 512, "Hassan 2023": 672, "Zhanfei 2024": 3392, "Gupta 2019": 3038, "Gope 2016": 3184}
msgs = {"Proposed": 4, "Hassan 2023": 6, "Zhanfei 2024": 3, "Gupta 2019": 5, "Gope 2016": 4}
def pear(a, b):
    ma, mb = sum(a)/len(a), sum(b)/len(b)
    return sum((x-ma)*(y-mb) for x, y in zip(a, b))/math.sqrt(sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b))
out["bits_vs_delay"] = {}
for g in range(6):
    names = list(bits); d = [J["fig7"]["series"][s][g] for s in names]
    out["bits_vs_delay"][g] = dict(pearson_bits=pear([bits[s] for s in names], d), pearson_msgs=pear([msgs[s] for s in names], d),
                                   delays=dict(zip(names, d)))
    print("g", g, "r(bits)=%.3f r(msgs)=%.3f" % (out["bits_vs_delay"][g]["pearson_bits"], out["bits_vs_delay"][g]["pearson_msgs"]))
json.dump(out, open(os.path.join(HERE, "shape.json"), "w"), indent=1)
