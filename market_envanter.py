# -*- coding: utf-8 -*-
"""
market_envanter.py
Tüm E0 CSV'lerindeki sütunları ve potansiyel bahis marketlerini listeler.
"""

import pandas as pd
import os

DOSYALAR = [
    ("E0.csv",       "2015/16"),
    ("E0 (1).csv",   "2016/17"),
    ("E0 (2).csv",   "2017/18"),
    ("E0 (3).csv",   "2018/19"),
    ("E0 (4).csv",   "2019/20"),
    ("E0 (5).csv",   "2020/21"),
    ("E0 (6).csv",   "2021/22"),
    ("E0 (7).csv",   "2022/23"),
    ("E0 (8).csv",   "2023/24"),
    ("E0 (9).csv",   "2024/25"),
]

YASAKLI = {"E0 (10).csv"}

# Potansiyel market sütunları
MARKET_PATTERNS = {
    "1X2_ACILIS":      ["B365H", "B365D", "B365A"],
    "1X2_KAPANIS":     ["B365CH", "B365CD", "B365CA"],
    "AH_ACILIS":       ["AHh", "B365AHH", "B365AHA"],
    "AH_KAPANIS":      ["AHCh", "B365CAHH", "B365CAHA"],
    "OU25_ACILIS":     ["B365>2.5", "B365<2.5"],
    "OU25_KAPANIS":    ["B365C>2.5", "B365C<2.5"],
    "MAX_ACILIS":      ["MaxH", "MaxD", "MaxA", "Max>2.5", "Max<2.5"],
    "AVG_ACILIS":      ["AvgH", "AvgD", "AvgA", "Avg>2.5", "Avg<2.5"],
    "MAX_KAPANIS":     ["MaxCH", "MaxCD", "MaxCA", "MaxC>2.5", "MaxC<2.5"],
    "AVG_KAPANIS":     ["AvgCH", "AvgCD", "AvgCA", "AvgC>2.5", "AvgC<2.5"],
    "P_ACILIS":        ["PH", "PD", "PA", "P>2.5", "P<2.5"],
    "P_KAPANIS":       ["PCH", "PCD", "PCA", "PC>2.5", "PC<2.5"],
    "IW_ACILIS":       ["IWH", "IWD", "IWA"],
    "IW_KAPANIS":      ["IWCH", "IWCD", "IWCA"],
    "BW_ACILIS":       ["BWH", "BWD", "BWA"],
    "BW_KAPANIS":      ["BWCH", "BWCD", "BWCA"],
    "WH_ACILIS":       ["WHH", "WHD", "WHA"],
    "WH_KAPANIS":      ["WHCH", "WHCD", "WHCA"],
    "VC_ACILIS":       ["VCH", "VCD", "VCA"],
    "VC_KAPANIS":      ["VCCH", "VCCD", "VCCA"],
    "PS_ACILIS":       ["PSH", "PSD", "PSA"],
    "PS_KAPANIS":      ["PSCH", "PSCD", "PSCA"],
    "HT_VERI":         ["HTHG", "HTAG", "HTR"],
    "KART_VERI":       ["HY", "AY", "HR", "AR"],
    "KORNER_VERI":     ["HC", "AC"],
    "SUT_VERI":        ["HS", "AS", "HST", "AST"],
    "FAUL_VERI":       ["HF", "AF"],
    "HAKEM":           ["Referee"],
}

print("=" * 80)
print("MARKET ENVANTERİ")
print("=" * 80)

# Her dosya için sütunları al (ilk dosyadan)
mevcut_sutunlar_per_dosya = {}
for dosya, sezon in DOSYALAR:
    if dosya in YASAKLI:
        continue
    if not os.path.exists(dosya):
        print(f"  {dosya} YOK")
        continue
    df = pd.read_csv(dosya, encoding="utf-8-sig", nrows=1)
    mevcut_sutunlar_per_dosya[sezon] = set(df.columns.tolist())

# Tüm sezonlarda ortak olan sütunlar
tum_sezonlar = list(mevcut_sutunlar_per_dosya.keys())
ortak = set.intersection(*mevcut_sutunlar_per_dosya.values())

print(f"\nToplam sezon: {len(tum_sezonlar)}")
print(f"Ortak sütun sayısı: {len(ortak)}")

print("\n--- MARKET ANALİZİ ---")
for market, cols in MARKET_PATTERNS.items():
    var = [c for c in cols if c in ortak]
    yok = [c for c in cols if c not in ortak]
    durum = "TAM" if len(yok) == 0 else ("KISMI" if len(var) > 0 else "YOK")
    print(f"\n  {market}: {durum}")
    if var:
        print(f"    VAR: {var}")
    if yok:
        print(f"    YOK: {yok}")

print("\n--- TÜM ORTAK SÜTUNLAR ---")
for c in sorted(ortak):
    print(f"  {c}")

print("\n--- SEZON BAZLI EKSİKLER ---")
# Hangi sezon hangi sütunları kaybediyor
for sezon in tum_sezonlar:
    eksik = ortak - mevcut_sutunlar_per_dosya[sezon]
    if eksik:
        print(f"  {sezon}: eksik {sorted(eksik)}")