# -*- coding: utf-8 -*-
"""
h15_tani.py — H15 ortak evren tutarsızlığı tanısı
"""
import os
import pandas as pd
import numpy as np
from collections import defaultdict

YASAKLI = {"E0 (10).csv"}

TUM_DOSYALAR = [
    ("E0.csv", "2015/16"), ("E0 (1).csv", "2016/17"),
    ("E0 (2).csv", "2017/18"), ("E0 (3).csv", "2018/19"),
    ("E0 (4).csv", "2019/20"), ("E0 (5).csv", "2020/21"),
    ("E0 (6).csv", "2021/22"), ("E0 (7).csv", "2022/23"),
    ("E0 (8).csv", "2023/24"), ("E0 (9).csv", "2024/25"),
]

GEREKLI = ["Date", "FTR",
           "B365H", "B365D", "B365A",
           "BWH", "BWD", "BWA",
           "WHH", "WHD", "WHA",
           "PSH", "PSD", "PSA"]

frames = []
for dosya, sezon in TUM_DOSYALAR:
    if os.path.basename(dosya) in YASAKLI:
        raise RuntimeError(f"YASAKLI: {dosya}")
    df = pd.read_csv(dosya, encoding="utf-8-sig")
    df = df.copy()
    df["Season"] = sezon
    frames.append(df[["Season"] + GEREKLI])

df = pd.concat(frames, ignore_index=True)
print(f"Ham toplam: {len(df)}")

df["Date_p"] = pd.to_datetime(df["Date"], dayfirst=True, format="mixed", errors="coerce")

ORAN_KOLONLARI = ["B365H", "B365D", "B365A",
                  "BWH", "BWD", "BWA",
                  "WHH", "WHD", "WHA",
                  "PSH", "PSD", "PSA"]

print("\n--- ORTAK EVREN TANISI ---")

# 1) Sadece oranların dolu olması
tam_dolu = pd.Series(True, index=df.index)
for c in ORAN_KOLONLARI:
    tam_dolu &= df[c].notna()
print(f"1. Sadece 12 oran tam dolu (notna): {int(tam_dolu.sum())}")
print(f"   Eksik oran nedeniyle düşen:      {int((~tam_dolu).sum())}")

# 2) 0 < odds <= 20
oran_aralik = pd.Series(True, index=df.index)
for c in ORAN_KOLONLARI:
    oran_aralik &= df[c].notna() & (df[c] > 0) & (df[c] <= 20)
print(f"2. 12 oran 0<odds<=20:              {int(oran_aralik.sum())}")
print(f"   Oran aralığı nedeniyle düşen:    {int((tam_dolu & ~oran_aralik).sum())}")

# 3) FTR
ftr_gec = df["FTR"].isin(["H", "D", "A"])
print(f"3. Geçerli FTR:                     {int(ftr_gec.sum())}")
print(f"   Geçersiz FTR:                    {int((~ftr_gec).sum())}")

# 4) Date
tarih_gec = df["Date_p"].notna()
print(f"4. Geçerli Date:                    {int(tarih_gec.sum())}")
print(f"   Geçersiz Date:                   {int((~tarih_gec).sum())}")

# 5) Sadece complete odds + FTR + Date
evren_complete = tam_dolu & ftr_gec & tarih_gec
print(f"\n5. Complete odds + FTR + Date:      {int(evren_complete.sum())}")

# 6) H15 mevcut filtresi
evren_h15 = oran_aralik & ftr_gec & tarih_gec
print(f"6. H15 mevcut filtresi:             {int(evren_h15.sum())}")

# 7) >20 oranlar
print("\n--- >20 OLAN ORANLAR (hangi sütunda kaç tane) ---")
for c in ORAN_KOLONLARI:
    n = int((df[c] > 20).sum())
    if n:
        print(f"  {c}: {n}")

# 8) NaN oranlar
print("\n--- NaN OLAN ORANLAR ---")
for c in ORAN_KOLONLARI:
    n = int(df[c].isna().sum())
    if n:
        print(f"  {c}: {n}")

# 9) Fark analizi: complete vs H15 filtresi
fark = evren_complete & ~evren_h15
print(f"\n--- FARK (complete ama >20 nedeniyle düşen): {int(fark.sum())} ---")

# 10) Farktaki maçların >20 sütun dağılımı
if int(fark.sum()) > 0:
    print("\nFark maçlarda hangi sütunlar >20?")
    fark_df = df[fark]
    for c in ORAN_KOLONLARI:
        n = int((fark_df[c] > 20).sum())
        if n:
            print(f"  {c}: {n} maçta >20")

# 11) Sezon bazlı fark
print("\n--- SEZON BAZLI FARK ---")
for sezon in df["Season"].unique():
    m = (df["Season"] == sezon)
    c_ok = int((m & evren_complete).sum())
    h_ok = int((m & evren_h15).sum())
    print(f"  {sezon}: complete={c_ok}, H15={h_ok}, fark={c_ok - h_ok}")