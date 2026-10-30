# Jan et al. (IEEE IoT J. 12(5), 2025) Figs 5-8 vs base paper Figs 1-3

> **Status and limits.** This file records a numerical relationship between plotted values. The values come from exact vector
> extraction (see `../targets/README.md`; both extractions reproduce), so the fit residuals are at the extraction noise floor.
> What it does not establish: how either figure was produced, which came first (the direction is inferred from publication
> dates and clipping), or any intent. The base paper's corresponding author is also a co-author of Jan et al., so reuse of an
> author's own data is one possible reading; whether it is disclosed or intended is not something these files can show. The
> comparison is not used in the manuscript, and wording such as "derived" or "hand-edited" below should be read as a description of
> the numbers, not of conduct.

Source PDF: `docs/references/jan_2025_ml_auth_edge_iov.pdf` (DOI 10.1109/JIOT.2024.3483275).
Exact values: `jan_targets.json` (from `jan_extract.py`); differences and model fits: `compare.json`
(`jan_compare.py`); shape fits: `shape.json` (`jan_shape.py`). Base values: `../targets/fig_targets.json`.
Scripts run with `python -I`; they need `pikepdf` (a venv).

## Verdicts

| base fig | Jan source | verdict | transformation | residual |
|---|---|---|---|---|
| Fig 1 | Fig 5 | derived | base = Jan + 7.227 for every series and group (Proposed included); x labels 200..1200 -> 300..1800 (x1.5 exact); y relabelled "ns" -> "Communication Overhead (%)" | rms 0.0186 over 33 cells, max 0.044; extraction noise floor 0.0168 |
| Fig 2 | Fig 7 | derived | base = Jan + 3.500 for Gope, Gupta, Hassan 2023, Zhanfei; Jan + 4.900 for Proposed; y relabelled "ms" -> "bits" | per-series-constant rms 0.0058, max 0.013; noise floor 0.0055 |
| Fig 3 | Fig 8 | derived, bars hand-edited | same legend order, bar order, colours. Zhanfei and Gupta unchanged; Proposed +0.020, Hassan 2023 +0.010, Hassan 2018 +0.006, Gope +0.023 | no constant model fits |

Uniform constant fits Fig 1 (rms 0.0186) but not Fig 2 (rms 0.560); per-series constants fit Fig 2.
The Fig 1 slope against Jan is 0.99994, i.e. a pure shift. The 7.227 offset is not round (s.e. ~0.008).

Direction of derivation is inferred from dates (Jan online Oct 2024; CMC 2025; base 2026) and from base's
clipped Gupta bars (Jan Gupta + 7.227 exceeds the base axis top of 100 in exactly the three groups that are
clipped in base). The CMC 2025 Fig. 6 is the same data again: CMC minus Jan is constant per series
(+7.63 Proposed, -5.82 Zhanfei, -7.54 Hassan 2023, -11.73 Gupta, -7.42 Gope, -6.69 Hassan 2018; pixel reads).

Other evidence: the within-group rank order, the dips (Hassan 2018 at group 2, Gupta at group 4), and all
identical-height coincidences are preserved cell for cell. Jan Fig 7 competitor series are on a 0.5 grid
(15 of 30 cells vs 1.4 expected): typed in by hand; the Proposed series is not round.
Negative control: base Fig 1 vs Jan Fig 6 is unrelated (differences +17.7 to +29.1).

Fig 1 table, Jan Fig 5 (ns; x = 200..1200):

| series | 200 | 400 | 600 | 800 | 1000 | 1200 |
|---|---|---|---|---|---|---|
| Proposed | 35.458 | 37.510 | 39.999 | 43.275 | 45.241 | 56.242 |
| Zhanfei | 65.461 | 69.695 | 74.538 | 78.994 | 83.579 | 85.238 |
| Hassan 2023 | 57.686 | 62.443 | 63.230 | 67.249 | 70.697 | 76.855 |
| Gupta | 87.597 | 89.650 | 93.535 | 92.662 | 95.673 | 96.767 |
| Gope | 78.994 | 80.782 | 83.056 | 85.238 | 87.991 | 89.128 |
| Hassan 2018 | 81.962 | 84.537 | 81.660 | 87.684 | 90.652 | 92.662 |

Jan Fig 7 (ms; group centres ~100, 300, ..., 1100):

| series | g1 | g2 | g3 | g4 | g5 | g6 |
|---|---|---|---|---|---|---|
| Gope | 26.450 | 27.982 | 30.996 | 33.654 | 34.976 | 37.243 |
| Gupta | 24.210 | 26.973 | 29.005 | 31.676 | 30.996 | 34.244 |
| Hassan 2023 | 24.995 | 27.995 | 30.000 | 32.004 | 32.502 | 35.501 |
| Zhanfei | 25.493 | 30.000 | 32.502 | 34.991 | 36.849 | 38.003 |
| Proposed | 17.503 | 18.447 | 19.848 | 20.936 | 22.206 | 23.686 |

## Jan's own setup and metric definitions

- Simulator: "python and OMNET++" (Sec. V). No code or data statement.
- Table II: 800 x 800 m, 550-1200 devices, 5-10 edge servers, 52000 mAh, Tx 91.4 mW, Rx 59.1 mW, channel
  delay 10 ms, idle 15.4 uW, range 500 m, 64-bit DES, dynamic and static topology. Base Table II (1500 x 1500 m,
  100-1000 devices, 75.6 mW) does not match it.
- Jan is inconsistent with itself: Table II says 550-1200 devices but Fig 5 plots 200-1200; 5-10 servers vs
  Fig 6 plots 2-12.
- Metrics: processing time = "time from message generation to its encryption", plotted in ns. Fig 7's caption
  says "communication overhead" but the axis is end-to-end delay (ms). Storage = "percentage of memory
  required for storing the crypto primitives", no formula. Neither Jan nor base defines the "%" or "bits".

## Can the curves be reproduced from the protocols? Not even Jan's own

- Ops x per-op time fails: a fit over the four schemes with pure hash/XOR counts gives Th ~3.9 ns,
  Txor ~3.5 ns with residuals up to +-18 ns; solving exactly gives a negative Th. Gope (12Th+5X) plots below
  Hasan 2018 (7Th+14X), impossible for any Th > Txor. Nanosecond hash times are not plausible on mote-class devices.
- Bits vs delay (Fig 7): r = 0.67-0.73 with bits, ~0 with message count. Hassan 2023 (672 bits) has about the
  same delay as Zhanfei (3,392 bits); 4 messages x 10 ms channel delay would be 40 ms, not 17.5.
- What is reproducible: curves rise ~linearly with N. Proposed slope: Fig 5 0.0186 ns/vehicle (R^2 0.88, +11
  jump at 1200), Fig 7 0.0062 ms/vehicle (R^2 0.997, intercept 16.7), Fig 6 1.25 ns/server (R^2 0.98).

## Jan Tables III-V (transcribed from a 400-dpi render; text is outlined)

Table III (ops): Proposed 4Th+6Txor total (device 2Th+3Txor, server 2Th+3Txor); Zhanfei 8Th+6Tecm;
Gupta 16Th+11Txor; Gope 12Th+5Txor; Li 16Th+11Txor; Makhalouf 9Th+13Txor; Abdelshafy 6Th+11Txor;
Liu 7Th+19Txor; Hasan [22] 7Th+14Txor; Hassan [26] 2Tpa+2Tpm / 2Te/d+2Tprng / 3Tts+1Ttkng (total blank).
Table IV (messages, bits): Proposed 4, 512; Hassan [26] 6, 672; Zhanfei 3, 3392; Li 4, 4672; Makhalouf 5, 6144;
Gupta 5, 3038; Gope 4, 3184; Hasan [22] 6, 32000; Liu 6, 30620; Abdelshafy 5, 24546.
Base Tables IV-V compare a different set (Poorambage, Turkanovic, Dhillon-Karla, Cheng-Le, Jiang, Shuai, Wazid,
Sadhukhan, Fakroon): none of Gope, Gupta, Hassan or Zhanfei, although base Figs 1-3 plot exactly those.

## Caveats

- Heights are read to the vector grid resolution (Fig 5 0.044, Fig 6 0.038, Fig 7 0.013, Fig 8 0.00012). The
  derivation claims rest on the differences being constant at the noise floor, which is much stronger than the
  heights themselves.
- The CMC comparison uses pixel reads from `provenance.md`, not a fresh extraction.
- Direction of derivation is inferred, not documented.
