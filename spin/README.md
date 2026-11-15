# SPIN 2027 submission version (Springer LNEE, `llncs`)

Same paper as `../paper/` (IEEE version), re-formatted for SPIN 2027 per its
[submission guidelines](https://conferences.amity.edu/SPIN2027/Paper-Submission-Guidelines.aspx) and Springer's
proceedings instructions (`llncs.cls` and `splncs04.bst` are Springer's official files, v2.25).

Build (from this folder): `pdflatex main && bibtex main && pdflatex main && pdflatex main`.
Figures: `python -I make_figs.py` (writes `figs/`, reads `../evaluation/resolution`).

| Requirement | How it is met |
|---|---|
| Springer conference template, one column | `llncs` class, Times via `newtxtext`/`newtxmath` as in Springer's sample |
| 8-15 pages | 13 pages (A4) |
| Blind review: no names/affiliations | `authors.tex` is anonymous; no repository link in the text |
| No own page numbers | `\pagestyle{empty}` |
| Springer reference format | BibTeX `splncs04`, entries in `refs.bib` |
| No password protection | none |
| Figures: alt text, vector, >= 6 pt | `\Description` on all figures, PDF vector figures |
| Table captions above, figure captions below | yes |

Camera-ready (after acceptance): in `main.tex` replace `\input{authors.tex}` with
`\input{authors_camera_ready.tex}`, mark one corresponding author with `\Envelope` (`bbding`), add the repository link
back in the Conclusion, and send Springer all sources (`main.tex`, `body.tex`, `refs.bib`, `figs/`, class and bst
files) plus the PDF.
