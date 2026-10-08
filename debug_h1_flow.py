# -*- coding: utf-8 -*-
"""
debug_h1_flow.py
H1 Edge v1.0 — Veri akışı teşhisi

AMAÇ:
- h1_features.csv ile market CSV'leri arasındaki eşleşmeyi teşhis et.
- _mac_anahtari() metodunun nerede bozulduğunu göster.
- Elo_Diff / Movement / kategori dağılımlarını incele.
- Çalışan h1_edge_v1.py dosyasını doğrula.

YAPMAZ:
- Bahis yapmaz, ROI hesaplamaz, sinyal üretmez.
- 2026/27'yi okumaz.
- Protokolü değiştirmez.

DÜZELTME (bu sürüm):
- main() içinde debug_crosstab() çağrısından önce Movement sütunu oluşturulur.
"""

import os
import hashlib
import numpy as np
import pandas as pd

H1_FEATURES = "h1_features.csv"
H1_EDGE_SCRIPT = "h1_edge_v1.py"
YASAKLI = {"E0 (10).csv"}

MARKET_DOSYALARI = {
    "2019/20": "E0 (4).csv",
    "2020/21": "E0 (5).csv",
    "2021/22": "E0 (6).csv",
    "2022/23": "E0 (7).csv",
    "2023/24": "E0 (8).csv",
    "2024/25": "E0 (9).csv",
}

MARKET_SUTUNLARI = ["Season", "Date", "HomeTeam", "AwayTeam",
                    "AHh", "AHCh", "B365AHH", "B365AHA",
                    "B365CAHH", "B365CAHA"]


# ==================================================================
# _mac_anahtari (h1_edge_v1.py ile birebir aynı)
# ==================================================================
def _mac_anahtari(df):
    tarih = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce").dt.strftime("%Y-%m-%d")
    return (df["Season"].astype(str).str.strip()
            + "|" + tarih.fillna("NA")
            + "|" + df["HomeTeam"].astype(str).str.strip()
            + "|" + df["AwayTeam"].astype(str).str.strip())


# ==================================================================
# 1. h1_features.csv teşhisi
# ==================================================================
def debug_features():
    print("=" * 80)
    print("1. h1_features.csv")
    print("=" * 80)

    if not os.path.exists(H1_FEATURES):
        print(f"  HATA: {H1_FEATURES} bulunamadı.")
        return None

    feat = pd.read_csv(H1_FEATURES, encoding="utf-8-sig")
    print(f"  Toplam satır: {len(feat)}")
    print(f"  Sütun sayısı: {len(feat.columns)}")

    print("\n  Sezon bazında satır sayısı:")
    for s, n in feat.groupby("Season").size().items():
        print(f"    {s}: {n}")

    print("\n  Tarih örnekleri (ilk 5):")
    print(f"    {feat['Date'].head(5).tolist()}")

    print("\n  Elo_Diff:")
    print(f"    NaN sayısı: {feat['Elo_Diff'].isna().sum()} / {len(feat)}")
    elo_clean = feat['Elo_Diff'].dropna()
    if len(elo_clean) > 0:
        print(f"    min: {elo_clean.min():.2f}")
        print(f"    %25: {elo_clean.quantile(0.25):.2f}")
        print(f"    %50: {elo_clean.quantile(0.50):.2f}")
        print(f"    %75: {elo_clean.quantile(0.75):.2f}")
        print(f"    max: {elo_clean.max():.2f}")

    def _kat(ed):
        if pd.isna(ed): return None
        if ed < 0: return "DUSUK"
        elif ed <= 100: return "ORTA"
        else: return "YUKSEK"
    feat["_kat"] = feat["Elo_Diff"].apply(_kat)
    print("\n  Elo kategori dağılımı (tüm sezonlar):")
    for k, n in feat["_kat"].value_counts(dropna=False).items():
        print(f"    {k}: {n}")

    return feat


# ==================================================================
# 2. Market CSV teşhisi
# ==================================================================
def debug_market():
    print("\n" + "=" * 80)
    print("2. Market CSV'leri")
    print("=" * 80)

    frames = []
    for sezon, dosya in MARKET_DOSYALARI.items():
        ad = os.path.basename(dosya)
        if ad in YASAKLI:
            print(f"  [ATLANDI] {ad}")
            continue
        if not os.path.exists(dosya):
            print(f"  HATA: {dosya} bulunamadı")
            continue
        df = pd.read_csv(dosya, encoding="utf-8-sig")
        df["Season"] = sezon
        print(f"  {ad:15s} → {sezon}  ({len(df)} satır)")
        if sezon == "2019/20":
            print(f"    Tarih örnekleri: {df['Date'].head(3).tolist()}")
        for c in ["AHh", "AHCh", "B365AHH", "B365AHA", "B365CAHH", "B365CAHA"]:
            if c in df.columns:
                nn = df[c].isna().sum()
                if nn > 0:
                    print(f"    {c}: NaN={nn}")
        frames.append(df[MARKET_SUTUNLARI].copy())

    market = pd.concat(frames, ignore_index=True)
    print(f"\n  Toplam market satırı: {len(market)}")
    print(f"  Sezon dağılımı:")
    for s, n in market.groupby("Season").size().items():
        print(f"    {s}: {n}")

    market["Movement"] = market["AHCh"] - market["AHh"]
    print("\n  Movement (AHCh - AHh):")
    print(f"    NaN: {market['Movement'].isna().sum()}")
    mv = market["Movement"].dropna()
    if len(mv) > 0:
        print(f"    min: {mv.min():.2f}")
        print(f"    %50: {mv.quantile(0.50):.2f}")
        print(f"    max: {mv.max():.2f}")
        print(f"    |Movement|>0.25 sayısı: {(mv.abs() > 0.25).sum()}")
        print(f"    |Movement|<=0.25 sayısı: {(mv.abs() <= 0.25).sum()}")

    return market


# ==================================================================
# 3. _key eşleşme teşhisi
# ==================================================================
def debug_keys(feat, market):
    print("\n" + "=" * 80)
    print("3. _mac_anahtari() eşleşme teşhisi")
    print("=" * 80)

    feat = feat.copy()
    market = market.copy()

    feat["_key"] = _mac_anahtari(feat)
    market["_key"] = _mac_anahtari(market)

    print("\n  Feature _key örnekleri (ilk 3):")
    for k in feat["_key"].head(3):
        print(f"    {k}")
    print("\n  Market _key örnekleri (ilk 3):")
    for k in market["_key"].head(3):
        print(f"    {k}")

    feat_ilgili = feat[feat["Season"].isin(MARKET_DOSYALARI.keys())]
    feat_keys = set(feat_ilgili["_key"].dropna().astype(str))
    market_keys = set(market["_key"].dropna().astype(str))

    print(f"\n  Feature (2019/20–2024/25) unique key: {len(feat_keys)}")
    print(f"  Market unique key: {len(market_keys)}")
    print(f"  Kesişim: {len(feat_keys & market_keys)}")
    print(f"  Yalnız feature: {len(feat_keys - market_keys)}")
    print(f"  Yalnız market: {len(market_keys - feat_keys)}")

    print(f"\n  Feature duplicate key sayısı: {feat_ilgili['_key'].duplicated().sum()}")
    print(f"  Market duplicate key sayısı: {market['_key'].duplicated().sum()}")

    return feat, market


# ==================================================================
# 4. Mevcut merge sonucu
# ==================================================================
def debug_merge(feat, market):
    print("\n" + "=" * 80)
    print("4. Mevcut merge sonucu (inner join)")
    print("=" * 80)

    feat = feat.copy()
    market = market.copy()
    feat["_key"] = _mac_anahtari(feat)
    market["_key"] = _mac_anahtari(market)

    merged = feat.merge(
        market[["_key", "AHh", "AHCh", "B365AHH", "B365AHA", "B365CAHH", "B365CAHA"]],
        on="_key", how="inner"
    )

    print(f"\n  Feature satır: {len(feat)}")
    print(f"  Market satır: {len(market)}")
    print(f"  Merge (inner) satır: {len(merged)}")

    if len(merged) == 0:
        print("\n  ⚠ MERGE SIFIR SATIR! _key uyuşmuyor.")
        return merged

    print(f"\n  Sezon dağılımı (merge sonrası):")
    for s, n in merged.groupby("Season").size().items():
        print(f"    {s}: {n}")

    print(f"\n  Elo_Diff NaN (merge öncesi): {feat['Elo_Diff'].isna().sum()} / {len(feat)}")
    print(f"  Elo_Diff NaN (merge sonrası): {merged['Elo_Diff'].isna().sum()} / {len(merged)}")

    return merged


# ==================================================================
# 5. Kategori çapraz tablosu
# ==================================================================
def debug_crosstab(merged):
    print("\n" + "=" * 80)
    print("5. Elo_Kategori × Market_Sinif çapraz tablosu")
    print("=" * 80)

    if len(merged) == 0:
        print("  Merge boş, çapraz tablo yok.")
        return

    def _kat(ed):
        if pd.isna(ed): return "NaN"
        if ed < 0: return "DUSUK"
        elif ed <= 100: return "ORTA"
        else: return "YUKSEK"
    def _mkt(mv):
        if pd.isna(mv): return "NaN"
        if mv > 0.25: return "EV_YONLU"
        elif mv < -0.25: return "DEPLASMAN_YONLU"
        else: return "NOTR"

    merged["_kat"] = merged["Elo_Diff"].apply(_kat)
    merged["_mkt"] = merged["Movement"].apply(_mkt)

    print("\n  Tüm sezonlar (2019/20–2024/25):")
    ct = pd.crosstab(merged["_kat"], merged["_mkt"], margins=True)
    print(ct.to_string())

    print("\n  2023/24 (Validation):")
    val = merged[merged["Season"] == "2023/24"]
    if len(val) > 0:
        ct_v = pd.crosstab(val["_kat"], val["_mkt"], margins=True)
        print(ct_v.to_string())
        print(f"\n  2023/24 toplam satır: {len(val)}")
    else:
        print("  2023/24 boş.")

    # Ek: her hücredeki |Movement|>0.25 dağılımı
    print("\n  Ek: |Movement|>0.25 olan maçların Elo_Kategori dağılımı:")
    hareketli = merged[merged["Movement"].abs() > 0.25]
    print(f"    Toplam hareketli maç: {len(hareketli)}")
    if len(hareketli) > 0:
        print(f"    Elo_Kategori dağılımı:")
        for k, n in hareketli["_kat"].value_counts().items():
            print(f"      {k}: {n}")
        print(f"    Market_Sinif dağılımı:")
        for k, n in hareketli["_mkt"].value_counts().items():
            print(f"      {k}: {n}")


# ==================================================================
# 6. Çalışan script doğrulaması
# ==================================================================
def debug_script():
    print("\n" + "=" * 80)
    print("6. h1_edge_v1.py dosya doğrulaması")
    print("=" * 80)

    if not os.path.exists(H1_EDGE_SCRIPT):
        print(f"  HATA: {H1_EDGE_SCRIPT} bulunamadı.")
        return

    with open(H1_EDGE_SCRIPT, "rb") as f:
        icerik = f.read()
    sha = hashlib.sha256(icerik).hexdigest()
    print(f"  SHA-256: {sha}")
    print(f"  Dosya boyutu: {len(icerik)} byte")

    metin = icerik.decode("utf-8", errors="replace")
    kontroller = {
        "_test_ah_settlement mevcut": "_test_ah_settlement" in metin,
        "fdr_uygula mevcut": "def fdr_uygula" in metin,
        "Test yok metni": "Test yok" in metin,
        "N<100 metni": "N<100" in metin,
        'if r["n"] == 0': 'if r["n"] == 0' in metin,
        'if r["n"] < N_MIN': 'if r["n"] < N_MIN' in metin,
    }
    for k, v in kontroller.items():
        print(f"  {k}: {v}")


# ==================================================================
# ANA
# ==================================================================
def main():
    print("=" * 80)
    print("DEBUG H1 FLOW — Veri akışı teşhisi")
    print("2026/27 (E0 (10).csv) KESİNLİKLE OKUNMAYACAK.")
    print("=" * 80)

    feat = debug_features()
    if feat is None:
        return

    market = debug_market()
    if market is None or len(market) == 0:
        return

    feat, market = debug_keys(feat, market)
    merged = debug_merge(feat, market)

    # ============ DÜZELTME: Movement sütununu merge sonrası oluştur ============
    if len(merged) > 0:
        merged["Movement"] = merged["AHCh"] - merged["AHh"]

    debug_crosstab(merged)
    debug_script()

    print("\n" + "=" * 80)
    print("TEŞHİS TAMAMLANDI")
    print("=" * 80)


if __name__ == "__main__":
    main()