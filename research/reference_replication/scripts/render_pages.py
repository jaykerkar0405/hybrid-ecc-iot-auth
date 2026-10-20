#!/usr/bin/env python3
"""Rasterise the pages that carry the tables we need, at 300 DPI, so values can be read visually.
Usage: render_pages.py [--all]   (default: only pages listed in PAGES)"""
import sys
from pathlib import Path
import pymupdf as fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
SRC = {
    "BASE": REPO / "docs/references/base_paper.pdf",
    "JIANG": REPO / "docs/references/chaotic_maps_three_factor_authentication.pdf",
    "DHILLON": REPO / "docs/references/lightweight_biometrics_remote_user_authentication_for_iot.pdf",
    "CHANGLE": REPO / "docs/references/provably_secure_authentication_for_ad_hoc_wsn.pdf",
    "OURS": REPO / "paper/main.pdf",
}
OUT = ROOT / "work/png"

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for k, p in SRC.items():
        doc = fitz.open(p)
        print(f"{k}: {p.name}: {doc.page_count} pages")
        for i, page in enumerate(doc, 1):
            txt = page.get_text()
            tags = [t for t in ("TABLE", "Table 2", "Table 3", "Table 4", "TABLE II", "TABLE III") if t in txt]
            print(f"   p{i}: {len(txt)} chars  {tags}")
            if "--all" in sys.argv or tags or k in ("CHANGLE",):
                page.get_pixmap(dpi=300).save(OUT / f"{k}_p{i}.png")

if __name__ == "__main__":
    main()
