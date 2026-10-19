# Protocol design notes

Design decisions, architecture and paper-to-code traceability for the Python reference implementation (`hybrid_ecc_auth/`). Source paper: Al-Rasheed et al., *IEEE Transactions on Consumer Electronics*, vol. 72, no. 2, May 2026 (`docs/references/base_paper.pdf`).

## Design decision: Section III, not Section II

The source paper describes the online mutual-authentication phase twice:
a narrative algorithmic version in Section II (Algorithms 1-2), which
reuses a static hash digest `H_D`/`R_D` pair across authentication
attempts with **no per-session nonce** -- making it replayable by an
eavesdropper who records one valid exchange -- and a more rigorous
mathematical model in Section III, which adds fresh per-session nonces
`N_i, N_j`, an epoch-rotated pseudonym `PID_{Vi,t}`, an explicit KDF, and
a security sketch (mutual authentication, key secrecy, unlinkability)
under a Dolev-Yao-style adversary.

This implementation follows **Section III's nonce-based model**
exclusively for the online authentication path, since it is the version
the paper's own security proof sketch actually covers. Field naming stays
close to the paper's notation (`PID`, `C1`, `mu1`, `C2`, `sigma2`,
`lambda_X`, `k*_ij`) so code stays traceable back to the source equations
(Eq. 8-23) -- see [Symbol-to-code traceability](#symbol-to-code-traceability).

The Section II-B login check (MAC + `H_D = h(MAC_D || PWD)`) is still
implemented, but as an *optional*, disabled-by-default pre-check
(`protocol/login_gate.py`) that can run before the Section III exchange,
not as the security boundary itself.

## Architecture

```
hybrid_ecc_auth/
  crypto/                 # FR-1: primitives only, no protocol logic
    curve.py              # NIST P-256 scalar mult (offline-phase only)
    hashes.py             # H1 (Eq 8), H2 (Eq 11), H3 (Eq 24)
    kdf.py                # HKDF-SHA256 (Eq 9, 16, 24)
    aead.py                # AES-256-GCM (Enc/Dec + MAC, per Eq 13/14/17/18)
    nonce.py              # CSPRNG nonces N_i/N_j
  protocol/                # FR-2..FR-8: transport-agnostic state machines
    ta.py                 # Offline TA: enroll, batch enroll, peer-key sharing
    entity.py              # Shared base: pairwise-root cache, session-key
                           # derivation, coverage/access-control gate
    device.py              # Builds M1, verifies M2, per-peer epoch tracking
    server.py               # Resolves pseudonym, verifies M1, builds M2
    messages.py             # Versioned M1/M2 wire format (JSON+base64)
    login_gate.py            # Optional Section II-B pre-check (FR-6)
    errors.py                # Typed exceptions (IntegrityError, ReplayDetected, ...)
    rekey.py                 # v2 stub (Eq 24)
  storage/
    session_log.py           # Replay window + 3-attempts block-list (FR-5.6)
    keystore.py               # Demo-grade file-based credential storage
  demo/                       # Runnable CLIs (Section 4.2)
    _transport.py              # Length-prefixed TCP framing + envelope
    ta_cli.py                  # hea-ta
    server_node.py              # hea-server
    device_node.py               # hea-device (incl. --replay-last)
  bench/                        # Section 6: cost measurement + reporting
    proposed.py                  # Real-code cost model (communication/processing/storage)
    baselines/                    # Paper-reference cost tables (Tables IV-VI)
    harness.py                     # CLI entry point, population-scaling sweep
    report.py                       # Markdown/HTML/JSON/PNG/CSV report generator
  tests/
    unit/  property/  adversarial/
```

### A note on where Eq. 16 lives

The PRD's traceability sketch (Appendix A) originally proposed `K_{ij,t}`
living in `server.py`. In the implementation it lives in `entity.py`
instead (`derive_session_key`), because both `device.py`'s
`complete_auth` and `server.py`'s `handle_auth_request` need to run the
*identical* Eq. 16 computation -- putting it in `entity.py` avoids
duplicating that logic (or having `device.py` import from `server.py`,
which would invert the natural dependency direction). See
[Symbol-to-code traceability](#symbol-to-code-traceability) for the
as-built mapping.

### A note on epoch semantics (implementation decision, flagged for review)

The paper does not specify how the epoch/time value `t` inside
`PID_{Vi,t} = H2(lambda_Vi || t)` evolves, nor how a server should handle
clock drift when resolving an incoming pseudonym. This implementation
tracks epoch **per peer relationship** (`Device._epoch: dict[peer_id,
int]`), not as one global counter, so that `Server.resolve_pseudonym`'s
bounded search window (`storage/session_log.py`) -- which starts at "never
seen" for each peer independently -- stays valid even when a device talks
to multiple servers. Trade-off: two different servers' *first* contact
with the same device both observe `PID = H2(lambda_Vi, 0)`; only
cross-session linkability *within* one peer relationship is defended
against, which matches the scope of the paper's own unlinkability sketch
(Section III-D). See the docstring in `protocol/device.py` for detail.

## Non-production disclaimers

- **Not an embedded/firmware implementation.** No MCU, RTOS, or radio
  stack (XBee, LoRa, Zigbee) work is in scope.
- **Not a production security product.** No HSM integration, no formal
  verification (Tamarin/ProVerif) of the protocol, no penetration-test
  engagement. The adversarial test suite (`tests/adversarial/`) is a set
  of targeted unit tests, not a proof.
- **Static devices only.** Mobility, hand-off, and coverage-radius
  dynamics (the paper's Table II "Hand-off Time" / "device Speed") are out
  of scope; `protocol/entity.py`'s coverage predicate defaults to
  "always in range" and is a pluggable stub.
- **`storage/keystore.py` is demo-grade.** File-based, protected only by
  OS-level file permissions (0600). Not equivalent to a hardware security
  module or secure element. Must not be used to store real secrets.
- **Timing/power/fault-injection side-channels are out of scope.**
  `Server.resolve_pseudonym` uses a constant-time compare per candidate
  (`hmac.compare_digest`) to avoid a trivial per-comparison timing leak,
  but the search loop itself is not constant-time across peers.
- **The nine baseline schemes are not re-implemented.** `bench/baselines/`
  reproduces their paper-reported reference numbers (Tables IV-VI),
  clearly labeled as such; full independent re-implementation is a v2
  backlog item.

## Symbol-to-code traceability

| Paper symbol | Eq. | Code reference |
|---|---|---|
| `lambda_X` | 8 | `protocol/ta.py :: derive_long_term_secret` |
| `k*_ij` | 9 | `protocol/entity.py :: derive_pairwise_root` (cached via `Entity.get_pairwise_root`, FR-3.2) |
| `cov_ij(t)` | 10 | `protocol/entity.py :: Entity.coverage_predicate` / `Entity.coverage_ok` |
| `PID_{Vi,t}` | 11 | `protocol/device.py :: Device.current_pseudonym` (uses `crypto/hashes.py :: h2_pseudonym`) |
| `N_i, C1, mu_1, M1` | 12-15 | `protocol/device.py :: Device.build_auth_request` |
| `K_{ij,t}` | 16 | `protocol/entity.py :: derive_session_key` (called from both `device.py` and `server.py`) |
| `sigma_2, C2, M2` | 17-19 | `protocol/server.py :: Server.handle_auth_request` |
| Correctness (Eq. 20) | 20 | `tests/property/test_session_key_agreement.py` |
| `Allow_ij(t)` | 23 | `protocol/entity.py :: Entity.access_control_gate` |
| Rekey (v2 stub) | 24 | `protocol/rekey.py` (raises `NotImplementedError` in v1) |
