# -*- coding: utf-8 -*-
"""
h16_fark_tani.py — 3554 vs 3656 fark tanısı
"""
import os
import pandas as pd
import numpy as np

YASAKLI = {"E0 (10).csv"}

TUM_DOSYALAR = [
    ("E0.csv", "2015/16"), ("E0 (1).csv", "2016/17"),
    ("E0 (2).csv", "2017/18"), ("E0 (3).csv", "2018/19"),
    ("E0 (4).csv", "2019/20"), ("E0 (5).csv", "2020/21"),
    ("E0 (6).csv", "2021/22"), ("E0 (7).csv", "2022/23"),
    ("E0 (8).csv", "2023/24"), ("E0 (9).csv", "2024/25"),
]

GEREKLI = ["Date", "FTR",
           "PSH", "PSD", "PSA", "PSCH", "PSCD", "PSCA",
           "B365H", "B365D", "B365A",
           "BWH", "BWD", "BWA",
           "WHH", "WHD", "WHA"]

ORAN_KOLONLARI = ["PSH", "PSD", "PSA", "PSCH", "PSCD", "PSCA",
                  "B365H", "B365D", "B365A",
                  "BWH", "BWD", "BWA",
                  "WHH", "WHD", "WHA"]

frames = []
for dosya, sezon in TUM_DOSYALAR:
    if os.path.basename(dosya) in YASAKLI:
        continue
    df = pd.read_csv(dosya, encoding="utf-8-sig")
    df = df.copy()
    df["Season"] = sezon
    frames.append(df[["Season"] + GEREKLI])

df = pd.concat(frames, ignore_index=True)
print(f"Ham: {len(df)}")

# Date parse
df["Date_p"] = pd.to_datetime(df["Date"], dayfirst=True, format="mixed", errors="coerce")

# --- Maske 1: Feasibility (notna + >0, <=20 YOK) ---
m_feas = pd.Series(True, index=df.index)
for c in ORAN_KOLONLARI:
    m_feas &= df[c].notna() & (df[c] > 0)
m_feas &= df["FTR"].isin(["H", "D", "A"])
m_feas &= df["Date_p"].notna()
print(f"\nMaske 1 (feasibility, <=20 yok):      {int(m_feas.sum())}")

# --- Maske 2: Kod (notna + >0 + <=20) ---
m_kod = pd.Series(True, index=df.index)
for c in ORAN_KOLONLARI:
    m_kod &= df[c].notna() & (df[c] > 0) & (df[c] <= 20)
m_kod &= df["FTR"].isin(["H", "D", "A"])
m_kod &= df["Date_p"].notna()
print(f"Maske 2 (kod, <=20 var):              {int(m_kod.sum())}")

# --- Fark ---
fark = m_feas & ~m_kod
print(f"\nFark (feasibility'de var, kod'da yok): {int(fark.sum())}")

# Fark nereden?
print("\n--- FARKTA HANGİ SÜTUN >20 ---")
fark_df = df[fark]
for c in ORAN_KOLONLARI:
    n = int((fark_df[c] > 20).sum())
    if n > 0:
        print(f"  {c}: {n}")

# Fark >20 toplamı
print("\n--- FARKTA TOPLAM >20 SAYISI ---")
toplam_gt20 = 0
for c in ORAN_KOLONLARI:
    toplam_gt20 += int((fark_df[c] > 20).sum())
print(f"  Toplam >20 hücresi: {toplam_gt20}")

# Farktaki maçların sezon dağılımı
print("\n--- FARK SEZON DAĞILIMI ---")
print(fark_df["Season"].value_counts().to_string())

# Farkta >20 olan ilk 20 maç
print("\n--- FARKTA >20 OLAN İLK 20 MAÇ ---")
sayac = 0
for idx, row in fark_df.iterrows():
    if sayac >= 20:
        break
    gt_cols = [c for c in ORAN_KOLONLARI if row[c] > 20]
    if gt_cols:
        print(f"  {row['Season']} {row.get('Date', '?')} "
              f"{row.get('HomeTeam', '?')} vs {row.get('AwayTeam', '?')} "
              f"→ >20: {gt_cols}")
        sayac += 1