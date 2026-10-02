# Re-evaluating "Low-Cost Hybrid ECC Authentication Protocol" (Al-Rasheed et al., IEEE TCE 72(2), 2026)

Status: working findings, not yet a manuscript. Everything below is reproducible from this directory;
raw data is in `results/`. Numbers are measured unless marked *modelled* or *projection*.

## 1. What the paper's evidence actually is
The paper's cost claims (about 17% communication, 21% processing, 12% storage) rest on an OMNeT++ simulation
and on the assumed per-operation times of its Table III (T_ECM 17.1 ms, T_SE/D 5.6 ms, T_H 0.32 ms, "SHA-1").
No operation was timed on hardware. We did that.

## 2. Consistency audit (paper's own tables; `audit.py`, tables transcribed from a 300-DPI render)
| # | Finding | Evidence |
|---|---|---|
| A1 | The abstract's 17% / 21% / 12% are **not derivable from Tables IV-VI** under any definition we tried (vs best, mean, median, worst, each scheme). | communication: 36.0% vs best, 57.5% vs mean; storage (device): 10.1% vs best; processing: see A3. Figs. 1-3 use a different scheme set whose values are not tabulated. Figures too (`figures_audit.py`, bar heights read from 600-DPI renders): none of 9 definitions gives 21% (Fig. 1: 24-49%), 17% (Fig. 2: 19-31%) or 12% (Fig. 3: 7-25%) within 1 point. |
| A2 | Messages and size are inconsistent. Text (Sec. III-E, Eq. 21, V-B): **two** messages, **264** bits. Table IV: proposed scheme = **4 messages, 1024 bits**. | Also "128 bits per message, therefore 264 total": 2 x 128 = 256. With the paper's own instantiation (SHA-256 PID = 256 b, GCM tag 128 b) M1 alone exceeds 264 bits. |
| A3 | Under Table III's constants, Table V ranks the proposed scheme (23.7 ms) **behind** Turkanovic (6.1), Dhillon-Karla (7.0), Jiang (7.0). | Hash-only schemes win unless T_SE/D < 2.0-4.5 x T_H; Table III has 17.5. |
| A4 | Table V charges 2T_H + 2T_SE/D per side; Eq. 22 says 1 KDF + 1 Enc + 1 MAC (device). Section II Algorithms 1-2 describe a different (MAC-address / hash-digest) protocol from the nonce protocol of Sections III-V. | |
| A5 | Table VI is captioned "Communication Cost" but reports storage; Table V cites [17] for two different schemes. | |
| A6 | Figures disagree with the text and tables. Fig. 1 is captioned "Processing requirements" but its y-axis is "Communication Overhead (%)". Fig. 2 plots "Communication Cost (bits)" on a 20-44 range while Table IV spans 1,024-3,360 bits. Fig. 3's y-axis is "Storage Overhead (%)" with values 0.5-0.75. Figs. 1-3 compare against schemes (Gope, Gupta, Hassan, Zhanfei) that do not appear in Tables IV-VI. | Digitised: see A1. Also, Figs. 1-2 are plotted against 'Vehicles in VANET' (300-1800), but the protocol's bit cost cannot depend on network size, and Fig. 2 shows the proposed scheme rising from 22.4 to 28.6 bits as vehicles grow; Fig. 1 clips two series at the 100% axis limit. |

## 3. Measured primitive costs (same BearSSL C code on every platform; median of 100 runs, 24 for EC; `results/*.csv`)
NodeMCU ESP8266 (L106, stock 80 MHz and 160 MHz, no crypto hardware, Wi-Fi off, cycle-counter timing). Every benchmark output
(hash, AES block, CTR, GCM ciphertext+tag, P-256/X25519 points) was checksummed: **all 35 digests are identical on the ESP8266
(both clocks) and the Mac**, no EC call reported failure, and all AES and P-256 implementations agree with each other on the host.

| Symbol | Paper (Table III) | ESP8266 @80 MHz | @160 MHz | measured / paper |
|---|---|---|---|---|
| T_H, SHA-1 (32 B, 1 block) | 0.32 ms | 0.0363 ms | 0.0182 ms | 0.11x |
| T_SE/D, AES-256-GCM 56 B incl. key setup | 5.6 ms | 0.48 (aes_big) / 0.83 (aes_small) / 1.15 ms (aes_ct, constant-time) | 0.24 / 0.42 / 0.57 ms | 0.09-0.20x |
| T_ECM, P-256 variable-base scalar mult | 17.1 ms | **276 ms** (m15); 624 ms (generic i15); X25519 131 ms | 138 ms | **16x** |
| T_ECM / T_H | 53 | 7,600 | 7,600 | 142x |

Timing spread is tiny (p25 = median = p75 on the MCU); ratios are identical at both clocks. Note the paper's own T_SE/D : T_H = 17.5.

Third platform, AWS t4g.nano (Graviton2 / Neoverse-N1, one pinned core, AL2023; instance since terminated), same BearSSL code, 41/41 digests identical to the Mac and the ESP8266: T_H 0.2 us, T_SE/D (GCM 56 B incl. key setup) 2.0 / 5.2 / 6.9 us (aes_big / small / ct), P-256 (m15) 1.75 ms. That core has AES and SHA instructions, but BearSSL does not use them, so this is a software-crypto number (`results/aws_t4g_nano.csv`, `reeval_t4g.txt`).

## 4. Table V recomputed with measured constants (`reeval.py`, `reeval_output.txt`)
Operation counts per role are the paper's; only per-operation times change. Competitor protocols are **not** re-implemented.

**4a. Against ECC-based schemes: the proposed scheme is far cheaper than the paper claims.** ESP8266 @80 MHz, device + server, AES-GCM (aes_big / aes_ct):
proposed 2.08 / 4.73 ms; Sadhukhan, Shuai, Cheng-Le 279-553 ms; Challa 2,487 ms; Poorambage 5,251 ms, i.e. **about 120-3,000x** more expensive. Because T_ECM is 16x worse than assumed, the advantage is much larger than Table III implies. (Wazid and Challa include T_fe, unmeasured and *modelled* at the paper's 17.1 ms.)

**4b. Against hash-only schemes: the ranking depends on what "T_SE/D" means, so we swept it** (4 definitions x 3 AES implementations x 2 T_H definitions; `sensitivity grid` in `reeval_output.txt`). The proposed scheme beats a hash-only scheme (Turkanovic, Dhillon-Karla, Jiang) only when r = T_SE/D / T_H is below about 2.0-4.5.
* **AES-GCM, the AEAD the paper's own instantiation requires** (Sec. IV "Enc = AES-GCM", tag doubles as the MAC of Eq. 14, 17), key schedule paid or cached, 1- or 2-block SHA-1: r = 6.7-31.5. **All three hash-only schemes are cheaper than the proposed scheme in all 12 cells, at both ESP8266 clocks and on the t4g.nano (r = 4.6-30.3 there)** (3.8-10.8x with the key schedule paid, aes_big vs aes_ct).
* The ranking flips only if T_SE/D is read as **unauthenticated** AES: one AES block with cached key (aes_big: r = 0.8, proposed cheaper than all three) or AES-CTR with no MAC (aes_big, 2-block SHA-1: r = 1.6, proposed cheaper). Those readings drop the MAC the paper's security goals require (Eq. 14, SUF-CMA), so we do not treat them as valid instantiations, but a reviewer may. 9 of 24 cells flip on the ESP8266; 17 of 24 on the Mac, where bare AES is relatively cheaper (aes_big GCM r = 4.0, at the crossover).
* **Hardware crypto can reverse 4b (proxy, not an MCU).** OpenSSL with hardware AES/PMULL/SHA-1, per 64 B call, key schedule cached (`results/openssl_hw_proxy.txt`, `openssl_hw_proxy_t4g.txt`): Apple-silicon Mac AES-256-GCM 119 ns vs SHA-1 145 ns (r = 0.82); Graviton2 (t4g.nano) 315 ns vs 297 ns (r = 1.06). Both are below every crossover (2.0-4.5), so with accelerated AES *and* SHA-1 the proposed scheme would beat the hash-only schemes. The 4b result therefore depends on the platform: it holds with software crypto (ESP8266, and BearSSL on the Mac and t4g) and flips where both primitives are hardware-accelerated. MCUs that accelerate AES but not SHA-1 would flip it more strongly. We have not measured such an MCU (no ESP32 or similar on hand).
* The op-count model under-predicts the real implementation: model 2.37 ms for the device (aes_ct) vs **5.26 ms** measured end-to-end in our firmware (the model omits HKDF at 0.63 ms, base64/JSON parsing, per-message key schedule).

Defensible statement: *under the AEAD the paper's instantiation requires, measured on a 32-bit MCU, the proposed scheme is 4-11x more expensive than the three hash-only schemes in Table V and 120-3,000x cheaper than the ECC-based ones; the claimed general processing advantage holds only against the ECC schemes.*

## 5. Protocol-level findings (this implementation of the paper's Section III model)
* **No forward secrecy.** K = KDF(k* || N_i || N_j || t); N_i, N_j and t travel encrypted only under k*. With k* an attacker recovered **5/5** past session keys from recorded M1/M2 (`no_forward_secrecy.py`). ECC key-agreement schemes can provide it; we have not checked whether the specific compared schemes do, so whether the cost comparison is like-for-like is open.
* **ECC is nominal (in the paper itself, not just this code).** Eq. 8 defines lambda_X = H1(ID_X || s) in Z_n: a hash reduced mod n, not a curve operation. Sec. IV-A only *optionally* sets a public point P_X = lambda_X G, and Eqs. 9-22 never use it. Every online operation is KDF / Enc / MAC / H (Eq. 22). The 'hybrid ECC' label describes offline key provisioning only; in this implementation the public point is optional and unused on the protocol path.
* **Server cost is O(N), not constant.** PID = H2(lambda || t) is unlinkable, so the server probes devices x epoch-window (13-25 epochs). Measured on the Mac: 4.8 ms at 1,000 devices, 23.9 ms at 5,000 (`results/server_scaling.txt`), versus Table V's constant 2T_H + 2T_SE/D. *Projection:* at 74.7 us per SHA-256 on the ESP8266, a gateway of that class would need about 1 s per authentication at 1,000 devices.
  A precomputed PID table does not escape this: N x W entries x 32 B = 1,000 x 25 x 32 B = **800 KB** at 1,000 devices, against the paper's Table VI server storage of 320 bits. So the scheme pays either O(N x W) compute per authentication or O(N x W) storage, and neither matches Tables V-VI.
* The epoch/replay-window is unspecified by the paper; this implementation keeps it in RAM (reset on reboot) and the demo device needed a flash-persisted epoch to run across reboots. Interop between an independent C implementation and the Python server, 20/20 handshakes with matching session keys, is in `firmware/esp8266`.

## 6. Threats to validity (state these in any write-up)
* One MCU (ESP8266, 32-bit); the paper's targets include 8/16-bit parts. Absolute numbers will differ; the **ratios** are the claim.
* Primitive costs are BearSSL's. Other libraries (micro-ecc, mbedTLS) and hardware AES (e.g. ESP32) change the constants. The crossover test is independent of absolute speed but not of the AES : SHA-1 ratio: the Mac already sits at the crossover (aes_big GCM r = 4.0). Hardware AES could move an MCU there too; this is the main way the 4b conclusion could change.
* Competitor costs are the paper's operation counts times our times, not re-implemented protocols. Their op counts are taken from the paper's Table V, which we have not checked against the original papers.
* T_C and T_fe not measured. SHA-1 is used for T_H because the paper does; the implementation uses SHA-256 (0.075 ms).
* P-256 timing ran on a temporary heap stack on the ESP8266 (the 4 KB task stack is too small for the m15 window table). Returning to the original stack reset the chip in testing (cause not found), so the benchmark never returns; the outputs are verified correct by checksum and were identical across 8 passes.
* Tables were transcribed from a rendered PDF. `verify_tables.py` OCR-checks Tables III, IV and VI (all cells match; `results/verify_tables.txt`). Table V (math typography) defeats OCR and was checked by two manual cell-by-cell readings at 300 and 600 DPI plus partial OCR agreement; all 30 cells agree. Figure values (`figures_audit.py`) are read by eye (about +/-0.2).
* No energy measurement; no 8/16-bit hardware; no Raspberry Pi 3 data point; no MCU with hardware AES. The t4g.nano is a shared-host cloud VM, pinned to one core, so its absolute numbers are indicative only.

## 7. Reproduce
    .venv/bin/python research/paper_audit/audit.py                       # section 2
    make -C firmware/esp8266/host -f Makefile.bench && firmware/esp8266/host/prim_bench <label> 100   # host
    cd firmware/esp8266 && pio run -e bench -t upload                    # ESP8266 @80 MHz (bench160 for 160 MHz)
    .venv/bin/python research/paper_audit/reeval.py results/*.csv        # sections 3-4
    .venv/bin/python research/paper_audit/no_forward_secrecy.py; .venv/bin/python research/paper_audit/server_scaling.py
