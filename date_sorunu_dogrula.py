# -*- coding: utf-8 -*-
"""
date_sorunu_dogrula.py
Hangi maçlarda Date parse edilemiyor?
"""
import pandas as pd
import os

DOSYALAR = [
    ("E0.csv", "2015/16"), ("E0 (1).csv", "2016/17"),
    ("E0 (2).csv", "2017/18"), ("E0 (3).csv", "2018/19"),
    ("E0 (4).csv", "2019/20"), ("E0 (5).csv", "2020/21"),
    ("E0 (6).csv", "2021/22"), ("E0 (7).csv", "2022/23"),
    ("E0 (8).csv", "2023/24"), ("E0 (9).csv", "2024/25"),
]

frames = []
for dosya, sezon in DOSYALAR:
    df = pd.read_csv(dosya, encoding="utf-8-sig")
    df["Season"] = sezon
    frames.append(df)

df = pd.concat(frames, ignore_index=True)
print(f"Ham: {len(df)}")

# Date parse
df["Date_p"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
nat = df[df["Date_p"].isna()]
print(f"NaT (parse edilemeyen): {len(nat)}")

if len(nat) > 0:
    print("\n--- NaT ÖRNEKLERİ ---")
    print(nat[["Season", "Date", "HomeTeam", "AwayTeam"]].head(20).to_string())

    print("\n--- NaT SEZON DAĞILIMI ---")
    print(nat["Season"].value_counts().to_string())

    print("\n--- HAM Date ÖRNEKLERİ (NaT) ---")
    for _, row in nat.head(10).iterrows():
        print(f"  {row['Season']} | '{row['Date']}' | tip: {type(row['Date']).__name__}")

    # Date kolonu dtypes
    print(f"\n--- Date kolon dtype: {df['Date'].dtype} ---")