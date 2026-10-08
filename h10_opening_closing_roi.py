# -*- coding: utf-8 -*-
"""
h10_opening_closing_roi.py
H10 FROZEN PROTOKOL v1.1 (REVİZE — Envanter Sonrası)
Tarih: 2026-10-08

REVİZYON GEREKÇESİ:
B365CH/CD/CA kapanış sütunları yalnız 2019/20 – 2024/25 (6 sezon) için mevcut.
2015/16 – 2018/19 için kapanış verisi yoktur (envanter ile tespit edildi).
Bu revizyon HİÇBİR ROI/p/MDD görülmeden yapıldı.
Bant sınırları, karar kriterleri, seed, eşikler DEĞİŞMEDİ.
Sadece bölmeler ve dosya listesi revize edildi.

VERİ BÖLMELERİ:
- Train:      2019/20 – 2022/23  (1520 maç)
- Validation: 2023/24            (380 maç)
- Blind OOS:  2024/25            (380 maç)
- Kilitli:    2026/27 (E0 (10).csv) — ASLA OKUNMAZ

Kapsam:
- Market: B365 1X2 (H/D/A)
- Açılış: B365H, B365D, B365A
- Kapanış: B365CH, B365CD, B365CA
- Movement: (kapanış − açılış) / açılış
- Bant: 6 kova, FROZEN sınırlar [-10%, -5%, 0%, +5%, +10%]
- Bahis: her maçta 3 taraf (H/D/A) bağımsız test edilir
- Stake: 1 birim sabit
- Settlement: Doğru → +(açılış odds − 1); Yanlış → −1
- Odds: AÇILIŞ (B365H/D/A) kullanılır (kapanış sadece sinyal)

KİLİTLER:
- E0 (10).csv ASLA OKUNMAZ.
- Bant sınırları FROZEN.
- Bootstrap: BCa 10.000, seed=20261008
- Permutation: FTR etiketleri, 10.000, iki taraflı, seed=20261008
- MDD: Bankroll 100, stable kronolojik
- Post-hoc değişiklik YASAK.

ÇIKTI: h10_opening_closing_roi_results.xlsx
"""

import os
import numpy as np
import pandas as pd
from scipy.stats import norm
from collections import defaultdict
import warnings
warnings.filterwarnings("ignore")

# ==================================================================
# 0. SABİTLER (KİLİTLİ — v1.1)
# ==================================================================
CIKTI = "h10_opening_closing_roi_results.xlsx"

# Kapanışı olmayan sezonlar da yasaklı — kazayla okunmasınlar
YASAKLI_DOSYALAR = {
    "E0 (10).csv",   # 2026/27 — kör OOS
    "E0.csv",        # 2015/16 — kapanış YOK
    "E0 (1).csv",    # 2016/17 — kapanış YOK
    "E0 (2).csv",    # 2017/18 — kapanış YOK
    "E0 (3).csv",    # 2018/19 — kapanış YOK
}

# Yalnız kapanış verisi olan 6 sezon
TUM_DOSYALAR = [
    ("E0 (4).csv",   "2019/20"),
    ("E0 (5).csv",   "2020/21"),
    ("E0 (6).csv",   "2021/22"),
    ("E0 (7).csv",   "2022/23"),
    ("E0 (8).csv",   "2023/24"),
    ("E0 (9).csv",   "2024/25"),
]

TRAIN_SEZONLAR = ["2019/20", "2020/21", "2021/22", "2022/23"]
VALIDATION_SEZON = "2023/24"
OOS_SEZON = "2024/25"

# Bant sınırları — FROZEN
BANT_SINIRLARI = [-np.inf, -0.10, -0.05, 0.00, 0.05, 0.10, np.inf]
BANT_ETIKETLERI = [
    "[-inf, -10%]",
    "(-10%, -5%]",
    "(-5%, 0%]",
    "(0%, +5%]",
    "(+5%, +10%]",
    "(+10%, +inf]",
]

# İstatistiksel parametreler
N_BOOTSTRAP = 10_000
N_PERMUTATION = 10_000
RANDOM_SEED = 20261008
BANKROLL = 100.0
MDD_ESIK = 0.20
ALPHA = 0.05
N_MIN = 100

BEKLENEN_TOPLAM = 2280     # 6 × 380
BEKLENEN_TRAIN = 1520      # 4 × 380
BEKLENEN_VAL = 380
BEKLENEN_OOS = 380

_okuma_sayaci = defaultdict(int)


# ==================================================================
# 1. VERİ YÜKLEME
# ==================================================================
def _guvenli_oku(dosya):
    ad = os.path.basename(dosya)
    if ad in YASAKLI_DOSYALAR:
        raise RuntimeError(f"YASAKLI DOSYA OKUNAMAZ: {ad}")
    _okuma_sayaci[ad] += 1
    return pd.read_csv(dosya, encoding="utf-8-sig")


def veri_yukle():
    print("\n--- Veri yükleniyor ---")

    GEREKLI = ["Date", "HomeTeam", "AwayTeam", "FTR",
               "B365H", "B365D", "B365A",
               "B365CH", "B365CD", "B365CA"]

    frames = []
    for dosya, sezon in TUM_DOSYALAR:
        if not os.path.exists(dosya):
            raise RuntimeError(f"EKSİK DOSYA: {dosya}")
        df = _guvenli_oku(dosya)
        eksik = [c for c in GEREKLI if c not in df.columns]
        if eksik:
            raise RuntimeError(f"{dosya}: eksik sütunlar {eksik}")
        df["Season"] = sezon
        frames.append(df[["Season"] + GEREKLI].copy())

    df = pd.concat(frames, ignore_index=True)
    print(f"  Ham toplam satır: {len(df)}")
    if len(df) != BEKLENEN_TOPLAM:
        raise RuntimeError(f"Ham toplam {len(df)} != {BEKLENEN_TOPLAM}")

    ORAN_SUTUNLARI = ["B365H", "B365D", "B365A", "B365CH", "B365CD", "B365CA"]

    print("\n  Oran sütunu temizlik raporu:")
    for c in ORAN_SUTUNLARI:
        n_nan = int(df[c].isna().sum())
        n_neg = int((df[c] <= 0).sum())
        print(f"    {c:10s} NaN={n_nan:3d}  ≤0={n_neg:3d}")

    gecerli_mask = np.ones(len(df), dtype=bool)
    for c in ORAN_SUTUNLARI:
        gecerli_mask &= df[c].notna().values
        gecerli_mask &= (df[c] > 0).values

    n_dusen = int((~gecerli_mask).sum())
    print(f"\n  Toplam düşen satır: {n_dusen}")
    print(f"  Temizlik öncesi: {len(df)}")
    df = df[gecerli_mask].copy().reset_index(drop=True)
    print(f"  Temizlik sonrası: {len(df)}")

    return df


# ==================================================================
# 2. HAREKET HESABI
# ==================================================================
def hareket_hesapla(df):
    df = df.copy()
    df["mov_H"] = (df["B365CH"] - df["B365H"]) / df["B365H"]
    df["mov_D"] = (df["B365CD"] - df["B365D"]) / df["B365D"]
    df["mov_A"] = (df["B365CA"] - df["B365A"]) / df["B365A"]
    return df


def bant_ata(mov):
    """mov değerini bant etiketine çevir. (sol açık, sağ kapalı)"""
    for i in range(len(BANT_SINIRLARI) - 1):
        alt = BANT_SINIRLARI[i]
        ust = BANT_SINIRLARI[i + 1]
        if mov > alt and mov <= ust:
            return BANT_ETIKETLERI[i]
    return None


# ==================================================================
# 3. BÖLME
# ==================================================================
def bolmeleri_ayir(df):
    train = df[df["Season"].isin(TRAIN_SEZONLAR)].copy().reset_index(drop=True)
    val = df[df["Season"] == VALIDATION_SEZON].copy().reset_index(drop=True)
    oos = df[df["Season"] == OOS_SEZON].copy().reset_index(drop=True)

    print(f"\n  Bölme boyutları (temizlik sonrası):")
    print(f"    Train: {len(train)} (beklenen {BEKLENEN_TRAIN}, fark {len(train) - BEKLENEN_TRAIN})")
    print(f"    Val:   {len(val)} (beklenen {BEKLENEN_VAL}, fark {len(val) - BEKLENEN_VAL})")
    print(f"    OOS:   {len(oos)} (beklenen {BEKLENEN_OOS}, fark {len(oos) - BEKLENEN_OOS})")

    return train, val, oos


# ==================================================================
# 4. BANT × TARAF ANALİZİ (ham ROI)
# ==================================================================
def bant_analiz(df_bolme, etiket):
    taraf_map = [("H", "mov_H", "B365H"),
                 ("D", "mov_D", "B365D"),
                 ("A", "mov_A", "B365A")]

    sonuclar = []
    for taraf, mov_kol, odds_kol in taraf_map:
        for bant in BANT_ETIKETLERI:
            mask = df_bolme[mov_kol].apply(lambda x: bant_ata(x) == bant)
            alt = df_bolme[mask]
            n = len(alt)

            if n == 0:
                sonuclar.append({
                    "Bolme": etiket, "Taraf": taraf, "Bant": bant,
                    "N": 0, "Win": 0, "Win_pct": None,
                    "Ort_oran": None, "Net_PL": None, "ROI": None,
                })
                continue

            kazandi = (alt["FTR"] == taraf).values
            odds = alt[odds_kol].values
            pl = np.where(kazandi, odds - 1.0, -1.0)

            sonuclar.append({
                "Bolme": etiket, "Taraf": taraf, "Bant": bant,
                "N": n, "Win": int(kazandi.sum()),
                "Win_pct": round(kazandi.sum() / n * 100, 2),
                "Ort_oran": round(float(odds.mean()), 4),
                "Net_PL": round(float(pl.sum()), 4),
                "ROI": round(float(pl.mean()), 4),
            })

    return pd.DataFrame(sonuclar)


# ==================================================================
# 5. BCa BOOTSTRAP (ROI)
# ==================================================================
def bca_bootstrap_roi(pl, n_boot=N_BOOTSTRAP, seed=RANDOM_SEED):
    if len(pl) < 5:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    n = len(pl)
    theta_hat = pl.mean()

    boot = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n, size=n)
        boot[b] = pl[idx].mean()

    prop_less = np.mean(boot < theta_hat)
    prop_less = min(max(prop_less, 1.0 / (n_boot + 1)), n_boot / (n_boot + 1))
    z0 = norm.ppf(prop_less)

    jack = np.array([np.delete(pl, i).mean() for i in range(n)])
    jm = jack.mean()
    num = ((jm - jack) ** 3).sum()
    den = 6.0 * (((jm - jack) ** 2).sum() ** 1.5)
    a = num / den if den != 0 else 0.0

    z_lo = norm.ppf(0.025)
    z_hi = norm.ppf(0.975)

    def _p(z):
        nn = z0 + z
        dd = 1 - a * nn
        return norm.cdf(z0 + nn / dd) if dd != 0 else np.nan

    p_lo = min(max(_p(z_lo), 0.0), 1.0)
    p_hi = min(max(_p(z_hi), 0.0), 1.0)

    ci_lo = float(np.quantile(boot, p_lo))
    ci_hi = float(np.quantile(boot, p_hi))
    return ci_lo, ci_hi


# ==================================================================
# 6. PERMUTATION (FTR etiketleri)
# ==================================================================
def permutation_test_ftr(ftr_arr, bahis_taraf, odds_arr,
                        n_perm=N_PERMUTATION, seed=RANDOM_SEED):
    """
    FTR etiketleri permüte edilir; bahis_taraf ve odds_arr sabit kalır.
    Her permütasyonda P/L yeniden hesaplanır.
    p = (1 + ekstrem) / (n_perm + 1), iki taraflı (|mean| karşılaştırması).
    """
    n = len(ftr_arr)
    if n < 5:
        return np.nan

    rng = np.random.default_rng(seed)

    def _pl(ftr):
        kazandi = (ftr == bahis_taraf)
        return np.where(kazandi, odds_arr - 1.0, -1.0)

    obs = _pl(ftr_arr).mean()
    ekstrem = 0
    for _ in range(n_perm):
        perm_ftr = rng.permutation(ftr_arr)
        if abs(_pl(perm_ftr).mean()) >= abs(obs):
            ekstrem += 1

    return (1 + ekstrem) / (n_perm + 1)


# ==================================================================
# 7. MDD (stabil sıralama)
# ==================================================================
def max_drawdown(pl, tarih):
    if len(pl) == 0:
        return 0.0
    idx = np.argsort(tarih, kind="stable")
    pl_sorted = pl[idx]
    cum = np.cumsum(pl_sorted)
    peak = np.maximum.accumulate(cum)
    dd = peak - cum
    return float(dd.max() / BANKROLL)


# ==================================================================
# 8. HÜCRE DETAYI
# ==================================================================
def hucre_detay(df_bolme, taraf, mov_kol, odds_kol, bant):
    mask = df_bolme[mov_kol].apply(lambda x: bant_ata(x) == bant)
    alt = df_bolme[mask].copy()

    n = len(alt)
    if n < 5:
        return None

    ftr = alt["FTR"].values
    odds = alt[odds_kol].values
    kazandi = (ftr == taraf)
    pl = np.where(kazandi, odds - 1.0, -1.0)

    tarih = pd.to_datetime(alt["Date"], dayfirst=True, errors="coerce").values

    ci_lo, ci_hi = bca_bootstrap_roi(pl)
    p_perm = permutation_test_ftr(ftr, taraf, odds)
    mdd = max_drawdown(pl, tarih)

    return {
        "N": n,
        "Win": int(kazandi.sum()),
        "Win_pct": round(kazandi.sum() / n * 100, 2),
        "Ort_oran": round(float(odds.mean()), 4),
        "Net_PL": round(float(pl.sum()), 4),
        "ROI": round(float(pl.mean()), 4),
        "ROI_GA_lo": round(ci_lo, 4) if not np.isnan(ci_lo) else None,
        "ROI_GA_hi": round(ci_hi, 4) if not np.isnan(ci_hi) else None,
        "Perm_p": round(p_perm, 4) if not np.isnan(p_perm) else None,
        "MDD": round(mdd, 4),
    }


# ==================================================================
# 9. KARAR
# ==================================================================
def karar_uygula(detay_oos, detay_val):
    if detay_oos is None or detay_val is None:
        return "YETERSIZ_VERI"

    roi = detay_oos["ROI"]
    ga_lo = detay_oos["ROI_GA_lo"]
    n = detay_oos["N"]
    p = detay_oos["Perm_p"]
    mdd = detay_oos["MDD"]
    roi_v = detay_val["ROI"]

    k_roi = roi is not None and roi > 0
    k_ga = ga_lo is not None and ga_lo > 0
    k_n = n >= N_MIN
    k_p = p is not None and p < ALPHA
    k_mdd = mdd is not None and mdd <= MDD_ESIK
    k_val = roi_v is not None and roi_v > 0

    if k_roi and k_ga and k_n and k_p and k_mdd and k_val:
        return "SUPPORTED"
    elif roi is not None and roi > 0:
        return "WEAK / UNCERTAIN"
    else:
        return "NOT SUPPORTED"


# ==================================================================
# 10. ANA AKIŞ
# ==================================================================
def main():
    print("=" * 80)
    print("H10 FROZEN PROTOKOL v1.1 — Opening → Closing Hareketi → ROI")
    print("E0 (10).csv + kapanışsız 4 sezon KESİNLİKLE OKUNMAYACAK.")
    print("Bant sınırları FROZEN: [-10%, -5%, 0%, +5%, +10%]")
    print("Train: 2019/20 – 2022/23 | Val: 2023/24 | OOS: 2024/25")
    print("=" * 80)

    df = veri_yukle()
    df = hareket_hesapla(df)

    train, val, oos = bolmeleri_ayir(df)

    print("\n--- Bant × Taraf Analizi ---")
    tab_train = bant_analiz(train, "Train")
    tab_val = bant_analiz(val, "Validation")
    tab_oos = bant_analiz(oos, "OOS")

    print("\n[TRAIN]")
    print(tab_train.to_string(index=False))
    print("\n[VALIDATION]")
    print(tab_val.to_string(index=False))
    print("\n[OOS]")
    print(tab_oos.to_string(index=False))

    print("\n--- OOS Detaylı Hücre Analizi ---")
    taraf_map = [("H", "mov_H", "B365H"),
                 ("D", "mov_D", "B365D"),
                 ("A", "mov_A", "B365A")]

    karar_satirlari = []
    for taraf, mov_kol, odds_kol in taraf_map:
        for bant in BANT_ETIKETLERI:
            d_val = hucre_detay(val, taraf, mov_kol, odds_kol, bant)
            d_oos = hucre_detay(oos, taraf, mov_kol, odds_kol, bant)
            if d_oos is None:
                continue

            d_train = hucre_detay(train, taraf, mov_kol, odds_kol, bant)

            karar = karar_uygula(d_oos, d_val)

            satir = {
                "Taraf": taraf, "Bant": bant,
                "Train_N": d_train["N"] if d_train else 0,
                "Train_ROI": d_train["ROI"] if d_train else None,
                "Val_N": d_val["N"] if d_val else 0,
                "Val_ROI": d_val["ROI"] if d_val else None,
                "OOS_N": d_oos["N"],
                "OOS_Win_pct": d_oos["Win_pct"],
                "OOS_Ort_oran": d_oos["Ort_oran"],
                "OOS_Net_PL": d_oos["Net_PL"],
                "OOS_ROI": d_oos["ROI"],
                "OOS_ROI_GA_lo": d_oos["ROI_GA_lo"],
                "OOS_ROI_GA_hi": d_oos["ROI_GA_hi"],
                "OOS_Perm_p": d_oos["Perm_p"],
                "OOS_MDD": d_oos["MDD"],
                "KARAR": karar,
            }
            karar_satirlari.append(satir)

            if karar == "SUPPORTED":
                print(f"  ✅ SUPPORTED: {taraf} / {bant} "
                      f"N={d_oos['N']} ROI={d_oos['ROI']} "
                      f"GA=[{d_oos['ROI_GA_lo']}, {d_oos['ROI_GA_hi']}] "
                      f"p={d_oos['Perm_p']} MDD={d_oos['MDD']}")

    karar_df = pd.DataFrame(karar_satirlari)

    print("\n--- KARAR ÖZETİ ---")
    if len(karar_df) > 0:
        print(karar_df["KARAR"].value_counts().to_string())
    else:
        print("  Hücre bulunamadı.")

    print("\n--- OOS En İyi 5 Hücre (ROI'ye göre) ---")
    if len(karar_df) > 0:
        top5 = karar_df.sort_values("OOS_ROI", ascending=False).head(5)
        cols = ["Taraf", "Bant", "Train_ROI", "Val_ROI", "OOS_N",
                "OOS_ROI", "OOS_ROI_GA_lo", "OOS_Perm_p", "OOS_MDD", "KARAR"]
        print(top5[cols].to_string(index=False))

    print(f"\n--- {CIKTI} yazılıyor ---")
    with pd.ExcelWriter(CIKTI, engine="openpyxl") as w:
        tab_train.to_excel(w, sheet_name="Band_Train", index=False)
        tab_val.to_excel(w, sheet_name="Band_Validation", index=False)
        tab_oos.to_excel(w, sheet_name="Band_OOS", index=False)
        karar_df.to_excel(w, sheet_name="Karar", index=False)

        pd.DataFrame([{
            "Protokol": "H10 FROZEN v1.1 (revize)",
            "Tarih": "2026-10-08",
            "Revizyon_gerekcesi": "B365CH/CD/CA yalniz 2019/20-2024/25 (6 sezon)",
            "Baglam": "Zincir 1 devami — fiyat hareketi -> ROI",
            "Movement": "(kapanis - acilis) / acilis",
            "Bant_sinirlari": "[-10%, -5%, 0%, +5%, +10%] (FROZEN)",
            "Odds": "ACILIS (B365H/D/A)",
            "Stake": 1,
            "Settlement": "Dogru: +(acilis_odds-1); Yanlis: -1",
            "Bootstrap": "BCa 10.000, seed=20261008",
            "Permutation": "FTR etiketleri, 10.000, iki tarafli, seed=20261008",
            "MDD_bankroll": 100,
            "MDD_sort": "stable (ayni tarihli maclar CSV sirasinda)",
            "N_min": N_MIN,
            "ALPHA": ALPHA,
            "MDD_esik": MDD_ESIK,
            "Train": "2019/20 - 2022/23 (1520)",
            "Validation": "2023/24 (380)",
            "OOS": "2024/25 (380)",
            "2026_27": "KILITLI - okunmadi",
            "Kapanissiz_sezonlar": "2015/16 - 2018/19 KULLANILMADI",
        }]).to_excel(w, sheet_name="Notlar", index=False)

    print(f"\n{CIKTI} başarıyla yazıldı.")

    print("\n" + "=" * 80)
    print("VERİ BÜTÜNLÜĞÜ VE KANIT")
    print("=" * 80)
    print(f"  Toplam: {len(df)}")
    print(f"  Train N: {len(train)}")
    print(f"  Val N:   {len(val)}")
    print(f"  OOS N:   {len(oos)}")
    print(f"  Okuma sayacı: {dict(_okuma_sayaci)}")
    print(f"  Yasaklı dosyalar (okunmadı): {sorted(YASAKLI_DOSYALAR)}")
    print("=" * 80)


if __name__ == "__main__":
    main()