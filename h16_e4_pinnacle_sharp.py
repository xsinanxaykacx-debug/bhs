# -*- coding: utf-8 -*-
"""
h16_e4_pinnacle_sharp.py
H16-E4 FROZEN v1.1 — Pinnacle Sharp vs Retail Lag
Tarih: 2026-10-08

Hipotez:
Pinnacle kapanış fiyatı, sharp son durumu temsil eder. Retail
bookmaker'ın açılış fiyatı, Pinnacle kapanış implied probability'sine
göre yeterince düşükse (gap > 0.02), o retail açılış fiyatından bahis
pozitif edge üretir.

Formül:
  gap = 1/retail_opening_odds - 1/pinnacle_closing_odds
  gap > 0.02 → bahis (retail opening odds)

9 strateji: B365/BW/WH × H/D/A

KİLİTLER:
- E0 (10).csv ASLA OKUNMAZ.
- Referans: Pinnacle KAPANIŞ (PSCH/PSCD/PSCA)
- Retail: B365 + BW + WH (ayrı ayrı)
- Eşik: 0.02 (FROZEN — H15 ile aynı)
- Ortak evren: PS açılış + PS kapanış + B365 + BW + WH açılış
  tam + FTR + Date + 0<odds<=20 → beklenen 3554
- Bahis oranı: retail AÇILIŞ
- Stake: 1
- Settlement: doğru → +(oran-1); yanlış → -1
- BCa 10.000, sign-permutation 10.000, seed=20261008
- MDD bankroll=100, stable kronolojik
- N_MIN=100, ALPHA=0.05, MDD_ESIK=0.20
- BH-FDR: 9 test tek aile, q<0.05
- Karar SADECE OOS üzerinden (Val sadece raporlanır)
- Karar ham değerlerle
- Post-hoc değişiklik YASAK.

KARAR (FROZEN):
- SUPPORTED:      K_ROI ∧ K_GA ∧ K_N ∧ K_P ∧ K_MDD ∧ K_Q
- NOT SUPPORTED:  ROI ≤ 0 VEYA MDD > 0.20
- WEAK/UNCERTAIN: ROI > 0 ve MDD ≤ 0.20 ama en az bir kriter eksik
- KIRMIZI BAYRAK: Train ROI > 0 ∧ OOS ROI < 0

DÜZELTME — 2026-10-08 (Implementation/Data-Integrity Correction)
Feasibility aşamasında hesaplanan 3656 ortak evren sayısının
0 < odds <= 20 koşulunu içermediği tespit edildi. Frozen protokol
bu koşulu zaten içerdiğinden protokol değiştirilmedi. Frozen
maskenin gerçek sonucu 3554 olarak doğrulandı. Bu nedenle yalnızca
beklenen evren kontrol sabiti 3554 olarak düzeltildi. OOS sonuçları
henüz çalıştırılmadı.

ÇIKTI: h16_e4_pinnacle_sharp_results.xlsx
"""

import os
import numpy as np
import pandas as pd
from scipy.stats import norm
from collections import defaultdict
import warnings
warnings.filterwarnings("ignore")

# ==================================================================
# 0. SABİTLER
# ==================================================================
CIKTI = "h16_e4_pinnacle_sharp_results.xlsx"

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

TRAIN_SEZONLAR = ["2015/16", "2016/17", "2017/18", "2018/19",
                  "2019/20", "2020/21", "2021/22", "2022/23"]
VALIDATION_SEZON = "2023/24"
OOS_SEZON = "2024/25"

ESIK = 0.02
N_BOOTSTRAP = 10_000
N_PERMUTATION = 10_000
RANDOM_SEED = 20261008
BANKROLL = 100.0
MDD_ESIK = 0.20
ALPHA = 0.05
N_MIN = 100

STRATEJILER = [
    ("B365", "H"), ("B365", "D"), ("B365", "A"),
    ("BW",   "H"), ("BW",   "D"), ("BW",   "A"),
    ("WH",   "H"), ("WH",   "D"), ("WH",   "A"),
]

BEKLENEN_TOPLAM = 3800
BEKLENEN_ORTAK_EVREN = 3554  # 4 bookmaker ortak, 0<odds<=20

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
    GEREKLI = ["Date", "FTR",
               "PSH", "PSD", "PSA", "PSCH", "PSCD", "PSCA",
               "B365H", "B365D", "B365A",
               "BWH", "BWD", "BWA",
               "WHH", "WHD", "WHA"]

    frames = []
    for dosya, sezon in TUM_DOSYALAR:
        if not os.path.exists(dosya):
            raise RuntimeError(f"EKSİK DOSYA: {dosya}")
        df = _guvenli_oku(dosya)
        eksik = [c for c in GEREKLI if c not in df.columns]
        if eksik:
            raise RuntimeError(f"{dosya}: eksik sütunlar {eksik}")
        df = df.copy()
        df["Season"] = sezon
        frames.append(df[["Season"] + GEREKLI])

    df = pd.concat(frames, ignore_index=True)
    print(f"  Ham toplam satır: {len(df)}")
    if len(df) != BEKLENEN_TOPLAM:
        raise RuntimeError(f"Ham toplam {len(df)} != {BEKLENEN_TOPLAM}")

    # Date parse
    df["Date_p"] = pd.to_datetime(
        df["Date"], dayfirst=True, format="mixed", errors="coerce"
    )

    # Ortak evren maskesi
    ORAN_KOLONLARI = ["PSH", "PSD", "PSA", "PSCH", "PSCD", "PSCA",
                      "B365H", "B365D", "B365A",
                      "BWH", "BWD", "BWA",
                      "WHH", "WHD", "WHA"]

    gecerli = pd.Series(True, index=df.index)
    for c in ORAN_KOLONLARI:
        gecerli &= df[c].notna() & (df[c] > 0) & (df[c] <= 20)

    gecerli &= df["FTR"].isin(["H", "D", "A"])
    gecerli &= df["Date_p"].notna()

    n_dusen = int((~gecerli).sum())
    print(f"  Ortak evren dışı düşen: {n_dusen}")
    df = df[gecerli].copy().reset_index(drop=True)
    print(f"  Ortak evren maç sayısı: {len(df)}")

    if len(df) != BEKLENEN_ORTAK_EVREN:
        raise RuntimeError(
            f"Ortak evren {len(df)} != beklenen {BEKLENEN_ORTAK_EVREN}"
        )

    return df


def bolmeleri_ayir(df):
    train = df[df["Season"].isin(TRAIN_SEZONLAR)].copy().reset_index(drop=True)
    val = df[df["Season"] == VALIDATION_SEZON].copy().reset_index(drop=True)
    oos = df[df["Season"] == OOS_SEZON].copy().reset_index(drop=True)
    print(f"  Train: {len(train)}, Val: {len(val)}, OOS: {len(oos)}")
    return train, val, oos


# ==================================================================
# 2. STRATEJİ SİMÜLASYONU
# ==================================================================
def strateji_simule(df_bolme, retail_prefix, taraf):
    if taraf == "H":
        retail_col = retail_prefix + "H"
        ps_close_col = "PSCH"
    elif taraf == "D":
        retail_col = retail_prefix + "D"
        ps_close_col = "PSCD"
    else:
        retail_col = retail_prefix + "A"
        ps_close_col = "PSCA"

    retail_oran = df_bolme[retail_col].values
    ps_close_oran = df_bolme[ps_close_col].values

    retail_prob = 1.0 / retail_oran
    ps_close_prob = 1.0 / ps_close_oran
    gap = retail_prob - ps_close_prob

    bahis_mask = gap > ESIK
    n_bahis = int(bahis_mask.sum())
    if n_bahis < 5:
        return None

    ftr = df_bolme["FTR"].values
    tarih = df_bolme["Date_p"].values

    ftr_b = ftr[bahis_mask]
    oran_b = retail_oran[bahis_mask]
    tarih_b = tarih[bahis_mask]
    gap_b = gap[bahis_mask]

    kazandi = (ftr_b == taraf)
    pl = np.where(kazandi, oran_b - 1.0, -1.0)

    win = int(kazandi.sum())
    roi = float(pl.mean())

    ci_lo, ci_hi = bca_bootstrap_roi(pl)
    p_perm = permutation_sign(pl)
    mdd = max_drawdown(pl, tarih_b)

    return {
        "Retail": retail_prefix,
        "Taraf": taraf,
        "N": n_bahis,
        "Win": win,
        "Win_pct": round(win / n_bahis * 100, 2),
        "Ort_gap": round(float(gap_b.mean()), 6),
        "Ort_oran": round(float(oran_b.mean()), 4),
        "Net_PL": round(float(pl.sum()), 4),
        "ROI": float(roi),
        "ROI_GA_lo": float(ci_lo) if not np.isnan(ci_lo) else None,
        "ROI_GA_hi": float(ci_hi) if not np.isnan(ci_hi) else None,
        "Perm_p": float(p_perm) if not np.isnan(p_perm) else None,
        "MDD": float(mdd),
    }


# ==================================================================
# 3. BCa
# ==================================================================
def bca_bootstrap_roi(pl, n_boot=N_BOOTSTRAP, seed=RANDOM_SEED):
    if len(pl) < 5:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    n = len(pl)
    theta_hat = pl.mean()

    idx = rng.integers(0, n, size=(n_boot, n))
    boot = pl[idx].mean(axis=1)

    prop_less = np.mean(boot < theta_hat)
    prop_less = min(max(prop_less, 1.0 / (n_boot + 1)), n_boot / (n_boot + 1))
    z0 = norm.ppf(prop_less)

    total = pl.sum()
    jack = (total - pl) / (n - 1) if n > 1 else np.array([pl.mean()])
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

    return float(np.quantile(boot, p_lo)), float(np.quantile(boot, p_hi))


def permutation_sign(pl, n_perm=N_PERMUTATION, seed=RANDOM_SEED):
    n = len(pl)
    if n < 5:
        return np.nan
    rng = np.random.default_rng(seed)
    obs = pl.mean()
    abs_pl = np.abs(pl)
    ekstrem = 0
    for _ in range(n_perm):
        signs = rng.choice([-1.0, 1.0], size=n)
        if abs((abs_pl * signs).mean()) >= abs(obs):
            ekstrem += 1
    return (1 + ekstrem) / (n_perm + 1)


def max_drawdown(pl, tarih):
    if len(pl) == 0:
        return 0.0
    idx = np.argsort(tarih, kind="stable")
    cum = np.cumsum(pl[idx])
    peak = np.maximum.accumulate(cum)
    return float((peak - cum).max() / BANKROLL)


# ==================================================================
# 4. BH-FDR
# ==================================================================
def bh_fdr(p_values, q=0.05):
    n = len(p_values)
    idx_valid = [i for i, p in enumerate(p_values)
                 if p is not None and not np.isnan(p)]
    m = len(idx_valid)
    q_out = [None] * n
    rej_out = [False] * n
    if m == 0:
        return q_out, rej_out
    sorted_idx = sorted(idx_valid, key=lambda i: p_values[i])
    sorted_p = [p_values[i] for i in sorted_idx]
    q_vals = [None] * m
    prev = 1.0
    for k in range(m - 1, -1, -1):
        qk = sorted_p[k] * m / (k + 1)
        qk = min(qk, prev)
        q_vals[k] = qk
        prev = qk
    for k, orig_i in enumerate(sorted_idx):
        q_out[orig_i] = q_vals[k]
        rej_out[orig_i] = q_vals[k] < q
    return q_out, rej_out


# ==================================================================
# 5. KARAR (FROZEN ile birebir)
# ==================================================================
def karar_uygula(d_oos, q_val):
    if d_oos is None:
        return "YETERSIZ_VERI", {}

    roi = d_oos["ROI"]
    ga_lo = d_oos["ROI_GA_lo"]
    n = d_oos["N"]
    p = d_oos["Perm_p"]
    mdd = d_oos["MDD"]

    k_roi = roi is not None and roi > 0
    k_ga = ga_lo is not None and ga_lo > 0
    k_n = n is not None and n >= N_MIN
    k_p = p is not None and p < ALPHA
    k_mdd = mdd is not None and mdd <= MDD_ESIK
    k_q = q_val is not None and q_val < ALPHA

    k_detay = {
        "K_ROI": k_roi, "K_GA": k_ga, "K_N": k_n,
        "K_P": k_p, "K_MDD": k_mdd, "K_Q": k_q,
    }

    # SUPPORTED: bütün kriterler
    if k_roi and k_ga and k_n and k_p and k_mdd and k_q:
        return "SUPPORTED", k_detay

    # NOT SUPPORTED: ROI <= 0 VEYA MDD > 0.20
    if not k_roi or not k_mdd:
        return "NOT SUPPORTED", k_detay

    # WEAK: ROI > 0 ve MDD <= 0.20 ama diğer kriterler eksik
    return "WEAK / UNCERTAIN", k_detay


# ==================================================================
# 6. ANA AKIŞ
# ==================================================================
def main():
    print("=" * 80)
    print("H16-E4 FROZEN v1.1 — Pinnacle Sharp vs Retail Lag")
    print(f"Eşik: gap = 1/retail_opening - 1/ps_close > {ESIK}")
    print("Referans: Pinnacle KAPANIŞ | Retail: B365/BW/WH AÇILIŞ")
    print("9 önceden tanımlanmış strateji")
    print("Karar yalnızca OOS üzerinden")
    print("E0 (10).csv KESİNLİKLE OKUNMAYACAK.")
    print("=" * 80)

    df = veri_yukle()
    train, val, oos = bolmeleri_ayir(df)

    print("\n--- Strateji Simülasyonları ---")
    tum_sonuclar = []
    oos_p_list = []

    for retail_prefix, taraf in STRATEJILER:
        d_train = strateji_simule(train, retail_prefix, taraf)
        d_val = strateji_simule(val, retail_prefix, taraf)
        d_oos = strateji_simule(oos, retail_prefix, taraf)

        tum_sonuclar.append({
            "Retail": retail_prefix, "Taraf": taraf,
            "_train": d_train, "_val": d_val, "_oos": d_oos,
        })
        oos_p_list.append(d_oos["Perm_p"] if d_oos else None)

    q_values, rejected = bh_fdr(oos_p_list, q=ALPHA)
    print("\n--- BH-FDR (9 test, q < 0.05) ---")
    for i, (rp, tf) in enumerate(STRATEJILER):
        print(f"  {rp}-{tf}: p={oos_p_list[i]} q={q_values[i]}")

    print("\n--- KARAR ---")
    karar_satirlari = []

    def r6(x):
        if x is None or pd.isna(x):
            return None
        return round(float(x), 6)

    for i, satir in enumerate(tum_sonuclar):
        d_train = satir["_train"]
        d_val = satir["_val"]
        d_oos = satir["_oos"]
        q = q_values[i]

        karar, k_detay = karar_uygula(d_oos, q)

        train_roi = d_train["ROI"] if d_train else None
        oos_roi = d_oos["ROI"] if d_oos else None
        kirmizi = (
            train_roi is not None and oos_roi is not None
            and train_roi > 0 and oos_roi < 0
        )

        out = {
            "Retail": satir["Retail"], "Taraf": satir["Taraf"],
            "Train_N": d_train["N"] if d_train else 0,
            "Train_ROI": r6(d_train["ROI"]) if d_train else None,
            "Val_N": d_val["N"] if d_val else 0,
            "Val_ROI": r6(d_val["ROI"]) if d_val else None,
            "OOS_N": d_oos["N"] if d_oos else 0,
            "OOS_ROI": r6(d_oos["ROI"]) if d_oos else None,
            "OOS_ROI_GA_lo": r6(d_oos["ROI_GA_lo"]) if d_oos else None,
            "OOS_ROI_GA_hi": r6(d_oos["ROI_GA_hi"]) if d_oos else None,
            "OOS_Perm_p": r6(d_oos["Perm_p"]) if d_oos else None,
            "OOS_q_FDR": r6(q),
            "OOS_MDD": r6(d_oos["MDD"]) if d_oos else None,
            "K_ROI": k_detay.get("K_ROI"),
            "K_GA": k_detay.get("K_GA"),
            "K_N": k_detay.get("K_N"),
            "K_P": k_detay.get("K_P"),
            "K_MDD": k_detay.get("K_MDD"),
            "K_Q": k_detay.get("K_Q"),
            "KIRMIZI_BAYRAK": kirmizi,
            "KARAR": karar,
        }
        karar_satirlari.append(out)
        kb = " ⚠ KIRMIZI BAYRAK" if kirmizi else ""
        print(f"  {satir['Retail']}-{satir['Taraf']:1s} → {karar}{kb}")

    karar_df = pd.DataFrame(karar_satirlari)
    print("\n--- KARAR ÖZETİ ---")
    print(karar_df["KARAR"].value_counts().to_string())
    kb_say = int(karar_df["KIRMIZI_BAYRAK"].sum())
    print(f"\n  KIRMIZI BAYRAK sayısı: {kb_say}")
    if kb_say > 0:
        for _, r in karar_df[karar_df["KIRMIZI_BAYRAK"]].iterrows():
            print(f"    {r['Retail']}-{r['Taraf']}: Train {r['Train_ROI']} → OOS {r['OOS_ROI']}")

    print("\n--- TAM KARAR TABLOSU ---")
    cols = ["Retail", "Taraf", "Train_N", "Train_ROI", "Val_N", "Val_ROI",
            "OOS_N", "OOS_ROI", "OOS_ROI_GA_lo", "OOS_Perm_p",
            "OOS_q_FDR", "OOS_MDD", "KIRMIZI_BAYRAK", "KARAR"]
    print(karar_df[cols].to_string(index=False))

    print(f"\n--- {CIKTI} yazılıyor ---")
    with pd.ExcelWriter(CIKTI, engine="openpyxl") as w:
        karar_df.to_excel(w, sheet_name="Karar", index=False)

        pd.DataFrame([{
            "Protokol": "H16-E4 FROZEN v1.1",
            "Tarih": "2026-10-08",
            "Duzeltme": "Implementation/Data-Integrity Correction: 3656 -> 3554 (0<odds<=20 zaten protokolde vardi)",
            "Hipotez": "Pinnacle closing sharp; retail opening lag; gap>0.02 -> retail opening bahis",
            "Referans": "Pinnacle KAPANIS (PSCH/PSCD/PSCA)",
            "Retail": "B365/BW/WH ACILIS (ayri ayri)",
            "Gap_formulu": "1/retail_opening - 1/ps_close",
            "Esik": ESIK,
            "Strateji_sayisi": 9,
            "Bahis_orani": "retail ACILIS",
            "Settlement": "Dogru: +(oran-1); Yanlis: -1",
            "Ortak_evren": f"PS ac + PS kap + B365 + BW + WH tam + 0<odds<=20, beklenen {BEKLENEN_ORTAK_EVREN}",
            "BCa": "10.000 vektorize, seed=20261008",
            "Permutation": "sign-permutation, 10.000, iki tarafli, seed=20261008",
            "MDD_bankroll": 100,
            "N_MIN": N_MIN, "ALPHA": ALPHA, "MDD_ESIK": MDD_ESIK,
            "BH_FDR": "9 test tek aile, q<0.05",
            "Karar_kaynagi": "Yalnizca OOS (Val sadece raporlanir)",
            "Karar_kurali": "SUPPORTED=hepsi; NOT SUPPORTED=ROI<=0 veya MDD>0.20; WEAK=ROI>0 & MDD<=0.20 & eksik kriter",
            "Kirmizi_bayrak": "Train ROI>0 ve OOS ROI<0",
            "Train": "2015/16 - 2022/23",
            "Validation": "2023/24",
            "OOS": "2024/25",
            "2026_27": "KILITLI - okunmadi",
            "KARAR_OZET": str(karar_df["KARAR"].value_counts().to_dict()),
            "KIRMIZI_BAYRAK_SAYISI": kb_say,
        }]).to_excel(w, sheet_name="Notlar", index=False)

    print(f"\n{CIKTI} yazıldı.")

    print("\n" + "=" * 80)
    print("VERİ BÜTÜNLÜĞÜ VE KANIT")
    print("=" * 80)
    print(f"  Ham toplam: {BEKLENEN_TOPLAM}")
    print(f"  Ortak evren: {len(df)} (beklenen {BEKLENEN_ORTAK_EVREN})")
    print(f"  Train: {len(train)}, Val: {len(val)}, OOS: {len(oos)}")
    print(f"  Okuma sayacı: {dict(_okuma_sayaci)}")
    print(f"  Yasaklılardan hiçbiri okunmadı: "
          f"{all(d not in _okuma_sayaci for d in YASAKLI_DOSYALAR)}")
    print("=" * 80)


if __name__ == "__main__":
    main()