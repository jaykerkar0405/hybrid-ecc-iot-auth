# Is our implementation accurate? Op-by-op against the base paper

`profile_ops.py` counts the primitive operations and message bits of one handshake of `hybrid_ecc_auth`
(`ops_profile.json`; server tested with 1, 20 and 100 enrolled devices, target device last in the table).
Run: `.venv/bin/python -I research/omnet_emulation/impl_profile/profile_ops.py` from the repo root.

| Per handshake | Base paper (Table V / IV) | Our implementation (measured) | Match? |
|---|---|---|---|
| Device: symmetric enc/dec (T_SE/D) | 2 | 2 (1 AES-GCM encrypt, 1 decrypt) | yes |
| Server: symmetric enc/dec | 2 | 2 | yes |
| Device: hashes (T_H) | 2 | 1 (pseudonym H2) | differs by 1 |
| Server: hashes (T_H) | 2 | 1 + lookup (see below) | differs |
| Session-key KDF (Eq. 12, 16) | not counted in Table V | 2 KDF calls per side | paper omits what its own equations require |
| Server pseudonym lookup | not counted | about 8 hashes per enrolled device scanned: 153 hashes at 20 devices, 793 at 100 (linear) | paper omits it |
| Message bits | Table IV: 1024 (4 msgs); text: 264 (2 msgs) | 1384 raw field bits (2 msgs); 2792 on the wire with the JSON/base64 envelope | paper contradicts itself |

Reading: the symmetric-crypto cost, which is what dominates Table V x Table III, is identical. The differences are the
three items the paper's own equations require but Table V leaves out (session KDF, pseudonym lookup, one hash), plus the
paper's inconsistent message size. Nothing here says the implementation is wrong; it says Table V is incomplete.

## Why our earlier numbers looked different

The earlier report priced operations with constants measured on an ESP8266 (e.g. P-256 scalar multiplication 276 ms vs the
paper's assumed 17.1 ms; symmetric operations 5-11x faster than assumed). A different set of constants is a different
environment, not an implementation error. With the paper's own Table III constants the same operation counts give the
paper's numbers (23.68 ms for the proposed scheme, from 2 T_H + 2 T_SE/D on each side).

## OMNeT++ runs that correspond to each column (BASE Table II/III constants, uncontended, no adversaries, N = 100)

| Configuration | Per-session latency | Config |
|---|---|---|
| Paper-faithful: Table V as printed, hash-indexed lookup | 23.98 ms (23.68 + 0.30 ms airtime) | `AH_Proposed_V1_T4__BASE` |
| Paper-faithful, text version (2 msgs, 264 bits) | 23.85 ms | `AH_Proposed_V1_text__BASE` |
| As implemented: Table V + session KDF, hash-indexed lookup | 35.18 ms | `AH_Proposed_V2_T4__BASE` |
| As implemented with our linear lookup (N = 1000, 5% adversaries) | see `../baseline/BASELINE.md` | `M_Proposed_V2_T4__BASE` |

Not yet done: feeding our implementation's own bit count (1384 raw) and op profile into the simulator as a third
configuration; the V2 row above prices the KDF at a measured ratio to a hash, since Table III has no KDF constant.
