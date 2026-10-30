# Base-paper baseline: what reproduces, what does not

Base paper: Al-Rasheed et al., IEEE TCE 72(2), 2026 (DOI 10.1109/TCE.2026.3662053).
Nothing below is fitted. Layer A is the published values as data. Layer B is a re-implementation in OMNeT++ 6.4.0
(macOS arm64) of the environment and costs the paper states.

## Layer A: published values

`published_baseline.json` (built by `build_published_baseline.py`): Table II environment, Tables III-VI, the
abstract's claims, and the exact bar heights of Figs. 1-3 (extracted from the PDF vector paths, +/-0.02 / 0.007 / 1e-4).

## Layer B: simulation (`../sim/`)

Model: `AuthNet.ned/.cc` (our re-implementation of the Table II environment; the base authors publish no code).
Inputs are generated from the paper's Tables III-V by `gen_omnet_ini.py`. `build_and_run.sh` builds and runs on macOS.
`omnet_results_macos.csv`: the earlier 3,385-run sweep re-run on this Mac; every row agrees with the stored WSL/OMNeT++ 6.0.3 results to a
relative difference of 5e-14 (the stored file is rounded to 14 significant digits).
`omnet_results_ext.csv` + `omnetpp_ext.ini`: added here (hash-indexed lookup variants; adversary-free runs; `HM_`/`AHM_` = the same with the measured ESP8266 80 MHz constants, used by `paper/make_figs.py`).
`baseline_compare.py` prints the comparison below.

**What Layer B does and does not show.** Table IV bits and Table V operation counts are *inputs* to the model
(`gen_omnet_ini.py` writes them into the ini), so the simulation echoing them back confirms the pipeline, not the paper.
The model adds two things the tables cannot give: contention/queueing effects and the cost of the server's pseudonym
lookup. With a hash-indexed lookup the proposed scheme's latency is flat across 300-1800 devices (24.04-24.09 ms), so the
simulation adds essentially nothing beyond the paper's own cost arithmetic; all N-dependence comes from the linear-scan
assumption, which the paper does not state.

| Quantity | Published | Simulated | Status |
|---|---|---|---|
| Table IV: bits per session, 9 schemes | 1024 / 3360 / 2720 / 2528 / 2272 / 1952 / 2368 / 2592 / 1600 | identical to 3 dp, no adversaries | Consistency check (input = output) |
| Proposed processing per session | Table V x III: 2T_H+2T_SE/D per side = 23.68 ms | 23.98 ms uncontended, hash-indexed lookup (+0.3 ms airtime) | Consistency check |
| Communication ranking (bits on air, N = 1000) | proposed lowest | proposed lowest of 9 | Follows from Table IV alone |
| Processing ranking | proposed lowest | **4th of 9**: 24.1 ms vs 4.2 / 4.8 / 5.1 (Turkanovic / Dhillon-Karla / Jiang); last of 9 with a linear pseudonym scan (19,010 ms at N = 1000). Still 4th of 9 if the User/Client column is also charged (23.68 vs 6.08 / 7.04 / 7.04 ms) | **Not reproduced**; follows from Table V x III alone |
| Table VI storage | 320 / 320 bits | not a simulated quantity | Arithmetic only (see `research/paper_audit`) |
| Figs. 1-3 as plotted | see JSON | not produced by any simulation: Jan et al. (IEEE IoT J. 2025) Figs. 5, 7, 8 plus constants (`../jan_compare/FINDINGS.md`). Side-by-side: `published_vs_simulated.png` | **Not derivable** |
| Abstract 17% / 21% / 12% | -- | no single definition reproduces all three (about 100 tried) | **Not derivable** |

Why the processing claim fails: the paper's own Table V gives the proposed scheme 2 hashes + 2 symmetric operations per
side; at its Table III timings (T_SE/D = 5.6 ms) that is 23.7 ms per session, against 3.8-7 ms for the hash-only schemes.
No simulation assumption is involved.

Modelling choices the paper does not specify (reported, not tuned): the device and server costs are charged but the User/Client role is not (checked: the ranking is unchanged if it is); how a server resolves a pseudonym (linear scan or
hash index), the adversary share and rate (5%, 1/s), the arrival window (10 s), and enrolment (every device in range).
The linear-scan variant is the existing model's choice; the hash-index variant is added here. The hash index is the
reading closer to the paper's cost model; both are reported.

## Reproduce

    cd research/omnet_emulation/sim
    for f in configs_main.txt configs_sens.txt configs_fig.txt; do ./build_and_run.sh $f $PWD/results_macos; done
    python3 make_ext_configs.py
    for f in configs_H.txt configs_HF.txt configs_A.txt configs_AH.txt configs_HM.txt configs_AHM.txt; do ./build_and_run.sh $f $PWD/results_ext; done
    python3 collect.py results_macos > omnet_results_macos.csv; python3 collect.py results_ext > omnet_results_ext.csv
    python3 -I baseline_compare.py

Requires OMNeT++ 6.4.0 in `~/opp/omnetpp-6.4.0` (headless build, see `../toolchain.md`). The figure needs `pip install matplotlib`; the PDF extraction scripts (`../targets/extract_figs.py`, `../jan_compare/jan_extract.py`) need `pip install pikepdf`. Run the scripts with `python -I`.
