#!/usr/bin/env python3
# Copyright (c) 2026 Jay Kerkar, Chaitanya Kelkar, Chirag Poornamath, Yash Kolekar and Shanta Sondur
# SPDX-License-Identifier: Apache-2.0
"""Build arxiv-submission.tar.gz from main.tex, ../body.tex and figs/ (run from the repository root:
python -I paper/arxiv/make_package.py). The shared sources are never modified: the package holds flattened copies
(\\iffv, \\ifanonymous, \\ifspringer, \\ifbibtexrefs resolved to the values below, comments removed)."""
import re
import subprocess
import sys
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE / "pkg"
VALUES = {"ifshortpaper": False, "iffv": True, "ifanonymous": False, "ifspringer": True, "ifbibtexrefs": False}
TOKEN = re.compile(r"\\(iffv|ifanonymous|ifspringer|ifbibtexrefs|ifshortpaper|else|fi)(?![A-Za-z])")


def strip_comments(text):
    out = []
    for line in text.split("\n"):
        if re.match(r"^\s*%", line):
            continue
        out.append(re.sub(r"(?<!\\)[ \t]+%[ \t]*\S.*$", "", line).rstrip() if re.search(r"(?<!\\)[ \t]%[ \t]*\S", line) else line)
    return "\n".join(out)


def flatten(text):
    # a conditional alone on its line must not leave a blank line (= a paragraph break) behind
    text = re.sub(r"^[ \t]*(" + TOKEN.pattern + r")[ \t]*\n", lambda m: m.group(1) + "\x01", text, flags=re.M)
    out, stack, pos = [], [], 0
    for m in TOKEN.finditer(text):
        active = all(v for v in stack)
        if active:
            out.append(text[pos:m.start()])
        pos = m.end()
        name = m.group(1)
        if name in VALUES:
            stack.append(VALUES[name])
        elif name == "else":
            stack[-1] = not stack[-1]
        else:
            stack.pop()
    assert not stack, "unbalanced conditionals"
    if all(v for v in stack):
        out.append(text[pos:])
    return "".join(out).replace("\x01", "")


def clean(text):
    text = strip_comments(text)
    for pat in (r"\\newif\\if(fv|anonymous|springer|bibtexrefs|shortpaper)\n", r"\\(fv|springer)true\n", r"\\(anonymous|bibtexrefs|shortpaper)false\n"):
        text = re.sub(pat, "", text)
    text = flatten(text)
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def main():
    if PKG.exists():
        for p in sorted(PKG.rglob("*"), reverse=True):
            p.unlink() if p.is_file() else p.rmdir()
    (PKG / "figs").mkdir(parents=True)
    (PKG / "main.tex").write_text(clean((HERE / "main.tex").read_text().replace("\\input{../body.tex}", "\\input{body.tex}")))
    (PKG / "body.tex").write_text(clean((HERE.parent / "body.tex").read_text()))
    (PKG / "figs/table_ranked.tex").write_text(clean((HERE / "figs/table_ranked.tex").read_text()))
    for n in ("latency", "probes", "storage"):
        (PKG / f"figs/fig_{n}.pdf").write_bytes((HERE / f"figs/fig_{n}.pdf").read_bytes())
    # processor selection documented by arXiv (00README.json): XeLaTeX, top-level file main.tex
    (PKG / "00README.json").write_text('{"process": {"compiler": "xelatex"}, "sources": [{"filename": "main.tex", "usage": "toplevel"}]}\n')
    tar = HERE / "arxiv-submission.tar.gz"
    files = sorted(str(p.relative_to(PKG)) for p in PKG.rglob("*") if p.is_file())
    for f in files:
        assert re.fullmatch(r"[A-Za-z0-9_\-./]+", f), f
    with tarfile.open(tar, "w:gz") as t:
        for f in files:
            ti = t.gettarinfo(str(PKG / f), arcname=f)
            ti.uid = ti.gid = 0
            ti.uname = ti.gname = ""
            ti.mtime = 1763164800  # 2025-11-15, fixed so the archive is reproducible
            ti.mode = 0o644
            with open(PKG / f, "rb") as fh:
                t.addfile(ti, fh)
    print("\n".join(files))


if __name__ == "__main__":
    sys.exit(main())
