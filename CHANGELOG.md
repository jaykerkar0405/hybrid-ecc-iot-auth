# Changelog

All notable changes to this project are documented in this file.

## [0.1.0] - 2026-08-25

Initial release: a Python proof-of-concept implementation of the hybrid
ECC + symmetric-key mutual authentication protocol from Al-Rasheed et al.
(IEEE TCE, vol. 72, no. 2, May 2026), following the paper's Section III
nonce-based mathematical model (see README "Design decision").

### Added

- `crypto/`: NIST P-256 curve helpers, SHA-256-based H1/H2/H3, HKDF-SHA256,
  AES-256-GCM AEAD, CSPRNG nonce generation (FR-1).
- `protocol/ta.py`: offline Trusted Authority, Eq. 8 lambda derivation,
  batch enrollment, peer-key list distribution (FR-2, FR-2.4).
- `protocol/entity.py`: pairwise root derivation and caching (Eq. 9,
  FR-3), session key derivation (Eq. 16), coverage/access-control gate
  (Eq. 10, 23, FR-7).
- `protocol/device.py`, `protocol/server.py`: the two-message mutual
  authentication exchange (Eq. 12-19, FR-5), per-peer epoch tracking,
  session timeouts, and block-list integration.
- `protocol/messages.py`: versioned M1/M2 wire format.
- `protocol/login_gate.py`: optional Section II-B login pre-check (FR-6).
- `protocol/rekey.py`: v2 stub for Eq. 24 TA-assisted rekeying (FR-8).
- `storage/session_log.py`: replay-window bookkeeping and the 3-attempts
  block-list with a pub/sub broadcast hook (FR-5.6).
- `storage/keystore.py`: demo-grade, file-permission-protected credential
  storage (explicitly not a production key store).
- `demo/`: `hea-ta`, `hea-server`, `hea-device` CLIs over a length-prefixed
  TCP transport, including a `--replay-last` adversarial demo mode.
- `bench/`: real-measurement cost model for the proposed scheme
  (communication, processing, storage), paper-reference cost tables for
  nine baseline schemes (Tables IV-VI), and a Markdown/HTML/JSON/PNG/CSV
  report generator (`python -m hybrid_ecc_auth.bench.harness`).
- Test suite: unit tests for every module, a >=10,000-trial correctness
  property test for the session-key-agreement invariant (Eq. 20), and the
  eight required adversarial test cases (SEC-01..SEC-08).

### Known limitations (see README for detail)

- Static devices only; mobility/coverage-radius dynamics are out of scope
  (NG3).
- No formal/mechanized protocol verification.
- Epoch/clock-drift tolerance is this implementation's own documented
  choice, not specified by the source paper.
- The nine baseline schemes are represented by their paper-reported
  reference numbers, not independently re-implemented.
