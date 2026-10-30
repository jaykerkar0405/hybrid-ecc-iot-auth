# Citation-chain investigation of the low-cost hybrid ECC paper

This investigation can proceed without the pending Jiang two-factor paper. The available originals already establish a numerical relationship to Sadhukhan's earlier paper, identify several comparison errors, and show why the advertised **17% communication / 21% processing / 12% storage** reductions remain unverified. They do not establish that those percentages are impossible under every experiment; they establish that the supplied evidence does not specify a reproducible calculation for them.

The strongest new finding is the exact correspondence between BASE's comparison tables and Sadhukhan's tables: **five timing constants, all nine competitor communication rows, and all five finite storage pairs** match. The storage roles do not retain their original meaning. These are observable numerical correspondences. Historical derivation is an inference; neither author intent nor the origin of unpublished simulation results is established here.

Scope: targeted reading of protocols, performance sections, tables, and references in the local PDFs, plus arithmetic and comparisons with repository artifacts. This is not an exhaustive verification of every security argument in every paper, an implementation of all competitors, or a formal proof of the C/Python implementation. The local reference inventory contains 21 PDFs, including our own literature survey, which is not treated as independent primary evidence.

## Evidence and reproduction

- [evidence.json](evidence.json): curated transcriptions, source pages, and qualifications.
- [results.json](results.json): recalculated costs, reductions, correspondence checks, and input hashes.
- [comparison.csv](comparison.csv): original-versus-BASE operation counts for each participant.
- [source_inventory.json](source_inventory.json): SHA-256, page counts, and embedded metadata for the local PDFs. Metadata titles are not authoritative bibliographic records.
- [recompute.py](recompute.py): standard-library recalculation and PDF page-anchor checks.

From the repository root, with Python 3 and Poppler installed:

```sh
python3 research/citation_investigation/recompute.py
python3 research/citation_investigation/recompute.py --check
```

The script checks 16 source pages, all nine communication correspondences, five storage pairs, and five timing constants, and regenerates three deterministic artifacts. Page anchors confirm the cited text occurs at the stated location; they do not automatically prove each manual transcription. All PDF page numbers below are **1-based file pages**, with printed page numbers given where useful. The existing [BASE table transcription](../paper_audit/paper_tables.py) and [digitized plot data](../omnet_emulation/targets/fig_targets.json) are inputs, not newly measured performance results.

## 1. The most useful base paper is Sadhukhan

Sources: [BASE](../../docs/references/base_paper.pdf), PDF pp.3–8; [Sadhukhan](../../docs/references/sadhukhan_2021_ecc_iot_auth.pdf), PDF pp.9–16 and 27–29 (printed pp.1122–1129 and 1140–1142).

### Protocol structure

Sadhukhan Section 3.1.1 and Fig.3 describe a three-message enrollment using an ECC/ECDH-derived symmetric key, an identity, random curve points, a password/biometric-derived hash, and a nested hash. BASE Section II-A, Eqs.(1)–(7), has a closely corresponding enrollment structure:

| Sadhukhan role or value | Corresponding BASE enrollment concept |
|---|---|
| User and gateway | Device/server and trusted authority |
| User identity | Device MAC address |
| User/gateway random points | Device/authority random values or points |
| Password plus biometric hash | Password plus MAC-address hash |
| Three encrypted enrollment messages | Three encrypted enrollment messages |
| Stored hash and random point | Stored hash and random value/point |

This correspondence helps explain the design, but does not prove algebraic equivalence. BASE's point/scalar notation is inconsistent in places, and the roles and factors change.

Sadhukhan's online protocol is a user–node–gateway exchange with four messages and timestamps. BASE's Section II online description uses two participants and stored hash/random values. Its later Section III, Eqs.(8)–(24), introduces a different specification: derived long-term secrets, pairwise KDFs, epoch pseudonyms, fresh nonces, authenticated encryption/MACs, and a session KDF. No equation-by-equation derivation of that entire later specification has been established from the downloaded predecessors.

Our implementation deliberately follows the later nonce-based model, as documented in [docs/design.md](../../docs/design.md). Therefore Sadhukhan's proofs and AVISPA results cannot be transferred to our implementation simply because the enrollment structures resemble each other. A proof must cover our actual transcript, state transitions, assumptions, and cryptographic instantiations.

### Numerical tables

Sadhukhan Table 3, PDF p.27, contains exactly the five constants of BASE Table III:

| Primitive | Time, ms |
|---|---:|
| ECC scalar multiplication | 17.1 |
| Hash | 0.32 |
| Symmetric encryption/decryption | 5.6 |
| Chaotic map | 0.32 |
| Fuzzy extraction | 17.1 |

Sadhukhan identifies its hash as SHA-1 and attributes these timings to its references [50] and [51]. They are reference cost constants, not measurements of our SHA-256/AES-GCM/HKDF implementation. Their hardware and input-size provenance still require the timing-source papers.

Sadhukhan Table 5, PDF p.28, matches every competitor tuple in BASE Table IV: message count, user bits, node/device bits, gateway/server bits, and total bits. Sadhukhan's own 1,600-bit proposed row becomes the Sadhukhan comparator in BASE.

| Comparator | Matching total bits |
|---|---:|
| Porambage | 3360 |
| Turkanović | 2720 |
| Dhillon–Kalra | 2528 |
| Chang–Le, labelled “Cheng–Le” | 2272 |
| Jiang, pending primary verification | 1952 |
| Shuai | 2368 |
| Wazid | 2592 |
| Sadhukhan | 1600 |
| Fakroon | 2304 |

This locates an earlier table with the same numbers; it does not independently validate each row against its original protocol.

Sadhukhan Table 6, PDF p.29, contains the same finite storage pairs as BASE Table VI. Crucially, its columns mean **smart card/device** and **sensor node**. BASE labels the corresponding numbers **server storage** and **device storage**. A user's smart card and a gateway/server are different participants. A cost table cannot preserve its meaning by changing that label alone. The symbolic Das row also reappears, but its undefined `CH*` term cannot be numerically verified here.

### Inconsistencies already present in Sadhukhan

- Sensor storage is stated as `32 + 320 = 356` bits; the sum is **352**. BASE retains 356.
- The communication paragraph reports four message costs of 352, 384, 512, and 384 bits, which sum to **1632**, whereas Table 5 reports **1600**.
- The literal addends printed for those messages sum to **1760** bits. In particular, `160+160+32+160+160` is 672, not 512, and `32+160+160` is 352, not 384.

These are internal arithmetic inconsistencies. **1760 is not asserted to be the correct encoded protocol length**: field sizes, encryption padding, and which fields actually travel still need a fresh transcript-level derivation. Thus even the 1600-bit comparator needs qualification.

## 2. What the original comparison papers now establish

`H` denotes a hash, `ECM` a curve scalar multiplication, and `SE/D` symmetric encryption/decryption. Costs below use BASE's constants solely to compare operation-count models. They are not new hardware timings or evidence of equivalent security.

| Original source and location | Verified finding | Consequence for BASE |
|---|---|---|
| [Turkanović](../../docs/references/turkanovic_2014_iot_wsn_auth.pdf), p.13, Table 2 | User 7H, sensor 5H, gateway 7H | BASE assigns 7H to device and 5H to server. The participant swap already occurs in Sadhukhan. Total hashes remain 19. |
| [Dhillon–Kalra](../../docs/references/lightweight_biometrics_remote_user_authentication_for_iot.pdf), p.11, Table 3 | User 8H, node 6H, gateway 8H | BASE's operation-count row matches. No independent communication/storage total is established from this original here. |
| [Chang–Le](../../docs/references/provably_secure_authentication_for_ad_hoc_wsn.pdf), p.9, Table III, P2 | User 7H+2ECM, sensor 5H+2ECM, gateway 9H | BASE uses 9H for user and 7H for gateway. Total remains 21H+4ECM. Its reference [14] is a different Wang paper. |
| [Challa](../../docs/references/challa_2017_signature_key_establishment.pdf), pp.12–13, Tables 3–4 | Own protocol: user 5ECM+5H, sensor 4ECM+3H, gateway 5ECM+4H; 3 messages, 2528 bits | BASE adds fuzzy extraction and changes the user's 5ECM into 5SE/D. Original operation counts cost **243.24 ms**, versus **202.84 ms** for the BASE row, counting all participants. |
| [Shuai](../../docs/references/shuai_2019_smart_home_auth.pdf), pp.5–7, Section 3.3; p.13, Tables 4–5 | Original total 16H+3ECM; tracing the algorithm places 2ECM at user, 0 at device, 1 at gateway. Original communication total 1728 bits | BASE preserves total ECM but moves one operation onto the constrained device. Its 2368-bit total differs from the original; any renormalization needs an explicit field-by-field derivation. |
| [Fakroon](../../docs/references/fakroon_2020_smart_home_auth.pdf), p.18, Section 5 and Table 3 | Message lengths 800+416+416+672 = **2304 bits** | This total is independently supported. The storage roles and arithmetic are not. |
| [Porambage 2014](../../docs/references/porambage_2014_two_phase_auth.pdf), pp.4–5 | Full mutual-authentication exchange explicitly has six transfers, including Hello messages; implementation reports 8444 ms per node on TelosB | Challa's later comparison counts four transfers, so message-count scope differs. BASE's 3360-bit comparison appears associated with a different Porambage paper; see below. |
| [Das–Goswami](../../docs/references/das_goswami_2015_biometric_auth.pdf), p.16, Table 5 | Three messages, 640+480+160 = **1280 bits** | Sadhukhan reports a different four-message/1984-bit row. No storage table explaining BASE's `768+CH*` was located. |

Shuai's per-role curve counts above are an algorithm recount, not a per-role table printed by Shuai. The hash allocation follows its described login/authentication operations. The CSV makes that distinction explicit.

Fakroon's storage section is particularly informative: **user 704 bits, gateway reported 1056 bits, smart device 384 bits**. The gateway's literal terms are `160 + 3×128 + 512 + 256 = 1312`, not 1056. BASE's 704/1056 server/device pair therefore reproduces user/gateway values and a source arithmetic error, rather than a verified gateway/smart-device comparison. A corrected implementation budget still requires checking the actual stored fields.

### Bibliographic identity matters

BASE's comparison labels do not consistently identify its bibliography:

- “Cheng–Le [14]” points to Wang's emergency-vehicle paper, not the available Chang–Le paper.
- “Jiang [15]” points to Wen's sensing/communication/computation article, not the requested Jiang two-factor paper.
- “Shuai [16]” points to Jiang's chaotic-map paper.
- “Wazid [17]” and “Challa [17]” share a citation, but [17] is Challa. Sadhukhan identifies the Wazid protocol separately as *Design of secure user authenticated key management protocol for generic IoT networks* (2018).

The available Jiang chaotic-map paper is a different protocol from the pending two-factor paper. Having one does not verify the other. Sadhukhan itself attaches a chaotic-map Jiang citation to its hash-only comparison row, so its citation cannot resolve the identity by itself.

For Porambage, Challa's references distinguish the downloaded **2014 two-phase** paper from a **2015 group-key-establishment** paper. Challa Table 4 attributes **1344 bits** to the former and **3360 bits** to protocol 1 of the latter. BASE and Sadhukhan use 3360 while citing the 2014 work. This supports a source-identity problem, but the 2015 primary PDF and a fresh bit-level derivation are needed before replacing that row.

## 3. BASE's figures have a separate relationship to Jan et al.

Source: [Jan 2025](../../docs/references/jan_2025_ml_auth_edge_iov.pdf). Existing repository work digitized BASE Figs.1–3 and Jan Figs.5, 7, 8. This investigation recalculates the correspondences from those stored coordinates; it does not independently digitize the PDFs again.

- For BASE Fig.1 versus Jan Fig.5, the 33 uncensored corresponding bar heights differ by a nearly uniform **+7.231**; the residual RMS after fitting that one offset is **0.0186**. The vehicle labels change from 200–1200 to 300–1800, an exact factor of 1.5.
- For BASE Fig.2 versus Jan Fig.7, competitor heights differ by about **+3.501** and proposed heights by **+4.899**. A two-offset fit has residual RMS **0.0060**. Jan labels the vertical axis end-to-end delay in ms; BASE labels it communication cost in bits. A numerical offset is not a valid conversion between those quantities.
- BASE Fig.3 and Jan Fig.8 have very close storage-percentage bar heights; the six observed differences range from approximately 0.00008 to 0.023 percentage points.

These demonstrate numerical correspondences, not independently reproduced measurements. They do not by themselves establish how either figure was generated. BASE Fig.1 also has a processing-time caption while its vertical axis says communication overhead, so treating the plot as a well-defined measurement is already problematic.

### Checking the originals behind Jan's comparator numbers

| Primary source and location | Result of checking its own scheme |
|---|---|
| [Ma/Zhanfei 2024](../../docs/references/ma_2024_blockchain_iov_auth.pdf), pp.9–10 | Its 8H+6ECM computation expression matches Jan. Its communication table gives **1088 registration + 1792 authentication + 352 reauthentication = 3232 bits**. The **3392** attributed to Ma in Jan belongs to Ma's **Wazid comparator**. For an online-authentication-only comparison, 1792 is a different scope from the 3232 phase sum. |
| [Gupta 2019](../../docs/references/gupta_2019_wearable_auth.pdf), p.12 | Own operations are 16H+11XOR, matching Jan's aggregate. Its own communication entry is **3808 bits in five messages**, whereas Jan reports **3038**. |
| [Gope 2016](../../docs/references/gope_2016_realistic_auth.pdf), p.7 | Own table gives user 7H, gateway 9H, sensor 3H, totaling **19H**. Jan's 12H corresponds to only gateway+sensor hash counts. Its 3184-bit figure appears in **Gupta's** comparison under common SHA3-256 assumptions; Gope's own communication table instead gives a sensor-transmission budget of 35 bytes. These scopes and encodings need reconciliation. |
| [Hasan 2023](../../docs/references/hasan_2023_kerberos_auth.pdf), pp.11–12 | Its **672-bit** result and computation expression support Jan's values. The original labels its message count “Forward message” = 3, while Jan lists 6; reconcile direction/count conventions before calling this an error. Its 11.14 ms timing belongs to its specified desktop/software environment. |
| [Hasan 2018](../../docs/references/hasan_2018_aodv_flooding.pdf), pp.5–6 | It evaluates FLOW-AODV flooding prevention using NS3 routing metrics. No mutual-authentication transcript, 7H+14XOR cryptographic cost derivation, or 32000-bit authentication total was located. It does not presently substantiate that authentication comparator. |

These findings weaken an attempt to reproduce BASE's headline reductions merely by reproducing Jan's comparator table or fitting its plots.

## 4. Can we calculate 17%, 21%, and 12% now?

Use an explicit reduction definition:

```text
reduction (%) = 100 × (comparator_cost − proposed_cost) / comparator_cost
```

| Claimed reduction | What available data actually permit | Status |
|---|---|---|
| Communication ≈17% | BASE Table IV gives 1024 versus smallest competitor 1600: **36%**. Versus the mean of its nine competitors: **57.52%**. | Neither selected calculation yields 17%; the original baseline/aggregation is unspecified. Further, the 1024 and 1600 totals require transcript validation. |
| Processing ≈21% | BASE III×V gives proposed **23.68 ms**, Turkanović **6.08 ms**, Dhillon **7.04 ms** for all roles. Even counting only device+server gives proposed 23.68 versus 3.84 and 4.48 ms. | The printed model does not support a universal “proposed is fastest” statement. It does not establish the advertised 21% reduction. |
| Storage ≈12% | Printed server column: 320 versus 480 → **33.33%**. Printed device column: 320 versus 356 → **10.11%**; correcting 356 to 352 gives **9.09%**. | No unique 12% derivation; role mismatch prevents interpreting these as a fair server/device comparison. |

The communication calculation remains **36% with Jiang excluded**. Its mean-comparator calculation changes to 58.51%. The processing counterexamples from Turkanović and Dhillon also remain available. Thus the pending Jiang PDF is not the reason the headline claims are unverified.

For completeness, simple calculations on the stored plot heights also do not recover the claimed triplet:

| BASE figure | Mean of pointwise reductions versus best competitor | Versus pointwise mean competitor |
|---|---:|---:|
| Fig.1, captioned processing | 32.07% | 43.30% |
| Fig.2, communication | 23.12% | 26.83% |
| Fig.3, storage | 7.01% | 16.79% |

These are descriptive plot calculations, subject to digitization and unit ambiguities. They are not independent experiment results. Trying more baselines until a number rounds to 17, 21, or 12 would not establish the authors' intended experiment.

## 5. What our current implementation and manuscript can support

The old `paper_baseline/` manuscript is now consolidated into [paper/main.tex](../../paper/main.tex) and [paper/main.pdf](../../paper/main.pdf). This investigation does not edit that manuscript or the protocol implementation.

| Evidence available now | Defensible interpretation | Limit |
|---|---|---|
| Common session-key derivation from the same pairwise key, nonces, and epoch | A narrow algebraic key-agreement statement: equal inputs to the deterministic KDF produce equal session keys. Existing property/interoperability tests can check executions. | This is not a security proof, full paper equivalence, or proof of all C/Python paths. |
| Table III×V and our OMNeT++ run | **23.68 ms** is the printed-operation arithmetic; approximately **23.98 ms** is our modeled session latency under stated assumptions. | The simulator includes timing/network effects and uses supplied operation counts. It does not independently measure those counts or reproduce a 21% advantage. |
| Simulated competitor message budgets match Table IV | The simulator accounts consistently for the budgets entered into it. | Those budgets are inputs, not nine independently encoded competitor protocols. |
| [Recorded operation profile](../omnet_emulation/impl_profile/ops_profile.json) | One AEAD encryption and decryption per side; device hashes once; server hash count grows with candidate search. | The whole implementation is not just 2H+2SE/D per side. |
| C/Python interoperability and archived primitive benchmarks | Evidence of compatible behavior on tested cases and measured primitive timings. | Finite tests do not establish universal conformance, equivalent security, or a common-environment performance comparison with all predecessors. |
| Modeled constant-time pseudonym lookup | A useful scalability scenario alongside modeled linear search. | Setting lookup cost to zero in a model is not evidence that an indexed implementation has been built and benchmarked. |

Two manuscript accounting details deserve correction before presenting the results as independent validation:

1. The profile's two KDF calls on a cold handshake are **one pairwise-root derivation plus one session-key derivation per side**, not two session-key derivations. Root caching changes subsequent sessions. Record cold and warm scope explicitly.
2. For the recorded message example, raw fields total **116+57 = 173 bytes = 1384 bits**. JSON/base64 serialization totals **216+133 = 349 bytes = 2792 bits**, before outer transport framing/envelopes. These are different from BASE's 1024-bit table entry. BASE's prose also says two 128-bit messages total 264 bits, which is itself inconsistent with 2×128=256. A wire budget must count the fields and encoding actually used.

The manuscript's firmware handshake figures of 5.26 ms device compute and 52 ms over Wi-Fi should be presented as that experiment's measurements. Raw primitive logs are archived; the cited end-to-end handshake timing log was not located in this investigation. Preserve the underlying run log before relying on those figures as independently auditable evidence.

## 6. Remaining source gaps and a credible mentor-facing rubric

The pending Jiang two-factor original will allow its algorithm, participant costs, and communication/storage scope to be checked. It cannot resolve the other citation, unit, and arithmetic problems by itself. Additional useful primary sources revealed by this investigation are:

- **Wazid et al. (2018)**, *Design of secure user authenticated key management protocol for generic IoT networks*, IEEE Internet of Things Journal 5(1):269–282. This is the Wazid protocol identified by Sadhukhan, distinct from Challa.
- **Porambage et al. (2015)**, *Group key establishment for enabling secure multicast communication in wireless sensor networks deployed for IoT applications*. Challa's reference [37], distinct from the downloaded 2014 two-phase paper.
- **Kilinc and Yanik (2014)**, *A survey of SIP authentication and key agreement schemes*, and **He et al. (2010)**, *An enhanced two-factor user authentication scheme in wireless sensor networks*. Sadhukhan's timing references [50]–[51].
- **Odelu, Das and Goswami (2015)**, *An efficient biometric-based privacy-preserving three-party authentication with key agreement protocol using smart cards*. Challa's timing reference [35].

The downloaded [Xie paper](../../docs/references/xie_2014_roaming_auth.pdf), pp.6–7, uses a different constant set: H=0.5 ms, SE/D=8.7 ms, ECM=63.075 ms, giving its own 6ECM+7H+7SE/D = **442.85 ms**. Its timing references [17]–[19] therefore do not explain BASE's 17.1/0.32/5.6 constants. Following a citation chain is useful only if the constants, primitive definitions, platform, and message sizes remain traceable at every step.

The downloaded [Alshawish paper](../../docs/references/alshawish_2022_mutual_auth.pdf), pp.22–23, reports six messages totaling **470 bytes** and **13.04 ms simulated network latency** at its stated channel rate. Its Section 4.2.3 explicitly says computational overhead is not measured in that NS3 setup. That latency cannot be relabelled as primitive computation time. The [Khan automotive paper](../../docs/references/khan_2024_automotive_iot_auth.pdf) provides related protocol context, but no equation-by-equation origin of BASE's entire later model is established here.

A rubric that can withstand review separates four deliverables:

1. **Specification conformance:** fix one precise protocol version, map each equation/message/state rule to Python and C, state every added encoding or epoch decision, and prove key agreement under explicit assumptions. Mark unimplemented rekeying and abstract coverage separately. Do not claim that passing an unrelated predecessor's proof verifies the modified protocol.
2. **Cost derivation:** independently enumerate each transmitted field, persistent stored field, and primitive invocation by participant and phase. Keep enrollment versus online, cold versus cached, payload versus framed wire bytes, and user versus sensor versus gateway distinct. Resolve source errors in a documented corrected model.
3. **Comparative measurement:** implement a declared comparator set, use the same hardware/software, security parameters, inputs, phase definitions, and network conditions, and report repeat counts and uncertainty. Measure compute, communication, storage, and network latency separately.
4. **Headline reproduction:** identify the authors' comparator and percentage aggregation, obtain sufficient original experiment parameters or code/data, and reproduce it independently. If those are unavailable, report the corrected model's own percentages and label the published 17/21/12 values **unreproduced**.

Suggested statement to the mentor:

> We can substantiate specific algorithmic behavior, implementation interoperability, and explicitly defined cost calculations. Tracing the original references revealed inherited table values, participant-label changes, and arithmetic/source-identity inconsistencies. The published 17%, 21%, and 12% reductions are not yet independently reproducible from the supplied specification. We will report our measured results under declared assumptions and distinguish them from those advertised percentages.

This report qualifies older secondary-table findings in [paper_audit](../paper_audit/FINDINGS.md), [reference_replication](../reference_replication/REPORT.md), and [jan_compare](../omnet_emulation/jan_compare/FINDINGS.md) using the newly available originals. Earlier stronger language about how plots were produced should not be treated as established author intent. No manuscript, implementation, or historical audit file was changed by this investigation.
