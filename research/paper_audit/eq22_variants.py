#!/usr/bin/env python3
"""How many of the three hash-only schemes (Turkanovic 7/7/5 T_H, Dhillon-Karla 8/6/8, Jiang 7/5/10: user/device/server)
cost LESS than the proposed scheme, under three definitions of the proposed scheme's cost:
  V1  Table V as printed:                 per side 2 T_H + 2 T_SE/D
  V2  Table V + the session KDF of Eq.16: per side 2 T_H + 2 T_SE/D + 1 KDF
  V3  Eq. 22 with an AEAD (tag = MAC):     device 1 KDF + 1 AEAD;  server 1 KDF + 2 AEAD (dec + enc)
  V4  Table V's "2 T_H" read as PID hash + KDF (the most favourable reading for the paper): per side T_H + KDF + 2 T_SE/D
Counted per column and in total. 'x/3' = number of hash-only schemes cheaper. Per-operation times are measured."""
import sys
from pathlib import Path
from reeval import load
RES = Path(__file__).parent / "results"
HASH_ONLY = {"Turkanovic": (7, 7, 5), "Dhillon-Karla": (8, 6, 8), "Jiang": (7, 5, 10)}  # user, device, server T_H counts

def get(rows, op, variant=None):
    for (o, v), ms in rows.items():
        if o.startswith(op) and (variant is None or v.startswith(variant)):
            return ms
    raise KeyError((op, variant))

PLATFORMS = []  # (label, rows, H, kdf, [(S label, S)])
for label, f in (("ESP8266 @80 MHz (BearSSL, software)", "esp8266_80mhz.csv"), ("ESP8266 @160 MHz (BearSSL)", "esp8266_160mhz.csv"),
                 ("t4g.nano Graviton2 (BearSSL, software)", "aws_t4g_nano.csv"), ("Apple-silicon Mac (BearSSL, software)", "mac.csv")):
    r = load(RES / f)
    H = get(r, "T_H: SHA-1 (paper", "bearssl"); K = get(r, "HKDF-SHA256", "bearssl")
    S = [("GCM, key schedule cached, aes_big", get(r, "AES-256-GCM encrypt 56 B (key schedule cached)", "aes_big")),
         ("GCM, key schedule cached, aes_ct", get(r, "AES-256-GCM encrypt 56 B (key schedule cached)", "aes_ct")),
         ("GCM incl. key setup, aes_big", get(r, "AES-GCM encrypt+tag (incl. key setup)", "aes_big(table,fast)/AES-256"))]
    PLATFORMS.append((label, H, K, S))
r = load(RES / "mac_libcrypto.csv")
H = get(r, "T_H: SHA-1 (1 block; libcrypto low-level)"); K = get(r, "HKDF-SHA256 on low-level")
PLATFORMS.append(("Apple-silicon Mac (OpenSSL, HARDWARE AES/SHA, low-level calls)", H, K,
                  [("GCM per message, key cached", get(r, "AES-256-GCM encrypt 56 B per message (libcrypto; key cached)")),
                   ("GCM per message incl. key setup", get(r, "AES-256-GCM encrypt 56 B per message (libcrypto; incl. key setup)"))]))

def cheaper(prop, H):
    """prop = (device, server); returns counts per column and totals"""
    dev = sum(1 for u, d, s in HASH_ONLY.values() if d * H < prop[0])
    srv = sum(1 for u, d, s in HASH_ONLY.values() if s * H < prop[1])
    ds = sum(1 for u, d, s in HASH_ONLY.values() if (d + s) * H < sum(prop))
    al = sum(1 for u, d, s in HASH_ONLY.values() if (u + d + s) * H < sum(prop))
    return dev, srv, ds, al

for label, H, K, Sdefs in PLATFORMS:
    print(f"\n##### {label}\n  T_H = {H*1e6:.1f} ns   HKDF = {K*1e6:.1f} ns  (= {K/H:.1f} T_H)")
    print(f"  {'T_SE/D definition':36s} {'T_SE/D ns':>10s} {'r':>5s}   {'variant':34s} dev srv dev+srv all-roles   (x/3 hash-only cheaper)")
    for sl, S in Sdefs:
        for vn, prop in (("V1 Table V as printed", (2*H + 2*S, 2*H + 2*S)),
                         ("V2 Table V + session KDF", (2*H + 2*S + K, 2*H + 2*S + K)),
                         ("V3 Eq.22 w/ AEAD (1 KDF + AEAD)", (K + S, K + 2*S)),
                         ("V4 2T_H = PID hash + KDF", (H + K + 2*S, H + K + 2*S))):
            d, s_, ds, al = cheaper(prop, H)
            print(f"  {sl:36s} {S*1e6:10.0f} {S/H:5.1f}   {vn:34s} {d}/3 {s_}/3  {ds}/3     {al}/3")
    print(f"  zero-cost-AES lower bound (device = 1 KDF only): hash-only device columns cheaper in "
          f"{sum(1 for u,d,s in HASH_ONLY.values() if d*H < K)}/3 cases (device columns are 7, 6, 5 T_H; KDF = {K/H:.1f} T_H)")
