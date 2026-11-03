# Black Book: flags to resolve

Every item tagged `[FLAG Fn]` appears in red in `main.pdf`. Send me the answers, or edit the `.tex` yourself. The file and macro to change are listed for each one.
The second section lists decisions I made where the template or the codebase was ambiguous. Confirm them or tell me what to change.

## A. Information only you can provide (shown in red in the PDF)

| Flag | What is needed | Where it appears | Where to edit |
|---|---|---|---|
| ~~**F1**~~ | **Resolved from the old blackbook draft:** Jay Kerkar 16, Chaitanya Kelkar 15, Chirag Poornamath 26, Yash Kolekar 17 | Title page, certificate, declaration, acknowledgement | `main.tex`: `\RollA` to `\RollD` |
| **F2** | Prefix for each member on the certificate (the template says "Mr/Miss."). I did not guess. | Certificate | `main.tex`, certificate block |
| **F3** | Name and designation of the Deputy HOD (the template's acknowledgement names one) | Acknowledgement | `main.tex`, acknowledgement |
| **F4** | Designation of Dr. Shanta Sondur (e.g. Assistant/Associate Professor). Also confirm whether the certificate should read "Dr." or "Prof." (template: "Prof. Guide Name") | Acknowledgement, certificate | `main.tex`: `\GuideName` and acknowledgement |
| **F5** | Links (DOI/URL) for literature papers 2–7 (Weis 2003, Ohkubo 2003, Molnar & Wagner 2004, Avoine & Oechslin 2005, Avoine–Dysli–Oechslin 2005, Tsudik 2006). The template asks for a link per paper. They are not in the repo, and I did not want to risk wrong DOIs. **Please also check my summaries of these papers against the PDFs.** They follow the final paper's description and the well-known content of each paper, but the PDFs are not in the repository. | Ch. 2, Section 2.2 | `chapters/ch2_literature.tex` |
| **F6** | Confirm that requirements were refined in review meetings with the guide. If not, delete that sentence. | Ch. 3, Section 3.2 | `chapters/ch3_methodology.tex` |
| **F7** | ESP8266 NodeMCU boards: how many were bought, the cost in ₹, and whether they were bought for the project or already owned. Git history mentions "two ESP8266 boards". | Hardware table 3.3, cost table 3.5 | `chapters/ch3_methodology.tex` |
| **F8** | AWS: an earlier experiment used an AWS instance (commit "AWS t4g.nano data point"). Was any money spent? If ₹0 (free tier), say so. Or tell me to drop the mention, since it is not part of the final work. | Cost table 3.5 | `chapters/ch3_methodology.tex` |
| **F9** | Other expenses (publication or conference fee, printing and binding) and the **total estimated cost** | Cost table 3.5 | `chapters/ch3_methodology.tex` |
| **F10** | **Gantt chart dates.** I took the bars from git commit dates. The resolution study, OMNeT++ ResolveNet, the ProVerif models and the final paper all landed in one commit on 3 Nov (`ec1f65b`), so their real start/end dates are **not** recoverable. I show them as a single 3 Nov milestone. Please give me the actual start and end dates for each activity, plus any work done before the repo was created on 25 Aug (e.g. topic selection in July). If the department wants planned and actual bars, give me the plan as well. | Ch. 3, Figure 3.2 (and timeline Figure 3.10) | `chapters/ch3_methodology.tex`, `ganttchart` block |
| **F11** | Specs of the team laptops (CPU, RAM, OS), especially the machine used for the original OMNeT++ and ProVerif runs. Git history suggests a Mac but does not record the specs. | Hardware table 3.3 | `chapters/ch3_methodology.tex` |
| **F12** | Publication details: venue, submission/acceptance status, camera-ready/published PDF, certificate of presentation. The repo calls the paper an "unpublished manuscript". | Appendix A.I | `chapters/ch5_conclusion.tex` |
| **F13** | Plagiarism report (attach as PDF/image) | Appendix A.I | `chapters/ch5_conclusion.tex` |
| **F14** | Any registered copyright or patent. If none, I will write "None" and drop the flag. The code itself is Apache-2.0. | Appendix A.II | `chapters/ch5_conclusion.tex` |

**Checked against the old blackbook draft** (commit `4462493` on the backup branch): it was written for the earlier audit paper, so only student details were reused (the F1 roll numbers). Its project-specific content (PRD, mentor conditions, hardware, AWS) belongs to the old paper and was not used. It did not contain answers to the other flags.

## B. Decisions I made: confirm or correct

1. **Template conflicts.** The template's Contents page and its body pages disagree. I followed the **Contents page** (the "index"), as the README of the revised LaTeX template also does:
   - Ch. 4 has **4.5 Limitations** (implementation-level). Ch. 5 is **5.1 Limitations, 5.2 Conclusion, 5.3 Future Scope**.
   - The body page's "5.3 Published Paper" is covered by **Appendix A.I Publication Details**.
   - Section 3.2 uses the index's subsections (Functional / Non Functional / User Requirements). The "requirement gathering approach" from the body page is the text of 3.2 itself.
   - The heading is **"References"** (Contents page), not "Bibliography" (body page). References are in IEEE style, as the paper uses.
2. **Template text kept verbatim**, even where it looks odd. Tell me if any of these should be changed:
   - Title page: "[TITLE] / ON / Submitted in partial fulfillment…" (the "ON" is as in the template).
   - Certificate: "Fourth Year (Sem. VI-Sem.VII)". This may be a template typo. Should it be Sem. VII–VIII?
   - Declaration: first-person singular text, as in the template. I added **four** signature blocks, one per member, instead of one.
   - The acknowledgement is lightly reworded from the template's wording, with real names filled in.
3. **Title and running header.** The project title is the final paper's title. The header ("Project Title" in the template) uses a short title, *Pseudonym Resolution in Two-Message IoT Authentication* (the README heading), because the full title does not fit on one line. Change `\ShortTitle` in `main.tex` if you prefer something else.
4. **Fonts.** The template uses Georgia (headings) and Times New Roman (body). Neither font is installed on this machine, and they cannot be redistributed. I bundled **Gelasio** (metric-compatible with Georgia) and **Liberation Serif** (metric-compatible with Times New Roman), both SIL OFL, in `fonts/`. Spacing and line breaks match the original fonts. To use the real fonts, change the three `\setmainfont` / `\newfontfamily` lines in `main.tex`.
5. **Logos** (University of Mumbai, VESIT, VES banner) were extracted at full resolution from `Capstone_BB Format_2026-27.docx.pdf` and are in `images/`.
6. **Literature survey.** I reviewed the seven papers the **final paper** builds on: the base protocol plus six RFID private-identification papers. The repo's reference catalogue also lists 19 IoT-authentication papers from your *earlier* literature review, marked "not used in final evaluation". Do you want some of them added to Chapter 2? The minimum is 5, so this is optional.
7. **Hardware claim.** The report says the ESP8266 port exists and runs the device side (firmware, host build and interop are in the repo). It does **not** claim any on-board timing results, because the final paper reports none. Confirm that the board demo was actually run, or tell me to describe it as "supported but not demonstrated".

## C. What was run vs. taken from the repository (no numbers were invented)

Re-run on 3 Nov 2026 on this machine (logs in `results/`):
- `pytest`: **125 passed**, coverage 96% of `protocol/` and `crypto/`
- C device core vs. reference vectors: **15 checks, 0 failed**
- C core vs. Python server (`interop.py -n 5`): **5/5 handshakes, keys agree, replay rejected**
- `desync_check.py`: identical to the committed output (lockout at 8 drops)
- `resolution_costs.py` (in a scratch copy): every non-TM row of `measured.csv` identical to the committed file. TM rows differ slightly, which is expected and documented (OS randomness). The report uses the committed data, as the paper does.
- `paper/make_figs.py`: regenerated figures, `table_ranked.tex` and `summary.json` **identical** to the committed files
- CLI demo (`hea-ta`, `hea-server`, `hea-device`, replay): output used in Listing 4.5. The server ran on port 18443 instead of 8443.

**Not** re-run (tools not installed here). The committed outputs are used and labelled as such in Section 4.1:
- OMNeT++ 6.4 sweep (`evaluation/resolution/sim/results.csv`, 960 runs)
- ProVerif 2.05 models (`evaluation/formal_verification/logs/`)

## D. Housekeeping done during `git pull`

`origin/main` had been **force-pushed** (rewritten history), so a plain `git pull` could not merge. I saved your old local `main` (87 commits) as branch **`backup/local-main-before-pull-2026-11-03`** and then reset `main` to `origin/main` (`e21993a`). Untracked files (template, `paper_repro/`, `bench_output/`, PDFs in `docs/`) were not touched. Delete the backup branch once you no longer need it.
