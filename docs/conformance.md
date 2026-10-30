# Conformance of the implementation to the base paper

Scope: the implementation follows **Section III (Eqs. 8–24)** of Al-Rasheed et al., IEEE TCE 72(2), 2026, with the
suggested primitives (AES-GCM, HKDF, SHA-256). It does not follow the narrative Algorithms 1–2 of Section II, which
describe a different protocol. This page maps each equation and rule to code and to the evidence that covers it.
A trace from an equation to a function is traceability; the **Evidence** column is what actually supports correctness.

Evidence kinds: **vectors** = byte-for-byte match with the independent reference vectors
([`hybrid_ecc_auth/tests/vectors/`](../hybrid_ecc_auth/tests/vectors/README.md)), **test** = existing unit, property or
adversarial test, **none** = no automated check.

## Equation-to-code matrix

Python paths are relative to `hybrid_ecc_auth/`; C is `firmware/esp8266/lib/hea_proto/hea_proto.c` (device side only).

| Eq. / rule | Python | C | Evidence |
|---|---|---|---|
| Eq. 8 `lambda_X = H1(ID ‖ s) mod n` | `crypto/hashes.py` `h1_derive_secret`; `protocol/ta.py` `derive_long_term_secret` | not implemented (the TA provisions λ) | vectors (λ for both parties); test `test_ta.py` |
| Eq. 9 `k* = KDF(λ_dev ‖ λ_srv)` | `protocol/entity.py` `derive_pairwise_root`, `Entity.get_pairwise_root` (cached) | `hea_init` | vectors (k\*); test `test_entity.py` (symmetry, caching, invalidation) |
| Eq. 10 coverage `cov_ij(t)` | `Entity.coverage_ok`, pluggable predicate | not implemented | test `test_entity.py`, `test_device_server.py`, `test_sec08` (a predicate, not radio range) |
| Eq. 11 `PID = H2(λ ‖ t)` | `crypto/hashes.py` `h2_pseudonym`; `Device.current_pseudonym` | `sha256_pid` | vectors (PID at epochs 0 and 3) |
| Eq. 12–15 M1 `<PID, C1, mu_1>` | `Device.build_auth_request`; `protocol/messages.py` `Message1` | `hea_build_m1` | vectors (plaintext, ciphertext, tag, exact wire bytes); tamper tests in vectors and `test_sec03` |
| Eq. 16 `K = KDF(k* ‖ N_i ‖ N_j ‖ t)` | `entity.py` `derive_session_key` | in `hea_complete` | vectors (K); test `test_entity.py`, property test |
| Eq. 17–19 M2 `<ID_R, C2, sigma_2>` | `Server.handle_auth_request`; `Device.complete_auth`; `Message2` | `hea_complete` | vectors (exact wire bytes, device accepts, tamper and cross-session rejection) |
| Eq. 20 `Pr[K_dev = K_srv] = 1` | both sides call `derive_session_key` | device side only | property test `test_session_key_agreement.py` (10,000 trials); vectors (both sides produce the vector K) |
| Eq. 21 communication bits | `Message1/2.to_bytes` | `hea_build_m1` | sizes in [`research/omnet_emulation/impl_profile/`](../research/omnet_emulation/impl_profile/README.md) |
| Eq. 22 online cost | whole flow | whole flow | op counts in the same profile (not a correctness check) |
| Eq. 23 `Allow = cov ∧ Auth` | `Entity.access_control_gate` | not implemented | test `test_sec08` |
| Eq. 24 TA-assisted rekey | `protocol/rekey.py` raises `NotImplementedError` (stub) | not implemented | test `test_rekey_stub.py` only checks the stub |
| Block after repeated failures | `storage/session_log.py`; `Server`/`Device` fail-fast checks | not implemented | test `test_session_log.py`, `test_sec05` |
| Replay rejection | `SessionLog.is_stale_epoch`; `Server.resolve_pseudonym` | not implemented (server side) | test `test_sec01`, `test_sec02`; vectors (replayed M1, foreign M2) |

Boundaries: the C port implements the **device** half of the handshake only and cannot act as a server. Coverage (Eqs. 10, 23)
is an abstract predicate in Python, with no radio model. Rekeying (Eq. 24) is a stub. The optional login hash of Section II
(`protocol/login_gate.py`) is outside Section III and off by default.

## Assumption register

Encodings, key-derivation parameters, the AEAD split and the wire format are listed with their provenance in the
[vector specification](../hybrid_ecc_auth/tests/vectors/README.md#specification-and-its-provenance). Further decisions
that the paper does not fix, or that mix sections:

| Decision | Our choice | Basis |
|---|---|---|
| Failure threshold | block after 3 failed attempts (`max_attempts=3`) | the paper states "a maximum of three attempts" in its Section II narrative; applying it to Section III is ours |
| Time frame to answer | 5 s device timeout (`session_timeout`) | the paper says "within the defined time frame" without a value: assumption |
| Epoch semantics | per-peer counter from 0; server accepts `last-16 … last+8` | paper silent; rationale in [`design.md`](design.md) |
| Epoch persistence | RAM only in Python; the firmware persists it to flash | paper silent: assumption |
| Pseudonym resolution | linear scan over known peers × epoch window | the paper does not say how a server resolves an unlinkable PID: assumption |
| Nonce length ℓ | 128 bits (192/256 selectable in Python, 128 in C) | the paper allows ℓ ∈ {128, 192, 256} |
| Public point `P_X = λ_X G` | optional at enrollment, unused online | paper lists it but Eqs. 9–22 never use it |

## Open questions only the authors can settle

1. Is Section III or Section II the protocol they simulated?
2. Does `mu_1` cover the cleartext PID? Eq. 14 MACs the plaintext fields; our GCM call has empty AAD and the server instead checks that the decrypted PID equals the header PID.
3. How is `sigma_2` built (Eq. 17 gives `MAC(PID ‖ N_i ‖ N_j ‖ t)`; ours is a GCM tag with AAD `PID ‖ N_i`)?
4. How do epochs advance and survive restarts, and how does a server resolve a pseudonym?
5. Does enrollment give each side the peer's λ (as implemented) or only the derived pairwise root?

None of these changes a value in the vectors if the answer matches our reading; a different answer would change the vectors, not just the code.
