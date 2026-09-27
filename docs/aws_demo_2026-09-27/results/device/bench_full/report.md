# Hybrid ECC IoT Authentication -- Benchmark Report

Source paper: Al-Rasheed et al., "A Low-Cost Hybrid Elliptic Curve
Cryptography Authentication Protocol for Trustworthy Internet of Things
Communication," IEEE Trans. Consumer Electronics, vol. 72, no. 2,
pp. 4483-4491, May 2026.

## Environment

- Python: `3.11.16 (main, Aug 24 2026, 00:00:00) [GCC 11.5.0 20240719 (Red Hat 11.5.0-5)]`
- Platform: `Linux-6.18.48-109.150.amzn2023.aarch64-aarch64-with-glibc2.34`
- Processor: `aarch64`
- `cryptography` version: `50.0.1`

**Methodology and disclosed deviation (PRD Section 6.2).** The paper's
Tables IV-VI numbers come from an OMNeT++ simulation using *assumed*
per-operation timing constants (Table III: T_ECM = 17.1 ms, T_H = 0.32 ms,
T_SE/D = 5.6 ms, ...), calibrated for resource-constrained embedded
hardware -- not measured on real hardware in that paper. This report
instead measures **real operation costs on this benchmarking host** (real
AES-256-GCM, real HKDF-SHA256, real SHA-256, via the `cryptography`
bindings to OpenSSL) for the proposed scheme, and separately reports the
**paper's own reference values** for the nine baseline schemes it cites
(full re-implementation of those nine external protocols is a v2 backlog
item, not done here). Both are shown below, never conflated: our numbers
are labeled "measured"; the paper's are labeled "paper-reported" /
"source paper".

## Summary: measured reduction vs. paper's claimed reductions

The paper claims approximately 17% lower communication cost, 21% lower
processing cost, and 12% lower storage cost versus the schemes it compares
against. The table below computes the analogous reduction from this
project's own measurements (proposed scheme) against the mean of the
paper-reported baseline values for the same metric.

| Metric | Measured | Baseline mean (paper-reported) | Our reduction | Paper claims | Direction matches? |
|---|---|---|---|---|---|
| Communication | 182 bytes | 301.333 bytes | 39.6% | ~17% | Yes |
| Processing | 0.118 ms | 78.727 ms | 99.9% | ~21% | Yes |
| Storage | 873 bytes | 1223.200 bytes | 28.6% | ~12% | Yes |

The communication row compares **raw field bytes** (PID + ciphertext + tag
+ nonce, 182 bytes)
against the paper's Table IV bit-packed totals, since that is the
apples-to-apples comparison. Our demo transport's actual JSON+base64 wire
size is larger (358 bytes) due to
envelope/encoding overhead (protocol/messages.py) that is a transport
choice (Section 4.3), not a property of the cryptographic protocol itself.

*"Direction matches?"* only checks whether our reproduction agrees with
the paper on the *sign* of the effect (lower cost or not) -- it does not
claim to reproduce the exact percentage, since we measure real wall-clock
time on different hardware rather than reusing the paper's assumed Table
III constants (see methodology note above).

## Communication cost (BR-1, Fig. 2 equivalent)

Proposed scheme, measured on real serialized M1/M2 wire messages:

- M1 (device -> server): 216 bytes
  (breakdown: {'pid': 32, 'gcm_nonce': 12, 'ciphertext': 56, 'tag': 16})
- M2 (server -> device): 142 bytes
  (breakdown: {'server_id_utf8': 14, 'gcm_nonce': 12, 'ciphertext': 24, 'tag': 16})
- Session total: 358 bytes
- Offline registration: 0 bytes
  -- FR-2.3: TA<->device/server registration performs no network I/O in this implementation -- lambda_X is derived and installed entirely locally/offline, so there is no wire message to size (unlike the paper's Section II registration Msg-I..IV, which this PoC deliberately does not implement -- see PRD 1.2 design decision).

![Communication cost](communication_cost.png)

## Processing cost (BR-2, Fig. 1 equivalent)

Warm (steady-state, pairwise root cached per FR-3.2), 1000 trials:

- Device (build + complete): mean 0.045 ms,
  p95 0.053 ms
- Server (handle_auth_request): mean 0.073 ms,
  p95 0.081 ms

Cold (pairwise root re-derived every session, matching the paper's literal
Eq. 22 per-session KDF cost), 100 trials:

- Device total: mean 0.053 ms
- Server total: mean 0.079 ms

![Processing cost vs device population](processing_cost.png)

Underlying data: `processing_cost_vs_population.csv`

### Paper-reported baseline computation formulas (Table V), evaluated with Table III constants

| Scheme | User/Client (ms) | Device (ms) | Server (ms) |
|---|---|---|---|
| Proposed scheme (paper-reported) | 11.840 | 11.840 | 86.780 |
| Challa et al. [17] | 46.700 | 69.360 | 86.780 |
| Turkanovic et al. [12] | 2.240 | 2.240 | 1.600 |
| Porambage et al. [11] | 70.960 | 191.300 | 138.400 |
| Dhillon and Karla [13] | 2.560 | 1.920 | 2.560 |
| Cheng and Le [14] | 37.080 | 35.800 | 2.240 |
| Shuai et al. [16] | 19.020 | 18.060 | 19.340 |
| Jiang et al. [15] | 2.240 | 1.600 | 3.200 |
| Wazid et al. [17] | 32.460 | 12.480 | 24.000 |
| Sadhukhan et al. [18] | 28.940 | 28.620 | 69.040 |

## Storage cost (BR-3, Fig. 3 equivalent)

- Device persisted state: 424 bytes
  (breakdown: {'credential': 263, 'pairwise_root_cache': 85, 'epoch_counters': 20})
- Server persisted state: 449 bytes
  (breakdown: {'credential': 263, 'pairwise_root_cache': 87, 'last_accepted_epoch': 22, 'block_list': 2})

![Storage cost](storage_cost.png)

## Raw data

Full machine-readable results: `results.json`
