# Do the Numbers Hold on Real Hardware? A Measurement-Based Re-evaluation of a "Low-Cost Hybrid ECC Authentication Protocol"

*Working draft. Every number is measured or recomputed in this repository (`research/paper_audit/`, `firmware/esp8266/`).
`[CITE]` marks places that need real references; none are invented here. Suggest sending the authors the audit before submission.*

Title alternatives: "Reproducing a Lightweight IoT Authentication Protocol's Cost Claims on a Microcontroller";
"Where Lightweight Authentication Cost Claims Break: Measured Primitive Costs vs. Assumed Constants".

## Abstract
Al-Rasheed et al. propose a two-message hybrid ECC/symmetric mutual-authentication protocol for IoT and report about 17%, 21% and 12% lower
communication, processing and storage cost than ten prior schemes, using OMNeT++ simulation and assumed per-operation times
(T_ECM = 17.1 ms, T_SE/D = 5.6 ms, T_H = 0.32 ms). We (i) audit the paper's own tables and figures, (ii) implement the device side in C
and interoperate with an independent Python server, and (iii) time the primitives on a 32-bit microcontroller (ESP8266), a cloud ARM core
and a laptop, then recompute the paper's cost model with measured values. The headline percentages cannot be derived from the paper's tables or
figures under any definition we tried, and the tables contradict the text (four messages and 1024 bits versus two messages and 264 bits).
Measured P-256 scalar multiplication is 16x slower than assumed (276 ms vs 17.1 ms), while symmetric operations are 5-11x faster. As a result the
protocol is about 120-3,000x cheaper than the ECC-based schemes it is compared with, but 4-11x more expensive than the hash-only schemes in
the same table on the ESP8266 with AES-GCM; the gap narrows on faster cores and the ranking reverses with hardware AES and SHA-1. The scheme also lacks
forward secrecy, uses no elliptic-curve operation online, and its server lookup scales linearly with the number of devices.

## 1. Introduction
Lightweight authentication papers commonly report cost from operation counts times assumed timings. This makes conclusions depend on a few constants
that are rarely measured on the target class of device [CITE: related work on benchmarking lightweight crypto on MCUs]. We test one such paper end to end.
Contributions: (1) a reproducibility audit of the paper's evidence; (2) the first (to our knowledge, to be checked) measured primitive costs
on an MCU for this protocol family's cost model, with a sensitivity analysis showing when the ranking flips; (3) protocol-level findings that bear on how
the scheme should be compared; (4) an open implementation and benchmark.

## 2. The protocol and its claimed evidence
Offline, a trusted authority derives lambda_X = H1(ID_X || s) mod n per entity and shares peer secrets; online, a device sends M1 = (PID, Enc, MAC),
the server replies M2, and both derive K = KDF(k* || N_i || N_j || t), k* = KDF(lambda_V || lambda_R). Costs are compared in Tables IV-VI against ten schemes using
Table III's constants. Figs. 1-3 compare against a different four schemes.

## 3. Method
**Audit.** Tables III-VI were transcribed from a 600-DPI render; Tables III, IV and VI were OCR-verified and Table V checked manually twice
(`verify_tables.py`). Figures were digitised by eye (about +/-0.2). **Implementation.** A portable C device core (BearSSL AES-256-GCM, SHA-256, HKDF) with the
paper's JSON/base64 wire format interoperates with the unmodified Python server: 20/20 handshakes on an ESP8266 over Wi-Fi with identical session keys and
replay rejection; 12/12 natively. **Benchmark.** One C source on every platform; ESP8266 (L106, 80/160 MHz, no crypto hardware, cycle counter),
AWS t4g.nano (one pinned Graviton2 core) and an Apple-silicon laptop. Median of 100 runs (24 for EC). Every output is checksummed; all digests are identical across
platforms and no EC call failed. **Recomputation.** The paper's per-role operation counts (Table V) times measured times, with a sensitivity grid over how T_SE/D (full GCM,
cached key schedule, CTR without MAC, one AES block) and T_H (one or two SHA-1 blocks) are defined. Competitor protocols are not re-implemented.

## 4. Results
**4.1 Audit.** (a) 17/21/12% are not derivable from Tables IV-VI or Figs. 1-3 (nine definitions each; e.g. Fig. 3 gives 7% vs the best competitor, 17% vs the mean). (b) Table IV lists the proposed scheme
with 4 messages / 1024 bits; text says 2 messages / 264 bits; 2 x 128 = 256; SHA-256 PID plus a 128-bit tag already exceed 264 bits. (c) Under Table III, three hash-only schemes cost less than the proposed one
(6.1-7.0 ms vs 23.7 ms). (d) Table V charges 2T_H + 2T_SE/D, Eq. 22 says 1 KDF + 1 Enc + 1 MAC; Algorithms 1-2 describe a different protocol from Sections III-V. (e) Fig. 2 shows a fixed-size protocol's
bit cost growing with vehicle count; Fig. 1's caption and axis disagree.

**4.2 Measured constants.** ESP8266 @80 MHz: T_H 0.036 ms (paper 0.32), T_SE/D 0.48-1.15 ms (paper 5.6), T_ECM 276 ms for P-256 (paper 17.1; 624 ms for generic code, 131 ms X25519). T_ECM/T_H is 7,600 vs the paper's 53.

**4.3 Recomputed ranking.** Against ECC-based schemes the proposed scheme is about 120-3,000x cheaper. Against Turkanovic, Dhillon-Karla and Jiang, with AES-GCM, all 12 AES-GCM sensitivity cells put the proposed scheme behind on the ESP8266 at both clocks
(3.8-10.8x; r = T_SE/D/T_H of 6.7-31.6 against a crossover of 2.0-4.5). The result weakens on faster cores with software crypto: 11 of 12 cells on the t4g.nano (r = 4.2-30.3) and only 6 of 12 on the laptop (r = 2.0-16.0). The ranking flips only for unauthenticated AES (which drops the MAC the scheme requires) or with hardware crypto:
OpenSSL on Graviton2 and on the laptop gives r = 1.06 and 0.82. The op-count model also under-predicts the real implementation (2.4 ms modelled vs 5.3 ms measured for the device).

**4.4 Protocol-level.** No forward secrecy (5/5 past session keys recovered from recorded traffic once k* is known). ECC appears only in offline provisioning; Eq. 8 is a hash mod n and the public point is optional and unused. Server pseudonym resolution is O(N x W):
4.8 ms at 1,000 and 23.9 ms at 5,000 devices on a laptop; a precomputed table would need about 800 KB at 1,000 devices x 25 epochs against the paper's 320-bit storage figure.

## 5. Discussion
The paper's headline advantage over ECC schemes is real and larger than reported, but it is a comparison with schemes that provide different properties (we have not verified which provide forward secrecy). Its claimed processing advantage over hash-only schemes is a statement about a
hardware regime: it holds when AES-GCM is cheap relative to SHA-1 (hardware acceleration, or a fast core running table-based AES) and fails on the low-end MCU we measured. Communication and storage claims cannot be checked from the paper because Tables and text disagree. Cost models based on assumed constants should state, and test, the ratio that decides the ranking.

## 6. Threats to validity
One MCU class (32-bit); no 8/16-bit parts, no MCU with hardware AES, no energy measurement. Primitive costs are BearSSL's; other libraries shift constants (the crossover depends on the AES:SHA-1 ratio, not absolute speed). Competitor costs use the paper's operation counts, unverified against the original papers; T_C and T_fe are not measured. The EC benchmark ran on a temporary
heap stack on the ESP8266 (outputs verified by checksum). The t4g.nano is a shared-host VM pinned to one core. Figure values are read by eye. Our implementation is one reading of a specification that leaves the epoch and replay window undefined.

## 7. Reproducibility
Code, raw data and scripts are in the repository: `research/paper_audit/` (audit, recomputation, results/), `firmware/esp8266/` (C core, firmware, benchmark, host and interop tests).
See `FINDINGS.md` for commands.

## Before submitting (checklist)
- [ ] Re-measure on an MCU with hardware AES (and one with AES but no SHA) to settle the 4.3 flip; add a Raspberry Pi 3 point.
- [ ] Verify competitor operation counts against their original papers; check which provide forward secrecy.
- [ ] Send the audit to the authors; check for an erratum or an extended version that explains the 17/21/12% derivation.
- [ ] Fill `[CITE]` with real references; check novelty claims in 1(2) against prior MCU benchmarking literature.
- [ ] Pick a venue (measurement/reproducibility tracks; IEEE TCE comments-and-responses if that format is open).
