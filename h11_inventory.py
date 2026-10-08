# -*- coding: utf-8 -*-
"""
h11_inventory.py
H11 ENVANTER — Veri mevcudiyeti ve bütünlük kontrolü
Tarih: 2026-10-08

BU SCRIPT YALNIZCA:
- Gerekli sütunların varlığını
- Sezon başına satır sayısını
- NaN / ≤0 sayılarını
- Temizlik sonrası satır sayısını
kontrol eder.

BU SCRIPT HİÇBİR ŞEKİLDE:
- ROI hesaplamaz
- Hareket dağılımına bakmaz
- Bant içeriklerini hesaplamaz
- Oran dağılımını incelemez
- Sonuç/istatistik üretmez

KİLİTLER:
- E0 (10).csv OKUNMAZ
- E0.csv, E0 (1).csv, E0 (2).csv, E0 (3).csv OKUNMAZ (kapanış yok)
"""

import os
import pandas as pd
from collections import defaultdict

# ==================================================================
# 0. SABİTLER
# ==================================================================
YASAKLI_DOSYALAR = {
    "E0 (10).csv",   # 2026/27 — kör OOS
    "E0.csv",        # 2015/16 — kapanış YOK
    "E0 (1).csv",    # 2016/17 — kapanış YOK
    "E0 (2).csv",    # 2017/18 — kapanış YOK
    "E0 (3).csv",    # 2018/19 — kapanış YOK
}

TUM_DOSYALAR = [
    ("E0 (4).csv",   "2019/20"),
    ("E0 (5).csv",   "2020/21"),
    ("E0 (6).csv",   "2021/22"),
    ("E0 (7).csv",   "2022/23"),
    ("E0 (8).csv",   "2023/24"),
    ("E0 (9).csv",   "2024/25"),
]

GEREKLI_SUTUNLAR = ["Date", "FTR", "B365D", "B365CD"]

_okuma_sayaci = defaultdict(int)


# ==================================================================
# 1. GÜVENLİ OKUMA
# ==================================================================
def _guvenli_oku(dosya):
    ad = os.path.basename(dosya)
    if ad in YASAKLI_DOSYALAR:
        raise RuntimeError(f"YASAKLI DOSYA OKUNAMAZ: {ad}")
    _okuma_sayaci[ad] += 1
    return pd.read_csv(dosya, encoding="utf-8-sig")


# ==================================================================
# 2. ANA ENVANTER
# ==================================================================
def main():
    print("=" * 80)
    print("H11 ENVANTER — Veri Mevcudiyeti ve Bütünlük Kontrolü")
    print("Yalnızca yapısal kontrol. ROI/hareket/bant HESAPLANMAZ.")
    print("=" * 80)

    # --- 1. Sütun mevcudiyeti ---
    print("\n--- 1. SÜTUN MEVCUDİYETİ ---")
    print(f"{'Sezon':10s} {'Dosya':14s} " +
          " ".join(f"{c:>10s}" for c in GEREKLI_SUTUNLAR))
    print("-" * 70)

    for dosya, sezon in TUM_DOSYALAR:
        if not os.path.exists(dosya):
            print(f"{sezon:10s} {dosya:14s} DOSYA YOK")
            continue
        # Yalnızca sütun başlıklarını oku (nrows=1)
        df_head = pd.read_csv(dosya, encoding="utf-8-sig", nrows=1)
        cols = df_head.columns.tolist()
        has = lambda c: 'VAR' if c in cols else 'YOK'
        satir = f"{sezon:10s} {dosya:14s} " + \
                " ".join(f"{has(c):>10s}" for c in GEREKLI_SUTUNLAR)
        print(satir)

    # --- 2. Satır sayıları ve NaN/≤0 kontrolü ---
    print("\n--- 2. SATIR SAYILARI ve NaN / ≤0 KONTROLÜ ---")

    ozet = []
    for dosya, sezon in TUM_DOSYALAR:
        if not os.path.exists(dosya):
            ozet.append({
                "Sezon": sezon, "Dosya": dosya,
                "Ham_satir": None, "B365D_NaN": None, "B365D_le0": None,
                "B365CD_NaN": None, "B365CD_le0": None,
                "FTR_NaN": None, "Date_NaN": None,
                "Temiz_satir": None,
            })
            continue

        df = _guvenli_oku(dosya)

        eksik = [c for c in GEREKLI_SUTUNLAR if c not in df.columns]
        if eksik:
            raise RuntimeError(f"{dosya}: eksik sütunlar {eksik}")

        n_ham = len(df)
        b365d_nan = int(df["B365D"].isna().sum())
        b365d_le0 = int((df["B365D"] <= 0).sum())
        b365cd_nan = int(df["B365CD"].isna().sum())
        b365cd_le0 = int((df["B365CD"] <= 0).sum())
        ftr_nan = int(df["FTR"].isna().sum())
        date_nan = int(df["Date"].isna().sum())

        # Temizlik maskesi (yalnız H11 için gerekli)
        gecerli = (
            df["B365D"].notna() & (df["B365D"] > 0) &
            df["B365CD"].notna() & (df["B365CD"] > 0) &
            df["FTR"].notna() &
            df["Date"].notna()
        )
        n_temiz = int(gecerli.sum())

        ozet.append({
            "Sezon": sezon, "Dosya": dosya,
            "Ham_satir": n_ham,
            "B365D_NaN": b365d_nan, "B365D_le0": b365d_le0,
            "B365CD_NaN": b365cd_nan, "B365CD_le0": b365cd_le0,
            "FTR_NaN": ftr_nan, "Date_NaN": date_nan,
            "Temiz_satir": n_temiz,
        })

    ozet_df = pd.DataFrame(ozet)
    print(ozet_df.to_string(index=False))

    # --- 3. Toplamlar ---
    print("\n--- 3. TOPLAMLAR ---")
    if ozet_df["Ham_satir"].notna().any():
        print(f"  Ham toplam:      {int(ozet_df['Ham_satir'].sum())}")
        print(f"  Temiz toplam:    {int(ozet_df['Temiz_satir'].sum())}")
        print(f"  Düşen toplam:    "
              f"{int(ozet_df['Ham_satir'].sum() - ozet_df['Temiz_satir'].sum())}")

    # --- 4. Bölme bazlı ---
    print("\n--- 4. BÖLME BAZLI TEMİZ SATIR ---")
    train_sezonlar = ["2019/20", "2020/21", "2021/22", "2022/23"]
    val_sezon = "2023/24"
    oos_sezon = "2024/25"

    train_n = int(ozet_df.loc[ozet_df["Sezon"].isin(train_sezonlar), "Temiz_satir"].sum())
    val_n = int(ozet_df.loc[ozet_df["Sezon"] == val_sezon, "Temiz_satir"].sum())
    oos_n = int(ozet_df.loc[ozet_df["Sezon"] == oos_sezon, "Temiz_satir"].sum())

    print(f"  Train (2019/20 – 2022/23): {train_n}")
    print(f"  Validation (2023/24):       {val_n}")
    print(f"  OOS (2024/25):              {oos_n}")
    print(f"  Toplam:                     {train_n + val_n + oos_n}")

    # --- 5. Yasaklı dosya kanıtı ---
    print("\n--- 5. YASAKLI DOSYA KANITI ---")
    print(f"  Okuma sayacı: {dict(_okuma_sayaci)}")
    print(f"  Yasaklı dosyalar: {sorted(YASAKLI_DOSYALAR)}")
    okunmamis = all(d not in _okuma_sayaci for d in YASAKLI_DOSYALAR)
    print(f"  Yasaklılardan hiçbiri okunmadı: {okunmamis}")

    # --- 6. Excel çıktı ---
    cikti = "h11_inventory.xlsx"
    with pd.ExcelWriter(cikti, engine="openpyxl") as w:
        ozet_df.to_excel(w, sheet_name="Envanter", index=False)

        pd.DataFrame([{
            "Protokol": "H11 FROZEN v1.0 — Draw Movement Edge",
            "Tarih": "2026-10-08",
            "Asama": "Envanter",
            "Not": "Yalnizca veri mevcudiyeti ve butunluk kontrolu yapildi. "
                   "Hicbir ROI/hareket/bant hesaplanmadi.",
            "Gerekli_sutunlar": ", ".join(GEREKLI_SUTUNLAR),
            "Train": "2019/20 - 2022/23",
            "Validation": "2023/24",
            "OOS": "2024/25",
            "2026_27": "KILITLI - okunmadi",
            "Kapanissiz_4_sezon": "2015/16 - 2018/19 KULLANILMADI",
            "Train_temiz_N": train_n,
            "Val_temiz_N": val_n,
            "OOS_temiz_N": oos_n,
        }]).to_excel(w, sheet_name="Notlar", index=False)

    print(f"\n--- {cikti} yazıldı ---")

    print("\n" + "=" * 80)
    print("ENVANTER TAMAMLANDI")
    print("=" * 80)
    print("Sonraki adım: Bu çıktı H11 FROZEN protokolüne uygun mu?")
    print("  - 4 gerekli sütun 6 sezonda da VAR mı?")
    print("  - Train/Val/OOS temiz satır sayıları kabul edilebilir mi?")
    print("  - Yasaklı dosyalar okunmadı mı?")
    print("  - Evet ise → h11_explore_v1.py yazılır ve tek çalıştırma yapılır.")
    print("=" * 80)


if __name__ == "__main__":
    main()