# Paper sources

One shared source, three venue builds. Content lives in `body.tex`; `ieee/`, `springer/` and `arxiv/` hold only a wrapper
(template, macros, author block) and their outputs. Numbers come from `figs/summary.json` and `figs/table_ranked.tex`,
written by `make_figs.py` from the committed evaluation data.

| Build | Build command (run in the folder) | Notes |
|---|---|---|
| `ieee/` | `pdflatex main.tex` (3 passes) | IEEE conference, US Letter. Variants: `pdflatex "\def\NOFV{}\def\ANON{}\input{main}"` |
| `springer/` | `pdflatex main; bibtex main; pdflatex main; pdflatex main` | SPIN 2027, `llncs` v2.25. Review build is the default; `\def\CAMERA{}` gives the camera-ready. `make_source_zip.py` builds the source zip |
| `arxiv/` | `xelatex main.tex` (2 passes) | Preprint, A4. `make_package.py` builds `arxiv-submission.tar.gz` |

Figures: `python -I paper/make_figs.py` (IEEE size) writes `figs/`. The single-column builds use
`--width 4.803 --hscale 0.95 --out paper/springer/figs` (Springer) and `--width 4.803 --stack --out paper/arxiv/figs` (arXiv).

Switches in the wrappers: `\iffv` (formal-verification material), `\ifanonymous`, `\ifspringer` (single-column floats),
`\ifbibtexrefs`, `\ifshortpaper` (Springer page-limit cuts only). `refs.bib` is used by the Springer build; the IEEE and
arXiv builds use the inline list in `body.tex`.

`vendor/` holds the checksum record of Springer's official proceedings package (`provenance.json`); `submission-evidence/` holds
the venue screenshots and reference-metadata checks.

## Springer class file (not in the repository)

`springer/llncs.cls` is not tracked: its files state no redistribution terms. Download Springer's proceedings package
(URL and SHA-256 checksums in `vendor/springer-proceedings-2026-11-15/provenance.json`), unpack it, and put `llncs.cls`
(v2.25, 2026/09/03) into `springer/`. Check it with `sha256sum springer/llncs.cls` against the `provenance.json` entry
before building. `splncs04.bst` (LPPL) is tracked.
