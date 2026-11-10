#!/usr/bin/env python3
"""Render the poster app (app/) to <NAME>.png (3648 x 4416) and <NAME>.pdf (vector text) in docs/poster/.
Run from the repository root: python -I docs/poster/build.py   (needs Node.js, and Google Chrome or Microsoft Edge)
First time: cd docs/poster/app && npm install. Charts: python -I docs/poster/make_charts.py. Source: docs/poster/app/src/App.tsx (shadcn/ui).
"""
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE
CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "google-chrome", "chromium", "chromium-browser", "microsoft-edge",
]
browser = next((c for c in CANDIDATES if Path(c).exists() or shutil.which(c)), None)
if browser is None:
    sys.exit("Chrome or Edge not found")
APP = HERE / "app"
npx = shutil.which("npx")
if npx is None:
    sys.exit("Node.js (npx) not found")
subprocess.run([npx, "vite", "build"], cwd=APP, check=True, stdout=subprocess.DEVNULL)
PORT = 4173
server = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1", "--directory", str(APP / "dist")],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
url = f"http://127.0.0.1:{PORT}/index.html"
out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT
# Submission naming: Year-Class-Sr.No-Project Title
NAME = "BE-D20A-4-Pseudonym Resolution and Formal Verification of an Unlinkable Two-Message IoT Authentication Protocol"
common = [browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
          "--run-all-compositor-stages-before-draw", "--virtual-time-budget=4000"]
dom = subprocess.run(common + ["--window-size=1824,2208", "--dump-dom", url], capture_output=True, text=True,
                     encoding="utf-8").stdout
import re  # noqa: E402
m = re.search(r'id="overflow"[^>]*>([^<]*)<', dom)
print("overflow px per column (must be <= 0):", m.group(1) if m else "not measured")
subprocess.run(common + ["--window-size=1824,2208", "--force-device-scale-factor=2",
                         f"--screenshot={out / f'{NAME}.png'}", url], check=True)
subprocess.run(common + ["--no-pdf-header-footer", f"--print-to-pdf={out / f'{NAME}.pdf'}", url], check=True)
server.terminate()
print("wrote", out / f"{NAME}.png", "and", out / f"{NAME}.pdf")
