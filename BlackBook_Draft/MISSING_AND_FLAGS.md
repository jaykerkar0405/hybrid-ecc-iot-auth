# Black Book draft (v2): what's missing and what needs checking

**v2 (27 Oct 2026)** was rebuilt after pulling 71 commits: the ESP8266 firmware,
the paper audit, the reference replication with OMNeT++, the AWS field test,
the team's IEEE manuscript, and `CITATION.cff`. The book now presents the
project as it is in the repo: an implementation followed by a measurement-based
audit of the base paper.

`main.tex` keeps the template's preamble and section order. Gaps appear as red
**[MISSING: …]** text in the PDF; items to confirm appear as orange **[VERIFY: …]** text.

## How to build

Upload `main.tex`, `references.bib` and `figures/` to Overleaf. Compile with
pdfLaTeX → BibTeX → pdfLaTeX ×2.

My local test build has no errors, no undefined references and 27 references
resolved, and is 61 pages long. It used Computer Modern and `ieeetr` instead of
`newtxtext` and `IEEEtran.bst`, which aren't installed here; Overleaf has both.

The draft adds these packages, all in the marked "DRAFT ADDITIONS" block:
`tikz`, `pgfgantt`, the MISSING/VERIFY macros, and ragged table columns.

## Format PDF elements (added after review)

Taken from `Capstone_BB Format_2026-27.docx.pdf`:
- **Logos** (extracted from that PDF into `figures/logos/`):
  - `mu_emblem.png`: University of Mumbai emblem, used on the title page.
  - `vesit_logo.png`: VESIT logo, used on the title page.
  - `ves_letterhead.png`: VES letterhead, used on the certificate.
- **Title page and certificate** now follow the Format PDF's layout.
- **Running header:** right-aligned, with a rule beneath, on every page from the Declaration onwards.
- **Chapter divider pages:** a "CHAPTER: n / TITLE" page before each chapter.

Please confirm:
- **Running header text:** the Format PDF's placeholder is "Project Title", but the full title doesn't fit on one header line. The header uses the short form "Do the Numbers Hold on Real Hardware?" (`\HeaderTitle`).
- **Principal's name, "Dr. (Mrs.) J. M. Nair":** taken from the Format PDF.
- **Certificate names:** printed without "Mr/Miss". Add the honorifics if the department wants them.

Kept as in the LaTeX template, where it differs from the Format PDF:
- **Declaration wording:** the template's group declaration, not the Format PDF's academic-integrity text.
- **Chapter heading style:** the template's centred style, not the Format PDF's left-aligned style.
- **Reference list title:** "References", not "Bibliography".
- **Section lists:** the template's sections for §3.2, Chapter 4 and Chapter 5, and its appendix headings.

`BlackBook_Draft.pdf` is a local XeLaTeX build with Liberation Serif, a Times-metric substitute, and the `ieeetr` reference style. Overleaf will use the template's Times font and IEEEtran.

## A. Still missing (please provide)

| # | Item | Where |
|---|------|-------|
| 1 | ~~Project title~~ **Done:** set to the paper title ("Do the Numbers Hold on Real Hardware? …") | `\ProjectTitle` |
| 2 | ~~Roll numbers~~ **Done:** Jay Kerkar 16, Chaitanya Kelkar 15, Chirag Poornamath 26, Yash Kolekar 17 | Title page, certificate, declaration |
| 3 | **Deputy HOD** name and designation, and anyone else to thank | Acknowledgement |
| 4 | **Paper status:** venue, submitted/accepted/published, date, DOI; certificate; plagiarism report | Appendix 1 |
| 5 | **Competition certificates**, or "Not applicable" | Appendix 2 |
| 6 | **Hardware ownership** (each laptop, the 2 ESP8266 boards), and the minimum spec if required | §3.6 |
| 7 | **Costs in Rs.:** ESP8266 board price, actual AWS bill, printing/binding/fees, total | §1.6, §3.8 |
| 8 | **Turkanović et al. DOI**, and DOIs for the other papers marked `DOI: MISSING` in `references.bib` | References |

**Now filled from the repo:**
- Student names (from CITATION.cff, README and the paper): Jay Kerkar, Chaitanya Kelkar, Chirag Poornamath, Yash Kolekar.
- Guide (README, paper): Dr. Shanta Sondur.
- Hardware and software, from result files and reports.
- The Gantt chart and timeline, built from commit dates.

## B. Filled from the repo, please confirm

- **Gantt chart and timeline** (§3.4, §3.5.4) are built from **git commit dates** (25 Aug – 27 Oct 2026). Commit dates show when work landed, not when it started. Add planned dates and work before 25 Aug.
- **HOD "Dr. (Mrs.) Shalu Chopra"** comes from the Format PDF. The certificate uses the template's version (guide and HOD only); the Format PDF's version adds External Examiner, Principal and Seal blocks.
- **Requirement gathering (§3.2):** the repo mentions "stakeholders" (PRD) and a "mentor's condition" (FINDINGS.md). Add the actual review meetings and guide inputs.
- **Delta work (§2.3):** the survey planned mobility and revocation extensions, and the manuscript lists revocation as future work. I described the audit as the main contribution. Confirm.
- **Paper 5 (Turkanović):** there's no full text in the repo. The entry relies on secondary sources. Read the original, or swap in another paper.
- **ESP8266 handshake numbers** (12/12 native, 20/20 on the board, 1.67/3.59/5.26 ms, 52 ms over Wi-Fi) are quoted from `paper/main.tex`. There's no raw log in the repo.
- **GitHub Actions "free"** assumes the repo is public. The paper says "all code and raw data are open".
- **The RFC 5869, NIST SP 800-38D and OMNeT++ URL details** came from general knowledge; the rest of each entry is from the repo.

## C. Findings worth knowing (all reported in Chapter 4)

1. **The `reference_data.py` transcription bug is still present after the pull.**
   `hybrid_ecc_auth/bench/baselines/reference_data.py` lists the Proposed server cost as `4*TH+5*TECM` and the Sadhukhan server cost as `2*TH+4*TECM`. These should be `2*TH+2*TSE_D` and `2*TH+4*TSE_D`. `research/paper_audit/paper_tables.py` has the correct values. I didn't change any code.
2. **Three implementation weaknesses** were found in the team's AWS field test (`docs/experiments/aws_demo_2026-09-27/report.html`). The book reports them as limitations.
   - The device epoch is held only in memory, so a restarted device is rejected or locked out.
   - Full-mesh key distribution in `hea-ta enroll` let one device's credential impersonate another device.
   - The block-list and replay window are lost when the server restarts.
3. **The "99.9% processing reduction"** in the benchmark report and the Review 7.1 slides isn't meaningful: it compares a laptop with the paper's embedded constants. The book says so and uses the ratio-based recomputation instead.
4. **The `hea-*` commands aren't installed in `.venv`.** Running `pip install -e .` fixes it.

## D. What I ran for v2

All outputs are in `run_outputs/v2/`. The v1 outputs (`bench_full/`, `demo_run/`, `paper_repro_results/`) are still valid because the package code didn't change, apart from two path comments.

| Command | Result |
|---|---|
| `pytest` (after the pull) | 108 passed, 97 % coverage |
| `research/paper_audit/`: `audit.py`, `figures_audit.py`, `fig1_repro.py`, `eq22_variants.py` (with and without `--rerun`), `no_forward_secrecy.py` | Output matches the committed results (apart from a harmless venv-path warning) |
| `reeval.py` on the BearSSL CSVs | Matches |
| `server_scaling.py` | New data point on this Linux laptop: 19.9 ms at 1,000 devices, 77.6 ms at 5,000 (the Mac gave 4.8 / 23.9 ms) |

**Not run:**
- **The C core's native build and interop test.** The Makefile clones BearSSL from GitHub, and that download and compile was blocked by the permission system. To run it yourself: `make -C firmware/esp8266/host && .venv/bin/python firmware/esp8266/tools/interop.py -n 20`.
- **The replication test suite.** It needs PyYAML, SimPy and PyMuPDF, which aren't installed. I didn't install them.
- **ESP8266, AWS and OMNeT++ runs.** These need the hardware, a cloud account and the toolchain; the committed results are cited instead.
