# Capstone Black Book (AY 2026-27)

Black Book for _Pseudonym Resolution and Formal Verification of an Unlinkable Two-Message IoT Authentication Protocol_. It follows the department format in `Capstone_BB Format_2026-27.docx.pdf`, with the same logos, running header and chapter divider pages.

| Path        | Content                                                                                       |
| ----------- | --------------------------------------------------------------------------------------------- |
| `main.tex`  | Preamble, title page, certificate, declaration, abstract, contents, lists and acknowledgement |
| `chapters/` | Chapters 1–5, references and appendix                                                         |
| `main.pdf`  | Compiled report                                                                               |
| `figures/`  | Evaluation figures, regenerated from the committed data with `paper/make_figs.py`             |
| `reports/`  | Turnitin similarity and AI writing detection reports for the project paper, embedded in the appendix |
| `ipr/`      | Submitted copyright Form XIV for the software, reproduced in Appendix A.II                   |
| `images/`   | Logos extracted from the format PDF                                                           |
| `fonts/`    | Gelasio (Georgia-compatible) and Liberation Serif/Mono (Times/Courier-compatible), SIL OFL    |
| `results/`  | Logs of the runs made for this report (tests, C vectors, interop, desync, probe sweep, demo)  |

The hardware section records the confirmed MacBook configuration used for the original OMNeT++ and ProVerif runs, separately from the Linux machine used for the report's re-runs.

The copyright application for the software was submitted on **17 November 2026**, diary number **SW-53605/2026-CO**; registration is pending. The original Form XIV is saved as [ipr/form-xiv-sw-53605-2026-co.pdf](ipr/form-xiv-sw-53605-2026-co.pdf). It names the work _hybrid-ecc-iot-auth Reference Implementation and Evaluation Framework for an Unlinkable Two-Message IoT Authentication Protocol_ and records a ₹500 application fee. Appendix A.II includes the form's eleven nonblank pages; the archived PDF preserves all twelve original pages.

The remaining submission details are:

- Publication venue and submission/acceptance details, the final paper and the presentation certificate when available.
- Publication, printing and binding expenses, and the overall estimated total.
- Certificate completion: external examiner's name, date, place, signatures and college seal, as required by the department.

## Build

The report needs **XeLaTeX**. On Overleaf, upload this folder and set _Menu → Compiler → XeLaTeX_. Locally:

```sh
xelatex main && xelatex main && xelatex main
```

On minimal TeX installations without Latin Modern OpenType, `tex-text.tec` or `pzdr.tfm`, install the missing TeX Live font packages. The preamble already includes a fallback for Latin Modern.
