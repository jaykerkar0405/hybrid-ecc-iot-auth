# Paper reproduction: analytic checks

## 1. Processing cost (Table V formulas x Table III constants, ms)

| Scheme | User | Device | Server | Device+Server |
|---|---|---|---|---|
| Proposed scheme | 0.00 | 11.84 | 11.84 | 23.68 |
| Challa [17] | 46.70 | 69.36 | 86.78 | 156.14 |
| Turkanovic [12] | 2.24 | 2.24 | 1.60 | 3.84 |
| Porambage [11] | 70.96 | 191.30 | 138.40 | 329.70 |
| Dhillon & Karla [13] | 2.56 | 1.92 | 2.56 | 4.48 |
| Cheng & Le [14] | 37.08 | 35.80 | 2.24 | 38.04 |
| Shuai [16] | 19.02 | 18.06 | 19.34 | 37.40 |
| Jiang [15] | 2.24 | 1.60 | 3.20 | 4.80 |
| Wazid [17] | 32.46 | 12.48 | 24.00 | 36.48 |
| Sadhukhan [18] | 28.94 | 28.62 | 23.04 | 51.66 |

Proposed scheme (paper): device 11.84 ms, server 11.84 ms (= 2*TH + 2*TSE_D = 11.84).
Reduction vs mean of the nine baselines (device+server): 67.8%  (paper claims ~21%).
Baselines costlier than proposed: 6/9. Cheaper or equal: ['Turkanovic [12]', 'Dhillon & Karla [13]', 'Jiang [15]'].
NOTE: Turkanovic, Dhillon&Karla and Jiang (hash-only schemes) come out cheaper than the proposed scheme under Table III, because T_SE/D=5.6 ms >> T_H=0.32 ms. The paper's processing claim only holds against the ECC-heavy baselines.

## 2. Our implementation's measured operation counts (instrumented)

| Regime | Side | H2 hashes | HKDF | AES-GCM | EC mult | TH (KDF as hash) | cost ms | TH (KDF ignored) | cost ms |
|---|---|---|---|---|---|---|---|---|---|
| warm | device | 1 | 1 | 2 | 0 | 2 | 11.84 | 1 | 11.52 |
| warm | server | 2 | 1 | 2 | 0 | 3 | 12.16 | 2 | 11.84 |
| cold | device | 1 | 2 | 2 | 0 | 3 | 12.16 | 1 | 11.52 |
| cold | server | 2 | 2 | 2 | 0 | 4 | 12.48 | 2 | 11.84 |

Warm (cached k*): device 11.84 ms, server 12.16 ms vs paper 11.84 / 11.84 ms.
Device matches the paper's 2TH + 2TSE_D exactly when HKDF counts as one T_H. The server does one extra H2 because resolve_pseudonym walks the epoch search window (FR-4.2); a first-hit lookup would likely also match (not tested).
Zero ECC scalar multiplications occur in the online phase, consistent with the paper.

Our device+server (warm): 24.00 ms -> reduction vs the paper's baseline mean 67.4% (paper claims ~21%).

## 3. Communication cost (Table IV, bits)

- Paper, proposed: 1024 bits (Table IV, 4 messages) or 264 bits (text, 2 messages).
- Ours, raw fields M1+M2: 1456 bits (182 bytes, 2 messages).
- Reduction vs mean of baselines using paper's 1024: 57.5%  (paper claims ~17%).
- Reduction vs mean of baselines using our 1456: 39.6%.
NOTE: the paper's three communication figures are mutually inconsistent (1024 bits/4 msgs in Table IV, 264 bits/2 msgs in text, '128 Kbps packet size' in Table II). The ~17% claim cannot be re-derived from any single one of them.

## 4. Storage (Table VI, bytes)

- Paper proposed: server 320 B, device 320 B. Baseline means: server 634 B, device 590 B.
- Paper-implied reduction: server 49.5%, device 45.7%, combined 47.7% (paper claims ~12%).
- Ours (JSON-serialised state, single peer): server 449 B, device 424 B. Not directly comparable: the paper does not state what its 320 B contains.

## 5. Where could the abstract's 17% / 21% / 12% come from? (figure-derived, approximate)

Values below are read by eye from Figs. 1-3, so treat them as +-2 points.

| Figure | Measure | Mean reduction vs figure baselines | Abstract claim |
|---|---|---|---|
| Fig. 1 | 'processing' (axis says communication) | 44% | 21% (processing) |
| Fig. 2 | communication | 27% | 17% (communication) |
| Fig. 3 | storage | 17% | 12% (storage) |

Conclusion: the abstract's percentages match neither the tables (68% / 57% / 48%) nor, cleanly, the figures. The figures compare against different schemes (Gope, Gupta, Hassan, Zhanfei) than the tables, and those schemes' costs are given nowhere in the paper, so the figure results cannot be independently recomputed.

