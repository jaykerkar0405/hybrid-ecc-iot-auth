#!/usr/bin/env python3
# Copyright (c) 2026 Jay Kerkar, Chaitanya Kelkar, Chirag Poornamath, Yash Kolekar and Shanta Sondur
# SPDX-License-Identifier: Apache-2.0
"""Build spin2027-source.zip (camera-ready sources: flattened main.tex and body.tex, figures, refs.bib, main.bbl, llncs.cls,
splncs04.bst). Run from the repository root after producing main.bbl: python -I paper/springer/make_source_zip.py.
Reuses the flattener of paper/arxiv/make_package.py; the shared sources are not modified."""
import importlib.util
import re
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("mp", HERE.parent / "arxiv/make_package.py")
mp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mp)
mp.VALUES.update({"ifshortpaper": True, "iffv": True, "ifanonymous": False, "ifspringer": True, "ifbibtexrefs": True})


def clean(text):
    text = mp.strip_comments(text)
    for pat in (r"^\\ifdefined\\(CAMERA|NOFV)\\[a-z]+\\fi\n", r"^\\(anonymous|bibtexrefs|shortpaper)true\n"):
        text = re.sub(pat, "", text, flags=re.M)
    return mp.clean(text)


def main():
    files = {
        "main.tex": clean((HERE / "main.tex").read_text().replace("\\input{../body.tex}", "\\input{body.tex}")),
        "body.tex": clean((HERE.parent / "body.tex").read_text().replace("\\bibliography{../refs}", "\\bibliography{refs}")),
        "figs/table_ranked.tex": clean((HERE / "figs/table_ranked.tex").read_text()),
    }
    binary = {f"figs/fig_{n}.pdf": (HERE / f"figs/fig_{n}.pdf").read_bytes() for n in ("latency", "probes", "storage")}
    binary["refs.bib"] = (HERE.parent / "refs.bib").read_bytes()
    binary["main.bbl"] = (HERE / "main.bbl").read_bytes()
    binary["llncs.cls"] = (HERE / "llncs.cls").read_bytes()
    binary["splncs04.bst"] = (HERE / "splncs04.bst").read_bytes()
    with zipfile.ZipFile(HERE / "spin2027-source.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(list(files) + list(binary)):
            zi = zipfile.ZipInfo(name, date_time=(2026, 11, 15, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            z.writestr(zi, files[name] if name in files else binary[name])
            print(name)


if __name__ == "__main__":
    main()
