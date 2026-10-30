# Figure values extracted from the base paper (Figs. 1-3)

`fig_targets.json` holds the bar heights of Figs. 1-3 of Al-Rasheed et al. (IEEE TCE 72(2), 2026), produced by
`extract_figs.py`.

## Method

The three charts are vector graphics embedded in the PDF (Form XObjects `Im5`, `Im7`, `Im9` on PDF pp. 6-8). The script reads
their drawing instructions with `pikepdf`, calibrates the y-axis by least squares on the tick marks, and takes each bar's top
edge from the vector path. Nothing is read from a rendered image, so these values are **not** eyeball readings.

This supersedes the values in `research/paper_audit/figures_audit.py`, which were read by eye from 600-DPI renders (error
about ±0.2 for Figs. 1-2). The ±0.2 figure does not apply to this file.

## Precision (from `precision` and `delta_vs_eyeball` in the JSON)

| Figure | Value resolution | Largest y-tick residual | Largest difference from the eyeball reading | Axis |
|---|---|---|---|---|
| Fig. 1 | 0.038 | 0.017 | 0.117 | Communication Overhead (%) |
| Fig. 2 | 0.014 | 0.008 | 0.026 | Communication Cost (bits) |
| Fig. 3 | 0.00014 | 0.00004 | 0.0001 | Storage Overhead (%) |

The eyeball readings were within their own ±0.2 error of these values, as expected.

## Limits

- Fig. 1 bars that reach the axis top (100) are flagged `censored`: the software truncated them, so the true value is at least
  100 and the raw height is not in the file. They are excluded from fits.
- Series order and colours were matched from the legend; the script checks the colour counts.
- The extraction describes the figures as drawn. It says nothing about how the plotted numbers were obtained.

## Reproduce

```sh
pip install pikepdf
python -I research/omnet_emulation/targets/extract_figs.py docs/references/base_paper.pdf out.json
```

Re-running it reproduces `series` and `censored` for all three figures exactly (checked 2026-10-30). The same holds for
`../jan_compare/jan_extract.py` and `jan_targets.json`.
