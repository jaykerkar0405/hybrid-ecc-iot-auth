# Capstone Black Book (AY 2026-27)

Black Book for *Pseudonym Resolution and Formal Verification of an Unlinkable Two-Message IoT Authentication Protocol*. It follows the department format in `Capstone_BB Format_2026-27.docx.pdf`, with the same logos, running header and chapter divider pages.

| Path | Content |
|---|---|
| `main.tex` | Preamble, title page, certificate, declaration, abstract, contents, lists and acknowledgement |
| `chapters/` | Chapters 1–5, references and appendix |
| `main.pdf` | Compiled report |
| `flags.md` | Items to resolve (shown as red `[FLAG Fn]` in the PDF) and decisions to confirm |
| `figures/` | Evaluation figures, regenerated from the committed data with `paper/make_figs.py` |
| `images/` | Logos extracted from the format PDF |
| `fonts/` | Gelasio (Georgia-compatible) and Liberation Serif/Mono (Times/Courier-compatible), SIL OFL |
| `results/` | Logs of the runs made for this report (tests, C vectors, interop, desync, probe sweep, demo) |

## Build

The report needs **XeLaTeX**. On Overleaf, upload this folder and set *Menu → Compiler → XeLaTeX*. Locally:

```sh
xelatex main && xelatex main && xelatex main
```

On minimal TeX installations without Latin Modern OpenType, `tex-text.tec` or `pzdr.tfm`, install the missing TeX Live font packages. The preamble already includes a fallback for Latin Modern.
