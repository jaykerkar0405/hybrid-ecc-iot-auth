#!/usr/bin/env python3
"""Independent check of paper_tables.py against docs/base_paper.pdf.
The PDF's text layer has no table cells, so: render pages 6-8 at 600 DPI, OCR Tables III, IV and VI with tesseract,
and compare every number with the transcription. Table V (math typography) defeats OCR; it was verified by two manual
cell-by-cell readings (300 and 600 DPI) and by partial OCR agreement, and is NOT checked by this script."""
import re, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image
from paper_tables import T3, T4, T6
Image.MAX_IMAGE_PIXELS = None
PDF = Path(__file__).resolve().parents[2] / "docs/base_paper.pdf"
tmp = Path(tempfile.mkdtemp())
subprocess.run(["pdftoppm", "-r", "600", "-f", "6", "-l", "8", "-png", str(PDF), str(tmp / "p")], check=True)

def ocr(page, box):
    im = Image.open(tmp / f"p-{page}.png"); w, h = im.size
    f = tmp / "c.png"; im.crop((int(box[0]*w), int(box[1]*h), int(box[2]*w), int(box[3]*h))).convert("L").save(f)
    return subprocess.run(["tesseract", str(f), "-", "--psm", "6"], capture_output=True, text=True).stdout

def nums(line): return [int(x) if "." not in x else float(x) for x in re.findall(r"\d+(?:\.\d+)?", re.sub(r"\[\d+\]", "", line))]
ok = True
def check(label, got, want):
    global ok; good = got == want; ok &= good
    print(f"  {'OK ' if good else 'DIFF'} {label}: {got if not good else ''}{'' if good else ' vs transcription ' + str(want)}")

print("Table IV (communication, bits)")
txt = ocr(7, (0.15, 0.06, 0.88, 0.24)).splitlines()
for name, (msgs, user, dev, srv, tot) in T4.items():
    key = name.split()[0].split("-")[0]
    line = next(l for l in txt if l.strip().startswith(key))
    want = [msgs] + ([] if user is None else [user]) + [dev, srv, tot]
    check(name, nums(line), want)
print("Table VI (storage, bits; Das et al. row excluded: '768 + CH*')")
txt = ocr(8, (0.10, 0.31, 0.55, 0.43)).splitlines()
for name, (srv, dev) in T6.items():
    key = name.split()[0].split("-")[0][2:] if name[0] in "TDS" else name.split()[0]  # OCR drops first letter on some rows
    line = next(l for l in txt if key in l and "Das" not in l)
    check(name, nums(line)[:2] if len(nums(line)) >= 2 else nums(line), [srv, dev])
print("Table III (reference times, ms)")
txt = ocr(6, (0.5, 0.34, 0.9, 0.47))
vals = [float(x) for x in re.findall(r"\b\d+\.\d+\b", txt)]
check("T_ECM, T_C, T_SE/D, T_H, T_fe", vals, [T3["ECM"], T3["C"], T3["SE/D"], T3["H"], T3["fe"]])
print("\nALL OCR-CHECKED CELLS MATCH" if ok else "\nMISMATCHES FOUND")
sys.exit(0 if ok else 1)
