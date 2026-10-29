# OMNeT++ toolchain on this Mac: feasibility study (Phase 0-C)

Date: 2026-10-29. Nothing was installed or pulled for this study. Evidence comes from local read-only checks, the omnetpp / inet / veins / opp_env / sumo source trees on GitHub, registry manifests (metadata only) and the official download pages. Figures marked **(est.)** are estimates. Only the 656 MB WSL build size was measured, in REPORT.md section 8.1.

## 0. This machine (checked locally)

| item | state |
|---|---|
| OS / CPU | macOS 26.6.2 (build 25G83), arm64, M2 Pro, 10 cores, 16 GB RAM |
| Disk | 36 GiB free on `/` (enough, but tight for the Nix route) |
| Compiler | Apple clang 21.0.0 (clang-2100.3.34.2), CLT 27.0, SDK 27.0, at `/Library/Developer/CommandLineTools` |
| bison | `/usr/bin/bison` **2.3 (too old)**. OMNeT++ `configure` requires >= 3.0. brew `bison` (3.8.2, keg-only) is **not installed** |
| flex | `/usr/bin/flex` 2.6.4 (OK). brew `flex` is not installed |
| make / perl | GNU Make 3.81 (works; OMNeT++ setenv prefers brew `make` if present), perl 5.34 |
| python | `/opt/homebrew/bin/python3` 3.14.7, numpy/pandas **not** installed. **There is no `python` on PATH** |
| Qt / llvm / sumo / nix / opp_run | none installed |
| Docker | Not Docker Desktop: the CLI talks to **OrbStack** (`docker context` = `orbstack`). Daemon **running**, server 29.8.2, VM arch aarch64, 10 vCPU, 7.8 GiB RAM. No OMNeT++ images present |

## 1. OMNeT++ versions on native arm64 macOS

| version | released | macos-aarch64 package | builds with this Mac's Apple clang 21? |
|---|---|---|---|
| 6.0.2 / 6.0.3 | 2023-10 / 2024-02 | "experimental" (asset exists on GitHub) | **No, not unpatched.** `src/common/exprnodes.cc:104` `createMathFunction("hypot", hypot)` is ambiguous with Apple clang >= 17 (issues #1354, #1368, #1395). It is a one-line patch |
| 6.1.0 | 2024-10-09 | yes | **No**, same `hypot` bug (fixed in 6.2) |
| 6.2.0 | 2025-07-14 | yes | yes (bug fixed via `_wrap_hypot`) |
| 6.3.0 | 2025-11-12 | yes | expected yes. 6.4's changelog fixes "incorrect clang toolchain name on macOS with newer (22.0+) clang", which should not affect clang 21 |
| **6.4.0** | 2026-05-08 (current) | yes (`omnetpp-6.4.0-macos-aarch64.tgz`, 400 MB; `-core.tgz`, 76 MB) | expected yes (latest macOS build fixes) |

Upstream's tested platform is "macOS 15 (and likely newer versions)". macOS 26 is not officially listed. No open OMNeT++ issue reports a build failure on Tahoe, only an IDE text-selection bug (#1479, closed).

**Prerequisites** (6.4.0 `doc/src/installguide/ch-macos.rst` and `install.sh`):
- `xcode-select --install` (already present).
- Full set from `install.sh`: `brew install bison ccache llvm flex perl python@3 make pkg-config doxygen graphviz`, plus `qt@6 qtkeychain` for the GUI and `openscenegraph` for 3D.
- Python: venv inside the OMNeT++ dir, then `pip install -r python/requirements.txt`. For 6.4 that installs matplotlib<4, numpy>=2,<3, pandas<3, scipy<2, ipython, packaging. It is only needed for the IDE analysis tool and `opp_charttool`. `configure` only *warns* if these are missing.
- **Headless (Cmdenv-only) avoids Qt completely:**

  `./configure WITH_QTENV=no WITH_OSG=no WITH_OSGEARTH=no WITH_PYTHON=no WITH_SCAVE_PYTHON_BINDINGS=no`

  then `make MODE=release base`. The `base` target is `common layout eventlog scave nedxml sim envir cmdenv utils`; `qtenv` is added only if `WITH_QTENV=yes`.
  - `WITH_PYTHON=no` drops the new embedded-Python `pyeval()`/`pycode()` NED functions, which we don't use, and avoids linking against Python 3.14.
  - Our `collect.py` parses `.sca` text itself, so no scave Python bindings are needed.
- **Minimum brew set for headless:** `bison flex` (both keg-only, so they are put on PATH by `source setenv`), plus `make pkgconf` (recommended). `llvm` is optional: 6.4's `setenv` prepends `$(brew --prefix llvm)/bin` to PATH, so **if brew llvm is ever installed, OMNeT++ silently switches from Apple clang to brew clang**. Pick one and keep it. Untested: whether skipping llvm/qt causes any issue in 6.4 (upstream always installs llvm).
- `source setenv` **must** run before `./configure` (since 6.0.2 configure refuses otherwise). On this Mac it is also what puts brew bison 3.8 ahead of `/usr/bin/bison` 2.3. `setenv` uses no bash-4-only syntax, so it works from `/bin/bash` 3.2 and from zsh.

**Known macOS issues:**
- The `hypot` ambiguity above (6.0.x / 6.1.0).
- Gatekeeper: download with `curl`, which sets no quarantine attribute. If you download in a browser, run `xattr -dr com.apple.quarantine omnetpp-6.x`.
- The guide recommends enabling *Privacy & Security > Developer Tools > Terminal*. It is optional for Cmdenv but speeds up the first launch of fresh binaries.
- `sudo spctl --global-disable` is only needed for IDE debugging. Do not do it for this work.
- IDE needs LLDB from Xcode/CLT. Irrelevant for headless.
- The macOS x86_64 package must not be used on Apple silicon (setenv detects it and re-execs under Rosetta).

**Disk and time on the M2 Pro:**
- OMNeT++ 6.4 core, headless, release-only: ~0.7 GB built (the measured 6.0.3 WSL build was 656 MB), ~3-6 min with `-j10` **(est.)**. The full macOS package with IDE: ~1.5-2 GB **(est.)**.
- brew bison/flex/make/pkgconf: <50 MB, about 1 min.
- INET 4.6.0, release-only: ~1.5-2.5 GB, ~10-20 min **(est.)**.
- Veins: <0.3 GB, 2-4 min **(est.)**.

## 2. INET, Veins and SUMO compatibility

| component | constraint (source) |
|---|---|
| INET 4.5.4 (2024-10-30) | OMNeT++ 6.0-6.3 (opp_env db; release notes: "OMNeT++ 6.1 compatibility fixes"). **Not 6.4** |
| INET 4.6.0 (2026-02-20) | "Requires OMNeT++ 6.2 or later". opp_env lists 6.2, 6.3, 6.4 |
| INET 4.7.0 (2026-07-07) | "Requires OMNeT++ 6.4 or later" |
| Veins 5.3.1 (latest release tag) | Official page: OMNeT++ <= 6.1.0, INET 4.4.0-4.5.4, SUMO 1.8-1.22. opp_env's tested matrix extends this to OMNeT++ 6.0-6.3 and INET 4.5.4 or 4.6.0 (4.6 only with opp_env's sed patches to veins_inet). The opp_env db says OMNeT++ 6.4 "not supported" for Veins |
| Veins TraCI gate | Veins 5.3.1 accepts TraCI API <= 21. Veins master (commits 2026-10-27/28: INET 4.6/4.7 whitelisted, SUMO 1.28 test fix) accepts API 22 |
| SUMO -> TraCI API | 1.19-1.22 = API 21; 1.23-1.28 = API 22 (`TRACI_VERSION` in `src/libsumo/TraCIConstants.h`). **So Veins 5.3.1 needs SUMO <= 1.22, and SUMO >= 1.23 needs Veins master** |

**SUMO on arm64 macOS:**
- **Not in homebrew-core.** The tap `brew tap dlr-ts/sumo && brew install sumo` is stale: it builds 1.20.0 with only `arm64_sonoma`/`arm64_ventura` bottles and pulls in X11/fox dependencies. SUMO's own docs say Homebrew "is no longer considered a good alternative".
- Official `sumo-1.28.0.pkg` (arch not documented; needs XQuartz for the GUI).
- **pip `eclipse-sumo`:** macOS arm64 wheels exist **only for 1.23.0+** (1.28.0: `macosx_15_0_arm64`). 1.22.0 has manylinux aarch64/x86_64 and win wheels only.
- So natively on this Mac the clean pairing is **Veins master (pinned SHA) + `pip install eclipse-sumo==1.28.0`**. In a linux/arm64 container the clean all-release-tag pairing is **Veins 5.3.1 + `eclipse-sumo==1.22.0`**.
- **Reconciling with opp_env:** the opp_env db excludes OMNeT++ 6.4 for Veins with the comment "SUMO 1.22.0 reports API v22". SUMO's source says 1.22 reports API 21. The likely explanation (an inference) is that 6.4-era opp_env workspaces pin a newer nixpkgs whose `sumo` is 1.28 (API 22), which Veins 5.3.1 rejects. The incompatibility is Veins 5.3.1 vs SUMO >= 1.23, not OMNeT++ 6.4 itself. That is consistent with route (a) in section 6 (Veins master on 6.4).

**INET without Veins:** yes, both radios are usable on their own. Verified in the v4.5.4 and v4.6.0 source trees.
- **IEEE 802.15.4 (XBee-like):**
  - `inet.linklayer.ieee802154.Ieee802154NarrowbandInterface` with `Ieee802154NarrowbandMac`: CSMA-CA, `macMaxFrameRetries = 3`, MTU 127-9 B, MAC acks.
  - Radios: `Ieee802154NarrowbandScalarRadio`, `...DimensionalRadio`, and (4.6) `...UnitDiskRadio`, plus a UWB-IR variant.
  - Node type: `inet.node.inet.SensorNode`. There is a `showcases/wireless/ieee802154` example.
- **IEEE 802.11p:**
  - `Ieee80211ModeSet("p", ...)` gives 10 MHz OFDM modes at 3-27 Mbps, and `Ieee80211CompliantBands::band5_9GHz` ("5.9 GHz", 5.855 GHz, 10 MHz spacing).
  - Configure with `**.wlan[*].opMode = "p"`, `**.wlan[*].bitrate = 6Mbps`, `**.wlan[*].radio.bandName = "5.9 GHz"`, and ad-hoc management (`Ieee80211MgmtAdhoc`) for OCB-like operation.
  - Mobility for the 160 km/h variant: INET's own models (`LinearMobility`, `RandomWaypointMobility`, `BonnMotionMobility`). **SUMO is only needed for road-network traffic.**
- **Caveat:** neither standard radio matches Table II's "10 Mbps". 802.15.4 runs at 250 kbps; 802.11p tops out at 27 Mbps with 6 Mbps typical. Using a real MAC therefore changes the bandwidth assumption, and that has to be stated.

## 3. Docker route

- **Every official image is linux/amd64-only** (checked via `docker buildx imagetools inspect`, metadata only):
  - `ghcr.io/omnetpp/omnetpp` tags: u18.04-*, `u22.04-6.0`/`6.0.1`/`6.0.3`, `u24.04-6.1.0`/`6.2.0`/`6.3.0`. These are core-only Cmdenv images (~1 GB compressed), workdir `/root/models`.
  - `ghcr.io/omnetpp/omnetpp-gui` (u22.04-6.0.1/6.0.3, u24.04-6.1.0..6.3.0).
  - `ghcr.io/omnetpp/opp_env` (latest, 241031, 250715, 0.36.2.261008): an OCI index with linux/amd64 only.
  - The download page advertises `ghcr.io/omnetpp/omnetpp:u26.04-6.4.0`, but **that tag is not in the registry** (tags/list checked).
  - INET images (`ghcr.io/omnetpp/inet`) are not publicly listable. There is no community arm64 image worth trusting.
- **Native arm64 image = local build.** The official Dockerfile (`releng/dockerfiles/omnetpp/Dockerfile` in the 6.4.0 tree) is arch-neutral: `ubuntu:24.04` + `omnetpp-$VERSION-core.tgz` + `./install.sh -y --no-gui`. Building it (or the slimmer recipe in section 6) on OrbStack yields linux/arm64.
- **Performance caveats (OrbStack on Apple silicon):**
  - amd64 images run under Rosetta: they work, but compiling is noticeably slower (~1.5-3x, est.) and Rosetta's future after macOS 27 is uncertain.
  - Native arm64 containers run near native speed.
  - The OrbStack VM has 7.8 GiB RAM: cap INET builds at `-j4`..`-j6`, or raise the memory limit in OrbStack settings.
  - Bind-mounted repo I/O is fine for `.ini`/`.sca`. Keep build trees inside the container or a named volume.
  - No GUI needed (Cmdenv).
- **Daemon:** running (`docker info` OK, OrbStack, aarch64, 10 CPUs). The previous Windows attempt with Docker Desktop failed (REPORT 8.1); that is not relevant here.

## 4. opp_env (Nix-based official installer)

- Supports Linux and macOS. On Apple silicon **only OMNeT++ 6.x** can be installed (`is_unsupported_apple_silicon = version < "6.0"`). The macOS install docs say "We do not provide precise installation instructions at the moment".
- **Every opp_env CI workflow (omnetpp/inet/veins smoketests and compatibility runs) is `runs-on: ubuntu-latest`. There is no macOS runner**, so macOS + Veins is **untested upstream**. nixpkgs `sumo` (1.28.0) has no platform restriction but is likewise untested on aarch64-darwin.
- **Reproducibility:** good in principle. Workspaces pin nixpkgs via flake.lock templates (22.11 ... 25.11), and the db encodes version matrices and patches, e.g.:
  - veins-5.3.1 with inet-4.6.0/4.5.4 on omnetpp 6.0-6.3, with sed patches for INET 4.6;
  - inet-4.6.0 on 6.2-6.4;
  - inet-4.7.0 on 6.4.

  Commands:

  ```
  opp_env init
  opp_env install veins-5.3.1 --options ...
  opp_env shell veins-5.3.1   # or: opp_env run veins-5.3.1 -c '...'
  ```
- **Cost on this Mac:**
  - It needs Nix (>= 2.8) installed system-wide. That creates a `/nix` APFS volume and a daemon and edits `/etc/zshrc`, which macOS upgrades overwrite.
  - opp_env builds OMNeT++ *with* Qtenv (Qt from Nix) by default.
  - Nix store ~5-15 GB (est.) against 36 GiB free.
  - There is a `--nixless-workspace` mode, but it just uses host packages, which gives no reproducibility gain over brew.
- **Verdict:** feasible but the heaviest and least-tested route on macOS. A viable reproducible alternative is opp_env inside a linux/arm64 container (the multi-arch `nixos/nix` base + `pip install opp-env`), which matches upstream's tested Linux path. It was not tried.

## 5. The existing AuthNet model: structure, and what must change for macOS

**Model summary** (`research/reference_replication/omnet/AuthNet.ned`, `AuthNet.cc`; plain OMNeT++, no INET):
1. Network `AuthNet` has `core: Core`, `devices[N]`, `servers[round(0.05N), >= 1]` and `adversaries[round(0.05N)]`, uniformly placed on 1500x1500 m. N comes from `*.numDevices = ${N=...}`.
2. `Core` holds every parameter. Table II gives: 10 Mbps, 500 m range, 15 us event quantum, 10 ns hand-off, 75.6 mW tx/rx, speed. `gen_omnet_ini.py` supplies the per-scheme values: `bitsTotal`, `nMessages`, `deviceProcMs`, `serverProcMs`, `pseudonymLookup`, `tProbeMs`, `rejectMs`. The assumptions are the arrival window, adversary rate and enrolment policy.
3. There are no gates or channels between modules. All traffic uses `sendDirect` into `@directIn` gates. The delay is computed in C++ as queue wait + airtime + distance/c + hand-off.
4. **Channel model:** one shared half-duplex "air" per server. `Server::reserveAir` serialises transmissions (FIFO, `airFree`), airtime is `bits/rate` rounded up to the 15 us quantum, and energy is (tx+rx power) x airtime. There is no MAC, collisions, loss or retransmission.
5. Each device attaches to the nearest server within range; otherwise it counts as `unreachable`. In the mobile variant it moves at constant velocity, reflects off the edges, and re-selects a server at session start.
6. **Session:** each device starts once at U(0, windowS). It alternates compute phases (`deviceProcMs / (nMsg/2 + 1)` each) with `nMsg/2` request/reply round trips of `bitsTotal/nMsg` bits.
7. **Server cost:** each request costs `serverProcMs / (nMsg/2)` on a single FIFO CPU (`cpuFree`). The proposed scheme adds a pseudonym scan of `0.5 x enrolled x W x tProbe` on step 1.
8. "Enrolled" is either every device in range (`reachable`, the default) or only attached devices (`nearest`), computed in init stage 2.
9. Adversaries send forged 128-bit requests to their nearest server as a Poisson process (1/s) within the window. Proposed scheme: a full miss scan (`enrolled x W x tProbe`). Others: `rejectMs`.
10. Per-scheme costs are therefore pure parameters. Processing times come from Table III constants x Table V op counts (or measured ESP8266 / papers' constants), and bits from Table IV, all generated by `scripts/gen_omnet_ini.py` with no hand-typed numbers.
11. **Statistics** are scalars only (vectors and params are off).
    - `core`: `latency_mean_ms`, `latency_p95_ms`, `sessions_completed`, `sessions_unreachable`, `kbit_on_air`, `energy_mJ`, `end_time_s`.
    - Per server: `busy_ms`, `enrolled`.
12. Runs: `repeat = 5`, `seed-set = ${repetition}`, `sim-time-limit = 1000s`, Cmdenv express mode. 122 configs, 3,385 runs, "a few minutes" in total.
13. `collect.py` parses `.sca` text into `omnet_results.csv`: one row per run, plus aggregated server busy (total/max), mean enrolled and number of servers.

**Changes needed to build and run on macOS:**

| file | issue | change |
|---|---|---|
| `omnet/setup_toolchain_and_omnetpp.sh` | Entirely Linux: micromamba `linux-64` toolchain, `x86_64-conda-linux-gnu-*` symlinks, `omnetpp-6.0.3-linux-x86_64.tgz` | Replace with the brew + 6.4.0 core recipe in section 6 (or a Dockerfile). Do not port it |
| `omnet/run_omnet.sh`, `omnet/smoke.sh` | "Run INSIDE WSL"; `export PATH=~/opp-toolchain/bin:$PATH`; `. ~/omnetpp-6.0.3/setenv`; `python collect.py` | Drop the toolchain PATH. Source `${OMNETPP_ROOT:-$HOME/opp/omnetpp-6.4.0}/setenv`. Use `python3`. Optionally `make -j$(sysctl -n hw.ncpu)` |
| `run_all.sh` lines 28-36 | Detects only `wsl -d Ubuntu-22.04` and converts the Windows path to `/mnt/c/...` | Add a `uname = Darwin` branch: if `opp_run` exists after sourcing setenv (or a docker image exists), call `bash omnet/run_omnet.sh "$PWD" all` directly. No path translation is needed |
| link flags | `-loppcommon -loppnedxml -loppscave -loppeventlog -lopplayout` | These libraries are still built by `make base` in 6.4, so this is harmless. They are not needed by the model and can be dropped |
| compiler / OMNeT++ version | 6.0.3 does not compile with Apple clang 21 (`hypot`) | Use 6.4.0 (or 6.2+). The C++ API used is unchanged in 6.4: 5-arg `sendDirect(msg, delay, duration, module, gate)`, `cMessage::addPar/hasPar/par`, `cPar::doubleValueInUnit/stdstringValue`, `numInitStages`, `recordScalar` |
| **baseline clobber** | `run_omnet.sh`'s last line copies the output over `results/omnet_results.csv`. That is the md5-pinned WSL baseline that REPORT.md numbers and `pytest tests` compare against | **Until parity is confirmed, write Mac output to a separate file**, e.g. `results/omnet_results_macos.csv`. Replace the baseline only after the diff below is understood and recorded |
| REPORT/PDF text | "OMNeT++ 6.0.3 (WSL2)" in `REPORT.md` 2 and 8.1, `scripts/report_to_pdf.py:233`, `scripts/step5b_omnet_results.py:2` | Update only after the Mac rerun is validated |

**Regression risk to the stored baseline.** REPORT.md claims `results/omnet_results.csv` is byte-identical across reruns (gcc 16.2 / x86_64 / OMNeT++ 6.0.3).
- On arm64 clang, `-ffp-contract=on` fuses multiply-adds, and libm differs (`sqrt` is exact; `cos`/`sin`/`fmod` and `log`/`exponential()` may differ in the last bit).
- 6.4 also adds a pluggable RNG manager. The default `cRngManager` is presumably the same mt19937 seeding, but that is unverified.
- The 15 us quantisation absorbs most last-bit noise, but not at the boundaries.
- **Procedure:**
  1. Rerun the full sweep on the Mac and diff it against the stored CSV.
  2. If rows differ, put `CFLAGS += -ffp-contract=off` in a `makefrag` next to the sources (`opp_makemake` includes it automatically) and rerun.
  3. Report any residual diff.
- Bit-exact old numbers are best reproduced on amd64 `ghcr.io/omnetpp/omnetpp:u22.04-6.0.3` under Rosetta. Even that is a different compiler from the original conda gcc 16.2.

## 6. Recommendation and exact commands

**Fastest reliable route (no INET/Veins): native, headless OMNeT++ 6.4.0 from the core tarball with Apple clang.**
- Estimated 10-15 min end to end; no Qt, no Nix, no Docker.
- It keeps the AuthNet model and scripts almost unchanged, and is fully scriptable: Cmdenv batch, `${N=...}` sweeps, and Python-generated `.ini` files.

```bash
# --- one-off: OMNeT++ 6.4.0, headless (Cmdenv only), into ~/opp ---
brew install bison flex make pkgconf          # bison is required (system bison 2.3 < 3.0); all keg-only/harmless
mkdir -p ~/opp && cd ~/opp
curl -fLO https://github.com/omnetpp/omnetpp/releases/download/omnetpp-6.4.0/omnetpp-6.4.0-core.tgz
shasum -a 256 omnetpp-6.4.0-core.tgz          # must start with db8de41f (omnetpp.org/download)
tar xzf omnetpp-6.4.0-core.tgz && cd omnetpp-6.4.0
source setenv                                  # puts brew bison/flex/make first; required before configure
./configure WITH_QTENV=no WITH_OSG=no WITH_OSGEARTH=no WITH_PYTHON=no WITH_SCAVE_PYTHON_BINDINGS=no
make -j10 MODE=release base
opp_run -v                                     # sanity check

# --- every session ---
source ~/opp/omnetpp-6.4.0/setenv -q

# --- build + run AuthNet (what run_omnet.sh does, minus WSL) ---
SRC=~/Documents/Stuff/hybrid-ecc-iot-auth/research/reference_replication
rm -rf ~/authnet && mkdir -p ~/authnet && cp $SRC/omnet/{AuthNet.ned,AuthNet.cc,omnetpp.ini,configs_*.txt,collect.py} ~/authnet/
cd ~/authnet
# optional, for cross-platform numeric parity: echo 'CFLAGS += -ffp-contract=off' > makefrag
opp_makemake -f --deep -o authnet && make -j10 MODE=release
./authnet -u Cmdenv -c M_Proposed_V1_T4__BASE -r 0 -f omnetpp.ini --result-dir=results_smoke
for c in $(cat configs_main.txt configs_sens.txt configs_fig.txt); do ./authnet -u Cmdenv -c "$c" -f omnetpp.ini --result-dir=results >/dev/null; done
python3 collect.py results > omnet_results.csv && diff <(sort omnet_results.csv) <(sort $SRC/results/omnet_results.csv) | head
```

For Python-driven sweeps, regenerate the ini with `scripts/gen_omnet_ini.py` (repo venv), then call `./authnet -u Cmdenv -c <cfg> -r <i>` per run from `subprocess` (or `opp_runall -j10 ./authnet -u Cmdenv -c <cfg>` to parallelise runs). `-q numruns` / `-q runs` list the run numbers a config expands to.

**With INET (802.15.4 / 802.11p, still native):** add INET 4.6.0 on top of 6.4.0. INET 4.5.4 does not support 6.4.

```bash
source ~/opp/omnetpp-6.4.0/setenv -q && cd ~/opp
curl -fL https://github.com/inet-framework/inet/releases/download/v4.6.0/inet-4.6.0-src.tgz | tar xz
cd inet4.6 && source setenv && make makefiles && make -j8 MODE=release    # ~10-20 min (est.)
# a model then builds with: opp_makemake -f --deep -o model -KINET_PROJ=$INET_ROOT -DINET_IMPORT -I$INET_ROOT/src -L$INET_ROOT/src -lINET
# and runs with:            ./model -u Cmdenv -n .:$INET_ROOT/src -c <cfg>
```

The unpacked directory name (`inet4.6`) is from INET convention; check after extracting.

**With Veins + SUMO**, two options:

- **(a) Native**, accepting an unreleased Veins: OMNeT++ 6.4.0 + INET 4.6.0 + Veins **master pinned to a commit SHA** (it whitelists INET 4.6/4.7 and TraCI API 22), with SUMO from the arm64 wheel:
  ```bash
  source ~/opp/omnetpp-6.4.0/setenv -q && source ~/opp/inet4.6/setenv     # INET 4.6.0 built as above
  python3 -m venv ~/opp/sumo-venv && ~/opp/sumo-venv/bin/pip install eclipse-sumo==1.28.0
  export PATH=~/opp/sumo-venv/bin:$PATH                                    # veins_launchd runs `sumo` from PATH
  export SUMO_HOME=$(~/opp/sumo-venv/bin/python -c 'import sumo;print(sumo.SUMO_HOME)')
  git clone https://github.com/sommer/veins ~/opp/veins && cd ~/opp/veins
  git checkout 62e43075c40028463fd4cd223cf26678323624a3                   # master HEAD on 2026-10-28 (INET 4.6/4.7 + SUMO 1.28 support)
  ./configure && make -j8 MODE=release
  cd subprojects/veins_inet && ./configure --with-inet=$INET_ROOT --with-veins=$HOME/opp/veins && make -j8 MODE=release
  # run: bin/veins_launchd -vv &   then the model with -u Cmdenv
  ```
  Untested combination: no upstream CI on macOS.
- **(b) Linux/arm64 container**, all release tags inside the opp_env-tested matrix: Ubuntu 24.04 + OMNeT++ **6.3.0** + INET **4.5.4** + Veins **5.3.1** + `eclipse-sumo==1.22.0` (TraCI API 21; the manylinux aarch64 wheel exists). veins_inet 5.3.1 reads INET's `Version` file and whitelists 4.5.4, so no patches are needed.

  Dockerfile (adapted from upstream `releng/dockerfiles/omnetpp/Dockerfile`; not yet built):
  ```dockerfile
  FROM ubuntu:24.04
  SHELL ["/bin/bash", "-c"]
  ENV DEBIAN_FRONTEND=noninteractive
  RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl git clang lld make bison flex perl python3 python3-venv pkg-config zlib1g-dev libxml2-dev \
      && rm -rf /var/lib/apt/lists/*
  WORKDIR /opt
  RUN curl -fsSL https://github.com/omnetpp/omnetpp/releases/download/omnetpp-6.3.0/omnetpp-6.3.0-core.tgz | tar xz \
      && cd omnetpp-6.3.0 && source setenv -q \
      && ./configure WITH_QTENV=no WITH_OSG=no WITH_OSGEARTH=no WITH_PYTHON=no WITH_SCAVE_PYTHON_BINDINGS=no \
      && make -j6 MODE=release base && rm -rf doc samples test
  RUN source /opt/omnetpp-6.3.0/setenv -q \
      && curl -fsSL https://github.com/inet-framework/inet/releases/download/v4.5.4/inet-4.5.4-src.tgz | tar xz \
      && mv inet4.5* inet && cd inet && source setenv \
      && make makefiles && make -j6 MODE=release
  RUN python3 -m venv /opt/sumo && /opt/sumo/bin/pip install --no-cache-dir eclipse-sumo==1.22.0
  ENV PATH=/opt/sumo/bin:$PATH
  RUN source /opt/omnetpp-6.3.0/setenv -q \
      && mkdir veins && curl -fsSL https://github.com/sommer/veins/archive/refs/tags/veins-5.3.1.tar.gz | tar xz -C veins --strip-components=1 \
      && cd veins && ./configure && make -j6 MODE=release \
      && cd subprojects/veins_inet && ./configure --with-inet=/opt/inet --with-veins=/opt/veins && make -j6 MODE=release
  RUN echo 'source /opt/omnetpp-6.3.0/setenv -q; export SUMO_HOME=$(/opt/sumo/bin/python -c "import sumo;print(sumo.SUMO_HOME)")' >> /root/.bashrc
  WORKDIR /work
  ```
  - Build and run on OrbStack:

    ```
    docker build --platform linux/arm64 -t authnet-opp:6.3-inet4.5.4-veins5.3.1 .
    docker run --rm -v "$PWD":/work authnet-opp:6.3-inet4.5.4-veins5.3.1 bash -ic '...'
    ```
  - Inside the container, the AuthNet commands are the same as the native block, with setenv at `/opt/omnetpp-6.3.0`.
  - `mv inet4.5*` hedges the INET tarball's top-level directory name, which I have not checked.
  - This is the most reproducible Veins setup on this Mac; **(est.)** 30-45 min first build, ~4-6 GB image.

**What I would not do:**
- amd64 official images under Rosetta for new work (slower, Rosetta sunset risk). Use them only for an exact-6.0.3 cross-check.
- opp_env on macOS (Nix system install, no macOS CI).
- OMNeT++ 6.0.3/6.1.0 natively (needs the `hypot` patch).

## Sources

- OMNeT++ downloads: https://omnetpp.org/download/ and https://omnetpp.org/download/old (6.x release dates, macos-aarch64 packages, 6.4.0 checksums, container tag).
- OMNeT++ 6.4.0 announcement: https://omnetpp.org/software/2026/05/08/omnet-640-released.html
- OMNeT++ sources at tag `omnetpp-6.4.0`: `doc/src/installguide/ch-macos.rst`, `install.sh`, `setenv`, `configure.in` (bison >= 3.0; LLD not used on macOS), `configure.user.dist`, `Makefile` (`base` target), `WHATSNEW.md`, `python/requirements.txt`, `releng/dockerfiles/omnetpp/Dockerfile`, `include/omnetpp/{cmessage,csimplemodule,cpar}.h`. Also `src/common/exprnodes.cc` at 6.0.3/6.1.0/6.2.0. https://github.com/omnetpp/omnetpp
- Install Guide PDF (6.2.0): https://doc.omnetpp.org/omnetpp/InstallGuide.pdf
- macOS build issues: https://github.com/omnetpp/omnetpp/issues/1354, /1368, /1395, /1237, /1479
- INET releases: https://github.com/inet-framework/inet/releases (4.5.4, 4.6.0 "Requires OMNeT++ 6.2 or later", 4.7.0 "Requires OMNeT++ 6.4 or later"). Source trees: `src/inet/linklayer/ieee802154/*`, `src/inet/physicallayer/wireless/ieee80211/mode/Ieee80211ModeSet.cc`, `Ieee80211Band.cc`.
- Veins: https://veins.car2x.org/download/ ; https://github.com/sommer/veins (`TraCICommandInterface.cc` versionConfigs at veins-5.3.1 and master; recent master commits)
- SUMO: https://sumo.dlr.de/docs/Installing/index.html , https://sumo.dlr.de/docs/Downloads.php , https://pypi.org/project/eclipse-sumo/ (wheel platforms), https://github.com/DLR-TS/homebrew-sumo , `src/libsumo/TraCIConstants.h` at v1_19..v1_28
- opp_env: https://github.com/omnetpp/opp_env (`INSTALL.md`, `README.md`, `opp_env/database/{omnetpp,inet,veins}.py`, `.github/workflows/*`)
- Docker images: https://github.com/omnetpp/dockerfiles ; ghcr.io registry tags/list and manifests for `omnetpp/omnetpp`, `omnetpp/omnetpp-gui`, `omnetpp/opp_env`
- Rosetta outlook: https://developer.apple.com/forums/thread/787530
