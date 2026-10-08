# -*- coding: utf-8 -*-
"""
check_seasons.py
10 sezonun market sütunlarını kontrol et.
"""
import os
import pandas as pd

DOSYALAR = [
    "E0.csv",       # 2015/16
    "E0 (1).csv",   # 2016/17
    "E0 (2).csv",   # 2017/18
    "E0 (3).csv",   # 2018/19
    "E0 (4).csv",   # 2019/20
    "E0 (5).csv",   # 2020/21
    "E0 (6).csv",   # 2021/22
    "E0 (7).csv",   # 2022/23
    "E0 (8).csv",   # 2023/24
    "E0 (9).csv",   # 2024/25
]

KONTROL_SUTUNLAR = ["B365H", "B365D", "B365A", "FTR", "FTHG", "FTAG",
                    "HomeTeam", "AwayTeam", "Date"]

print("=" * 100)
print("SEZON DOSYALARI KONTROLÜ")
print("=" * 100)

for f in DOSYALAR:
    if not os.path.exists(f):
        print(f"{f:15s} | [DOSYA YOK]")
        continue
    df = pd.read_csv(f, encoding="utf-8-sig", nrows=1)
    cols = set(df.columns)
    n_rows = len(pd.read_csv(f, encoding="utf-8-sig"))

    durumlar = []
    for c in KONTROL_SUTUNLAR:
        durumlar.append(f"{c}={'V' if c in cols else 'X'}")

    print(f"{f:15s} | n={n_rows:4d} | " + " | ".join(durumlar))

print("\nSütunlar kontrol edildi:")
print("  V = VAR, X = YOK")