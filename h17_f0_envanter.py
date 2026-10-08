# -*- coding: utf-8 -*-
"""
h17_f0_envanter.py
H17-F0 — Veri / Leakage Feasibility Envanteri
Tarih: 2026-10-08

Bu script YALNIZCA:
- H1 feature setinin yapısını
- NaN dağılımını
- Sezon kapsamını
- Sütun isimlerini
- Date sıralaması güvenilirliğini
- Hedef değişken (FTR) mevcudiyetini
- B365 opening odds mevcudiyetini
- Pre-match / leakage risklerini

kontrol eder.

BU SCRIPT HİÇBİR ŞEKİLDE:
- Model eğitmez
- ROI hesaplamaz
- Residual hesaplamaz
- Threshold seçmez
- "En iyi feature" aramaz

KİLİTLER:
- E0 (10).csv ASLA OKUNMAZ
"""

import os
import pandas as pd
import numpy as np

# ==================================================================
# 0. SABİTLER
# ==================================================================
H1_FEATURES = "h1_features_v2.csv"   # veya h1_features.csv
YASAKLI_DOSYALAR = {"E0 (10).csv"}

# Ana veri dosyaları (H1 features hangisini kullanıyorsa)
TUM_DOSYALAR = [
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


# ==================================================================
# 1. H1 FEATURE DOSYASI VARLIĞI
# ==================================================================
def h1_dosya_kontrol():
    print("=" * 80)
    print("H17-F0 — VERİ / LEAKAGE FEASIBILITY")
    print("Yalnızca yapısal kontrol. Model/ROI/residual HESAPLANMAZ.")
    print("=" * 80)

    print("\n--- 1. H1 FEATURE DOSYASI ---")
    adaylar = ["h1_features_v2.csv", "h1_features.csv"]
    bulunan = None
    for a in adaylar:
        if os.path.exists(a):
            print(f"  {a}: VAR")
            if bulunan is None:
                bulunan = a
        else:
            print(f"  {a}: YOK")

    if bulunan is None:
        raise RuntimeError("H1 feature dosyası bulunamadı.")

    df = pd.read_csv(bulunan, encoding="utf-8-sig")
    print(f"\n  Seçilen dosya: {bulunan}")
    print(f"  Satır: {len(df)}")
    print(f"  Sütun: {len(df.columns)}")
    return bulunan, df


# ==================================================================
# 2. SÜTUN LİSTESİ VE KATEGORİZASYON
# ==================================================================
def sutun_listesi(df):
    print("\n--- 2. SÜTUN LİSTESİ ---")
    sutunlar = df.columns.tolist()
    for i, c in enumerate(sutunlar, 1):
        print(f"  {i:2d}. {c}")

    # Kategorizasyon (isim bazlı tahmin)
    print("\n--- 3. SÜTUN KATEGORİZASYONU (isim bazlı) ---")
    kat = {
        "Kimlik/Anahtar": [],
        "Hedef/Outcome": [],
        "Oran (B365 vd)": [],
        "Elo": [],
        "Form": [],
        "Gol/GD": [],
        "Rest/Maç sayısı": [],
        "Diğer": [],
    }
    for c in sutunlar:
        cl = c.lower()
        if c in ["Season", "Date", "HomeTeam", "AwayTeam", "_key",
                 "FTHG", "FTAG", "FTR", "HTHG", "HTAG", "HTR"]:
            if c in ["FTR"]:
                kat["Hedef/Outcome"].append(c)
            else:
                kat["Kimlik/Anahtar"].append(c)
        elif c.startswith("B365") or c.startswith("PS") or c.startswith("BW") or c.startswith("WH"):
            kat["Oran (B365 vd)"].append(c)
        elif "elo" in cl:
            kat["Elo"].append(c)
        elif "form" in cl:
            kat["Form"].append(c)
        elif "goal" in cl or "gd" in cl:
            kat["Gol/GD"].append(c)
        elif "rest" in cl or "mac" in cl or "count" in cl:
            kat["Rest/Maç sayısı"].append(c)
        else:
            kat["Diğer"].append(c)

    for k, v in kat.items():
        print(f"\n  {k} ({len(v)}):")
        for c in v:
            print(f"    - {c}")


# ==================================================================
# 3. NaN DAĞILIMI
# ==================================================================
def nan_dagilimi(df):
    print("\n--- 4. NaN DAĞILIMI ---")
    n = len(df)
    nan_ozet = []
    for c in df.columns:
        n_nan = int(df[c].isna().sum())
        if n_nan > 0:
            nan_ozet.append({"Sütun": c, "NaN": n_nan, "NaN%": round(n_nan/n*100, 2)})

    if not nan_ozet:
        print("  NaN yok.")
    else:
        nan_df = pd.DataFrame(nan_ozet).sort_values("NaN", ascending=False)
        print(nan_df.to_string(index=False))


# ==================================================================
# 4. SEZON KAPSAMI
# ==================================================================
def sezon_kapsam(df):
    print("\n--- 5. SEZON KAPSAMI ---")
    if "Season" not in df.columns:
        print("  Season sütunu yok.")
        return
    print(df["Season"].value_counts().sort_index().to_string())


# ==================================================================
# 5. DATE KONTROLÜ
# ==================================================================
def date_kontrol(df):
    print("\n--- 6. DATE KONTROLÜ ---")
    if "Date" not in df.columns:
        print("  Date sütunu yok.")
        return
    d = pd.to_datetime(df["Date"], dayfirst=True, format="mixed", errors="coerce")
    n_nat = int(d.isna().sum())
    print(f"  Date parse: {len(d) - n_nat} başarılı, {n_nat} NaT")
    if n_nat > 0:
        print("  NaT sezon dağılımı:")
        print(df.loc[d.isna(), "Season"].value_counts().to_string()
              if "Season" in df.columns else "  (Season yok)")


# ==================================================================
# 6. HEDEF DEĞİŞKEN KONTROLÜ
# ==================================================================
def hedef_kontrol(df):
    print("\n--- 7. HEDEF DEĞİŞKEN (FTR) ---")
    if "FTR" not in df.columns:
        print("  FTR sütunu yok.")
        return
    print(df["FTR"].value_counts(dropna=False).to_string())


# ==================================================================
# 7. ORAN SÜTUNU KONTROLÜ
# ==================================================================
def oran_kontrol(df):
    print("\n--- 8. ORAN SÜTUNLARI (açılış) ---")
    oran_sutunlari = [c for c in df.columns
                     if c.startswith("B365") and len(c) == 5]
    print(f"  B365 açılış sütunları: {oran_sutunlari}")
    for c in oran_sutunlari:
        n_nan = int(df[c].isna().sum())
        n_gec = int((df[c] > 0).sum())
        print(f"    {c}: NaN={n_nan}, >0={n_gec}")


# ==================================================================
# 8. LEAKAGE RİSK KONTROLÜ
# ==================================================================
def leakage_kontrol(df):
    print("\n--- 9. LEAKAGE RİSK KONTROLÜ ---")
    print("  Aşağıdaki sütunlar MAÇ SONRASI bilgi içerir.")
    print("  Bunlar feature olarak KULLANILMAMALI:")
    leak_sutunlar = ["FTHG", "FTAG", "FTR", "HTHG", "HTAG", "HTR",
                     "HS", "AS", "HST", "AST", "HF", "AF", "HC", "AC",
                     "HY", "AY", "HR", "AR"]
    mevcut_leak = [c for c in leak_sutunlar if c in df.columns]
    for c in mevcut_leak:
        print(f"    ⚠ {c}")

    print("\n  Feature olarak KULLANILABILECEK (pre-match) adaylar:")
    pre_match_aday = [c for c in df.columns
                      if any(k in c.lower() for k in
                             ["elo", "form", "goal", "gd", "avg", "rest", "count"])
                      and c not in leak_sutunlar]
    for c in pre_match_aday:
        print(f"    ✓ {c}")


# ==================================================================
# 9. VERİ BOYUT ÖZETİ
# ==================================================================
def boyut_ozet(df):
    print("\n--- 10. BOYUT ÖZETİ ---")
    print(f"  Toplam satır: {len(df)}")
    if "Season" in df.columns:
        train_sez = ["2015/16", "2016/17", "2017/18", "2018/19",
                     "2019/20", "2020/21", "2021/22", "2022/23"]
        n_train = int(df["Season"].isin(train_sez).sum())
        n_val = int((df["Season"] == "2023/24").sum())
        n_oos = int((df["Season"] == "2024/25").sum())
        n_2026 = int((df["Season"] == "2026/27").sum()) if "2026/27" in df["Season"].unique() else 0
        print(f"  Train (2015/16-2022/23): {n_train}")
        print(f"  Validation (2023/24):     {n_val}")
        print(f"  OOS (2024/25):            {n_oos}")
        if n_2026 > 0:
            print(f"  ⚠ 2026/27 satırı bulundu: {n_2026} — ASLA KULLANILMAYACAK")


# ==================================================================
# 10. ANA
# ==================================================================
def main():
    bulunan, df = h1_dosya_kontrol()
    sutun_listesi(df)
    nan_dagilimi(df)
    sezon_kapsam(df)
    date_kontrol(df)
    hedef_kontrol(df)
    oran_kontrol(df)
    leakage_kontrol(df)
    boyut_ozet(df)

    print("\n" + "=" * 80)
    print("H17-F0 TAMAMLANDI")
    print("Yalnızca yapısal kontrol yapıldı.")
    print("Model/ROI/residual/threshold HESAPLANMADI.")
    print("Sonraki adım: F1 — Model tasarımının önceden kilitlenmesi")
    print("=" * 80)


if __name__ == "__main__":
    main()