# Hybrid ECC IoT Authentication

[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)

Reference implementation and measurement-based re-evaluation of a hybrid
ECC + symmetric-key **mutual authentication protocol for IoT devices**.

The repository contains five things:

| Component | Location | What it is |
|---|---|---|
| Python reference implementation | [`hybrid_ecc_auth/`](hybrid_ecc_auth/) | Crypto primitives, protocol state machines, demo CLIs, benchmark harness and test suite |
| ESP8266 firmware | [`firmware/esp8266/`](firmware/esp8266/) | C port of the device side, interoperating with the unmodified Python server |
| Reference vectors | [`hybrid_ecc_auth/tests/vectors/`](hybrid_ecc_auth/tests/vectors/) | Independently computed expected values that the Python and C implementations must reproduce byte for byte |
| Paper re-evaluation | [`research/`](research/) | Consistency audit of the source paper, citation trace, OMNeT++ model and cost model re-run with measured timings |
| IEEE manuscript | [`paper/`](paper/) | LaTeX source of the paper written from those findings |

> **Research artifact, not production firmware.** There is no HSM, no formal
> verification and no side-channel hardening. See
> [Scope and limitations](#scope-and-limitations).

**Source paper:** A. Al-Rasheed, R. Khan, A. Ahmad, A. Saeed, F. Alturise and
S. Alkhalaf, "A Low-Cost Hybrid Elliptic Curve Cryptography Authentication
Protocol for Trustworthy Internet of Things Communication," *IEEE Transactions
on Consumer Electronics*, vol. 72, no. 2, pp. 4483-4491, May 2026
(DOI [10.1109/TCE.2026.3662053](https://doi.org/10.1109/TCE.2026.3662053)).
This project is independent and not affiliated with the paper's authors or IEEE.

## What this project establishes

The source paper publishes no code or simulation model, so the findings are grouped by what each one depends on.
Details and raw data are in [`research/paper_audit/FINDINGS.md`](research/paper_audit/FINDINGS.md) and
[`research/citation_investigation/`](research/citation_investigation/).

**Follows from the paper's own tables and text (no implementation involved)**

- The tables disagree with the text: Table IV gives 4 messages and 1024 bits, Section V-B gives 2 messages and
  264 bits (and 2 x 128 is 256). The abstract's savings of about 17% / 21% / 12% cannot be derived from
  Tables IV-VI under any definition we tried (best, mean, median, worst, each scheme).
- Table V omits the session-key KDF that the paper's own Eq. 22 requires. With it counted, the hash-only rows of the
  table (Turkanovic, Dhillon-Kalra and an unidentified row labelled "Jiang") are cheaper than the proposed scheme
  (about 4-14x on the ESP8266). Jiang et al. as published is not hash-only, so this holds firmly only for the first two.
- The Table III constants, the nine competitor rows of Table IV and the finite storage entries also appear in an earlier
  paper the source cites (Sadhukhan et al., 2021), with the storage columns relabelled. We note the correspondence and
  draw no conclusion about how the values were obtained.

**Verified here**

- The Python implementation and the C device core reproduce independent reference vectors byte for byte, and reject
  tampered and replayed messages ([`docs/conformance.md`](docs/conformance.md)). This shows agreement with our reading of
  Section III, not that the reading is the authors'.
- Measured on an ESP8266, P-256 scalar multiplication is about 16x slower than the paper assumes (276 ms vs. 17.1 ms),
  while symmetric operations are 5-11x faster. The timings were identical on two boards.
- With measured constants the protocol is roughly 60-2,500x cheaper than the ECC-based schemes in the same table.
- The protocol has no forward secrecy (the paper does not claim it), no elliptic-curve operation on the online path, and
  a server lookup that scales linearly with the number of devices to resolve.

**Not verifiable without the authors**

- The paper's Figs. 1-3 and the OMNeT++ simulation behind them. We built our own model of the stated environment; it is a
  sensitivity analysis, not a reproduction. We emailed the corresponding author on 27 October 2026
  ([`docs/author-contact.md`](docs/author-contact.md)); anything that depends on their simulation stays unverified until
  they reply.

## Quick start

Requires Python 3.11+.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,bench]"
```

Run the three-party demo (offline TA provisioning, server, device) in three terminals:

```bash
# 1. Provision credentials offline
cat > manifest.json <<'JSON'
[
  {"identity": "device-001", "role": "device"},
  {"identity": "server-A", "role": "server"}
]
JSON
hea-ta enroll --manifest manifest.json --out-dir creds/

# 2. Start the server
hea-server start --credential creds/server-A.json --port 8443

# 3. Authenticate a device
hea-device authenticate --credential creds/device-001.json \
    --server-id server-A --server-addr 127.0.0.1:8443
```

Expected: `Mutual authentication succeeded with 'server-A'.` plus a session-key
fingerprint (never the raw key). Add `--replay-last` to the device command to
replay the previous request and watch the server reject it.

### Tests

```bash
pytest hybrid_ecc_auth/tests/ -q
pytest hybrid_ecc_auth/tests/ --cov=hybrid_ecc_auth.protocol --cov=hybrid_ecc_auth.crypto --cov-report=term-missing
```

The suite has unit tests per module, a 10,000-trial property test of
session-key agreement (Eq. 20), the eight adversarial cases SEC-01..SEC-08
(replay, tamper, forgery, block-list, unlinkability, key freshness, coverage gate), and
conformance tests against the [independent reference vectors](hybrid_ecc_auth/tests/vectors/README.md).

### Benchmarks

```bash
python -m hybrid_ecc_auth.bench.harness          # quick run
python -m hybrid_ecc_auth.bench.harness --full   # paper-scale sweep
```

Writes `bench_output/` (Markdown, HTML, JSON, PNG and CSV). The report separates
costs **measured on this host** from the **paper's reference values** for the nine baseline schemes.

### Docker

```bash
docker compose up        # runs the benchmark; see docker-compose.yml and docker-entrypoint.sh
```

### ESP8266 firmware

```bash
make -C firmware/esp8266/host                              # build the C core natively
python firmware/esp8266/tools/interop.py -n 20             # check it against the Python server
make -C firmware/esp8266/host check                        # check it against the reference vectors
```

Flashing instructions are in [`firmware/esp8266/README.md`](firmware/esp8266/README.md).

### Reproducing the paper audit

The commands are in section 7 of [`research/paper_audit/FINDINGS.md`](research/paper_audit/FINDINGS.md).

## Repository layout

```
hybrid_ecc_auth/            Python package
  crypto/                   P-256, hashes, HKDF, AES-256-GCM, nonces
  protocol/                 TA, device, server, messages, login gate, errors
  storage/                  Replay window and block-list, demo keystore
  demo/                     hea-ta, hea-server, hea-device CLIs
  bench/                    Cost model, baseline tables, report generator
  tests/                    unit/, property/, adversarial/, vectors/ (reference vectors)
firmware/esp8266/           C protocol core, Arduino firmware, host tests, tools
research/                   paper_audit/ (audit, measured results), citation_investigation/,
                            reference_replication/, omnet_emulation/ (OMNeT++ model)
paper/                      IEEE manuscript (LaTeX)
docs/
  design.md                 Design decisions, architecture, symbol-to-code traceability
  conformance.md            Equation-to-code matrix, assumption register
  author-contact.md         Record of the email to the source paper's authors
  references/               Source paper and literature survey
  project/                  Product requirements and review presentation
  experiments/              AWS demo run (logs, results, report)
.github/                    CI workflow, issue and PR templates
```

See [`docs/README.md`](docs/README.md) for a document index and
[`docs/design.md`](docs/design.md) for the protocol design.

## Scope and limitations

- Not production firmware or a security product: no HSM, no formal verification
  (Tamarin/ProVerif), no penetration test.
- Static devices only; mobility and hand-off are out of scope.
- `storage/keystore.py` is demo-grade (file permissions only). Do not store real secrets in it.
- Timing, power and fault-injection side channels are out of scope.
- The nine baseline schemes are represented by the paper's reported numbers, not re-implemented.
- Conformance means agreement with our reading of Section III. Where the paper is silent (encodings, epochs, pseudonym
  resolution) the choices are recorded in [`docs/conformance.md`](docs/conformance.md) and need the authors' confirmation.

The implementation follows the paper's **Section III nonce-based model**, not the
replayable Section II algorithms. See [`docs/design.md`](docs/design.md).

## Authors

Department of Information Technology,
[Vivekanand Education Society's Institute of Technology (VESIT)](https://vesit.ves.ac.in/), Mumbai, India.

Jay Kerkar, Chaitanya Kelkar, Chirag Poornamath, Yash Kolekar.
Project guide: Dr. Shanta Sondur.

## Citation

See [`CITATION.cff`](CITATION.cff). Please also cite the source paper above.

## License

Apache License 2.0. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
