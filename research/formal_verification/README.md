# Formal verification of the Section III exchange (ProVerif)

These are our models of the Section III exchange of Al-Rasheed et al. (IEEE TCE 72(2), 2026), not the authors'. They use
ProVerif 2.05 in the symbolic (Dolev-Yao) model: primitives are perfect, and the attacker controls the network.

Run with `./run.sh [path-to-proverif]`. The full outputs are in `logs/`, and every model finishes in under one second.

ProVerif 2.05 was built from the INRIA source (`proverif2.05.tar.gz`, SHA-256
`4871f53c32ab4a04669a060c4886ba5d9080496963fb980a9a62d2c429ceabc4`) with Homebrew OCaml 5.5.2, using `./build -nointeract`.

## What is modelled

| File | Scenario |
|---|---|
| `common.pvl` | Primitives: `kdf_root` (Eq. 9), `h2` (Eq. 11), `aead` with associated data (Eqs. 13-15, 17-18), `kdf_sess` (Eq. 16) |
| `auth.pv` | Unbounded servers, unbounded honest and corrupt devices per server, unbounded sessions. A corrupt device's `lambda` and `k*` go to the attacker. The server may resolve a pseudonym to **any** enrolled device (`get`) and must then decrypt and check `PID = H2(lambda || t)`, so the results hold for every resolution method that returns a correct device. |
| `fs.pv` | One device and one server; `k*` leaks after the sessions (phase 1) |
| `unlink_counter.pv` | Biprocess: device A twice, against device A then device B. Each session has its own epoch (counter epochs). The server knows both devices on both sides and resolves with one destructor. |
| `unlink_clock.pv` | The same, with both sessions in one epoch (clock epochs longer than the gap between sessions) |

Epochs are fresh names: a counter that never repeats a value. No model has the server's replay window, because ProVerif has no
mutable state; that is why Q4 fails.

## Results

| # | Property | Result | Reading |
|---|---|---|---|
| Q1 | Session key secret (device side), honest pair | **true** | |
| Q2 | Session key secret (server side), honest device | **true** | |
| Q3 | Server accepts M1 of an honest device ⇒ that device sent it (non-injective agreement on V, R, N_i, t) | **true** | |
| Q4 | Same, injective | **false** | Trace: the attacker replays one M1 and the server accepts it twice. Injective agreement needs replay state (the epoch window or a nonce cache), which the specification leaves open and the model omits. |
| Q5 | Device accepts M2 ⇒ server derived the same key with the same nonces (injective) | **true** | N_i is fresh and bound as associated data of M2. |
| FS | Session key secret after a later leak of `k*` | **false** | No forward secrecy. The base paper does not claim it. |
| U1 | Unlinkability, counter epochs | **true** (observational equivalence) | |
| U2 | Unlinkability, clock epochs, two sessions in one epoch | **cannot be proved**; the derivation shows a real distinguisher | The attacker tests `h2(lamA, t) = h2(lamA, t)` on the left against `h2(lamA, t) ≠ h2(lamB, t)` on the right, so equal pseudonyms link the sessions. |

## Limits

- Symbolic model only: no computational bounds, no timing.
- Q4 cannot be decided in ProVerif without state. The replay window is checked by test (SEC-01) instead.
- The resolution destructor in the unlinkability models assumes that the server finds the right device. Its cost is not modelled.
  The cost is the subject of `research/pseudonym_resolution/`.
