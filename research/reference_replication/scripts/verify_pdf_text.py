#!/usr/bin/env python3
"""Check that the key strings behind data/extracted.yaml are present on the cited PDF pages (text layer).
The CHANGLE tables are images and are covered by the visual read documented in REPORT.md instead; their surrounding text is checked here."""
import re
import unicodedata
import sys
import pymupdf
from common import REPO, RESULTS, write_csv

DOCS = REPO / "docs" / "references"
CHECKS = [  # (paper, pdf_page, regex on whitespace-normalised text, what)
    ("JIANG", "chaotic_maps_three_factor_authentication.pdf", 15, r"21T\s*H\s*\+\s*6T\s*C", "Table 2 overall cost, Jiang scheme"),
    ("JIANG", "chaotic_maps_three_factor_authentication.pdf", 15, r"1312 bits", "Table 2 communication, 1312 bits"),
    ("JIANG", "chaotic_maps_three_factor_authentication.pdf", 15, r"32\.40 ms", "T_C constant"),
    ("JIANG", "chaotic_maps_three_factor_authentication.pdf", 15, r"0\.20 ms", "T_H constant"),
    ("DHILLON", "lightweight_biometrics_remote_user_authentication_for_iot.pdf", 11, r"Turkanovic et al\. \[26\]\s+7T h\s+5T h\s+7T h", "Table 3 Turkanovic row"),
    ("DHILLON", "lightweight_biometrics_remote_user_authentication_for_iot.pdf", 12, r"128 bits", "hash size"),
    ("CHANGLE", "provably_secure_authentication_for_ad_hoc_wsn.pdf", 8, r"0\.063075", "t_mul"),
    ("CHANGLE", "provably_secure_authentication_for_ad_hoc_wsn.pdf", 9, r"0\.0005 seconds", "t_h"),
    ("CHANGLE", "provably_secure_authentication_for_ad_hoc_wsn.pdf", 9, r"approximately 14 times faster", "14x claim"),
    ("BASE", "base_paper.pdf", 9, r"\[14\] C\. Wang.*VANETs", "ref [14] is the VANET paper"),
    ("BASE", "base_paper.pdf", 9, r"\[15\] D\. Wen.*edge artificial intelligence", "ref [15] is the Wen et al. paper"),
    ("BASE", "base_paper.pdf", 9, r"\[16\] Q\. Jiang.*chaotic maps", "ref [16] is the Jiang chaotic-maps paper"),
]


def run():
    rows, ok_all = [], True
    cache = {}
    for paper, fn, page, rx, what in CHECKS:
        doc = cache.setdefault(fn, pymupdf.open(DOCS / fn))
        txt = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", doc[page - 1].get_text()))
        ok = re.search(rx.replace(r"\s+", r"\s*"), txt, re.S) is not None
        ok_all &= ok
        rows.append((paper, page, what, "FOUND" if ok else "NOT FOUND"))
    return ok_all, rows


if __name__ == "__main__":
    ok, rows = run()
    write_csv(RESULTS / "pdf_text_checks.csv", ["paper", "pdf_page", "what", "status"], rows)
    for r in rows:
        print(r)
    sys.exit(0 if ok else 1)
