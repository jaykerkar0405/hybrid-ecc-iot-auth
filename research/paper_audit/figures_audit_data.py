"""Digitised Fig. 1 values (shared with figures_audit.py)."""
N = [300, 600, 900, 1200, 1500, 1800]  # "Vehicles in VANET"

# Fig. 1 (journal p.4488) captioned "Processing requirements" but y-axis reads "Communication Overhead (%)", axis 30-100
FIG1 = {
    "Proposed":       [42.7, 44.8, 47.3, 50.5, 52.5, 63.5],
    "Zhanfei 2024":   [72.7, 76.9, 81.8, 86.2, 90.8, 92.5],
    "Hassan 2023":    [65.0, 69.7, 70.5, 74.5, 77.9, 84.1],
    "Gupta 2019":     [94.8, 96.8, 100.0, 99.9, 100.0, 100.0],   # 900, 1500, 1800 clipped (*)
    "Gope 2016":      [86.2, 88.0, 90.3, 92.5, 95.2, 96.4],
    "Hassan 2018":    [89.3, 91.8, 89.0, 94.9, 97.9, 100.0],     # 1800 clipped (*)
}