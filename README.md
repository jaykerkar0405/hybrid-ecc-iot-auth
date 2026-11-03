# Pseudonym resolution in two-message IoT authentication

[![Licence: Apache-2.0](https://img.shields.io/badge/licence-Apache--2.0-blue)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)

Implementation, models and data for _Pseudonym Resolution and Formal Verification of an Unlinkable Two-Message IoT Authentication Protocol_ ([paper PDF](paper/main.pdf)). The server must identify an incoming pseudonym before it can perform a cryptographic check. The protocol specification leaves that resolution step and its cost open. This work compares seven resolution strategies, measures their probe counts, prices them in an OMNeT++ network model, demonstrates counter desynchronisation, and checks secrecy, agreement and unlinkability symbolically.

## Paper

**Pseudonym Resolution and Formal Verification of an Unlinkable Two-Message IoT Authentication Protocol**. Jay Kerkar, Chaitanya Kelkar, Chirag Poornamath, Yash Kolekar and Dr. Shanta Sondur (project guide / mentor), 2026. Department of Information Technology, Vivekanand Education Society's Institute of Technology (VESIT), Mumbai. Unpublished manuscript; [source](paper/main.tex).

The specification is Amal Al-Rasheed, Rahim Khan, Aftab Ahmad, Aamir Saeed, Fahad Alturise and Salem Alkhalaf, “A Low-Cost Hybrid Elliptic Curve Cryptography Authentication Protocol for Trustworthy Internet of Things Communication,” _IEEE Transactions on Consumer Electronics_, 72(2), 4483–4491, May 2026, [doi:10.1109/TCE.2026.3662053](https://doi.org/10.1109/TCE.2026.3662053). This work is independent of and not affiliated with the base paper's authors or IEEE. It takes the two-message protocol as its specification and does not re-evaluate the other results of that paper.

## Key results

| Contribution                    | Result reported in the paper                                                                                                         |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Independent conformance vectors | Python and C: 15 checks each                                                                                                         |
| Resolution strategies           | O1–O4, TM, CR and MW; measured probes checked against closed forms                                                                   |
| Network evaluation              | 960 OMNeT++ runs; base column at N=1: 23.68 ms for every strategy                                                                    |
| Table strategy at N=1000        | O2: 24.4 ms with 5% adversaries                                                                                                      |
| On-demand counter scan          | About 44 s at N=1000 with 5% adversaries                                                                                             |
| Counter desynchronisation       | Permanent lockout after eight dropped M1 messages                                                                                    |
| ProVerif 2.05                   | Q1–Q3 and Q5 true; Q4 false without replay state; forward secrecy false; U1 counter unlinkability true; U2 clock unlinkability fails |

The base column uses the specification's arithmetic value. The model without resolution gives 23.86 ms at N=1 and 24.07 ms at N=1000 because it includes airtime and quantisation.

## What is in this repository

| Paper contribution                                 | Directory                                                         |
| -------------------------------------------------- | ----------------------------------------------------------------- |
| Python exchange, resolvers and independent vectors | [implementation/python](implementation/python/hybrid_ecc_auth/)   |
| C device port, host checks and interop tool        | [implementation/c](implementation/c/)                             |
| Probe counts, cost model, lockout and ResolveNet   | [evaluation/resolution](evaluation/resolution/)                   |
| Symbolic models and committed logs                 | [evaluation/formal_verification](evaluation/formal_verification/) |
| Manuscript, figure generator, figures and PDF      | [paper](paper/)                                                   |

## Quick start

Python 3.11 or newer and a C compiler are required. From the repository root:

```sh
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev,figures]"
hea-ta --help
hea-server --help
hea-device --help
```

The help commands print usage for `hea-ta`, `hea-server` and `hea-device`. The `figures` extra supplies matplotlib, including its STIX fonts. The lock file records the development dependency versions.

Terminal 1, provision demo credentials:

```sh
python -c 'import json; from pathlib import Path; Path("manifest.json").write_text(json.dumps([{"identity":"server-A","role":"server"},{"identity":"device-A","role":"device"}]))'
hea-ta enroll --manifest manifest.json --out-dir creds
```

Terminal 2, activate the same environment and start the server:

```sh
hea-server start --credential creds/server-A.json --host 127.0.0.1 --port 8443
```

Terminal 3, activate the same environment, authenticate once and replay that message:

```sh
hea-device authenticate --credential creds/device-A.json --server-id server-A --server-addr 127.0.0.1:8443
hea-device authenticate --credential creds/device-A.json --server-id server-A --server-addr 127.0.0.1:8443 --replay-last
```

A successful session prints `Mutual authentication succeeded with 'server-A'.`, a session-key fingerprint and a measured round-trip latency. Replaying exits with status 1 and prints a server rejection followed by `[replay-demo] rejection confirms the server's freshness check is working as intended.` Fingerprints and latency vary on each run. Use fresh credentials for a new demo; the device CLI counter lives in RAM.

```sh
pytest implementation/python/hybrid_ecc_auth/tests -q
make -C implementation/c/host check
```

Observed demo output (fingerprint and times are examples from one run):

```text
Mutual authentication succeeded with 'server-A'.
  session key fingerprint: c58040aa780504ee (SHA-256[:16] of K_ij,t -- never the raw key)
  round-trip latency: 5.161 ms
REJECTED by server: ReplayDetected: pseudonym for 'device-A' reuses stale epoch 0 (round-trip 3.139 ms)
[replay-demo] rejection confirms the server's freshness check is working as intended.
```

Expected test results: `125 passed` and `15 checks, 0 failed`.

## Reproducing the paper

Run from the repository root with the environment above active. The full probe sweep takes about three minutes; the OMNeT++ sweep about ten seconds in the original environment. Every ProVerif model finishes in under one second there. Actual times depend on the machine.

1. Unit, property, adversarial and Python vector tests, then the C vectors and interoperability:

   ```sh
   pytest implementation/python/hybrid_ecc_auth/tests -q --cov=hybrid_ecc_auth.protocol --cov=hybrid_ecc_auth.crypto --cov-report=term-missing --cov-fail-under=90
   make -C implementation/c/host check
   make -C implementation/c/host
   python implementation/c/tools/interop.py -n 5
   ```

2. Probe counts and the cost model; this rewrites the CSV and summary files. Peer secrets use OS randomness, so TM measurements vary; preserve the committed data when reproducing the published figures:

   ```sh
   python -I evaluation/resolution/resolution_costs.py
   python -I evaluation/resolution/desync_check.py
   ```

3. Install OMNeT++ **6.4.0** at `~/opp/omnetpp-6.4.0`, then run the 960-run sweep:

   ```sh
   bash evaluation/resolution/sim/build_and_run.sh
   ```

4. Install ProVerif **2.05** on PATH (or pass its executable as the first argument):

   ```sh
   bash evaluation/formal_verification/run.sh
   ```

5. Generate the figures and ranked table, then build the paper with Tectonic (validated with 0.17.0):

   ```sh
   python -I paper/make_figs.py
   (cd paper && tectonic main.tex)
   ```

Committed results allow inspection without installing the simulator or verifier. See the [resolution notes](evaluation/resolution/README.md), [formal results](evaluation/formal_verification/README.md), [design](docs/design.md) and [conformance matrix](docs/conformance.md).

## Repository layout

```text
implementation/
  python/hybrid_ecc_auth/   crypto, protocol, storage, demo, tests and vectors
  c/                       device core, Arduino sketch, host checks and tools
evaluation/
  resolution/              probe counts, cost model, desynchronisation, sim/
  formal_verification/     ProVerif models, runner and logs
paper/                     main.tex, authors.tex, body.tex, main.pdf, figures
docs/                      design, conformance and reference access catalogue
```

## Scope and limitations

This is a research artefact, not production firmware. The file-based demo keystore is not a secure element. Conformance means agreement with our reading of the specification; only its authors can confirm that reading. Epoch semantics, windows, table choices, the adversary rate, authentication window and enrolment rule are our assumptions.

The network model is ours, not the base paper authors' simulation. Saturated latencies depend on those assumptions. Probes use the base paper's Table III constant, with no hardware timings reported. CR and MW change M1 and are modelled at the resolution level only. The TM parameters are one point of its trade-off curve.

Verification is symbolic only and assumes perfect primitives. Q4 needs replay state; the implementation's replay window is tested, with a stateful proof left to future work. Clock epochs permit linking sessions in the same epoch. Counter epochs can permanently desynchronise. Rekeying remains a stub and coverage is an abstract predicate.

## Third-party material

Closed third-party papers, including the base paper, are not redistributed. The [reference access catalogue](docs/references/README.md) provides citations, publisher links and document-level access evidence. Four openly licensed references are tracked under their own licences.

## Citation

```bibtex
@unpublished{kerkar2026pseudonym,
  title = {Pseudonym Resolution and Formal Verification of an Unlinkable Two-Message IoT Authentication Protocol},
  author = {Kerkar, Jay and Kelkar, Chaitanya and Poornamath, Chirag and Kolekar, Yash and Sondur, Shanta},
  year = {2026},
  note = {Department of Information Technology, Vivekanand Education Society's Institute of Technology, Mumbai},
  url = {https://github.com/jaykerkar0405/hybrid-ecc-iot-auth}
}
```

Software metadata and the preferred manuscript citation are in [CITATION.cff](CITATION.cff). Cite the base paper too.

## Authors and licence

Jay Kerkar, Chaitanya Kelkar, Chirag Poornamath, Yash Kolekar and Dr. Shanta Sondur (project guide / mentor), in paper order. All are affiliated with the Department of Information Technology, Vivekanand Education Society's Institute of Technology (VESIT), Mumbai.

Copyright 2026 Jay Kerkar, Chaitanya Kelkar, Chirag Poornamath, Yash Kolekar and Shanta Sondur. Software is licensed under [Apache-2.0](LICENSE); see [NOTICE](NOTICE). VESIT is the affiliation and is not claimed as a copyright owner.
