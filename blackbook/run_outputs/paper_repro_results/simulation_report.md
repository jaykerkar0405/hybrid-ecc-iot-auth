# Simulation (Table II re-creation, Python, 30 runs/point)

Devices [300, 600, 900, 1200, 1500, 1800], servers = 5% of N, area 1500x1500, range 500 m, 10 Mbps.

## Mean per-device authentication latency (ms)

| Scheme | 300 | 600 | 900 | 1200 | 1500 | 1800 |
|---|---|---|---|---|---|---|
| Proposed scheme | 171.0 | 178.2 | 180.2 | 180.4 | 179.6 | 177.8 |
| Turkanovic [12] | 24.0 | 25.0 | 25.2 | 25.3 | 25.2 | 24.9 |
| Porambage [11] | 2050.5 | 2135.6 | 2158.4 | 2161.1 | 2151.1 | 2130.8 |
| Dhillon & Karla [13] | 36.6 | 38.1 | 38.6 | 38.6 | 38.4 | 38.0 |
| Cheng & Le [14] | 66.1 | 67.5 | 67.9 | 67.9 | 67.7 | 67.4 |
| Shuai [16] | 278.1 | 289.9 | 293.1 | 293.5 | 292.1 | 289.3 |
| Jiang [15] | 44.8 | 46.7 | 47.3 | 47.3 | 47.1 | 46.6 |
| Wazid [17] | 335.1 | 349.8 | 353.8 | 354.3 | 352.5 | 349.0 |
| Sadhukhan [18] | 338.2 | 352.4 | 356.2 | 356.6 | 355.0 | 351.6 |

## Per-session transmit energy (mJ) at 75.6 mW

| Scheme | mJ |
|---|---|
| Proposed scheme | 0.0077 |
| Turkanovic [12] | 0.0206 |
| Porambage [11] | 0.0254 |
| Dhillon & Karla [13] | 0.0191 |
| Cheng & Le [14] | 0.0172 |
| Shuai [16] | 0.0179 |
| Jiang [15] | 0.0148 |
| Wazid [17] | 0.0196 |
| Sadhukhan [18] | 0.0121 |

## Server coverage within 500 m

| N | 300 | 600 | 900 | 1200 | 1500 | 1800 |
|---|---|---|---|---|---|---|
| covered | 97.0% | 99.9% | 100.0% | 100.0% | 100.0% | 100.0% |

Latency ranking at N=1800 (best first): Turkanovic [12] < Dhillon & Karla [13] < Jiang [15] < Cheng & Le [14] < Proposed scheme < Shuai [16] < Wazid [17] < Sadhukhan [18] < Porambage [11]

Proposed latency as % of the worst scheme per N (cf. Fig. 1 proposed bars [43, 45, 47, 50, 52, 63]): 8, 8, 8, 8, 8, 8
