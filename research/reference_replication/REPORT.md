# Reference-paper replication and re-evaluation of BASE

Status: working report, not a manuscript. Everything here regenerates with `bash research/reference_replication/run_all.sh`.
All new files live in `research/reference_replication/`; no existing file was modified (see "Repository state").

## 0. Premise (read first)

**The task.** BASE's authors simulated their proposed scheme against schemes taken from other papers, three of which are JIANG, DHILLON and CHANGLE. The comparison this report is about is **BASE's simulated results versus the main paper (OURS)**, using the environment BASE took from those three papers (section A). Checking the three papers' own numbers and BASE's transcription of them (sections 5 and 6) is supporting evidence for that comparison, not the comparison itself.

The three reference papers (JIANG, DHILLON, CHANGLE) contain **no datasets**: only operation counts, per-operation time constants,
message/bit sizes and security-feature tables. "Simulating from them" therefore means:

* (a) reproduce each paper's own numbers from its own model (Step 2);
* (b) cross-check how BASE transcribed them (Step 3);
* (c) run all schemes under one common environment and compare with BASE's claims and with OURS (Steps 4-6).

Nothing in this study re-measures hardware. Measured ESP8266 / Mac / t4g constants are the existing ones in `research/paper_audit/results/*.csv`.
The network simulation (Step 5) uses **OMNeT++ 6.0.3 with a model we wrote ourselves**, because BASE publishes no project files; it is presented as a **sensitivity analysis, not evidence**, and is not bit-comparable to BASE's figures. An independent SimPy model is kept as a cross-check.

Input location: the five PDFs are in `docs/references/` and `paper/main.pdf`, not in `research/reference_replication/pdfs/` (that folder did not exist). They are read in place.
Mapping: BASE = `base_paper.pdf`; JIANG = `chaotic_maps_three_factor_authentication.pdf`; DHILLON = `lightweight_biometrics_remote_user_authentication_for_iot.pdf`;
CHANGLE = `provably_secure_authentication_for_ad_hoc_wsn.pdf` (Chang and Le, IEEE TWC 15(1), 357-366, Jan 2016; authors read from its first page); OURS = `paper/main.pdf`.

## A. Head-to-head: BASE's simulated results versus OURS

**What is compared.** BASE evaluates its proposed scheme in an OMNeT++ simulation against schemes taken from earlier papers, among them the three papers JIANG, DHILLON and CHANGLE (and Turkanovic, which DHILLON and CHANGLE both tabulate). It reports communication (Table IV, Fig. 2), processing (Table V, Fig. 1), storage (Table VI, Fig. 3) and an abstract of "approximately 17%, 21%, and 12% reductions in communication, processing, and storage costs". OURS (the main paper) re-evaluates that comparison with measured constants. This section sets the two side by side, with our replication in between.

**The same environment as BASE.** The environment is what BASE took from the three papers: the network of BASE Table II (1500 x 1500 m, 100-1000 devices, 5% servers, 10 Mbps, 500-800 m, 15 µs, 160 km/h or static, adversaries), the operation counts, bit sizes and storage of the compared schemes as they appear in Tables IV-VI, and the per-operation times. We ran it twice: with BASE's own Table III times (**BASE environment**) and with the constants of the three papers themselves (**papers' environment**: JIANG T_H 0.20 and T_C 32.40 ms; CHANGLE t_mul 63.075 and t_h 0.5 ms; DHILLON gives none and borrows CHANGLE's t_h; the proposed scheme has no constants of its own and keeps BASE's). OURS' own environment (**measured**) uses constants timed on an ESP8266. BASE does not publish its simulation output beyond Tables IV-VI and Figs. 1-3, so "what BASE reports" means those tables, figures and claims; the replication is a model we wrote (section 8) and is a sensitivity analysis, not BASE's simulation.

| topic | what BASE reports | same environment: our replication | what OURS reports | verdict |
|---|---|---|---|---|
| Environment: constants BASE used versus the constants of the three papers | Table III as above | BASE: Table III: T_H 0.32, T_C 0.32, T_ECM 17.1, T_SE/D 5.6, T_fe 17.1 ms. Papers: JIANG: T_H 0.20, T_C 32.40 ms. CHANGLE: t_h 0.5, t_mul 63.075 ms. DHILLON: none | measured ESP8266: T_H 0.036, T_SE/D 0.48-1.15, T_ECM 276 ms (16x the 17.1) | BASE's environment is not that of the papers its competitors come from: T_C is 101x lower than JIANG's, T_ECM 3.7x lower than CHANGLE's t_mul, and T_H is 1.6x JIANG's but 0.64x CHANGLE's |
| Processing: does the proposed scheme have the lowest cost? (device + server, ms) | text Sec. V-A: 'minimum possible processing cost'; abstract ~21% lower; Table V gives counts only | **BASE environment:** BASE Table V x III: proposed 23.7 ms, rank 5 of 6; cheaper: Turkanovic (7/5/7), Dhillon-Karla, Chang-Le P1, JIANG published (T_C 0.32 BASE, 32.40 papers, 0.32 measured). **Papers' environment:** papers' constants: proposed 23.7 ms; cheaper: Turkanovic (7/5/7), Dhillon-Karla, Chang-Le P1; dearer: Chang-Le P2, JIANG published (T_C 0.32 BASE, 32.40 papers, 0.32 measured). | measured: proposed 2.08 ms; cheaper: Turkanovic (7/5/7), Dhillon-Karla, Chang-Le P1; ECC schemes 60-2,520x dearer; OURS: not the cheapest once the session KDF is counted | BASE's claim is NOT supported by its own Table V x III (rank 5 of 6) nor by the papers' own constants against the hash-only schemes. It holds against the ECC scheme (Chang-Le P2) and against JIANG only when JIANG's own T_C = 32.40 ms is used, not with Table III's T_C = 0.32 ms. OURS agrees (and adds that the session KDF is missing from Table V) |
| Processing in the OMNeT++ model: mean authentication latency at N = 1000 (ms) | Fig. 1 (Processing): proposed lowest, all curves rise with vehicles; values not tabulated | **BASE environment:** BASE env: proposed 19,010, Dhillon-Karla 4.8, JIANG 5.6. **Papers' environment:** papers' env: proposed 19,010, Dhillon-Karla 7.4, JIANG 214. | measured env: proposed 1,045, Dhillon-Karla 0.83, JIANG 2.49; OURS: lookup cost grows with devices per server | BASE's Fig. 1 claim (proposed lowest) is NOT reproduced in any environment: the proposed scheme ranks 6/6 (BASE), 6/6 (papers), 6/6 (measured) by latency; it is slower than every non-ECC scheme in all three environments. The size is set by the pseudonym lookup, which BASE does not specify (nearest-only enrolment: see 8.5) |
| Communication: bits | Table IV: proposed 1,024 bits (4 msgs) vs 1,600-3,360; 36.0% fewer than best, 57.5% than mean; text: 264 bits, 2 msgs; abstract ~17% | **BASE environment:** OMNeT++ (N = 1000, kbit on air incl. forged traffic): proposed 1,088 (264-bit variant 328) vs JIANG 1,376, Turkanovic 2,784, Dhillon-Karla 2,592. **Papers' environment:** bits are identical in the papers' environment (sizes come from Table IV; JIANG's own 1,312 bits is used). | OURS: same arithmetic (36.0% / 57.5%), flags 4 msgs/1,024 bits vs 2 msgs/264 bits; 17% not derivable | Direction REPRODUCED (proposed lowest in every variant); magnitude depends on 1,024 vs 264 bits and on the unverifiable competitor sizes; 17% not reproduced |
| Storage | Table VI: proposed 320 / 320 bits vs best 480 (server) / 356 (device); 33.3% / 10.1%; abstract ~12% | **BASE environment:** model: a server resolving every device in range holds ~258 enrolled devices at N = 1000; a precomputed pseudonym table of 13 epochs x 32 B is ~107 KB (vs 40 B). **Papers' environment:** not simulated (storage is not a simulated quantity); no storage table in JIANG, DHILLON or CHANGLE. | OURS: same arithmetic (10.1% / 33.3%); pseudonym lookup needs O(N x W) compute or storage (800 KB at 1,000 devices) | Table VI arithmetic REPRODUCED, not 12%; the 320-bit server storage holds only if the server does not keep a per-device pseudonym table |
| Scaling with vehicles (BASE Figs. 1-2 axis, 300-1800 devices) | curves rise slowly with vehicles; proposed lowest in Figs. 1-3 | **BASE environment:** OMNeT++ BASE env: bits proposed 321 -> 1,954 kbit (lowest); latency proposed 2,666 -> 40,407 ms, Dhillon-Karla 4.8 -> 4.8 ms. **Papers' environment:** see section 8 (papers' environment curves in results/step5b_omnet_papers.png). | OURS: Fig. 2 plots a fixed per-session bit cost rising with vehicles (22.4 -> 28.6 'bits'), impossible for a per-session protocol | Communication ordering REPRODUCED; processing ordering NOT reproduced |
| Abstract: ~17% communication, ~21% processing, ~12% storage | 17 / 21 / 12 % | **BASE environment:** 36.0 / 57.5 (comm), -517 / 68 (proc, best / mean), 10.1 / 33.3 (storage). **Papers' environment:** not computable (no values). | OURS: not derivable under any of the nine definitions | NOT reproduced by BASE's own tables; consistent with OURS |

**Bottom line.**

1. **Communication:** BASE's claim that the proposed scheme sends the fewest bits holds in every environment and variant we ran (1,088 kbit on air at N = 1000 against 1,376 to 2,784 for the schemes taken from the three papers; only its own 264-bit variant is lower). The abstract's 17% is not reproduced: the tables give 36.0% against the best competitor and 57.5% against the mean, and BASE's own text (2 messages, 264 bits) disagrees with Table IV (4 messages, 1,024 bits). OURS reports the same.
2. **Processing:** BASE's claim of the lowest processing cost is not supported by its own Table V x Table III (rank 5 of 6 among the schemes taken from the three papers plus the proposed one), nor by the papers' own constants against the hash-only schemes (Turkanovic, Dhillon-Karla, Chang-Le P1 are cheaper); it holds only against the ECC scheme (Chang-Le P2) and against JIANG when JIANG's own T_C = 32.40 ms is used. In the OMNeT++ model the proposed scheme has the highest latency among the non-ECC schemes in all three environments (7th of 8 in the papers' environment). OURS reaches the same direction with measured constants (4-11x dearer than the hash-only schemes) and adds the missing session KDF.
3. **Storage:** Table VI's arithmetic reproduces (10.1% device, 33.3% server) but not the abstract's 12%, and none of the three papers gives storage figures to check the competitor rows; the 320-bit server storage holds only if the server keeps no per-device pseudonym table.
4. **The environment itself:** BASE's Table III constants are not those of the papers its competitors come from (T_C 0.32 ms against JIANG's 32.40 ms; T_ECM 17.1 ms against CHANGLE's t_mul 63.075 ms). Costing JIANG with its own T_C changes it from 5.4 ms (cheaper than the proposed scheme) to 196.6 ms (dearer), so the ranking BASE reports depends on mixing the constants.
5. **Where OURS differs from this head-to-head:** OURS lists "Jiang" among the hash-only schemes (it is not: 6 T_C per run in the paper OURS cites), states "120-3000x" against the ECC schemes (60-2,520x here), and states the server lookup cost as linear in the number of devices (it is linear in the devices a server must resolve; that number is not specified by BASE). Everything else in OURS' direction is reproduced.


Figure A1 (end of report): processing cost of the proposed scheme and of the schemes taken from the three papers in the three environments.

Sections 5 and 6 below are the supporting evidence for this comparison: they check the three papers' own numbers and how BASE used them.

## 1. Supporting findings (how BASE used the three papers, and checks of OURS)

1. **CHANGLE P2 user cost is misprinted, as suspected.** Table III prints `2t_mul + 7t_h ≈ 0.12765 s`; the paper's own constants give **0.12965 s** (error 2.0 ms). The printed value equals Shi's *sensor* cell. All other 17 numeric cells of its Tables II-III match; the "about 14x faster" gateway claim computes to 14.46-14.57. CHANGLE's text says P1 is "slightly more efficient than Turkanovic at the sensor node", but Table II shows identical cells (5t_h+4t_XOR); P1's gateway is 14% *more* expensive (0.004 vs 0.0035 s).
2. **BASE's Turkanovic row has device and server swapped.** BASE Table V: 7/7/5 T_H (user/device/server). CHANGLE Table II and DHILLON Table 3 both: 7/5/7 (user/sensor-node/gateway). Totals unaffected, device-only and server-only comparisons are.
3. **Three BASE row labels do not match their reference numbers.** [14] "Cheng and Le" is a VANET paper, [15] "Jiang et al." is an edge-AI magazine article, [16] "Shuai et al." is the Jiang chaotic-maps paper (JIANG). The "Cheng-Le" row is CHANGLE's P2 with the user and gateway hash counts exchanged (likely source, not stated by BASE). The "Jiang [15]" and "Shuai [16]" rows could not be traced to any of the available papers (UNVERIFIED).
4. **JIANG is not a hash-only scheme.** It costs 21 T_H + 6 T_C overall, 7 T_H + 4 T_C for authentication (Table 2), with T_H = 0.20 ms and **T_C = 32.40 ms**. BASE Table III sets T_C = T_H = 0.32 ms (101x lower than JIANG's) and no BASE Table V row uses T_C. OURS lists "Jiang" as one of three hash-only schemes (ref [5] = JIANG); that holds only for BASE's unidentified row [15].
5. **OURS' main conclusion survives for two of three hash-only schemes** (Turkanovic, Dhillon-Karla are cheaper than every reading V1-V4 of the proposed scheme in all constant sets tested). For JIANG as published, "cheaper than the proposed scheme" holds only if T_C is below a crossover of 0.14-5.2 ms (platform and reading dependent), well under JIANG's own 32.40 ms; at 32.40 ms JIANG costs ~195-198 ms versus 1-35 ms for the proposed scheme.
6. **OURS "120-3000x cheaper than ECC schemes" is off at both ends:** like-for-like ratios on the ESP8266 are 60x (Sadhukhan, aes_ct) to 2,520x (Poorambage, aes_big). Order of magnitude stands.
7. **OMNeT++ sensitivity analysis (our model of BASE's Table II environment; guesses flagged in 8.3).** Bits on air and radio energy come out lowest for the proposed scheme against all 11 other configurations in the main grid and against Dhillon-Karla and Sadhukhan in every sensitivity variant (tested), *if* Table IV's 1,024 bits is right (264 bits if the text is). Latency and server work come out higher than Dhillon-Karla's in every variant run for both (tested; even with a laptop-class server: 1.86 vs 0.56 ms at N = 1000), but their magnitude spans 1.9 ms to 5.5 s at N = 1000 depending on the adversary share, arrival window, server class, range and whether a server must resolve every device in range or only its own (~20). The O(N x W) growth is real in the model but its size is set by those unspecified inputs, so it should be stated as a conditional, not as a fact about the scheme.
8. **Communication/storage percentages reproduce arithmetically** (36.0%, 57.5%, 10.1%, 33.3%) but rest on rows that cannot be checked against the originals: DHILLON and CHANGLE contain no bit-size or storage tables; JIANG's 1312/1584 bits do not appear in BASE (1952/2368 for the rows with its name or reference).

## 2. Environment and reproduction

| item | value |
|---|---|
| OS | Windows 11 Home 10.0.26300, Git Bash |
| Python | 3.11.9 (venv `research/reference_replication/.venv`, git-ignored) |
| packages | `requirements.txt`: pymupdf 2.0, numpy 2.4.6, matplotlib 3.11.2, PyYAML 6.0.3, simpy 4.1.2, pytest 9.1.1 |
| seeds | model of Steps 2-4 is deterministic; Step 5 uses `numpy.random.default_rng(seed)` for seeds 1-5 (averaged); `PYTHONHASHSEED=0` |
| determinism check | Steps 2-4 and the SimPy model: full pipeline run twice, all CSV and PNG outputs byte-identical (md5). OMNeT++: the final 3,385-run sweep was run twice and `omnet_results.csv` is byte-identical (md5 501e8ce2...); every run of the earlier, smaller sweeps is byte-identical inside it |
| OMNeT++ | 6.0.3 in WSL2 Ubuntu 22.04.5, user-space gcc 16.2.0 (see 8.1); run automatically by `run_all.sh` when present, otherwise the stored `results/omnet_results.csv` is used |
| tests | `pytest tests`: 46 passed (PDF strings on cited pages, Step 2 match/mismatch, audit tags, model arithmetic, T_C crossover exactness, SimPy seeding and shape, OMNeT++ ini traceability to the paper tables, sweep completeness, sanity and sensitivity direction, and every number quoted in this report against the data) |

Commands (repo root):

```
bash research/reference_replication/run_all.sh     # venv, pip install, text extract, 300-DPI render, steps 2-6 (OMNeT++ via WSL if installed), patch, PDF, tests
make -C research/reference_replication reproduce   # same thing (make is not installed on this machine: Makefile is untested; run_all.sh is the tested path)
```

One-off OMNeT++ setup (inside WSL, no root): `omnet/setup_toolchain_and_omnetpp.sh`. Individual steps: `scripts/render_pages.py`, `verify_pdf_text.py`, `step2_reproduce.py`, `step3_audit_base.py`, `step4_common_env.py`, `step5_netsim.py` (SimPy cross-check), `gen_omnet_ini.py`, `step5b_omnet_results.py`, `step6_compare_ours.py`, `step7_base_vs_ours.py`, `make_patch.py`.
The scripts import (read-only) `research/paper_audit/paper_tables.py` (BASE Tables III-VI) and `reeval.py` (measured-constant loader).

## 3. Step 0: recon

Existing work, reused rather than duplicated: `research/paper_audit/` has the transcription of BASE Tables III-VI (`paper_tables.py`), the consistency audit, the measured primitive costs (ESP8266 80/160 MHz, Mac, t4g.nano), the V1-V4 readings of the proposed scheme (`eq22_variants.py`), the server-scaling measurement and `FINDINGS.md`. `firmware/esp8266` holds the benchmark and device firmware.
Not present before this study: any check of BASE's competitor rows against the original papers (OURS says so in its threats-to-validity).

Tooling: `pdftotext` exists, `pdftoppm` does not; pages were rendered at 300 DPI with PyMuPDF (`work/png/`, git-ignored). Table pages read visually: BASE pp.6-8 (Tables II-VI, Figs. 1-3), CHANGLE p.9 (Tables II-IV), JIANG pp.14-15 (Tables 1-2, Fig. 3), DHILLON pp.11-12 (Tables 3-4); section 13.1 lists what was checked how. My visual reading of BASE Tables IV, V and VI agrees with `paper_tables.py` in every cell.
OMNeT++ was not installed at the start (nothing on PATH or in `C:\Program Files`); after your instruction it was installed in WSL (section 8.1).

## 4. Step 1: extracted constants (`data/extracted.yaml`)

| paper | T_H | T_C | other | cite |
|---|---|---|---|---|
| BASE | 0.32 ms | 0.32 ms | T_ECM 17.1, T_SE/D 5.6, T_fe 17.1 | BASE pdf p.6 (journal 4488), Table III |
| JIANG | 0.20 ms | 32.40 ms | PIV 3.2 GHz, "according to [20]" | JIANG pdf p.15, Sec. 7 |
| CHANGLE | t_h = 0.5 ms | n/a | t_mul = 63.075 ms, t_XOR neglected; one citation "[14]" (Xie et al.) follows the sentence giving both | CHANGLE pdf p.8-9 (journal 364-365), Sec. VI |
| DHILLON | **none** | n/a | only "hash value ... 128 bits" | DHILLON pdf p.12, Sec. 5.2 |

The YAML also holds JIANG Table 2 (per phase), DHILLON Table 3, CHANGLE Tables II-IV, JIANG/DHILLON security tables, and BASE Table II (simulation parameters), each with page/table citation and a `status`. `verify_pdf_text.py` confirms 12 key strings are on the cited PDF pages (`results/pdf_text_checks.csv`); CHANGLE's tables are images and were read visually.

BASE Table II as printed: 1500x1500, OMNeT++, 100-1000 devices, "Server 5% (one per hundred devices)" (5% is one per twenty), 15 µs sampling, 10 Mbps, "Packet Size 128 Kbps" (a rate; text says 128 bits), 500-800 m, "device Speed (Max) 160 km/hour" and hand-off time 10 ns (conflicts with "static"), adversary "Randomly Generated".

## 5. Step 2 (supporting): the three papers' own numbers

### CHANGLE (`results/step2_changle.csv`), t_mul = 0.063075 s, t_h = 0.0005 s

| table / cell | formula | printed (s) | computed (s) | result |
|---|---|---|---|---|
| II Li user / sensor / gateway | 9t_h+6t_X / 5t_h+3t_X / 12t_h+6t_X | .0045 / .0025 / .006 | same | match |
| II Turkanovic user / sensor / gateway | 7t_h+4t_X / 5t_h+4t_X / 7t_h+4t_X | .0035 / .0025 / .0035 | same | match |
| II P1 user / sensor / gateway | 7t_h+4t_X / 5t_h+4t_X / 8t_h+1t_X | .0035 / .0025 / .004 | same | match |
| III Shi user / sensor / gateway | 3t_mul+5t_h / 2t_mul+3t_h / t_mul+4t_h | .191725 / .12765 / .065075 | same | match |
| III Choi user / sensor / gateway | 3t_mul+9t_h / 2t_mul+6t_h / t_mul+5t_h | .193725 / .12915 / .065575 | same | match |
| III P2 sensor / gateway | 2t_mul+5t_h / 9t_h | .12865 / .0045 | same | match |
| **III P2 user** | **2t_mul+7t_h** | **.12765** | **.12965** | **MISMATCH (-0.002 s)** |
| text "gateway ~14x faster in P2" | Shi, Choi gateway / P2 gateway | ~14 | 14.46, 14.57 | match |
| text "P1 slightly more efficient than Turkanovic at sensor" | Table II sensor cells | P1 < Turkanovic | identical | **contradicted by its own table** |

(18 numeric cells, 17 match.) The corrected P2 user cost still beats Shi and Choi, so CHANGLE's conclusion is unchanged. CHANGLE gives message names m1-m4 but no bit sizes.

### JIANG (`results/step2_jiang.csv`), T_H = 0.20 ms, T_C = 32.40 ms

Overall T_H and T_C counts equal the sum of P1-P5 for all three schemes (6/6 match): Lee-Hsu 25 T_H + 8 T_C, Islam 18 + 10, JIANG 21 + 6. Times are not printed (Fig. 3 only); computed: JIANG P1 0.6, P2 65.6, P3 131.0, P4 0.8, P5 0.6, overall **198.6 ms** (Islam 327.6, Lee-Hsu 264.2; Fig. 3's axis tops at 350). 1312/1584 bits and 2/3 rounds are printed without derivation; only |p| = 256 bits is given, hash output length was not found in the text layer, so the bit totals are UNVERIFIED. Table 2's costs are per *phase* (both parties combined): no user/server split exists in the paper.

### DHILLON (`results/step2_dhillon.csv`)

Table 3 (user/node/gateway, T_h): proposed 8/6/8 (sum 22), An 4/5/6, Chen 4/1/5, Das 5T_h+1T_E/D, 4T_h+1T_E/D, 2T_h+1T_D/E, Turkanovic 7/5/7, He 5/1/5, Xue 7/6/13. No totals, no times, no communication or storage table. Its own table shows its scheme with a higher hash count than An (15), Chen (10), Das (11), Turkanovic (19) and He (11).

## 6. Step 3 (supporting): how BASE used the three papers (`results/step3_findings.csv`)

| id | subject | tag | evidence |
|---|---|---|---|
| F1 | BASE Table V Turkanovic device/server | **CONTRADICTED** | BASE 7/7/5; CHANGLE Table II 7/5/7; DHILLON Table 3 7/5/7. Swapped; sum 19 unchanged |
| F2 | BASE Dhillon-Karla counts | CONFIRMED | 8/6/8 = DHILLON Table 3 |
| F3 | BASE Dhillon-Karla bits 992/512/1024 = 2528 | UNVERIFIED | DHILLON has no bit-size table |
| F4 | BASE "Cheng and Le [14]" row | **CONTRADICTED as printed**; source UNVERIFIED | BASE 9/5/7 T_H with 2/2/0 T_ECM; CHANGLE P2 7/5/9 with 2/2/0 t_mul. Same totals (21 hashes, 4 ECM); user and server hash counts exchanged |
| F5 | BASE ref [14] | CONFIRMED mis-citation | [14] = Wang et al., VANET emergency vehicle protocol; Chang and Le is not in BASE's references |
| F6 | BASE Cheng-Le bits 2272 | UNVERIFIED | CHANGLE has no sizes |
| F7 | BASE "Shuai [16]" vs JIANG | **CONTRADICTED** | [16] is JIANG, but the row is 6T_H+1T_ECM / 3T_H+1T_ECM / 7T_H+1T_ECM; JIANG has no ECM, 7T_H+4T_C in P3. True source of the row UNVERIFIED |
| F8 | BASE "Jiang [15]" row (7/5/10 T_H) | UNVERIFIED | [15] = Wen et al., edge AI, not an authentication scheme; (7,5,10) is in none of JIANG, DHILLON Table 3, CHANGLE II-III |
| F9 | T_C 0.32 ms (BASE) vs 32.40 ms (JIANG) | **CONTRADICTED** | ratio T_C/T_H is 1 in BASE, 162 in JIANG; BASE's T_C is inert (no row uses it) |
| F10 | JIANG time under both constants | CONFIRMED (computed) | P3: 3.52 ms (BASE constants) vs 131.0 ms (JIANG's); whole scheme 8.64 vs 198.6 ms |
| F11 | BASE bits Jiang 1952, Shuai 2368 vs JIANG 1312/1584 | **CONTRADICTED** | neither BASE row equals JIANG's totals; JIANG has 2 rounds, BASE says 4 messages for all |
| F12 | Table IV totals = user + device + server | CONFIRMED | all 10 rows |
| F13 | OURS labels "Jiang" hash-only | **CONTRADICTED** | OURS ref [5] = JIANG, 6 T_C per run. Holds only for BASE's unidentified row [15] |
| F14 | Turkanovic, Dhillon-Karla hash/XOR-only | CONFIRMED | CHANGLE Table II, DHILLON Table 3 |
| F15 | BASE Table II internal consistency | CONFIRMED (inconsistencies) | 5% vs "one per hundred"; "128 Kbps" packet size; 160 km/h vs static |

Note on the Turkanovic origin: CHANGLE (Table II, ref [1]) and DHILLON (Table 3) both name Turkanovic et al.'s 2014 Ad Hoc Netw. paper, the same one as BASE [12], so their agreement is two readings of one source, not a check of that paper itself. DHILLON's Tables 3-4 label it "[26]", but DHILLON's reference [26] is Weber's IoT-challenges article and Turkanovic is its [43] (a numbering slip inside DHILLON; the name and counts identify the scheme).

## 7. Step 4: common-environment cost model

Model: `scripts/refmodel.py`, `step4_common_env.py`. Readings V1-V4 of the proposed scheme are exactly those of `paper_audit/eq22_variants.py`. Constant sets: (A) BASE Table III, with KDF = 17.3 T_H because BASE has no KDF constant (ratio measured on the ESP8266, so this is our assumption); (B) each paper's own constants (JIANG, CHANGLE; DHILLON gives none, so DHILLON and Turkanovic borrow CHANGLE's t_h = 0.5 ms and are flagged); (C) measured ESP8266 80 and 160 MHz (BearSSL `aes_big`, GCM including key setup; `aes_ct` also run). T_C is unmeasured: every set is run at T_C = 0.32 ms and 32.40 ms. JIANG is costed as published (P2 + P3, user and server combined; role split UNVERIFIED), the Turkanovic row with its corrected split, and Cheng-Le as CHANGLE P2.

Device + server time, ms (`results/step4_costs.csv`; "Jiang [15]", "Shuai [16]", "Cheng-Le [14]" are BASE's rows):

| scheme | A (BASE) | C: ESP8266 80 MHz | C: ESP8266 160 MHz |
|---|---|---|---|
| Proposed V1 / V2 / V3 / V4 | 23.68 / 34.76 / 27.88 / 34.12 | 2.08 / 3.34 / 2.71 / 3.27 | 1.05 / 1.68 / 1.36 / 1.64 |
| Turkanovic (7/5/7) | 3.84 | 0.436 | 0.218 |
| Dhillon-Karla | 4.48 | 0.509 | 0.254 |
| Jiang [15] (BASE row, hash-only) | 4.80 | 0.545 | 0.273 |
| JIANG published, P2+P3, T_C = 0.32 | 5.44 | 2.32 | 2.12 |
| JIANG published, P2+P3, T_C = 32.40 | 197.9 | 194.8 | 194.8 |
| Chang-Le P1 / Li (CHANGLE) | 4.16 / 5.44 | 0.472 / 0.618 | 0.236 / 0.309 |
| Chang-Le P2 / Cheng-Le [14] | 38.68 / 38.04 | 553.2 / 553.1 | 276.6 / 276.6 |
| Shuai [16] / Sadhukhan | 37.40 / 51.66 | 553.1 / 279.4 | 276.5 / 139.7 |
| Wazid | 36.48 | 3.23 | 1.63 |
| Challa / Poorambage | 156.1 / 329.7 | 2,487 / 5,251 | 1,244 / 2,626 |

(B) own constants, device + server: JIANG published 196.6 ms (P3 only 131.0), Chang-Le P1 6.5, Li 8.5, P2 133.2 (all roles 262.8), Turkanovic 6.0 and Dhillon-Karla 7.0 (borrowed t_h); proposed has no constants of its own and is shown under (A): 23.7-34.8 ms. So under each paper's own constants the proposed scheme is cheaper than JIANG and P2, dearer than the hash-only schemes and P1.

Ranks (1 = cheapest, BASE-as-printed pool of 9 competitors, `results/step4_ranks.csv`): proposed is 4th of 10 under (A) for V1-V4 (behind Turkanovic, Dhillon-Karla, Jiang[15]); on the ESP8266 it is 4th for V1/V3 and 5th for V2/V4 with `aes_big` because Wazid (no ECM; 9 T_H + 6 T_SE/D) also undercuts it (3.23 vs 3.34 ms). With the corrected pool (Turkanovic fixed, Cheng-Le as P2, Jiang[15] and Shuai[16] dropped, JIANG published added) the rank is 3rd (V1, ESP8266, T_C = 0.32: only Turkanovic and Dhillon-Karla cheaper), 4th-5th for V2-V4.

**T_C sensitivity** (`results/step4_tc_sensitivity.csv`, `.png`). JIANG published is cheaper than the proposed scheme iff T_C < T_C*:

| platform | V1 | V2 | V3 | V4 |
|---|---|---|---|---|
| A BASE Table III | 3.36 ms | 5.21 | 4.06 | 5.10 |
| C ESP8266 80 MHz | 0.28 | 0.49 | 0.39 | 0.48 |
| C ESP8266 160 MHz | 0.14 | 0.25 | 0.19 | 0.24 |

At BASE's 0.32 ms JIANG beats V2-V4 on the 80 MHz ESP8266 and everything under (A); at JIANG's own 32.40 ms it loses everywhere. A 256-bit extended chaotic-map evaluation (|p| = 256 in JIANG) costing about one SHA-1 block on a 32-bit MCU, as T_C = 0.32 ms would imply, is implausible but is argued here, not measured; the Chebyshev operation was not benchmarked.

**Reductions** (definitions of `audit.py` that apply to a table: best, mean, median, worst; ratio-of-sums equals the mean). Processing, (A) V1, BASE-as-printed pool: vs best -516.7%, mean 67.8%, median 36.7%, worst 92.8%; none within one point of 21%. Communication, Table IV (1024 bits): vs best 36.0%, mean 57.5%, median 56.8%, worst 69.5%; with 264 bits (text) 83.5/89.1/88.9/92.1%. Replacing Jiang[15] and Shuai[16] by JIANG's 1312 bits: 22.0/56.2/57.6/69.5% (exploratory: JIANG has two rounds, BASE counts four messages for all). Storage (Table VI): 10.1% device and 33.3% server vs best. Full list in `results/step4_reductions.csv`.

## 8. Step 5: OMNeT++ simulation with the BASE environment (sensitivity analysis, not evidence)

**Read this as a sensitivity analysis.** BASE publishes no OMNeT++ project (no `.ned`, `.ini`, C++), so the model in `omnet/AuthNet.ned`, `omnet/AuthNet.cc` is **our own re-implementation** of the environment BASE describes in Table II, written for this study. Several inputs it needs are not given by BASE and are guesses of ours; the results depend on them (section 8.3). The figures below therefore show *how much the conclusions move when the guesses move*; they are not measurements of the BASE protocol and are not comparable bit-for-bit with BASE's figures.

### 8.1 Environment

| item | value |
|---|---|
| simulator | OMNeT++ 6.0.3 (Academic Public License), headless: no Qtenv, IDE, OSG; NED loaded at run time |
| host | WSL2, Ubuntu 22.04.5, 16 logical CPUs, 7 GB RAM |
| toolchain | no root on the distro and no compiler preinstalled, so a user-space toolchain was installed with micromamba 2.9.0 (conda-forge): gcc/g++ 16.2.0, GNU Make 4.4.1, Bison 3.8.2; everything lives under the WSL home (`~/omnetpp-6.0.3` 656 MB, `~/opp-toolchain` 2.5 GB, `~/mamba-root` 668 MB) and is removed by deleting those folders |
| not used | INET, Veins, SUMO (BASE's conclusion mentions "Simulation of Urban Mobility" but its model is not provided). Docker Desktop was started on request but did not work on this laptop and was not used |
| runs | 3,385 runs in 122 configurations: 38 main (15 schemes in the BASE and measured environments, plus 8 in the papers' environment; 10 values of N x 5 repetitions), 69 sensitivity (N = 100, 500, 1000 x 5), 15 on the BASE-figure axis (N = 300..1800 x 5); `seed-set = ${repetition}`, repetitions 0-4, OMNeT++'s default Mersenne Twister; the whole sweep takes a few minutes. Adding the mobile, figure-axis and papers'-environment configs left all 2,855 earlier rows byte-identical |
| setup / run | `omnet/setup_toolchain_and_omnetpp.sh` (once), `omnet/run_omnet.sh`, `scripts/gen_omnet_ini.py` (writes `omnet/omnetpp.ini` from the paper tables), `scripts/step5b_omnet_results.py` |

### 8.2 How BASE Table II maps to the model

| BASE Table II item | in the model | status |
|---|---|---|
| Coverage area 1500 x 1500 | uniform random positions of devices, servers, adversaries | BASE |
| Active devices 100 to 1000 | N = 100, 200, ..., 1000 | BASE (step of 100 is ours) |
| Server 5% ("one per hundred devices") | round(0.05 N), at least 1 | BASE, but its own parenthesis says 1%; we used 5% |
| Trusted module (TA) one | not simulated (offline phase only) | interpretation |
| Sampling interval 15 µs | event-time quantum (all delays rounded up to 15 µs) | interpretation |
| Bandwidth 10 Mbps | per-server shared radio channel, one transmission at a time | BASE rate; the channel model is ours |
| Energy tx / rx 75.6 mW | energy = (75.6 + 75.6) mW x airtime | BASE values; use is ours |
| XBee coverage 500 to 800 m | 500 m default, 800 m as a sensitivity | BASE |
| Packet size "128 Kbps" | not used (a rate); bits per message = Table IV total / number of messages (or 264 bits / 2 messages from the text) | BASE conflict |
| Hand-off time 10 ns | added once per hop | BASE |
| Device speed (max) 160 km/h | static by default (Sec. V text); **160 km/h run as a variant** (random direction, reflected at the border, server chosen when the session starts) | BASE conflict, both run |
| Transmission interval "application oriented" | one authentication per device at a uniform random time in a 10 s window | **assumption** |
| Adversary "randomly generated" | adversaries = 5% of N, each sending forged 128-bit requests as a Poisson stream, 1 per second | **assumption** |
| per-operation delays | BASE Table III (environment `BASE`), the three papers' own constants (`PAPERS`, 8.9) or our measured ESP8266 constants (`MEAS`); per-scheme operation counts from BASE Table V, bits from Table IV | BASE / measured |

### 8.3 Inputs that are guesses, and what they control

| guess | values tried | what it changes |
|---|---|---|
| adversary share and rate | 0%, 5%, 10% of N; 1 request/s | server load for the proposed scheme only (each forged pseudonym forces a full scan); hash-only schemes are unaffected (checked) |
| arrival pattern | window 1, 10, 60 s | queueing at the server |
| who the server must resolve | every device in range ("reachable", default) or only devices attached to it ("nearest") | the number of pseudonyms scanned: about 258 vs 20 per server at N = 1000 |
| server class | ESP8266 80 MHz or laptop (Mac BearSSL constants) | cost of each probe: 74.6 µs vs 0.375 µs |
| range | 500 or 800 m | coverage and enrolled devices (258 vs 537 per server at N = 1000) |
| JIANG device / server split | 0, 50, 100% on the device (JIANG gives only a combined cost) | server busy time (18 / 1,178 / 2,338 ms at N = 1000, T_C = 0.32); mean latency barely moves (2.48-2.49 ms) because total compute is unchanged |
| T_C | 0.32 and 32.40 ms | JIANG latency: 2.5-5.6 ms vs 195-333 ms |
| proposed-scheme message count and size | 4 messages / 1,024 bits (Table IV) or 2 / 264 (text) | bits on air and energy (factor 3.3) |
| other fixed choices | scan covers half the table on average; window W = 13 epochs (measured); reject cost 1 T_H; user role not charged | not varied |

### 8.4 Main grid (mean of 5 repetitions; `results/step5b_omnet_main.csv`)

Each cell is mean latency (ms) / total server busy time (ms) / kbit on air / radio energy (mJ). Adversaries 5% of N, window 10 s, "reachable" enrolment, ESP8266-class server; the last two columns are per scheme.

BASE environment (BASE Table III constants, T_C = 0.32 ms, probe cost = T_H = 0.32 ms):

| scheme | N = 100 | N = 1000 |
|---|---|---|
| Proposed, Table IV size (V1) | 129 / 8,984 / 75 / 1.1 | 19,010 / 1,100,916 / 1,088 / 16.4 |
| Proposed, text size 264 bits, 2 msgs | 103 / 8,984 / 23 / 0.3 | 9,768 / 1,100,916 / 328 / 5.0 |
| Turkanovic (7/5/7) | 4.2 / 165 / 190 / 2.9 | 4.2 / 2,399 / 2,784 / 42.1 |
| Dhillon-Karla | 4.8 / 187 / 177 / 2.7 | 4.8 / 2,719 / 2,592 / 39.2 |
| Jiang [15] (BASE row) | 5.1 / 230 / 138 / 2.1 | 5.1 / 3,359 / 2,016 / 30.5 |
| JIANG published, T_C = 0.32 | 5.6 / 198 / 94 / 1.4 | 5.6 / 2,879 / 1,376 / 20.8 |
| Wazid / Shuai [16] / Cheng-Le as P2 | 37 / 1,649 / 182 / 2.7; 38 / 1,331 / 166 / 2.5; 39 / 208 / 160 / 2.4 | 38 / 24,159 / 2,656 / 40.2; 38 / 19,499 / 2,432 / 36.8; 39 / 3,039 / 2,336 / 35.3 |
| Sadhukhan / Poorambage | 52 / 1,583 / 114 / 1.7; 352 / 9,451 / 234 / 3.5 | 53 / 23,199 / 1,664 / 25.2; 382 / 138,559 / 3,424 / 51.8 |

Measured ESP8266 constants (probe = SHA-256 74.6 µs):

| scheme | N = 100 | N = 1000 |
|---|---|---|
| Proposed (V1) | 17.0 / 1,977 / 75 / 1.1 | 1,045 / 254,950 / 1,088 / 16.4 |
| Proposed (V2, + KDF) | 18.3 / 2,020 / 75 / 1.1 | 1,050 / 255,579 / 1,088 / 16.4 |
| Turkanovic / Dhillon-Karla / Jiang [15] | 0.80 / 19 / 190 / 2.9; 0.83 / 21 / 177 / 2.7; 0.86 / 26 / 138 / 2.1 | 0.80 / 272; 0.83 / 309; 0.86 / 381 (same bits, energy as above) |
| JIANG published, T_C = 0.32 | 2.5 / 80 / 94 / 1.4 | 2.5 / 1,178 / 1,376 / 20.8 |
| Wazid | 3.6 / 146 / 182 / 2.7 | 3.6 / 2,138 / 2,656 / 40.2 |
| Sadhukhan / Cheng-Le as P2 | 280 / 139 / 114 / 1.7; 553 / 24 / 160 / 2.4 | 280 / 2,029 / 1,664 / 25.2; 553 / 345 / 2,336 / 35.3 |
| Shuai [16] / Poorambage | 677 / 18,866 / 166 / 2.5; 24,447 / 150,790 / 234 / 3.5 | 1,159 / 276,622 / 2,432 / 36.8; 38,629 / 2,211,000 / 3,424 / 51.8 |

Ranks of the proposed scheme at N = 1000 among 12 configurations (1 = lowest; `results/step5b_omnet_ranks_N1000.csv`): **bits on air and energy: V1 2nd and V2 3rd, behind only the proposed scheme's own 264-bit variant, i.e. lowest of all competitors**, in both environments; **latency: 11th-12th (BASE) / 9th-10th (measured)**; **server busy time: 10th-12th (BASE) / 8th-10th (measured)**. The ECC schemes (Shuai, Poorambage) queue up on an ESP8266-class server because each session needs a server scalar multiplication; that is a consequence of the server class we chose.

### 8.5 Sensitivity of the proposed scheme (V1, measured constants; `results/step5b_omnet_sensitivity.csv`)

Mean latency in ms, mean of 5 repetitions (standard deviation over repetitions in brackets where it is large):

| variant | N = 100 | N = 1000 | N = 1000 p95 |
|---|---|---|---|
| reference: 5% adversaries, 10 s window, reachable, ESP8266 server | 17.0 | 1,045 (370) | 5,225 |
| no adversaries | 16.2 | 227 (28) | 585 |
| 10% adversaries | 17.5 | 2,687 (1,039) | 13,003 |
| window 1 s / 60 s | 23.7 / 16.2 | 2,760 (196) / 1,070 (783) | 6,615 / 5,834 |
| 800 m range | 38.1 | 5,554 (805) | 20,631 |
| 160 km/h mobile devices (BASE Table II speed) | 17.2 | 1,021 (398) | n/a |
| each server resolves only its own devices (~20) | 11.4 | **17.5** | 38 |
| laptop-class server | 1.29 | **1.86** | 2.1 |
| comparison: Dhillon-Karla, laptop-class server | | 0.56 | |

BASE environment (probe cost 0.32 ms): 94 / 6,762 (no adversaries), 129 / 19,010 (5%), 145 / 32,486 (10%), 89 / 316 (nearest), 1,036 / 47,214 (800 m) for N = 100 / 1,000. These are tens of seconds of queueing, mostly reflecting BASE's own 0.32 ms hash constant applied to a scan of thousands of pseudonyms.

What this shows: at N = 1000 the proposed scheme's mean latency spans **1.9 ms to 5.5 s** depending on guessed inputs. The only statement that holds in every variant is the ordering against the hash-only schemes: even in the most favourable variant (laptop-class server) the proposed scheme (1.86 ms) is slower than Dhillon-Karla (0.56 ms) and its server does more work. The *magnitude* of the O(N x W) growth is not determined by BASE's parameters; it is determined by the enrolment policy, server class and adversary load.

### 8.6 JIANG's unverified split, and T_C

At T_C = 0.32 ms JIANG's mean latency is 5.6 ms (BASE constants) or 2.5 ms (measured) for every split; at T_C = 32.40 ms it is 198 / 216 / 333 ms (BASE constants; split 100% device / 50% / 0%) and 195 / 212 / 323 ms (measured). So the unverified device/server split moves server busy time (18 vs 2,338 ms, a factor of about 130, between 100% device and 100% server at T_C = 0.32; over 10,000x at 32.40) and queueing, but not the conclusion that JIANG costs hundreds of milliseconds at its own T_C.

### 8.7 Cross-check against the independent SimPy model (`results/step5b_crosscheck_simpy.csv`)

An earlier, separately written SimPy model (`scripts/step5_netsim.py`, same parameters) gives the same results where queues are not saturated: Dhillon-Karla 0.83 vs 0.80 ms, JIANG 2.49 vs 2.48 ms, Sadhukhan 279.6 vs 279.6 ms (N = 1000); total server busy time agrees to within 1-4% (e.g. Proposed 254,950 vs 252,668 ms). In the saturated case (Proposed, N = 1000) the two differ by 1,045 +/- 370 vs 683 ms, about one standard deviation of the OMNeT++ repetitions. The agreement checks the coding of the two models against each other, not the validity of either.

### 8.9 The three papers' environment (constants of JIANG and CHANGLE)

Same model, same Table II network and the same Table IV/V operation counts and bits, but each compared scheme is costed with the constants of the paper it comes from: JIANG with T_H 0.20 and T_C 32.40 ms; Chang-Le P1/P2 with t_mul 63.075 and t_h 0.5 ms; Dhillon-Karla and Turkanovic with CHANGLE's t_h (DHILLON gives no times, flagged); the proposed scheme with BASE's Table III (it has no constants of its own, so its row is identical to the BASE environment). Bits and energy are the same as in the other environments. `results/step5b_omnet_papers.png`.

Each cell is mean latency (ms) / total server busy time (ms) / kbit on air / radio energy (mJ), 5 repetitions, 5% adversaries, 10 s window, "reachable" enrolment:

| scheme | N = 100 | N = 1000 |
|---|---|---|
| Proposed, Table IV size (V1) | 129.2 / 8,984 / 75 / 1.1 | 19,009.8 / 1,100,916 / 1,088 / 16.4 |
| Proposed, text size 264 bits, 2 msgs | 103.3 / 8,984 / 23 / 0.3 | 9,768.0 / 1,100,916 / 328 / 5.0 |
| Turkanovic (7/5/7) | 6.3 / 258 / 190 / 2.9 | 6.4 / 3,749 / 2,784 / 42.1 |
| Dhillon-Karla | 7.3 / 292 / 177 / 2.7 | 7.4 / 4,249 / 2,592 / 39.2 |
| Chang-Le P1 | 6.8 / 292 / 160 / 2.4 | 6.8 / 4,249 / 2,336 / 35.3 |
| Chang-Le P2 (ECC) | 133.4 / 326 / 160 / 2.4 | 133.4 / 4,749 / 2,336 / 35.3 |
| JIANG published (T_C 32.40) | 204.2 / 6,712 / 94 / 1.4 | 214.1 / 98,399 / 1,376 / 20.8 |

At N = 1000 the proposed scheme (V1) ranks 7th of 8 by latency, 6th of 8 by server busy time, and 2nd (behind only its own 264-bit variant) by bits on air and radio energy. The proposed scheme's latency is set by the pseudonym lookup (N_s x W probes at BASE's 0.32 ms hash cost); with own-devices-only enrolment it falls to 316 ms in the BASE environment (section 8.5).

### 8.8 Plots and shape versus BASE Figs. 1-3 (qualitative)

* `results/step5b_omnet_base.png` and `step5b_omnet_meas.png`: latency, bits on air, radio energy and server busy time versus N, all 12 configurations, 5 seeds.
* `results/step4_tc_sensitivity.png` (Step 4) and the SimPy plots `step5_cost_vs_devices.png`, `step5_storage_vs_devices.png` (storage versus N, model, not simulated by OMNeT++).

BASE's Figs. 1-2 (viewed in this pass) show every scheme rising with "Vehicles in VANET" (300-1800) and the proposed scheme lowest; BASE's Fig. 3 is a single group of bars with no vehicle axis and the proposed scheme lowest. We ran the same 300-1800 axis (`results/step5b_omnet_fig_axis.png`, `.csv`; BASE environment). Our curves: bits on air and radio energy rise with N for every scheme (more sessions) and the proposed scheme is lowest (321 to 1,954 kbit against 764 to 4,662 for Dhillon-Karla), consistent with BASE's communication claim *if Table IV's 1,024 bits is right*; per-session latency of the hash-only, JIANG and ECC schemes is flat in N (Dhillon-Karla 4.8 ms throughout, JIANG 5.6 ms), unlike BASE's rising curves; the proposed scheme's latency rises steeply (2.7 s at 300 to 40 s at 1800 with BASE's 0.32 ms hash cost, 20.6 s at 1800 for the 264-bit variant) and is the *highest* among the non-ECC schemes, which is opposite to BASE's Fig. 1. BASE Fig. 2 plots a fixed per-session bit cost rising with the number of vehicles (22.4 to 28.6 "bits"), which no per-session protocol can do; none of our curves behaves like that. Because BASE's figures compare other schemes (Gope, Gupta, Hassan, Zhanfei) with no tabulated values, only shapes can be compared.

## 9. Step 6: OURS versus Steps 2-5 (`results/step6_claims.csv`)

| id | OURS claim | verdict | note |
|---|---|---|---|
| C1 | P-256 on ESP8266 is 16x the assumed 17.1 ms | NOT TESTABLE HERE | 276.35/17.1 = 16.16 from the existing CSV; no hardware re-measured |
| C2 | 120-3000x cheaper than ECC schemes | **PARTIAL** | like-for-like 60x-2,520x (see Finding 6) |
| C3 | all three hash-only schemes cheaper in every column, V1-V4 | **PARTIAL** | holds for Turkanovic and Dhillon-Karla in every case; for JIANG as published only if T_C < 0.14-5.2 ms |
| C4 | Table V under Table III: 23.7 ms vs 6.1/7.0/7.0 | REPRODUCED | 23.68; 6.08/7.04/7.04 |
| C5 | Table IV: 36.0% vs best, 57.5% vs mean | REPRODUCED (arithmetic); label-dependent | with JIANG's 1312 bits in place of the two mislabelled rows: 22.0% vs best |
| C6 | Table VI: 10.1% device, 33.3% server | REPRODUCED (arithmetic); rows UNVERIFIED | no original gives storage |
| C7 | 17/21/12% not derivable | REPRODUCED for the five table-applicable definitions | the four figure-averaging definitions were not re-run (need digitised figure values) |
| C8 | 4-11x more expensive than hash-only on ESP8266 | REPRODUCED (arithmetic) | V1: 3.8-10.8x; V1-V4: 3.8-13.7x. Rests on two verified schemes; BASE's "Jiang" row would be replaced by JIANG at 2.32 ms (T_C = 0.32), i.e. only 1.11x *above* V1 |
| C9 | HKDF 6-17 T_H vs hash-only device columns 5-7 T_H | PARTIAL | verified device columns are 5 (Turkanovic, not 7) and 6 (Dhillon-Karla); conclusion unchanged |
| C10 | server lookup O(N x W), Table V constant | **PARTIAL (sensitivity, not evidence)** | OMNeT++, N = 100 -> 1000, mean latency: 17 -> 1,045 ms (all devices in range, 5% adversaries), 16 -> 227 (no adversaries), 11 -> 17.5 (own devices only, ~20 per server), 1.3 -> 1.9 (laptop-class server); SimPy agrees. Linear in devices a server must resolve; whether that is N or ~20 is not specified by BASE |
| C11 | precomputed table 800 KB | REPRODUCED (arithmetic) | measured window is 13 epochs, i.e. 416 KB |
| C12 | forward secrecy of compared schemes unchecked | now partly answerable | CHANGLE Table IV: P2, Shi, Choi have PFS; P1, Turkanovic, Li do not; JIANG Table 1 claims PFS. Turkanovic is like-for-like with the proposed scheme (no PFS); JIANG and the ECC schemes are not |
| C13 | "Jiang" is hash-only | **CONTRADICTED as stated** | see Finding 4 |
| C14 | two schemes share reference [17] | CONFIRMED and extended | plus [14], [15], [16] as above |

Caveat on C3/C8: Step 4's measured sets use GCM *including* key setup (`aes_big`), whereas OURS Table II uses the cached-key variant; the direction of every conclusion is unchanged, but absolute V1 numbers differ (V1 with cached key is 1.97 ms vs 2.08 ms here).

Sentences in OURS to change, as a proposed patch only: `proposed_patches/ours_main_tex.diff` (8 edits, passes `git apply --check`, not applied, LaTeX compile not tested):
(i) abstract and Sec. IV-C "120-3000x" -> "60-2,500x"; (ii) Sec. IV-A item 3, name which three rows are "hash-only"; (iii) new audit item on row/reference mismatches, the Turkanovic swap and T_C 0.32 vs 32.40; (iv) Sec. IV-C "(Turkanovic, Dhillon-Karla, Jiang)" -> BASE's row "Jiang"; (v) "5-7 T_H" qualifier; (vi) threats to validity: replace "which we did not verify against the original papers" with what was and was not verified, and state that JIANG is not hash-only; (vii) add Chang and Le to the bibliography. Not edited but worth a decision: the abstract and conclusion sentence "it costs more than each of the three hash-only schemes ... in every cost column on every platform" (should say two of three, or restrict to BASE's rows) and the server-lookup sentence (add "per enrolled device set").

## 10. Limitations and things I could not do

* **No hardware work**: C1 and all measured constants are the repository's existing measurements. T_C and T_fe remain unmeasured.
* **OMNeT++ model is ours.** BASE gives no `.ned`/`.ini`/C++, no INET/SUMO setup and no MAC or propagation model; the model is a plain-OMNeT++ re-implementation of Table II (FIFO shared channel, no propagation loss, no interference, mobility only as a constant-velocity variant, one authentication per device, user role not charged, no rogue-server adversary). Its inputs include guesses (adversary share and rate, arrival window, enrolment policy, server class, JIANG split, probe and reject costs; section 8.3), so Step 5 is a sensitivity analysis and not evidence about BASE's protocol or its figures. OMNeT++ 6.0.3 is not necessarily BASE's version (BASE gives none).
* Saturated cases (proposed scheme at N = 1000) have large run-to-run spread (standard deviation over 5 repetitions is 35% of the mean in the reference case and up to 77% in other variants: BASE environment with own-devices-only enrolment 316 +/- 242 ms, 60 s window 1,070 +/- 783 ms); I did not run more repetitions.
* **Unidentified sources**: BASE's "Jiang [15]" and "Shuai [16]" rows. I did not search the network for them (permission needed); if you know the intended papers I can add them to `data/extracted.yaml` and re-run.
* **Bit totals** of BASE Table IV for Turkanovic, Dhillon-Karla, Cheng-Le cannot be checked: none of the originals give message sizes. JIANG's 1312/1584 are printed without derivation.
* The four figure-based definitions of the nine reduction definitions were not re-run.
* CHANGLE's time constants carry one citation, to Xie et al. [14], which I do not have; DHILLON gives no times, so any DHILLON cost under "its own constants" is not possible (borrowed t_h is flagged).
* Turkanovic's counts are verified against two papers that tabulate the same original (CHANGLE, DHILLON), not against Turkanovic et al. itself, which I do not have.
* `make` is not installed on this machine, so the Makefile is untested; `run_all.sh` is the tested path.
* The proposed patch edits were not compiled with LaTeX.

## 11. Repository state

No existing file was modified. `git status` shows only the pre-existing `M paper/main.tex` (modified before this study began, not by it) and the new untracked directory `research/reference_replication/` (a local `.gitignore` excludes `.venv/`, `work/`, caches). OMNeT++, the compiler toolchain and its Python modules were installed **outside the repository**, in the WSL Ubuntu home (`~/omnetpp-6.0.3`, `~/opp-toolchain`, `~/mamba-root`, `~/bin/micromamba`, `~/authnet`, 3.8 GB total); Docker Desktop was launched once on request and not used. No `git add`, `commit`, `push`, `stash`, `reset` or config change was run, and `git apply --check` was the only apply-style command (read-only).

## 12. Files

```
research/reference_replication/
  REPORT.md  run_all.sh  Makefile  requirements.txt  .gitignore
  data/extracted.yaml
  scripts/   common.py refmodel.py render_pages.py verify_pdf_text.py step2_reproduce.py step3_audit_base.py
             step4_common_env.py step5_netsim.py gen_omnet_ini.py step5b_omnet_results.py step6_compare_ours.py step7_base_vs_ours.py make_patch.py report_to_pdf.py
  tests/     conftest.py test_reproduction.py test_model.py test_netsim.py test_omnet.py test_report_numbers.py
  results/   step2_*.csv step3_findings.csv step4_*.csv/.png step5_*.csv/.png step5b_*.csv/.png step7_*.csv/.png/.md omnet_results.csv step6_claims.csv pdf_text_checks.csv *_summary.txt
  omnet/     AuthNet.ned AuthNet.cc omnetpp.ini (generated) configs_{main,sens,fig}.txt collect.py run_omnet.sh smoke.sh setup_toolchain_and_omnetpp.sh
  proposed_patches/ours_main_tex.diff
  REPORT.pdf (rendered from REPORT.md by scripts/report_to_pdf.py)
  work/      (git-ignored) extracted text, 300-DPI page renders, patched copy of main.tex
```

## 13. Evidence and BASE-conformance audit

This section was added after a second verification pass requested by the authors. It records (a) how every source value was checked, (b) whether the simulation uses the same things as BASE, and (c) what the pass corrected.

### 13.1 How each source value was verified

| source | verified how | result |
|---|---|---|
| BASE Tables II, III (p.4488) | read from 300-DPI render | agree with `extracted.yaml` |
| BASE Tables IV, V (p.4489) | read from render; compared cell by cell with `research/paper_audit/paper_tables.py` | agree (all 10 + 10 rows) |
| BASE Table VI and Fig. 3 (p.4490) | read from render in this pass | all 6 rows agree with `paper_tables.py` (Das et al. row excluded there because "768 + CH*" and "-"); Fig. 3 is a **single group of bars** (y-axis "Storage Overhead (%)", 0.50-0.75, proposed lowest at about 0.53), not a curve against vehicles |
| BASE Figs. 1-2 (pp.4488-4489) | viewed | x-axis "Vehicles in VANET" 300-1800, y-axes 30-100 ("Communication Overhead (%)", captioned "Processing") and 20-44 ("Communication Cost (bits)"); proposed lowest in all three figures |
| BASE Sec. V text (static devices; "every message consists of 128 bits; therefore a total of 264 bits"; processing cost "of both parties") | viewed on p.4489 render | quoted correctly |
| BASE reference list [11]-[20] (p.4491) | PDF text layer, regex-checked by `verify_pdf_text.py` | [14] Wang et al. VANET, [15] Wen et al. edge AI, [16] Jiang et al. chaotic maps |
| JIANG Table 1, Table 2, Fig. 3 and the T_H/T_C sentence | viewed | Table 2 agrees; Fig. 3 bars (about 33 / 66, 98, 66 / 131 / 33 / 264, 328, 198) agree with the times computed from Table 2 |
| DHILLON Tables 3 and 4 and the 128-bit sentence | viewed | agree |
| CHANGLE Tables II-IV and the t_h sentence | viewed (p.9) | agree; the t_mul sentence is at the foot of the previous page and was checked in the text layer only |
| JIANG hash output length | searched the text layer for "bits", "128", "160", "SHA" | not found; reported as "not found in the text layer", not as "not stated" |
| measured constants (ESP8266, Mac, t4g) | not re-measured; read from `research/paper_audit/results/*.csv` | `tests/test_model.py` pins T_H = 36.342 µs, T_ECM = 276.35 ms, HKDF/T_H = 17.31 |
| numbers quoted in this report | `tests/test_report_numbers.py` recomputes them from the paper tables and result files and fails if REPORT.md disagrees | passes |

### 13.2 Does the simulation use the same things as BASE?

| item | BASE | used here | same? |
|---|---|---|---|
| simulator | OMNeT++ (version not given) | OMNeT++ 6.0.3, **our own model** (no BASE project files) | **no**: same tool, different model |
| area, device count | 1500 x 1500; 100-1000 (Table II) | same; plus 300-1800, the x-axis of BASE's Figs. 1-2 | yes (Table II); the two BASE ranges disagree, both run |
| servers | 5% ("one per hundred") | 5% | yes, BASE's own text is inconsistent |
| link rate, range, hand-off, energy | 10 Mbps, 500-800 m, 10 ns, 75.6 mW tx/rx | same (500 m default, 800 m variant) | yes |
| sampling interval 15 µs | not defined | event-time quantum | interpretation |
| device speed 160 km/h | Table II value, but Sec. V says static | static by default; **160 km/h run as a variant** (random direction, reflected at the border, server chosen at session start) | yes, both; mobility changes nothing measurable (N = 1000, measured constants: 1,021 +/- 398 vs 1,045 +/- 370 ms; hash-only schemes identical to two digits) because sessions last milliseconds |
| per-operation times | Table III (T_H = 0.32 SHA-1, T_SE/D 5.6, T_ECM 17.1, T_C 0.32, T_fe 17.1 ms) | environment `BASE` uses exactly these; `MEAS` uses our measurements | yes / sensitivity |
| operation counts, message bits | Table V, Table IV | same, per scheme; proposed also at 2 messages / 264 bits (BASE's text) | yes |
| roles costed | processing "of both parties, source and destination" (Sec. V-A) | device + server; the user/client column of Table V is not charged | consistent with the text; Table V's user column is ignored |
| packet size | "128 Kbps" in Table II, "128 bits" per message in the text | per-message bits = total / number of messages | BASE conflict, not resolvable |
| adversary | "randomly generated"; a device attacking, and a device pretending to be a server | forged requests to servers only (5% of N, 1 per second, our assumption); **rogue-server adversary not modelled** | partial |
| TA | one | not simulated (offline phase only; BASE does not count offline messages either) | consistent |
| metrics | processing, communication, storage overhead as "%" with undefined baselines | latency (ms), server busy time (ms), kbit on air, energy (mJ); storage as arithmetic only | **no**: BASE's % definitions cannot be recovered (audit A1) |
| schemes in BASE's figures | Gope, Gupta, Hassan 2018/2023, Zhanfei (no data given) | the Tables IV-VI schemes | **no**: Figs. 1-3 cannot be reproduced; the compared schemes are not tabulated |
| mobility model, MAC, propagation, SUMO | SUMO is mentioned in the Conclusion, nothing else is given | FIFO shared channel, no loss, no interference | no |
| seeds, run lengths | not given | 5 repetitions, one authentication per device | unknown |

### 13.3 What the verification pass corrected

1. **BASE Fig. 3** is not a curve against vehicles: my shape comparison said all three figures rise with vehicle count; corrected in 8.8.
2. Run-to-run spread of the proposed scheme's latency at N = 1000 was stated as "up to 35%" of the mean; that is the reference case only. It is **up to 77%** in other variants (found by the new report-number test).
3. CHANGLE's "[14]" is cited once, after the sentence that gives both t_mul and t_h (was "both [14]").
4. The statement that JIANG's hash length is "not stated" is now "not found in the text layer".
5. Device speed (160 km/h) was a documented omission; it is now run as a variant (result: no effect).
6. The N = 300-1800 grid (BASE Figs. 1-2 axis) was added; it extends the earlier runs, and the 2,345 earlier OMNeT++ rows are byte-identical in the new results file.
7. `tests/test_report_numbers.py` was added so that the report's quoted numbers are tied to the data.
8. The report was restructured around the intended comparison (BASE's simulated results versus OURS in the environment BASE took from the three papers, section A); the audit of the three papers had been presented as the main comparison and is now labelled supporting evidence.
9. The first PDF contained no figures (the images failed to load); this was not noticed until the figures page was opened. Fixed and checked page by page.

### 13.4 Still not matched to BASE, and why

* BASE's simulation project, version, seeds and run lengths are unavailable.
* BASE's Figs. 1-3 compare schemes with no tabulated values, and their "%" definitions are not recoverable; we can only compare shapes.
* The user/client role and the rogue-server adversary of BASE's Sec. V are not simulated.
* The "128 Kbps" packet size in Table II conflicts with the "128 bits" in the text.
* Because of all this, Step 5 is a sensitivity analysis of our model, and nothing in it supports or refutes BASE's figures.

## 14. What is needed to make the simulation the same as BASE

Section 13.2 lists where the simulation differs from BASE. Closing those gaps depends mostly on things only the BASE authors can supply; a few can be closed from our side.

### 14.1 Only the BASE authors can provide

| gap | what is needed |
|---|---|
| model and simulator | their OMNeT++ project (`.ned`, `.ini`, C++ sources), the OMNeT++ version and any frameworks used (INET, Veins, SUMO; the Conclusion mentions "Simulation of Urban Mobility", nothing else is given) |
| run settings | seeds, number of repetitions, simulation length, how often each device authenticates |
| BASE's "%" metrics and Figs. 1-3 | the formula and baseline behind each "%" overhead, and the raw values plotted for each number of vehicles |
| schemes in Figs. 1-3 | per-scheme costs for Gope 2016, Gupta 2019, Hassan 2018 and 2023, Zhanfei 2024 (they appear in no BASE table); the original papers would help for the costs but not for BASE's "%" formula |
| adversary | what the "randomly generated" adversaries do, in particular the device that pretends to be a server; the adversary share and rate; how adversaries enter the reported costs |
| unclear Table II entries | what "Packet Size 128 Kbps" means (128 bits per message, as the text says, or 128 kbit packets) and how the 15 µs sampling interval is used |

With only the first two rows answered, BASE's setup could be reproduced; without the project files any model of ours remains our own interpretation.

### 14.2 Can be done from our side if decided

| item | what it needs |
|---|---|
| user/client role | Tables IV and V already give per-role operation counts and bits, so a three-party flow (user, device, server) can be simulated; a decision is needed on how users map onto devices (Table V gives the proposed scheme no user cost) |
| 128 kbit packet reading | a further sensitivity run (each message would take about 12.8 ms on a 10 Mbps link, far from the text's 128 bits) |
| INET or SUMO radio and mobility | another download and a model of our own; without BASE's configuration it would still be a guess |
| contacting the authors | a message listing the main requests in 14.1 was sent on 2026-10-27 (status in `docs/author-contact.md`) |
