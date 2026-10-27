#!/usr/bin/env python3
"""Build proposed_patches/ours_main_tex.diff by editing a COPY of paper/main.tex in work/. The original is never modified."""
import difflib
import shutil
from common import REPO, ROOT

SRC = REPO / "paper" / "main.tex"
DST = ROOT / "work" / "main.tex.proposed"
OUT = ROOT / "proposed_patches" / "ours_main_tex.diff"

EDITS = [
    # (old, new, reason)
    (r"roughly 120--3\,000$\times$ cheaper than the ECC-based schemes",
     r"roughly 60--2\,500$\times$ cheaper than the ECC-based schemes",
     "C2: like-for-like ratios over both AES implementations are 60x (Sadhukhan, aes_ct) to 2,520x (Poorambage, aes_big)"),
    (r"i.e.\ about 120--3\,000$\times$ more.",
     r"i.e.\ about 60--2\,500$\times$ more (the range spans the two AES implementations).",
     "C2"),
    (r"three hash-only schemes cost 6.1, 7.0 and 7.0~ms (all roles).",
     r"three hash-only schemes cost 6.1, 7.0 and 7.0~ms (all roles): Turkanovic, Dhillon--Karla and the row that Table~V labels ``Jiang''.",
     "F8/F13: name which rows are meant"),
    (r"""\item \textbf{The figures are inconsistent.}""",
     r"""\item \textbf{Row labels and references do not match.} In Tables~IV--V the rows labelled Cheng--Le~[14], Jiang~[15] and Shuai~[16] carry reference numbers that point to a VANET paper, to an edge-AI magazine article and to the chaotic-maps scheme of Jiang et al.~\cite{jiang}, respectively. The Turkanovic row lists 7/7/5 hash operations for user/device/server, whereas Chang and Le~\cite{changle} (Table~II) and Dhillon and Kalra~\cite{dhillon} (Table~3) both give 7/5/7; the Cheng--Le row equals the ECC protocol $\mathcal{P}_2$ of~\cite{changle} with the user and gateway hash counts exchanged. Jiang et al.~\cite{jiang} cost their scheme at $21T_H+6T_C$ with $T_C=32.40$~ms and $T_H=0.20$~ms (Table~2), whereas Table~III of~\cite{base} sets $T_C=T_H=0.32$~ms and no row of Table~V uses $T_C$.
\item \textbf{The figures are inconsistent.}""",
     "new audit item: findings F1, F4, F5, F7, F8, F9, F11"),
    (r"""\textbf{Against the hash-only schemes} (Turkanovic, Dhillon--Karla, Jiang) the outcome""",
     r"""\textbf{Against the hash-only schemes} (Turkanovic, Dhillon--Karla and the row that Table~V labels ``Jiang'') the outcome""",
     "F13"),
    (r"""against $5$--$7\,T_H$ for the hash-only device columns, so""",
     r"""against $5$--$7\,T_H$ for the hash-only device columns ($5$ and $6\,T_H$ for the two schemes we could check against their original papers), so""",
     "C9"),
    (r"""Competitor costs use the operation counts of~\cite{base}, which we did not verify against the original papers; $T_C$ and $T_{fe}$ were not measured.""",
     r"""Competitor costs use the operation counts of~\cite{base}. We checked the Turkanovic and Dhillon--Karla rows against~\cite{changle,dhillon} (the Turkanovic device and server columns are swapped in~\cite{base}); the rows labelled Cheng--Le, Jiang and Shuai could not be traced to their cited sources, and the chaotic-map scheme of~\cite{jiang} is not hash-only: costed as published ($11\,T_H+6\,T_C$ for login plus authentication) it is cheaper than the proposed scheme only if $T_C$ is below roughly 0.1--5\,ms, against 32.40\,ms in~\cite{jiang}. $T_C$ and $T_{fe}$ were not measured.""",
     "F7, F13, C3"),
    (r"""\bibitem{challa}""",
     r"""\bibitem{changle} C.-C. Chang and H.-D. Le, ``A provably secure, efficient, and flexible authentication scheme for ad hoc wireless sensor networks,'' \emph{IEEE Trans. Wireless Commun.}, vol.~15, no.~1, pp.~357--366, Jan. 2016.
\bibitem{challa}""",
     "new reference"),
]


def main():
    with open(SRC, encoding="utf8", newline="") as f:
        text = f.read()
    new = text
    for old, rep, why in EDITS:
        old_n = old.replace("\n", "\r\n") if "\r\n" in text else old
        rep_n = rep.replace("\n", "\r\n") if "\r\n" in text else rep
        assert new.count(old_n) == 1, f"edit target not unique/found: {why}: {old[:60]}"
        new = new.replace(old_n, rep_n)
    DST.parent.mkdir(parents=True, exist_ok=True)
    with open(DST, "w", encoding="utf8", newline="") as f:
        f.write(new)
    d = difflib.unified_diff(text.splitlines(True), new.splitlines(True), "a/paper/main.tex", "b/paper/main.tex", n=1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf8", newline="") as f:
        f.writelines(d)
    print("wrote", OUT, "(", len(EDITS), "edits ); original untouched")


if __name__ == "__main__":
    main()
