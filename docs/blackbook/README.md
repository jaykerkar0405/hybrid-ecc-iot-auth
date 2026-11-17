# Capstone Black Book (AY 2026-27)

Black Book for _Pseudonym Resolution and Formal Verification of an Unlinkable Two-Message IoT Authentication Protocol_. It follows the department format in `Capstone_BB Format_2026-27.docx.pdf`, with the same logos, running header and chapter divider pages.

| Path        | Content                                                                                       |
| ----------- | --------------------------------------------------------------------------------------------- |
| `main.tex`  | Preamble, title page, certificate, declaration, abstract, contents, lists and acknowledgement |
| `chapters/` | Chapters 1–5, references and appendix                                                         |
| `main.pdf`  | Compiled report                                                                               |
| `figures/`  | Evaluation figures, regenerated from the committed data with `paper/make_figs.py`             |
| `reports/`  | Turnitin similarity and AI writing detection reports for the project paper, embedded in the appendix |
| `publication/` | Submitted SPIN 2027 review manuscript and submission record for Appendix A.I             |
| `ipr/`      | Submitted copyright Form XIV for the software, reproduced in Appendix A.II                   |
| `images/`   | Logos extracted from the format PDF                                                           |
| `fonts/`    | Gelasio (Georgia-compatible) and Liberation Serif/Mono (Times/Courier-compatible), SIL OFL    |
| `results/`  | Logs of the runs made for this report (tests, C vectors, interop, desync, probe sweep, demo)  |

The hardware section records the confirmed MacBook configuration used for the original OMNeT++ and ProVerif runs, separately from the Linux machine used for the report's re-runs.

The paper was submitted to **SPIN 2027** through Microsoft CMT on **15 November 2026 at 23:21:57 IST (17:51:57 GMT)**, paper ID **307**, CMT track **SPIN2027**. The status is **Submitted**; under-review status and acceptance are unconfirmed. Appendix A.I reproduces the [submitted review manuscript](publication/spin2027-review.pdf), labelled **Submitted manuscript — publication pending**. The [submission record](publication/submission-record.md) preserves the team-provided acknowledgement details and links to the official conference information. The original acknowledgement email/PDF has not yet been archived.

The copyright application for the software was submitted on **17 November 2026**, diary number **SW-53605/2026-CO**; registration is pending. The original Form XIV is saved as [ipr/form-xiv-sw-53605-2026-co.pdf](ipr/form-xiv-sw-53605-2026-co.pdf). It names the work _hybrid-ecc-iot-auth Reference Implementation and Evaluation Framework for an Unlinkable Two-Message IoT Authentication Protocol_ and records a ₹500 application fee. Appendix A.II includes the form's eleven nonblank pages; the archived PDF preserves all twelve original pages.

Section 3.8 budgets **₹6,500 plus GST on conference registration**: ₹500 for the copyright application, ₹1,000 for printing and binding (₹250 per member, four members), and ₹5,000 plus GST for one SPIN 2027 regular Indian student registration, subject to acceptance. An equal split is ₹1,625 per member plus one-fourth of the registration GST. The [official registration page](https://conferences.amity.edu/SPIN2027/registration.aspx) specifies GST extra without a percentage; its amount will follow the organiser's invoice. Printing and registration remain estimates. Extra registrations, travel and accommodation would be added if required by the team's participation arrangements.

The remaining submission details are:

- Original submission acknowledgement email/PDF, acceptance details, the final paper, presentation schedule/mode and certificate, and final publication details when available.
- Final registration invoice/GST amount and actual printing/binding costs when paid; the estimated costs and total are recorded in Section 3.8.
- Certificate completion: external examiner's name, date, place, signatures and college seal, as required by the department.

## Build

The report needs **XeLaTeX**. On Overleaf, upload this folder and set _Menu → Compiler → XeLaTeX_. Locally:

```sh
xelatex main && xelatex main && xelatex main
```

On minimal TeX installations without Latin Modern OpenType, `tex-text.tec` or `pzdr.tfm`, install the missing TeX Live font packages. The preamble already includes a fallback for Latin Modern.
