# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np

DOSYALAR = [
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
for dosya, sezon in DOSYALAR:
    df = pd.read_csv(dosya, encoding="utf-8-sig")
    df = df.copy()
    df["Season"] = sezon
    frames.append(df[["Season"] + GEREKLI])

df = pd.concat(frames, ignore_index=True)
print(f"Ham toplam: {len(df)}")

# Date parse — mixed
df["Date_p"] = pd.to_datetime(df["Date"], dayfirst=True, format="mixed", errors="coerce")
print(f"Date_p NaT: {int(df['Date_p'].isna().sum())}")

# NaT olanları göster
nat = df[df["Date_p"].isna()]
if len(nat) > 0:
    print(f"\n--- NaT SEZON DAĞILIMI ---")
    print(nat["Season"].value_counts().to_string())
    print(f"\n--- NaT Date ÖRNEKLERİ ---")
    print(nat["Date"].head(10).to_string())

# Filtre adımları
ORAN_KOLONLARI = ["B365H", "B365D", "B365A", "BWH", "BWD", "BWA",
                  "WHH", "WHD", "WHA", "PSH", "PSD", "PSA"]

gecerli = pd.Series(True, index=df.index)
for c in ORAN_KOLONLARI:
    gecerli &= df[c].notna() & (df[c] > 0) & (df[c] <= 20)

print(f"\nSadece oranlar: {int(gecerli.sum())}")

gecerli &= df["FTR"].isin(["H", "D", "A"])
print(f"+ FTR: {int(gecerli.sum())}")

gecerli &= df["Date_p"].notna()
print(f"+ Date_p: {int(gecerli.sum())}")

# Sezon bazlı
print(f"\n--- SEZON BAZLI FİLTRE SONRASI ---")
for sezon in df["Season"].unique():
    alt = df[(df["Season"] == sezon) & gecerli]
    print(f"  {sezon}: {len(alt)}")