# Provenance of base-paper Figs. 1-3 (Al-Rasheed et al., IEEE TCE 72(2):4483-4491, 2026)

Researched 2026-10-29. Sources: OpenAlex API (reference lists, abstracts), publisher HTML/PDF of open-access
CMC papers, IEEE Xplore figure-caption metadata. Downloaded copies (untrusted, not in repo):
`/private/tmp/claude-501/-Users-anonjr-Documents-Stuff-hybrid-ecc-iot-auth/284f8737-bd60-456c-8b0a-67b67b7cace4/scratchpad/provenance/`
(`cmc_64102/`, `cmc_60372/`, `cmc_49017/`: paper.pdf plus fig-N.png and table-N.png).

Note on authors: OpenAlex lists the base paper as Amal Al-Rasheed, Rahim Khan, **Aftab Ahmed**, **Aamir Saeed**,
Fahad Alturise, Salem Alkhalaf (Qassim Univ. / PNU / Abdul Wali Khan Univ. Mardan).

## TL;DR

| Base fig | Origin found | Confidence |
|---|---|---|
| Fig. 1 "Communication Overhead (%)" vs "Vehicles in VANET" | **Same data as Fig. 6 of Al-Rasheed, Khan, Alturise, Alkhalaf, CMC 84(1), 2025, DOI 10.32604/cmc.2025.064102** ("Approximate Communication Overhead (Resources)" vs "Devices in the IoT" 5..30). Proposed series unchanged. Each competitor series is shifted up by a constant (+13.1 to +19.3). Legends were relabelled: "Ma et al (2024)" became "Zhanfei 2024", and "Kazmi et al (2023)" became "Hassan 2023". | **High** (per-series slope 0.996-1.002, max residual ≤0.07 units ≈ 1 px) |
| Fig. 3 "Storage Overhead (%)" | Partial match to Fig. 6 of HybridEdge (Khan A., Khan R., Alturise, Alkhalifah, CMC 82(2), 2025, DOI 10.32604/cmc.2025.060372). Gupta has the same value (0.615). HybridEdge's "Proposed" (0.570) equals base "Zhanfei" (0.57). The other bars moved by 0.006-0.023. Plot style and legend order are the same. | **Moderate** |
| Fig. 2 "Communication Cost (bits)" | **Not found.** No first-difference match with CMC-2025 Fig. 5 or HybridEdge Figs. 3/4. | open |
| Likely common parent of all three (VANET axis, same 5 schemes) | M. A. Jan, S. Abbas, H. Song, **R. Khan**, "An ML-Based Authentication for Privacy Preservation in a Distributed Edge-Enabled Internet of Vehicles," IEEE IoT J. 12(5):4715-4725, 2025 (online 18 Oct 2024), DOI **10.1109/JIOT.2024.3483275**, Xplore 10722874. Closed access. | **Moderate (unverified, needs the PDF)** |

## 1. Figure-origin evidence

### 1a. Base Fig. 1 vs CMC-2025 "Optimal Route Finding" Fig. 6 (strong match)

- Paper: A. Al-Rasheed, R. Khan, F. Alturise, S. Alkhalaf, "Distributed Computing-Based Optimal Route Finding
  Algorithm for Trusted Devices in the Internet of Things," *CMC* 84(1):957-?, 2025, DOI 10.32604/cmc.2025.064102.
  Open access: https://www.techscience.com/cmc/v84n1/61755
- Fig. 6 caption: "Average communication cost overhead ratio of devices in the proposed secured communication
  infrastructure for IoT [19,20,25-27]". Y axis: "Approximate Communication Overhead (Resources)", ticks 30-90.
  X axis: "Devices in the Internet of Things" 5,10,...,30. Legend: Proposed Scheme, Ma et al (2024), Kazmi et al (2023),
  Gupta et al (2019), Gope et al (2016), Hassan et al (2018).
- Same colour per series, same in-group order: black, red, blue, magenta, green, navy. Base Fig. 1 uses the identical
  colour map (`fig_targets.json` → `colour_to_series`). Red = Ma becomes "Zhanfei 2024" (Zhanfei is Ma's given name),
  and blue = Kazmi becomes "Hassan 2023" (Kazmi's co-author is Rosilah Hassan).
- I read the CMC Fig. 6 bar tops from the published PNG. Pixel calibration uses the 30/45/60/75/90 ticks
  (217.5 px per 15 units, so 1 px ≈ 0.069). Then I fit `base = a + b·route` per series, using only the points that
  are not clipped at 100:

| Series (base label ← CMC label) | CMC Fig. 6 values | base Fig. 1 values | slope b | offset a | max resid |
|---|---|---|---|---|---|
| Proposed | 43.1 45.1 47.6 50.9 52.9 63.9 | 42.7 44.8 47.2 50.5 52.5 63.5 | 0.999 | −0.38 (bar-outline bias) | 0.05 |
| Zhanfei 2024 ← Ma 2024 | 59.6 63.9 68.7 73.2 77.8 79.4 | 72.7 76.9 81.8 86.2 90.8 92.5 | 0.999 | +13.1 | 0.04 |
| Hassan 2023 ← Kazmi 2023 | 50.1 54.9 55.8 59.7 63.1 69.3 | 64.9 69.7 70.5 74.5 77.9 84.1 | 0.997 | +15.0 | 0.04 |
| Gupta 2019 | 75.8 77.9 81.8 80.9 84.0 85.1 | 94.8 96.9 [100] 99.88 [100] [100] | 0.996 (n=3) | +19.3 | 0.00 |
| Gope 2016 | 71.6 73.3 75.7 77.8 80.6 81.7 | 86.2 88.0 90.3 92.5 95.2 96.4 | 1.002 | +14.5 | 0.07 |
| Hassan 2018 | 75.3 77.9 74.9 81.0 83.9 86.0 | 89.2 91.8 88.9 94.9 97.9 99.9 | 0.999 | +14.0 | 0.06 |

- Fingerprints that don't depend on calibration, all reproduced:
  - Hassan 2018 dips at group 3.
  - Gupta dips at group 4. In base this becomes 99.88, between the clipped 100s.
  - Hassan 2023/Kazmi has an almost flat step from group 2 to 3 (+0.8).
  - Proposed jumps about 11 units at group 6 (52.5 → 63.5).
- Conclusion: base Fig. 1 is CMC-2025 Fig. 6 with the x-axis relabelled (5..30 devices → 300..1800 vehicles), the
  y-label changed, two legends renamed, and **a constant added to every competitor series**. The added constant differs
  per series, so this is an additive shift and not a rescale (all slopes ≈ 1.00). The base caption ("Processing
  requirements") does not match either y-label.
- **Setup of the source paper:** it states NS-3, not OMNeT++: "the proposed decision-tree-enabled authentication and
  communication methodology is implemented in NS-3 … The transmission range, Tp, of every device transmitter is
  approximately 450 m in the presence of obstacles." It defines the metric only verbally: "Communication cost overhead
  is the number of bits transmitted to ensure mutual authentication of both devices and server modules." This
  contradicts the plotted "(Resources)" values of 43-86. No formula is given for any "%".
- **Simulation-parameter table is the template of base Table II.** CMC-2025 Table 1, "Secure internet of things
  parameters setup", compared with base Table II:

| CMC-2025 Table 1 (NS-3) | Base Table II (OMNeT++) |
|---|---|
| Area 500 × 500 | 1500 × 1500 m |
| Devices 40-350 | 100-1000 |
| Servers 5% | 5% |
| Device's transmission interval 20 u Sec | sampling 15 µs |
| Link bandwidth 10 Mbps | 10 Mbps |
| Transmission cost (Packet) 75.6 mW | 75.6 mW |
| Receiving cost (Packet) 75.6 mW | 75.6 mW |
| Coverage area of XBEE module 450 M | XBEE range 500-800 m |
| Packet Size **128 Kbps** (same unit error) | packet size "128 Kbps" |
| UDP and CBR, random deployment | – |

### 1b. Base Fig. 3 vs HybridEdge Fig. 6 (partial match)

- Paper: A. Khan, R. Khan, F. Alturise, T. Alkhalifah, "HybridEdge: A Lightweight and Secure Hybrid Communication
  Protocol for the Edge-Enabled Internet of Things," *CMC* 82(2):3161-?, 2025, DOI 10.32604/cmc.2025.060372 (OA:
  https://www.techscience.com/cmc/v82n2/59517).
- Fig. 6 shows "Storage Cost Overhead (%)" on a meaningless x axis (0.5…2.5), one group of bars, in the same Origin
  plot style. Pixel reads: Proposed 0.570, Hassan 2023 0.620, Gupta 2019 0.615, Hassan 2018 0.654, Gope 2016 0.687.
- Base Fig. 3 reads: Proposed 0.530, **Zhanfei 0.570**, Hassan 2023 0.630, **Gupta 0.615**, Hassan 2018 0.660,
  Gope 0.710.
- Base keeps the legend order and inserts Zhanfei after Proposed. HybridEdge's own "Proposed" value becomes
  "Zhanfei", Gupta is identical, and the rest are rounded up.
- No storage formula or "%" denominator is given anywhere. The text only lists the stored items (MaskIDs + λ).
- HybridEdge setup: "implemented in OMNET++ … member modules … an exact copy of the Wasp-mote boards". Table 3:
  900 × 900 m, 500-2000 devices, 1 edge module, Tx 91.4 mW, Rx 59.1 mW, channel delay 10 ms, range 500 m,
  128-byte packets, 128-bit AES, 30-150 ms sampling, static random topology, CBR/UDP.
- HybridEdge Figs. 3/4 plot "Computational Cost Overhead (ms)" for modules 300-2100 against the same four
  competitors.
- HybridEdge also carries VANET leftovers. Its Table 6 includes "PK_RSU + PK_TA + V_i + Kv_i + IDv_i", with the gloss
  "V_i … represent sender vehicle".

### 1c. Base Fig. 2: unresolved

- Base Fig. 2 series: Gope, Gupta, Hassan 2023, Zhanfei, Proposed, 22-41 "bits", for 300-1800 vehicles.
- No first-difference match with CMC-2025 Fig. 5 ("Approximate Processing Time (nano seconds)" vs 3-18 neighbours)
  or with the HybridEdge figures.
- Best remaining candidate: JIOT-2024 IoV Fig. 5, 6 or 7 (below).

### 1d. Likely common parent: JIOT 2024 IoV paper (not verified)

- M. A. Jan, S. Abbas, H. H. Song, R. Khan, IEEE IoT J. 12(5):4715-4725, DOI 10.1109/JIOT.2024.3483275.
- Its OpenAlex reference list contains **exactly the five figure schemes** together: Gope & Hwang TIE 2016,
  Gupta et al. CompNet 2019, Hasan M.R. et al. 2018, Hasan M.M. et al. 2023, and Zhanfei Ma et al. IEEE Access 2024.
- It is the only candidate whose domain fits "Vehicles in VANET".
- Abstract: "Our scheme requires that each vehicle participates in an offline phase, where a trusted authority shares a
  list of MaskIDs and secret keys … simulation results verify … computational overhead, communication overhead, and
  storage overhead." That is the same MaskID/λ offline-phase design as HybridEdge and the base paper.
- Xplore figure captions:
  - Fig. 5 "Average processing time at the vehicular devices."
  - Fig. 6 "Average processing time at the edge servers."
  - Fig. 7 "Average communication overhead in a multihop infrastructure."
  - Fig. 8 "Average storage overhead."
- Figs. 5-8 map plausibly onto base Figs. 1-3. I could not view the images: the Xplore mediastore download was
  refused by the sandbox permission classifier, and I did not retry it.
- Also note: Ma et al. 2024's abstract says it "uses SUMO for simulation verification". That is the probable source
  of the stray "Simulation of Urban Mobility" in the base paper's conclusion.

### Lineage of the comparison set (from OpenAlex reference lists)

1. Jan et al. TII 2020 (10.1109/TII.2020.3043802): Gope16, Gupta19.
2. Khan et al. TII 2022 (10.1109/TII.2022.3179728): adds Hasan18.
3. Jan et al. JIOT 2023 AIoMT (10.1109/JIOT.2023.3317292): Gope16, Gupta19, Hasan18. Its figures are delay, PDR and
   throughput, not the same figures.
4. Al-Otaibi, Khan, … CMC 2024 (10.32604/cmc.2024.049017, claims NS-2 and OMNeT++). Gives tables only, no plots.
5. **Jan, Abbas, Song, Khan JIOT 2024 IoV**: all five schemes.
6. HybridEdge CMC 2025: four of the five, plus plots.
7. Route-finding CMC 2025: Ma24, Kazmi23, Gupta (cites Gupta D. 2014 VANET routing), Gope (cites JSYST 2015),
   Hasan18, plus plots.
8. Base TCE 2026: none of the five is cited.

## 2. The five comparison schemes

| Legend | Primary identification (as cited in JIOT-2024 IoV and HybridEdge) | Alternate seen in the group's papers | OA? |
|---|---|---|---|
| Gope 2016 | P. Gope, T. Hwang, "A Realistic Lightweight Anonymous Authentication Protocol for Securing Real-Time Application Data Access in WSNs," IEEE TIE 63(11):7124-7132, 2016, DOI 10.1109/TIE.2016.2585081 (high) | Gope & Hwang, "Lightweight and Energy-Efficient Mutual Authentication … Global Mobility Networks," IEEE Syst. J., DOI 10.1109/JSYST.2015.2416396 (cited in route-finding CMC) | closed |
| Gupta 2019 | A. Gupta, M. Tripathi, T. J. Shaikh, A. Sharma, "A lightweight anonymous user authentication and key establishment scheme for wearable devices," Comput. Netw. 149:29-42, 2019, DOI 10.1016/j.comnet.2018.11.021 (high) | route-finding CMC ref [20] is D. Gupta & R. Kumar, "An improved genetic based routing protocol for VANETs," 2014 | closed |
| Hassan 2018 | M. R. Hasan, Y. Zhao, Y. Luo, G. Wang, R. M. Winter, "An Effective AODV-based Flooding Detection and Prevention for Smart Meter Network," Procedia CS 129:454-460, 2018, DOI 10.1016/j.procs.2018.03.024 (high). **It is not an authentication scheme**: FLOW-AODV is a routing/flooding defence simulated in NS-3. | – | OA (Elsevier) |
| Hassan 2023 | M. M. Hasan, N. A. M. Ariffin, N. F. M. Sani, "Efficient mutual authentication using Kerberos for resource constraint smart meter in AMI," J. Intell. Syst. 32(1):20210095, 2023, DOI 10.1515/jisys-2021-0095 (Kerberos + ECC, verified with AVISPA) (high for JIOT/HybridEdge) | S. H. A. Kazmi, **R. Hassan**, F. Qamar, K. Nisar, …, "Security Concepts in Emerging 6G Communication …," Symmetry 15(6):1147, 2023, DOI 10.3390/sym15061147, a survey. It is the series that becomes "Hassan 2023" in base Fig. 1 (high for Fig. 1) | OA |
| Zhanfei 2024 | Zhanfei Ma, Jing Jiang, Hui Wei, Bisheng Wang, Wenli Luo, Haoye Luo, Dongxiang Liu, "A Blockchain-Based Secure Distributed Authentication Scheme for Internet of Vehicles," IEEE Access 12:81471-81482, 2024, DOI 10.1109/ACCESS.2024.3409361 (smart contracts + optimised PBFT, ROR/AVISPA, SUMO) (high) | – | OA |

**Costs as stated by the group.** These are not primary-source values, and they are internally inconsistent.

- From CMC 2024 Tables 2-4 and HybridEdge Tables 4-6:
  - Gope16: 12Th+5TXOR; 4 msgs; **31,184 bits** (CMC 2024) vs **3,184 bits** (HybridEdge). Storage: server
    x_id+Ts_ug+ω+K_ug+Ts_ug^new+Sn^new+id_i+k_gsi^new, device none.
  - Gupta19: 16Th+11TXOR; 5 msgs; 3,038 bits. Storage: e_j+f_j+x_j+MI_u+MGID_i (device), MSID_j+Z_j+x_i (server).
  - Hasan18: 11Th+18TXOR (CMC 2024) vs 7Th+14TXOR (HybridEdge); 6 msgs; 32,000 bits. These are the group's
    attribution, since the source paper is a routing protocol.
  - Hasan23 (HybridEdge [15]): 2TPA+2TPM / 2TE/D+2TPRNG / 3TTS+1TTKNG; 6 msgs; 672 bits. Storage Q_AG+μ_i.
  - Ma 2024 appears in no table of any group paper.
- I could not pull primary costs: the IEEE Access, De Gruyter and ScienceDirect fetches returned 403/405.

## 3. Public code or data

- None found.
  - GitHub (`gh api search/repositories`; queries: omnetpp/MaskID/hybrid ECC/IoV authentication): no related repo.
  - Zenodo API ("Rahim Khan" authentication): nothing relevant.
  - Web search: nothing relevant.
- The CMC papers state "This article does not involve data availability" or "Not applicable".
- The base paper has no data/code statement.

## 4. Other figure reuse by the group

- CMC-2025 route-finding Fig. 6 → base Fig. 1: same data with per-series shifts (above).
- HybridEdge Fig. 6 → base Fig. 3: partial.
- HybridEdge Figs. 3/4 and route-finding Fig. 5 use the same Origin template: black/red/blue/magenta/green(/navy)
  bars, legend box at top left, bold axis titles, the same competitor set. Their numbers differ from base Fig. 2.
- Simulator claims for related data vary across the group: NS-2 and OMNeT++ in CMC 2024; OMNeT++ in HybridEdge; NS-3
  in route-finding; OMNeT++ in base, which also says SUMO in its conclusion.

## Implications for the OMNeT++ emulation (PLAN.md)

- Base Fig. 1 values for competitors equal another paper's NS-3 "(Resources)" values plus an undocumented constant.
  No simulator configuration can produce them from first principles. Its x-axis was relabelled from 5-30 devices.
  The only honest route is a **calibrated reproduction** that states this provenance.
- No paper in the chain defines "overhead (%)" or "storage overhead (%)".

## PDFs to obtain via institutional access (IEEE Xplore / Elsevier)

1. **Jan, Abbas, Song, Khan, IEEE IoT J. 2024/25, DOI 10.1109/JIOT.2024.3483275** (essential: check Figs. 5-8 against
   base Figs. 1-3, especially Fig. 2; check its simulator and parameter table).
2. Gope & Hwang, IEEE TIE 2016, DOI 10.1109/TIE.2016.2585081.
3. Gupta et al., Comput. Netw. 2019, DOI 10.1016/j.comnet.2018.11.021.
4. (alternate) Gope & Hwang, IEEE Syst. J., DOI 10.1109/JSYST.2015.2416396.
5. OA but blocked to automated fetch, so download manually: Ma et al. IEEE Access 2024 (10.1109/ACCESS.2024.3409361);
   Hasan et al. J. Intell. Syst. 2023 (10.1515/jisys-2021-0095); Hasan et al. Procedia CS 2018
   (10.1016/j.procs.2018.03.024).
6. Optional: Jan et al. JIOT 2023 AIoMT (10.1109/JIOT.2023.3317292); Khan et al. TII 2022 (10.1109/TII.2022.3179728).
