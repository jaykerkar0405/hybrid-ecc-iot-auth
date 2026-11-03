# Pseudonym resolution: cost, design space and simulation

The base paper's server must map an incoming pseudonym `PID = H2(lambda || t)` to a device before it can decrypt M1, but
the paper does not specify how. This folder measures seven ways of doing it. One probe is one `H2` evaluation.

| Code | Strategy | Origin | Where |
|---|---|---|---|
| O1 | Counter epochs + linear scan (original behaviour) | OSK hash chains (Ohkubo et al. 2003) | `implementation/python/hybrid_ecc_auth/protocol/resolution.py` |
| O2 | Counter epochs + precomputed table | ours | same |
| O3 | Clock epochs + linear scan | ours | same |
| O4 | Clock epochs + table extended per epoch | YA-TRAP (Tsudik 2006) | same |
| TM | Rainbow time-memory trade-off | Avoine and Oechslin 2005; Avoine, Dysli and Oechslin 2005 | same |
| CR | Randomized hash lock (changes M1) | Weis et al. 2003 | `rfid_schemes.py` |
| MW | Key tree (changes M1) | Molnar and Wagner 2004 | `rfid_schemes.py` |

## Reproduce (from the repository root)

```bash
python -m pytest implementation/python/hybrid_ecc_auth/tests/unit/test_resolution.py -q      # 12 tests
python -I evaluation/resolution/resolution_costs.py           # measured.csv, cost_model.csv, summary.txt (~3 min)
evaluation/resolution/sim/build_and_run.sh                              # OMNeT++ 6.4, 960 runs -> sim/results.csv (~10 s)
python -I paper/make_figs.py                               # figures + ranked table
(cd paper && tectonic main.tex)
evaluation/formal_verification/run.sh                                             # ProVerif (paper version 2)
python -I evaluation/resolution/desync_check.py               # dropped-M1 and restart lockout
```

## Files

| File | Content |
|---|---|
| `resolution_costs.py` | Builds each server in steady state and counts probes for honest and forged pseudonyms, plus the resolution state, for N = 1 to 10,000. Asserts the closed forms. |
| `measured.csv` | One row per strategy and N, as measured |
| `cost_model.csv` | Probes and state for n = 0 to 10,000: the closed form where one exists, otherwise log-log interpolation of `measured.csv`. Read by the OMNeT++ model. |
| `summary.txt` | Result of the closed-form checks |
| `sim/ResolveNet.*` | Self-contained network model. The only change is that the server's resolution work comes from `cost_model.csv`, priced at T_H = 0.32 ms (Table III). |
| `sim/omnetpp.ini` | Table II environment and Tables III-V constants. `R_*` runs have 5% adversaries at 1 Hz; `H_*` runs have none. N = 1, 10, 100 to 1,000, 5 seeds. |
| `sim/results.csv` | One row per run (960 rows) |

## Conventions

- In the paper's table, the N = 1 column is the published value: 23.68 ms (Tables III and V) and 320 bits (Table VI).
  The model without resolution gives 23.86 ms at N = 1, the difference being airtime.
- Storage is Table VI's 320 bits per enrolled device plus the resolution state, with one table entry charged at 40 B.
- Assumptions that the paper does not fix: the adversary share and rate, the 10 s window, enrolment of every reachable
  device, and one O4 table extension per server per window.

The sweep draws peer secrets from OS randomness. In particular, TM coverage and measurements vary between runs. The committed CSVs and summary are the published run; preserve them when regenerating the paper figures.
