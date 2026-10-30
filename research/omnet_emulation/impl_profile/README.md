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
| Session-key KDF (Eq. 16) | not counted in Table V | 1 per side | paper omits what its own equations require |
| Pairwise-root KDF (Eq. 9) | not counted | 1 per side on first contact, then cached (0 on later handshakes) | offline-derivable; a one-time cost per peer |
| Server pseudonym lookup | not counted | about 8 hashes per enrolled device scanned: 153 hashes at 20 devices, 793 at 100 (linear) | paper omits it |
| Message bits | Table IV: 1024 (4 msgs); text: 264 (2 msgs) | 1384 raw field bits (2 msgs); 2792 on the wire with the JSON/base64 envelope | paper contradicts itself; see the size breakdown below |

`ops_profile.json` records the first handshake (`device_ops`, `server_ops`) and a second one with the pairwise roots already cached
(`*_warm`). Earlier versions of this table counted both KDF calls of the first handshake as session-key derivations; only one of them is.

Size breakdown (identities `dev-0` / `srv-A`): M1 = PID 32 + GCM IV 12 + ciphertext 56 (PID 32 + N_i 16 + t 8) + tag 16 = 116 B; M2 = server id 5 + IV 12 +
ciphertext 24 (N_j 16 + t 8) + tag 16 = 57 B. Raw fields total 173 B = 1384 bits. The JSON/base64 messages are 216 B + 133 B = 349 B = 2792 bits, before
any transport framing (the demo adds a 4-byte length prefix and an `{"ok": true, "payload": ...}` envelope on M2). M2 grows with the server identity length. Both
figures exceed the base paper's 1024 bits (Table IV) and 264 bits (text); with a 256-bit SHA-256 pseudonym, M1 alone is above 264 bits.

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

Not yet done: feeding our implementation's own bit count (1384 raw) and warm-handshake op profile into the simulator as a third
configuration; the V2 row above prices the KDF at a measured ratio to a hash, since Table III has no KDF constant.
