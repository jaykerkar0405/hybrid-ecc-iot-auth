#!/usr/bin/env python3
"""Render REPORT.md to REPORT.pdf with ReportLab: title page, table of contents, wrapped tables with repeating headers,
code blocks, page numbers, and the result plots as figures. Handles the small Markdown subset that REPORT.md uses."""
import html
import os
import re
import textwrap

import matplotlib
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, PageBreak, PageTemplate, Paragraph, Preformatted, Spacer,
                                Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

from common import RESULTS, ROOT

FONT_DIR = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
for name, f in (("DV", "DejaVuSans.ttf"), ("DV-B", "DejaVuSans-Bold.ttf"), ("DV-I", "DejaVuSans-Oblique.ttf"),
                ("DV-BI", "DejaVuSans-BoldOblique.ttf"), ("DVM", "DejaVuSansMono.ttf"), ("DVM-B", "DejaVuSansMono-Bold.ttf")):
    pdfmetrics.registerFont(TTFont(name, os.path.join(FONT_DIR, f)))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-BI")
pdfmetrics.registerFontFamily("DVM", normal="DVM", bold="DVM-B", italic="DVM", boldItalic="DVM-B")

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
CONTENT_W = PAGE_W - 2 * MARGIN
INK, MUTED, ACCENT, RULE, HEAD_BG, ZEBRA = (colors.HexColor(c) for c in ("#1f2328", "#59636e", "#0b5cab", "#c9d1d9", "#e6edf5", "#f6f8fa"))

S = {
    "title": ParagraphStyle("title", fontName="DV-B", fontSize=21, leading=26, textColor=INK, spaceAfter=6),
    "subtitle": ParagraphStyle("subtitle", fontName="DV", fontSize=10.5, leading=15, textColor=MUTED, spaceAfter=14),
    "h2": ParagraphStyle("H2", fontName="DV-B", fontSize=14, leading=18, textColor=ACCENT, spaceBefore=16, spaceAfter=6, keepWithNext=1),
    "h3": ParagraphStyle("H3", fontName="DV-B", fontSize=11, leading=14.5, textColor=INK, spaceBefore=11, spaceAfter=4, keepWithNext=1),
    "body": ParagraphStyle("body", fontName="DV", fontSize=8.8, leading=12.6, textColor=INK, spaceAfter=5, alignment=TA_LEFT),
    "bullet": ParagraphStyle("bullet", fontName="DV", fontSize=8.8, leading=12.6, textColor=INK, leftIndent=14, bulletIndent=3, spaceAfter=3),
    "cell": ParagraphStyle("cell", fontName="DV", fontSize=7.4, leading=9.6, textColor=INK),
    "cellh": ParagraphStyle("cellh", fontName="DV-B", fontSize=7.4, leading=9.6, textColor=INK),
    "code": ParagraphStyle("code", fontName="DVM", fontSize=6.9, leading=8.8, textColor=INK, backColor=ZEBRA, borderColor=RULE, borderWidth=0.5,
                           borderPadding=5, spaceBefore=3, spaceAfter=9, leftIndent=4, rightIndent=4),
    "caption": ParagraphStyle("caption", fontName="DV-B", fontSize=8.3, leading=11, textColor=INK, spaceBefore=8, spaceAfter=3),
    "toc2": ParagraphStyle("toc2", fontName="DV-B", fontSize=9, leading=13.5, leftIndent=0, textColor=INK),
    "toc3": ParagraphStyle("toc3", fontName="DV", fontSize=8.2, leading=11.5, leftIndent=14, textColor=MUTED),
}

FIGS = [("step7_environments.png", "Figure A1: processing cost of the proposed scheme and of the schemes taken from the three papers, in the BASE, papers' and measured environments"),
        ("step5b_omnet_papers.png", "Step 5: OMNeT++ 6.0.3, BASE Table II environment, constants of the three papers (our model)"),
        ("step5b_omnet_base.png", "Step 5: OMNeT++ 6.0.3 sensitivity analysis, BASE Table II environment, BASE Table III constants (our model)"),
        ("step5b_omnet_meas.png", "Step 5: OMNeT++ 6.0.3 sensitivity analysis, BASE Table II environment, measured ESP8266 constants (our model)"),
        ("step5b_omnet_fig_axis.png", "Step 5: OMNeT++ on the x-axis of BASE Figs. 1-2 (300-1800 devices), BASE environment (our model)"),
        ("step4_tc_sensitivity.png", "Step 4: sensitivity of JIANG (published operation count) to T_C"),
        ("step5_cost_vs_devices.png", "Step 5 cross-check: independent SimPy model, same parameters"),
        ("step5_storage_vs_devices.png", "Step 5: server storage versus devices (model)")]


def inline(text, fs, bold=False):
    """Markdown inline subset -> ReportLab paragraph markup."""
    codes = []

    def stash(m):
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"

    t = re.sub(r"`([^`]+)`", stash, text)
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)([^*]+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", t)
    face, drop = ("DVM-B", 2.2) if bold else ("DVM", 0.8)
    return re.sub("\x00(\\d+)\x00", lambda m: f'<font face="{face}" size="{fs - drop:.1f}">{html.escape(codes[int(m.group(1))], quote=False)}</font>', t)


def split_row(line):
    """Split a pipe-table row, ignoring pipes inside backticks."""
    cells, cur, tick = [], "", False
    for ch in line.strip().strip("|") if False else line.strip()[1:-1]:
        if ch == "`":
            tick = not tick
        if ch == "|" and not tick:
            cells.append(cur.strip())
            cur = ""
        else:
            cur += ch
    cells.append(cur.strip())
    return cells


def plain(t):
    return re.sub(r"[`*]", "", t)


def make_table(rows):
    header, body = rows[0], rows[1:]
    n = len(header)
    body = [(r + [""] * n)[:n] if len(r) <= n else r[:n - 1] + [" | ".join(r[n - 1:])] for r in body]
    fs = 7.4 if n <= 5 else 6.8
    data = [[Paragraph(inline(c, fs), S["cellh"]) for c in header]] + [[Paragraph(inline(c, fs), S["cell"]) for c in r] for r in body]
    # column weights from content length (square-root damped so short columns stay readable)
    w = []
    for j in range(n):
        longest = max(len(plain(r[j])) for r in [header] + body)
        mean = sum(len(plain(r[j])) for r in [header] + body) / (len(body) + 1)
        word = max(len(wd) for r in [header] + body for wd in (plain(r[j]).split() or [""]))
        w.append(min(max((0.6 * mean + 0.4 * longest) ** 0.85, 6, 0.9 * min(word, 24) + 2), 70))
    # every column gets room for its longest word (no mid-word breaks); the rest is shared in proportion to content length
    floor = [min(max(len(wd) for r in [header] + body for wd in (plain(r[j]).split() or [""])), 24) * (fs * 0.62) + 8 for j in range(n)]
    spare = max(CONTENT_W - sum(floor), 0)
    widths = [f + spare * x / sum(w) for f, x in zip(floor, w)]
    widths = [x * CONTENT_W / sum(widths) for x in widths]
    t = Table(data, colWidths=widths, repeatRows=1, splitByRow=1)
    st = [("BACKGROUND", (0, 0), (-1, 0), HEAD_BG), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), 0.4, RULE),
          ("LEFTPADDING", (0, 0), (-1, -1), 3.5), ("RIGHTPADDING", (0, 0), (-1, -1), 3.5), ("TOPPADDING", (0, 0), (-1, -1), 2.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6)]
    st += [("BACKGROUND", (0, i), (-1, i), ZEBRA) for i in range(2, len(data), 2)]
    t.setStyle(TableStyle(st))
    return [t, Spacer(1, 7)]


def parse(md):
    lines = md.split("\n")
    story, i, para = [], 0, []
    title = lines[0].lstrip("# ").strip()

    def flush():
        nonlocal para
        if para:
            text = " ".join(para)
            style = S["body"]
            if re.fullmatch(r"\*\*[^*]+\*\*", text):     # a bold run-in label stays with what follows
                style = ParagraphStyle("lead", parent=S["body"], keepWithNext=1)
            story.append(Paragraph(inline(text, 8.8), style))
            para = []

    i = 1
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("```"):
            flush()
            j, code = i + 1, []
            while not lines[j].startswith("```"):
                code.append(lines[j])
                j += 1
            wrapped = []
            for c in code:
                wrapped += textwrap.wrap(c, 112, subsequent_indent="        ", drop_whitespace=False, replace_whitespace=False) or [""]
            story.append(Preformatted("\n".join(wrapped), S["code"]))
            i = j + 1
            continue
        if ln.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            flush()
            rows = [split_row(ln)]
            j = i + 2
            while j < len(lines) and lines[j].startswith("|"):
                rows.append(split_row(lines[j]))
                j += 1
            story += make_table(rows)
            i = j
            continue
        m = re.match(r"^(#{2,3}) (.*)", ln)
        if m:
            flush()
            story.append(Paragraph(inline(m.group(2), 14 if len(m.group(1)) == 2 else 11, bold=True), S["h2" if len(m.group(1)) == 2 else "h3"]))
            i += 1
            continue
        m = re.match(r"^(\*|-|\d+\.) (.*)", ln)
        if m:
            flush()
            text, j = m.group(2), i + 1
            while j < len(lines) and lines[j].strip() and not re.match(r"^(\*|-|\d+\.) ", lines[j]) and not lines[j].startswith(("|", "#", "```")):
                text += " " + lines[j].strip()
                j += 1
            bullet = "•" if m.group(1) in ("*", "-") else m.group(1)
            story.append(Paragraph(inline(text, 8.8), S["bullet"], bulletText=bullet))
            i = j
            continue
        if not ln.strip():
            flush()
        else:
            para.append(ln.strip())
        i += 1
    flush()
    return title, story


class Doc(BaseDocTemplate):
    def afterFlowable(self, fl):
        if isinstance(fl, Paragraph) and fl.style.name == "H2":
            self.notify("TOCEntry", (0, re.sub(r"<[^>]+>", "", fl.getPlainText()), self.page))


def page_deco(canvas, doc):
    canvas.saveState()
    canvas.setFont("DV", 7.2)
    canvas.setFillColor(MUTED)
    if doc.page > 1:
        canvas.drawString(MARGIN, PAGE_H - 11 * mm, "Reference-paper replication and re-evaluation of BASE")
        canvas.setStrokeColor(RULE)
        canvas.line(MARGIN, PAGE_H - 12.5 * mm, PAGE_W - MARGIN, PAGE_H - 12.5 * mm)
    canvas.drawCentredString(PAGE_W / 2, 10 * mm, f"{doc.page}")
    canvas.restoreState()


def figures():
    out = [PageBreak(), Paragraph("Figures", S["h2"])]
    for f, cap in FIGS:
        path = RESULTS / f
        from reportlab.lib.utils import ImageReader
        iw, ih = ImageReader(str(path)).getSize()
        w = CONTENT_W
        h = w * ih / iw
        if h > 108 * mm:
            h = 108 * mm
            w = h * iw / ih
        out.append(KeepTogether([Paragraph(inline(cap, 8.3), S["caption"]), Image(str(path), width=w, height=h)]))
    return out


def main():
    md = (ROOT / "REPORT.md").read_text(encoding="utf8")
    title, story = parse(md)
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle("toc", fontName="DV", fontSize=9, leading=14, textColor=INK)]
    toc.dotsMinLevel = 0
    front = [Spacer(1, 10 * mm), Paragraph(inline(title, 21), S["title"]),
             Paragraph("BASE's simulated results (Al-Rasheed et al., IEEE TCE 2026) compared with the main paper (OURS), in the environment BASE took from "
                       "Jiang 2016, Dhillon and Kalra 2017 and Chang and Le 2016. Supporting evidence: the three papers' own numbers, BASE's use of them, "
                       "a common-environment cost model and an OMNeT++ sensitivity analysis.", S["subtitle"]),
             Table([[Paragraph("<b>Status</b>", S["cell"]), Paragraph("Working report, not a manuscript. Nothing here modifies the paper or the repository sources.", S["cell"])],
                    [Paragraph("<b>Reproduce</b>", S["cell"]), Paragraph("<font face='DVM' size='6.8'>bash research/reference_replication/run_all.sh</font> regenerates every table, figure and this PDF from the PDFs and data files.", S["cell"])],
                    [Paragraph("<b>Simulation</b>", S["cell"]), Paragraph("OMNeT++ 6.0.3 (WSL2) with a model written for this study, because BASE publishes no project files. Presented as a sensitivity analysis, not as evidence about BASE's protocol.", S["cell"])],
                    [Paragraph("<b>Verification</b>", S["cell"]), Paragraph("Every source table was read from a 300-DPI render; numbers quoted in this report are checked against the data by the test-suite (section 13).", S["cell"])]],
                   colWidths=[26 * mm, CONTENT_W - 26 * mm],
                   style=TableStyle([("GRID", (0, 0), (-1, -1), 0.4, RULE), ("BACKGROUND", (0, 0), (0, -1), HEAD_BG), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                     ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)])),
             Spacer(1, 10 * mm), Paragraph("Contents", S["h3"]), toc, PageBreak()]
    out = ROOT / "REPORT.pdf"
    doc = Doc(str(out), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=18 * mm, bottomMargin=17 * mm,
              title=title, author="", subject="Reference-paper replication report")
    doc.addPageTemplates([PageTemplate(id="p", frames=[Frame(MARGIN, 17 * mm, CONTENT_W, PAGE_H - 35 * mm, id="f", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)],
                                       onPage=page_deco)])
    doc.multiBuild(front + story + figures())
    import pymupdf
    print("wrote", out, pymupdf.open(out).page_count, "pages")


if __name__ == "__main__":
    main()
