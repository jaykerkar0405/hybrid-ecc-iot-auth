# Independent reference vectors

`generate_reference_vectors.py` restates the Section III protocol of the base paper
(Al-Rasheed et al., IEEE TCE 72(2), 2026) from the table below and computes every
expected value without importing anything from `hybrid_ecc_auth`. Both
implementations must reproduce those values byte for byte:

| Implementation | Check | Run |
|---|---|---|
| Python reference | `hybrid_ecc_auth/tests/unit/test_reference_vectors.py` | `pytest hybrid_ecc_auth/tests/unit/test_reference_vectors.py` |
| C device core (ESP8266 port, built for the host) | `firmware/esp8266/host/vector_test.c` | `make -C firmware/esp8266/host check` |

Regenerate with `python generate_reference_vectors.py`; `--check` fails if the committed
files are stale. The generator first checks its own primitives against RFC 5869
(A.1, A.3), NIST/McGrew-Viega GCM test case 16 and FIPS 180 SHA-256, so a wrong helper
fails there.

## What this establishes, and what it does not

- Python and C compute the same values as an independent restatement, so a shared
  mistake in the project's own helpers would be caught.
- Tampered or replayed messages are rejected: any altered M1 field (Python), any
  altered M2 ciphertext, tag or IV (both), a replayed M1 (Python) and an M2 from another
  session (both).
- It does **not** show that this specification matches the authors' intent. Rows marked
  "assumption" below are our choices where the paper is silent or ambiguous; only the
  authors can confirm them. The vectors cover the honest handshake, the listed tamper
  and replay cases, and two epochs. They are not a security proof.

## Specification and its provenance

Status: **paper** = stated by the paper, **suggested** = the paper's instantiation notes,
**assumption** = our choice.

| Item | Rule | Status |
|---|---|---|
| Eq. 8 | `lambda_X = H1(ID_X ‖ s) mod n`, 0 mapped to 1 | paper; SHA-256 suggested; UTF-8 identity, concatenation order, 0→1: assumption |
| Group | NIST P-256 order `n` | assumption |
| Eq. 9 | `k* = KDF(lambda_dev ‖ lambda_srv)`, device first | paper; HKDF-SHA256 suggested; each lambda as 32 bytes big-endian, no salt, info `hybrid-ecc-auth/pairwise-root/v1`, 32-byte output: assumption |
| Eq. 11 | `PID = H2(lambda_dev ‖ t)` | paper; `t` as 8 bytes big-endian: assumption |
| Eq. 12–15 (M1) | `C1 = Enc_k*(PID ‖ N_i ‖ t)`, `mu_1` = AES-256-GCM tag, one call | Enc/MAC split and GCM tag suggested; plaintext layout, 96-bit IV, **empty AAD**, `N_i` 128 bits: assumption |
| Eq. 16 | `K = KDF(k* ‖ N_i ‖ N_j ‖ t)` | paper; info `hybrid-ecc-auth/session-key/v1`, 32 bytes, `t` 8 bytes big-endian: assumption |
| Eq. 17–19 (M2) | `C2 = Enc_k*(N_j ‖ t)`, AAD `PID ‖ N_i`, `sigma_2` = GCM tag | Eq. 17 gives `MAC(PID ‖ N_i ‖ N_j ‖ t)`; carrying `PID ‖ N_i` as AAD to obtain the same coverage is our construction: assumption |
| Responder name | server identity in the clear in M2 | paper allows `ID_R` or `PID_R`: assumption |
| Wire format | JSON, base64 fields, `v=1`, key order `v,type,pid,nonce,ct,tag` / `v,type,sid,nonce,ct,tag`, compact separators | assumption |
| Envelope | `{"ok": true, "payload": "<M2 JSON>"}` as sent by the demo server | assumption |
| Epoch | per-peer counter starting at 0, advanced after each request | paper silent: assumption |

The scheme also has Section II narrative algorithms that describe a different protocol;
this implementation follows Section III (Eqs. 8–23).

## Files

- `reference_vectors.json`: all inputs and expected values (hex, plus the exact wire strings).
- `reference_vectors.txt`: the same data as `key=value` lines, read by the C test.
