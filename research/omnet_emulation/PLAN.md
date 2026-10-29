> **Superseded by `baseline/BASELINE.md`** (baseline = published values + faithful re-implementation; no calibration was done).

# Plan: OMNeT++ emulation of the base paper's simulated results

Goal (mentor, non-negotiable): implement the base paper (Al-Rasheed et al., TCE 2026) in OMNeT++ and
reproduce its reported results exactly or very closely.

## What "the results" are

| Target | Source | Nature | How we hit it |
|---|---|---|---|
| Table IV comm. bits | p.4489 | arithmetic | sim emits per-session bits from message sizes: exact |
| Table V proc. cost | p.4489 x Table III | arithmetic | sim emits per-role op counts x Table III: exact |
| Table VI storage | p.4490 | arithmetic | sim emits per-entity stored bits: exact |
| Fig. 1 "Communication Overhead (%)" (caption: processing) | 6 schemes x 6 N (300-1800 vehicles) | rises with N, Gupta/Hassan18 clip at 100 | needs contention model + calibration |
| Fig. 2 "Communication Cost (bits)" | 5 schemes x 6 N | 22-41, rises with N | needs contention/retx model + calibration |
| Fig. 3 "Storage Overhead (%)" | 6 bars | 0.53-0.71 | needs a defined denominator + calibration |
| Abstract 17/21/12 % | p.4483 | claim | our own audit shows these are not derivable from Tables IV-VI; report which definition comes closest |

Facts established so far:
- Figs. 1-3 compare Gope 2016, Gupta 2019, Hassan 2018, Hassan 2023, Zhanfei 2024. None of these appear in
  the paper's tables or reference list. The x-axis is "Vehicles in VANET", not the 100-1000 IoT devices of Table II.
- The figures are vector graphics (no raster images on pp. 6-8), so exact bar heights can be extracted.
- The earlier OMNeT++ model (`research/reference_replication/omnet/AuthNet.*`) was an honest first-principles model
  and did NOT reproduce Fig. 1. A model can only match the figures by (a) recovering the setup that produced them,
  or (b) calibrating parameters the paper does not specify.

## Phase 0 results (2026-10-29)

- Targets: exact bar heights in `targets/fig_targets.json` (from the PDF vector paths, +/-0.02 / 0.007 / 1e-4).
  Fig. 3 and the Hassan 2023 / Zhanfei series of Fig. 2 sit on round-number grids; several bars in different
  series have identical heights. Gupta @1200 and Hassan 2018 @1800 are real values (99.883), not clipped.
- Provenance (`provenance.md`): base Fig. 1 = Fig. 6 of Al-Rasheed, Khan et al., CMC 84(1) 2025
  (DOI 10.32604/cmc.2025.064102, NS-3, "Devices in the IoT" 5-30), Proposed series unchanged, each competitor
  shifted by a per-series constant (+13 to +19), legends renamed (Ma -> Zhanfei, Kazmi -> Hassan 2023).
  Verified visually. Fig. 3 partly matches HybridEdge Fig. 6 (CMC 82(2) 2025). Fig. 2 source not found;
  probable parent Jan et al., IEEE IoT J. 2024 (DOI 10.1109/JIOT.2024.3483275, paywalled).
- Toolchain (`toolchain.md`): native headless OMNeT++ 6.4.0 with Apple clang (6.0.x/6.1.0 fail on clang 21);
  INET 4.6.0 if a real MAC is needed; Veins + SUMO via a locally built arm64 Docker image. AuthNet C++ needs no
  changes; scripts need macOS paths. Mac output goes to a separate CSV, never over `results/omnet_results.csv`.

Consequence: no simulation of this protocol produced Fig. 1. Matching it is curve fitting by definition.

## Integrity constraint (must be agreed with the mentor)

`paper/main.tex`, `FINDINGS.md` and the Black Book state Fig. 1 could not be reproduced. A simulation tuned to match
must be presented as a **calibrated reproduction**: every fitted parameter listed with its value and the fit
residual. Uncalibrated exact agreement is only possible if the figures' origin (setup + metric definitions) is found.

## Phases

**Phase 0: pin the targets (parallel)**
- A. Vector extraction: exact bar heights for Figs. 1-3 from PDF drawing operators; axis calibration from tick marks.
- B. Provenance: find the earlier paper(s) (likely same author group, VANET) with the same figures/schemes; identify
  the five comparison schemes, their op counts and message sizes; any metric definition for "overhead %".
- C. Toolchain: OMNeT++ 6.x (+ INET / Veins + SUMO) on Apple-silicon macOS, native vs Docker; reuse of AuthNet.

**Phase 1: reverse-engineer the metrics**
- Fit candidate metric definitions (channel utilisation %, control-overhead share, retransmission-inflated bits,
  storage share of a memory budget, ...) to the extracted values; pick the family with fewest free parameters
  that fits all schemes within tolerance.

**Phase 2: build the OMNeT++ model**
- Extend AuthNet (or move to INET 802.15.4 / Veins 802.11p if contention must come from a real MAC).
- Schemes: proposed + the five figure schemes + the Table IV-VI schemes. Parameters generated from tables.
- Outputs: per-N scalars for each figure metric, plus Tables IV-VI exactly.

**Phase 3: calibrate**
- Optimise the unspecified parameters (adversary rate, beacon/auth interval, retx limit, payload overheads,
  memory budget, ...) against the extracted targets. Seeds fixed, repetitions reported.
- Acceptance: agreed tolerance (proposal: every bar within +/-1 axis unit and RMS <= 0.5 per figure).

**Phase 4: report**
- Overlay plots (paper vs sim), residual table, fitted-parameter table, reproducibility script.

## Needed from the user / mentor
1. Tolerance that counts as "very very close".
2. Confirmation that a disclosed calibrated model is acceptable.
3. PDFs (via institutional access) of Gope 2016, Gupta 2019, Hassan 2018, Hassan 2023, Zhanfei 2024 once identified.
4. Which machine runs OMNeT++ (this Mac, M2 Pro, or the WSL box used before).
