"""Shared loaders. Existing audit tables are imported read-only from research/paper_audit (never modified)."""
import sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
AUDIT = REPO / "research" / "paper_audit"
RESULTS = ROOT / "results"
sys.path.insert(0, str(AUDIT))
from paper_tables import T3, T4, T5, T6  # noqa: E402  (BASE Tables III-VI, transcribed by the earlier audit)

def load_extracted():
    with open(ROOT / "data" / "extracted.yaml", encoding="utf8") as f:
        return yaml.safe_load(f)

def write_csv(path, header, rows):
    import csv
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf8") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)
