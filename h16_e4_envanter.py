# -*- coding: utf-8 -*-
"""
h16_e4_envanter.py
H16-E4 FEASIBILITY / DATA INVENTORY

Bu script YALNIZCA veri mevcudiyeti ve eşleştirilebilirlik kontrol eder.
HİÇBİR ŞEKİLDE:
- ROI hesaplamaz
- Hareket dağılımına bakmaz
- Threshold seçmez
- "En iyi gecikme" aramaz
- Sonuç/istatistik üretmez

KİLİTLER:
- E0 (10).csv ASLA OKUNMAZ
"""

import os
import pandas as pd
import numpy as np

# ==================================================================
# 0. SABİTLER
# ==================================================================
YASAKLI_DOSYALAR = {"E0 (10).csv"}

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

# H16-E4 için gereken sütunlar
PS_ACILIS = ["PSH", "PSD", "PSA"]
PS_KAPANIS = ["PSCH", "PSCD", "PSCA"]
RETAIL_ACILIS = ["B365H", "B365D", "B365A",
                 "BWH", "BWD", "BWA",
                 "WHH", "WHD", "WHA"]

GEREKLI = ["Date", "FTR"] + PS_ACILIS + PS_KAPANIS + RETAIL_ACILIS


# ==================================================================
# 1. GÜVENLİ OKUMA
# ==================================================================
def _guvenli_oku(dosya):
    ad = os.path.basename(dosya)
    if ad in YASAKLI_DOSYALAR:
        raise RuntimeError(f"YASAKLI DOSYA OKUNAMAZ: {ad}")
    return pd.read_csv(dosya, encoding="utf-8-sig")


# ==================================================================
# 2. SÜTUN VARLIK KONTROLÜ
# ==================================================================
def sutun_varlik():
    print("=" * 80)
    print("H16-E4 FEASIBILITY / DATA INVENTORY")
    print("Yalnızca yapısal kontrol. ROI/hareket/threshold HESAPLANMAZ.")
    print("=" * 80)

    print("\n--- 1. SÜTUN VARLIK KONTROLÜ ---")
    print(f"{'Sezon':10s} {'Dosya':14s} " +
          " ".join(f"{c:>7s}" for c in GEREKLI))
    print("-" * 120)

    for dosya, sezon in TUM_DOSYALAR:
        if not os.path.exists(dosya):
            print(f"{sezon:10s} {dosya:14s} DOSYA YOK")
            continue
        df = pd.read_csv(dosya, encoding="utf-8-sig", nrows=1)
        cols = df.columns.tolist()
        has = lambda c: "VAR" if c in cols else "YOK"
        satir = f"{sezon:10s} {dosya:14s} " + \
                " ".join(f"{has(c):>7s}" for c in GEREKLI)
        print(satir)


# ==================================================================
# 3. SEZON BAZLI NaN VE COVERAGE
# ==================================================================
def coverage_analiz():
    print("\n--- 2. SEZON BAZLI COVERAGE (PS açılış + kapanış) ---")

    ozet = []
    for dosya, sezon in TUM_DOSYALAR:
        if not os.path.exists(dosya):
            continue
        df = _guvenli_oku(dosya)
        n_ham = len(df)

        # PS açılış tam
        ps_ac_ok = (
            df["PSH"].notna() & (df["PSH"] > 0) & (df["PSH"] <= 20) &
            df["PSD"].notna() & (df["PSD"] > 0) & (df["PSD"] <= 20) &
            df["PSA"].notna() & (df["PSA"] > 0) & (df["PSA"] <= 20)
        ) if all(c in df.columns for c in PS_ACILIS) else pd.Series([False]*n_ham)

        # PS kapanış tam
        ps_kap_ok = (
            df["PSCH"].notna() & (df["PSCH"] > 0) & (df["PSCH"] <= 20) &
            df["PSCD"].notna() & (df["PSCD"] > 0) & (df["PSCD"] <= 20) &
            df["PSCA"].notna() & (df["PSCA"] > 0) & (df["PSCA"] <= 20)
        ) if all(c in df.columns for c in PS_KAPANIS) else pd.Series([False]*n_ham)

        # Retail B365 açılış tam
        b365_ok = (
            df["B365H"].notna() & (df["B365H"] > 0) & (df["B365H"] <= 20) &
            df["B365D"].notna() & (df["B365D"] > 0) & (df["B365D"] <= 20) &
            df["B365A"].notna() & (df["B365A"] > 0) & (df["B365A"] <= 20)
        )

        # BW açılış tam
        bw_ok = (
            df["BWH"].notna() & (df["BWH"] > 0) & (df["BWH"] <= 20) &
            df["BWD"].notna() & (df["BWD"] > 0) & (df["BWD"] <= 20) &
            df["BWA"].notna() & (df["BWA"] > 0) & (df["BWA"] <= 20)
        )

        # WH açılış tam
        wh_ok = (
            df["WHH"].notna() & (df["WHH"] > 0) & (df["WHH"] <= 20) &
            df["WHD"].notna() & (df["WHD"] > 0) & (df["WHD"] <= 20) &
            df["WHA"].notna() & (df["WHA"] > 0) & (df["WHA"] <= 20)
        )

        # FTR ve Date
        ftr_ok = df["FTR"].isin(["H", "D", "A"])
        date_ok = df["Date"].notna()

        # H16-E4 tam evreni: PS açılış + PS kapanış + B365 açılış + FTR + Date
        e4_ok = ps_ac_ok & ps_kap_ok & b365_ok & ftr_ok & date_ok

        ozet.append({
            "Sezon": sezon, "Ham": n_ham,
            "PS_ac": int(ps_ac_ok.sum()),
            "PS_kap": int(ps_kap_ok.sum()),
            "B365_ac": int(b365_ok.sum()),
            "BW_ac": int(bw_ok.sum()),
            "WH_ac": int(wh_ok.sum()),
            "E4_evren": int(e4_ok.sum()),
        })

    ozet_df = pd.DataFrame(ozet)
    print(ozet_df.to_string(index=False))

    # Toplam
    print(f"\n--- TOPLAMLAR ---")
    print(f"  Ham toplam:       {int(ozet_df['Ham'].sum())}")
    print(f"  PS açılış tam:    {int(ozet_df['PS_ac'].sum())}")
    print(f"  PS kapanış tam:   {int(ozet_df['PS_kap'].sum())}")
    print(f"  B365 açılış tam:  {int(ozet_df['B365_ac'].sum())}")
    print(f"  BW açılış tam:    {int(ozet_df['BW_ac'].sum())}")
    print(f"  WH açılış tam:    {int(ozet_df['WH_ac'].sum())}")
    print(f"  E4 evreni:        {int(ozet_df['E4_evren'].sum())}")

    # Bölme bazlı
    print(f"\n--- BÖLME BAZLI E4 EVRENİ ---")
    train_sezonlar = ["2015/16", "2016/17", "2017/18", "2018/19",
                      "2019/20", "2020/21", "2021/22", "2022/23"]
    for etiket, sezonlar in [
        ("Train", train_sezonlar),
        ("Validation", ["2023/24"]),
        ("OOS", ["2024/25"]),
    ]:
        alt = ozet_df[ozet_df["Sezon"].isin(sezonlar)]
        print(f"  {etiket:11s}: {int(alt['E4_evren'].sum())}")


# ==================================================================
# 4. DATE FORMAT KONTROLÜ (mixed parse)
# ==================================================================
def date_kontrol():
    print("\n--- 3. DATE PARSE KONTROLÜ (format=mixed) ---")

    frames = []
    for dosya, sezon in TUM_DOSYALAR:
        if not os.path.exists(dosya):
            continue
        df = _guvenli_oku(dosya)
        df = df.copy()
        df["Season"] = sezon
        frames.append(df[["Season", "Date"]])

    df = pd.concat(frames, ignore_index=True)
    df["Date_p"] = pd.to_datetime(df["Date"], dayfirst=True, format="mixed", errors="coerce")

    nat = int(df["Date_p"].isna().sum())
    print(f"  Toplam: {len(df)}")
    print(f"  NaT:    {nat}")
    if nat > 0:
        print(f"  NaT sezon dağılımı:")
        print(df[df["Date_p"].isna()]["Season"].value_counts().to_string())


# ==================================================================
# 5. EŞLEŞTİRİLEBİLİRLİK
# ==================================================================
def eslestirilebilirlik():
    print("\n--- 4. AYNI MAÇTA PS AÇILIŞ + PS KAPANIŞ + B365 + BW + WH ---")

    toplam = {"hepsi": 0, "b365_ps": 0, "ps_only": 0}
    for dosya, sezon in TUM_DOSYALAR:
        if not os.path.exists(dosya):
            continue
        df = _guvenli_oku(dosya)

        ps_ac_ok = (
            df["PSH"].notna() & (df["PSH"] > 0) &
            df["PSD"].notna() & (df["PSD"] > 0) &
            df["PSA"].notna() & (df["PSA"] > 0)
        )
        ps_kap_ok = (
            df["PSCH"].notna() & (df["PSCH"] > 0) &
            df["PSCD"].notna() & (df["PSCD"] > 0) &
            df["PSCA"].notna() & (df["PSCA"] > 0)
        )
        b365_ok = (
            df["B365H"].notna() & (df["B365H"] > 0) &
            df["B365D"].notna() & (df["B365D"] > 0) &
            df["B365A"].notna() & (df["B365A"] > 0)
        )
        bw_ok = (
            df["BWH"].notna() & (df["BWH"] > 0) &
            df["BWD"].notna() & (df["BWD"] > 0) &
            df["BWA"].notna() & (df["BWA"] > 0)
        )
        wh_ok = (
            df["WHH"].notna() & (df["WHH"] > 0) &
            df["WHD"].notna() & (df["WHD"] > 0) &
            df["WHA"].notna() & (df["WHA"] > 0)
        )

        toplam["ps_only"] += int((ps_ac_ok & ps_kap_ok).sum())
        toplam["b365_ps"] += int((ps_ac_ok & ps_kap_ok & b365_ok).sum())
        toplam["hepsi"] += int((ps_ac_ok & ps_kap_ok & b365_ok & bw_ok & wh_ok).sum())

    print(f"  PS açılış + PS kapanış:              {toplam['ps_only']}")
    print(f"  + B365 açılış:                       {toplam['b365_ps']}")
    print(f"  + B365 + BW + WH açılış:             {toplam['hepsi']}")


# ==================================================================
# 6. HAREKET ÖLÇÜLEBİLİRLİĞİ
# ==================================================================
def hareket_kontrol():
    print("\n--- 5. HAREKET ÖLÇÜLEBİLİRLİĞİ (yalnızca sayı) ---")

    frames = []
    for dosya, sezon in TUM_DOSYALAR:
        if not os.path.exists(dosya):
            continue
        df = _guvenli_oku(dosya)
        df = df.copy()
        df["Season"] = sezon
        # PS açılış ve kapanış tam olan maçlar
        gerekli = ["PSH", "PSD", "PSA", "PSCH", "PSCD", "PSCA"]
        gecerli = pd.Series(True, index=df.index)
        for c in gerekli:
            gecerli &= df[c].notna() & (df[c] > 0) & (df[c] <= 20)
        alt = df[gecerli].copy()
        # Hareket hesapla
        alt["mov_H"] = (alt["PSCH"] - alt["PSH"]) / alt["PSH"]
        alt["mov_D"] = (alt["PSCD"] - alt["PSD"]) / alt["PSD"]
        alt["mov_A"] = (alt["PSCA"] - alt["PSA"]) / alt["PSA"]
        frames.append(alt[["Season", "mov_H", "mov_D", "mov_A"]])

    df = pd.concat(frames, ignore_index=True)
    print(f"  PS açılış+kapanış tam olan maç: {len(df)}")

    # Hareket büyüklüğü dağılımı (yalnızca kaç tanesi > eşik)
    for esik in [0.01, 0.02, 0.05]:
        print(f"\n  |hareket| > {esik*100:.0f}% olan maç sayısı:")
        for taraf in ["H", "D", "A"]:
            n = int((df[f"mov_{taraf}"].abs() > esik).sum())
            print(f"    {taraf}: {n}")


# ==================================================================
# 7. ANA
# ==================================================================
def main():
    sutun_varlik()
    coverage_analiz()
    date_kontrol()
    eslestirilebilirlik()
    hareket_kontrol()

    print("\n" + "=" * 80)
    print("ENVANTER TAMAMLANDI")
    print("Yalnızca yapısal kontrol yapıldı.")
    print("ROI/hareket/strateji/threshold hesaplanmadı.")
    print("Sonraki adım: Bu çıktı H16-E4 protokolü için yeterli mi?")
    print("=" * 80)


if __name__ == "__main__":
    main()