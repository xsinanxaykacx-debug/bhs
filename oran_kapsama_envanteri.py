# -*- coding: utf-8 -*-
"""
oran_kapsama_envanteri.py
Bookmaker oran kapsama ve kalite kontrolü.
"""

import pandas as pd
import numpy as np
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

# Test edilecek oran sütunları
ORAN_SUTUNLARI = [
    "B365H", "B365D", "B365A",
    "BWH", "BWD", "BWA",
    "WHH", "WHD", "WHA",
    "PSH", "PSD", "PSA",
    "PSCH", "PSCD", "PSCA",
]

print("=" * 80)
print("ORAN KAPSAMA VE KALİTE ENVANTERİ")
print("=" * 80)

# Her dosyayı yükle ve tüm oran sütunlarını topla
tum_dosyalar = []
for dosya, sezon in DOSYALAR:
    if dosya in YASAKLI:
        continue
    if not os.path.exists(dosya):
        print(f"  {dosya} YOK")
        continue
    df = pd.read_csv(dosya, encoding="utf-8-sig")
    df["Season"] = sezon
    tum_dosyalar.append(df)

birlesik = pd.concat(tum_dosyalar, ignore_index=True)
print(f"\nToplam satır: {len(birlesik)}")

# Sütun var mı kontrolü
print("\n--- SÜTUN VARLIK KONTROLÜ ---")
for c in ORAN_SUTUNLARI:
    if c in birlesik.columns:
        print(f"  {c:8s} VAR")
    else:
        print(f"  {c:8s} YOK")

# Her sütun için genel istatistik
print("\n--- GENEL ORAN İSTATİSTİKLERİ ---")
print(f"{'Sütun':8s} {'Toplam':>8s} {'NaN':>8s} {'NaN%':>8s} "
      f"{'<=0':>6s} {'>20':>6s} {'Min':>8s} {'Max':>8s} {'Ort':>8s}")
print("-" * 90)

for c in ORAN_SUTUNLARI:
    if c not in birlesik.columns:
        continue
    s = birlesik[c]
    n = len(s)
    n_nan = int(s.isna().sum())
    pct_nan = n_nan / n * 100
    n_le0 = int((s <= 0).sum())
    n_gt20 = int((s > 20).sum())
    s_gec = s[(s > 0) & (s <= 20)]
    print(f"{c:8s} {n:>8d} {n_nan:>8d} {pct_nan:>7.2f}% "
          f"{n_le0:>6d} {n_gt20:>6d} "
          f"{s_gec.min():>8.3f} {s_gec.max():>8.3f} {s_gec.mean():>8.3f}")

# Sezon bazlı NaN kontrolü
print("\n--- SEZON BAZLI GEÇERLİ ORAN SAYISI ---")
print(f"{'Sezon':10s}", end="")
for c in ORAN_SUTUNLARI:
    print(f"{c[:6]:>8s}", end="")
print()
print("-" * (10 + 8 * len(ORAN_SUTUNLARI)))

for sezon in birlesik["Season"].unique():
    alt = birlesik[birlesik["Season"] == sezon]
    print(f"{sezon:10s}", end="")
    for c in ORAN_SUTUNLARI:
        if c in alt.columns:
            gecerli = int(((alt[c] > 0) & (alt[c] <= 20)).sum())
            print(f"{gecerli:>8d}", end="")
        else:
            print(f"{'YOK':>8s}", end="")
    print()

# Birlikte bulunma (co-occurrence)
print("\n--- AYNI MAÇTA BİRLİKTE BULUNMA ---")
print("En az 1 bookmaker'ın H/D/A açılış oranı geçerli olan maç sayısı:")

# B365 var mı
def gecerli_maske(df, prefix):
    h = df.get(prefix + "H", pd.Series([np.nan]*len(df)))
    d = df.get(prefix + "D", pd.Series([np.nan]*len(df)))
    a = df.get(prefix + "A", pd.Series([np.nan]*len(df)))
    return (h > 0) & (h <= 20) & (d > 0) & (d <= 20) & (a > 0) & (a <= 20)

b365 = gecerli_maske(birlesik, "B365")
bw = gecerli_maske(birlesik, "BW")
wh = gecerli_maske(birlesik, "WH")
ps = gecerli_maske(birlesik, "PS")
ps_c = (birlesik.get("PSCH", pd.Series([np.nan]*len(birlesik))) > 0) & \
       (birlesik.get("PSCD", pd.Series([np.nan]*len(birlesik))) > 0) & \
       (birlesik.get("PSCA", pd.Series([np.nan]*len(birlesik))) > 0)

print(f"  B365 açılış tam:        {int(b365.sum())}")
print(f"  Betway (BW) açılış tam: {int(bw.sum())}")
print(f"  William Hill (WH):      {int(wh.sum())}")
print(f"  Pinnacle (PS) açılış:   {int(ps.sum())}")
print(f"  Pinnacle (PS) kapanış:  {int(ps_c.sum())}")
print(f"  B365 + BW + WH + PS:    {int((b365 & bw & wh & ps).sum())}")
print(f"  BW + WH + PS:           {int((bw & wh & ps).sum())}")
print(f"  PS açılış + kapanış:    {int((ps & ps_c).sum())}")
print(f"  Hepsi (4 aç + PS kap):  {int((b365 & bw & wh & ps & ps_c).sum())}")

# Sadece açılış oranları için implied prob karşılaştırması
print("\n--- BOOKMAKER OVERROUND ORTALAMASI (açılış) ---")
for isim, prefix in [("B365", "B365"), ("Betway", "BW"),
                     ("William Hill", "WH"), ("Pinnacle", "PS")]:
    h = birlesik.get(prefix + "H")
    d = birlesik.get(prefix + "D")
    a = birlesik.get(prefix + "A")
    if h is None or d is None or a is None:
        continue
    gecerli = (h > 0) & (h <= 20) & (d > 0) & (d <= 20) & (a > 0) & (a <= 20)
    overround = (1/h + 1/d + 1/a)[gecerli]
    print(f"  {isim:15s} ort overround: {overround.mean():.4f} "
          f"(min {overround.min():.4f}, max {overround.max():.4f})")