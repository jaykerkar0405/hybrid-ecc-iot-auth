# Poster

Poster for _Pseudonym Resolution and Formal Verification of an Unlinkable Two-Message IoT Authentication Protocol_
(BE, D20A, project 4). Size 3648 x 4416 px (1824 x 2208 CSS px at 2x). Theme: white background, indigo `#382bad`.

| File | Purpose |
|---|---|
| `BE-D20A-4-Pseudonym Resolution ... Protocol.png` / `.pdf` | The finished poster (the PDF keeps selectable text) |
| `app/src/App.tsx` | All poster text, tables and layout |
| `app/src/components/ui/` | shadcn/ui components used (`card`, `table`, `badge`, `separator`, `alert`), downloaded with `npx shadcn@latest add` |
| `app/src/index.css` | Indigo theme (shadcn CSS variables) |
| `app/src/assets/` | VESIT logo (`docs/blackbook/images/vesit_logo.png`) and the latency chart |
| `make_charts.py` | Redraws the latency chart from `evaluation/resolution/` (same data as `paper/make_figs.py`) |
| `build.py` | Builds the app and renders the PNG and PDF with headless Chrome or Edge |

Every number on the poster comes from `paper/body.tex`, `paper/figs/` and the logs in `evaluation/`.

## Rebuild

From the repository root (needs Node.js and Chrome or Edge):

```
cd docs/poster/app && npm install      # once
cd ../../..
python -I docs/poster/make_charts.py   # only if the data changed
python -I docs/poster/build.py         # writes the PNG and PDF here; prints the per-column overflow check (must be <= 0)
```
