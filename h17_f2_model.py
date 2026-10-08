# -*- coding: utf-8 -*-
"""
h17_f2_model.py
H17-F2 — Train-Only LightGBM Model + Residual Betting
Tarih: 2026-10-08

Hipotez:
EPL'de maç öncesi takım/form bağlamından öğrenilen LightGBM model
olasılığı ile B365 açılış piyasa olasılığı arasındaki sistematik
residual, bağımsız bir ekonomik bahis sinyali içerir.

KİLİTLER (H17-F1 FROZEN):
- Model: LightGBM Multiclass (>= 4.0)
- Feature: 49 pre-match (h1_features_v2.csv)
- NaN: Native LightGBM (imputation YOK)
- Train: SADECE 2015/16 – 2022/23 (3040)
- Validation: 2023/24 (380) — sadece tahmin
- OOS: 2024/25 (380) — kör
- 2026/27: ASLA OKUNMAZ
- Market prob: 1 / B365 açılış (overround düzeltmesi YOK)
- Residual: P_model − P_market
- Bet: Her maçta max residual > 0.02 → o tarafa 1 bahis
- Stake: 1
- Settlement: doğru → +(oran-1); yanlış → -1
- BCa 10.000, sign-perm 10.000, seed=20261008
- MDD bankroll=100, stable
- BH-FDR tek aile, q<0.05
- N_MIN=100, ALPHA=0.05, MDD_ESIK=0.20
- Hyperparam search YOK, early stopping YOK
- Feature selection YOK, ensemble YOK

ÇIKTI: h17_f2_model_results.xlsx
"""

import os
import sys
import platform
import numpy as np
import pandas as pd
from scipy.stats import norm
from collections import defaultdict
import warnings
warnings.filterwarnings("ignore")

# ==================================================================
# 0. SABİTLER
# ==================================================================
H1_FEATURES = "h1_features_v2.csv"
CIKTI = "h17_f2_model_results.xlsx"

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

FEATURES = [
    "Home_Elo_Pre", "Away_Elo_Pre", "Elo_Diff",
    "Home_Form3_Pre", "Home_Form5_Pre", "Home_Form10_Pre",
    "Away_Form3_Pre", "Away_Form5_Pre", "Away_Form10_Pre",
    "Form3_Diff", "Form5_Diff", "Form10_Diff",
    "Home_HomeForm3_Pre", "Home_HomeForm5_Pre", "Home_HomeForm10_Pre",
    "Away_AwayForm3_Pre", "Away_AwayForm5_Pre", "Away_AwayForm10_Pre",
    "HomeForm3_Diff", "HomeForm5_Diff", "HomeForm10_Diff",
    "Home_GoalAvg5_Pre", "Home_GoalAvg10_Pre",
    "Away_GoalAvg5_Pre", "Away_GoalAvg10_Pre",
    "Home_GoalAgainstAvg5_Pre", "Home_GoalAgainstAvg10_Pre",
    "Away_GoalAgainstAvg5_Pre", "Away_GoalAgainstAvg10_Pre",
    "Home_GD5_Pre", "Home_GD10_Pre",
    "Away_GD5_Pre", "Away_GD10_Pre",
    "Home_HomeGoalAvg5_Pre", "Home_HomeGoalAvg10_Pre",
    "Away_AwayGoalAvg5_Pre", "Away_AwayGoalAvg10_Pre",
    "Home_HomeGoalAgainstAvg5_Pre", "Home_HomeGoalAgainstAvg10_Pre",
    "Away_AwayGoalAgainstAvg5_Pre", "Away_AwayGoalAgainstAvg10_Pre",
    "Home_HomeGD5_Pre", "Home_HomeGD10_Pre",
    "Away_AwayGD5_Pre", "Away_AwayGD10_Pre",
    "Home_RestDays", "Away_RestDays",
    "Home_MatchesPlayed", "Away_MatchesPlayed",
]

LGBM_PARAMS = {
    "objective": "multiclass",
    "num_class": 3,
    "metric": "multi_logloss",
    "boosting_type": "gbdt",
    "num_leaves": 31,
    "learning_rate": 0.05,
    "n_estimators": 300,
    "max_depth": -1,
    "min_child_samples": 20,
    "subsample": 1.0,
    "colsample_bytree": 1.0,
    "reg_alpha": 0.0,
    "reg_lambda": 0.0,
    "random_state": 20261008,
    "n_jobs": -1,
    "verbose": -1,
}

ESIK = 0.02
N_BOOTSTRAP = 10_000
N_PERMUTATION = 10_000
RANDOM_SEED = 20261008
BANKROLL = 100.0
MDD_ESIK = 0.20
ALPHA = 0.05
N_MIN = 100

_okuma_sayaci = defaultdict(int)


# ==================================================================
# 1. ORTAM KANITI
# ==================================================================
def ortam_bilgisi():
    print("=" * 80)
    print("H17-F2 — Train-Only LightGBM Model + Residual Betting")
    print("=" * 80)
    print(f"  Python:   {sys.version.split()[0]}")
    print(f"  Platform: {platform.platform()}")
    try:
        import lightgbm as lgb
        print(f"  LightGBM: {lgb.__version__}")
    except ImportError:
        raise RuntimeError("LightGBM kurulu değil. pip install lightgbm")


# ==================================================================
# 2. VERİ YÜKLEME
# ==================================================================
def _guvenli_oku(dosya):
    ad = os.path.basename(dosya)
    if ad in YASAKLI_DOSYALAR:
        raise RuntimeError(f"YASAKLI DOSYA OKUNAMAZ: {ad}")
    _okuma_sayaci[ad] += 1
    return pd.read_csv(dosya, encoding="utf-8-sig")


def ham_veri_yukle():
    """H1 features + ham EPL B365 açılış birleştirme."""
    print("\n--- Ham veri yükleniyor ---")

    if not os.path.exists(H1_FEATURES):
        raise RuntimeError(f"{H1_FEATURES} bulunamadı.")
    h1 = pd.read_csv(H1_FEATURES, encoding="utf-8-sig")
    print(f"  H1: {len(h1)} satır, {len(h1.columns)} sütun")

    # Ham EPL
    raw_frames = []
    for dosya, sezon in TUM_DOSYALAR:
        if not os.path.exists(dosya):
            raise RuntimeError(f"EKSİK DOSYA: {dosya}")
        df = _guvenli_oku(dosya)
        df = df.copy()
        df["Season"] = sezon
        raw_frames.append(df[["Season", "Date", "HomeTeam", "AwayTeam",
                              "B365H", "B365D", "B365A"]])
    raw = pd.concat(raw_frames, ignore_index=True)
    print(f"  Ham EPL: {len(raw)} satır")

    # Merge
    merged = h1.merge(raw, on=["Season", "Date", "HomeTeam", "AwayTeam"],
                      how="inner")
    print(f"  Merge sonrası: {len(merged)}")
    if len(merged) != 3800:
        raise RuntimeError(f"Merge {len(merged)} != 3800")

    # B365 kontrol
    for c in ["B365H", "B365D", "B365A"]:
        n_nan = int(merged[c].isna().sum())
        n_le0 = int((merged[c] <= 0).sum())
        if n_nan > 0 or n_le0 > 0:
            raise RuntimeError(f"{c}: NaN={n_nan}, ≤0={n_le0}")

    return merged


# ==================================================================
# 3. BÖLME
# ==================================================================
def bolmeleri_ayir(df):
    train = df[df["Season"].isin(TRAIN_SEZONLAR)].copy().reset_index(drop=True)
    val = df[df["Season"] == VALIDATION_SEZON].copy().reset_index(drop=True)
    oos = df[df["Season"] == OOS_SEZON].copy().reset_index(drop=True)
    print(f"\n  Train: {len(train)}")
    print(f"  Val:   {len(val)}")
    print(f"  OOS:   {len(oos)}")
    if len(train) != 3040:
        raise RuntimeError(f"Train {len(train)} != 3040")
    if len(val) != 380:
        raise RuntimeError(f"Val {len(val)} != 380")
    if len(oos) != 380:
        raise RuntimeError(f"OOS {len(oos)} != 380")
    return train, val, oos


# ==================================================================
# 4. MODEL EĞİTİMİ
# ==================================================================
def model_egit(train):
    import lightgbm as lgb

    print("\n--- Model eğitiliyor (YALNIZCA Train 3040) ---")
    X_train = train[FEATURES].values
    y_train = train["FTR"].values

    model = lgb.LGBMClassifier(**LGBM_PARAMS)
    model.fit(X_train, y_train)

    classes = list(model.classes_)
    print(f"  Model fit edildi.")
    print(f"  Classes: {classes}")

    # Kritik doğrulama
    if set(classes) != {"H", "D", "A"}:
        raise RuntimeError(f"Beklenmeyen sınıflar: {classes}")

    return model, classes


# ==================================================================
# 5. TAHMİN + RESIDUAL
# ==================================================================
def tahmin_ve_bahis(df_bolme, model, classes):
    """Bir bölme için P_model, P_market, residual ve bahis P/L hesapla."""
    X = df_bolme[FEATURES].values
    proba = model.predict_proba(X)

    # classes_ üzerinden KESİN eşleme (sessiz indeksleme yok)
    idx_H = classes.index("H")
    idx_D = classes.index("D")
    idx_A = classes.index("A")

    p_model_H = proba[:, idx_H]
    p_model_D = proba[:, idx_D]
    p_model_A = proba[:, idx_A]

    b365H = df_bolme["B365H"].values
    b365D = df_bolme["B365D"].values
    b365A = df_bolme["B365A"].values

    p_market_H = 1.0 / b365H
    p_market_D = 1.0 / b365D
    p_market_A = 1.0 / b365A

    res_H = p_model_H - p_market_H
    res_D = p_model_D - p_market_D
    res_A = p_model_A - p_market_A

    # En yüksek residual
    residuals = np.vstack([res_H, res_D, res_A]).T  # N × 3
    max_res = residuals.max(axis=1)
    max_taraf = residuals.argmax(axis=1)  # 0=H, 1=D, 2=A

    bahis_mask = max_res > ESIK
    n_bahis = int(bahis_mask.sum())

    ftr = df_bolme["FTR"].values
    tarih = pd.to_datetime(df_bolme["Date"], dayfirst=True,
                          format="mixed", errors="coerce").values

    # P/L hesapla (yalnız bahis yapılan maçlar)
    idx_b = np.where(bahis_mask)[0]
    ftr_b = ftr[idx_b]
    taraf_b = max_taraf[idx_b]
    oran_b = np.where(taraf_b == 0, b365H[idx_b],
             np.where(taraf_b == 1, b365D[idx_b], b365A[idx_b]))
    tarih_b = tarih[idx_b]

    taraf_str = np.where(taraf_b == 0, "H",
                np.where(taraf_b == 1, "D", "A"))
    kazandi = (ftr_b == taraf_str)
    pl = np.where(kazandi, oran_b - 1.0, -1.0)

    return {
        "n_bahis": n_bahis,
        "bahis_mask": bahis_mask,
        "max_res": max_res,
        "max_taraf": max_taraf,
        "pl": pl,
        "oran_b": oran_b,
        "tarih_b": tarih_b,
        "ftr_b": ftr_b,
        "taraf_b": taraf_b,
        "max_res_b": max_res[idx_b],
    }


# ==================================================================
# 6. BCa
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
# 7. BÖLME ÖZET
# ==================================================================
def bolme_ozet(bilgi, etiket):
    n = bilgi["n_bahis"]
    if n < 5:
        return {
            "Bolme": etiket, "N": n, "ROI": None,
            "ROI_GA_lo": None, "ROI_GA_hi": None,
            "Perm_p": None, "MDD": None, "Net_PL": None,
            "Win_pct": None, "Ort_oran": None, "Ort_max_res": None,
        }

    pl = bilgi["pl"]
    oran = bilgi["oran_b"]
    tarih = bilgi["tarih_b"]
    max_res = bilgi["max_res_b"]

    win = int((pl > 0).sum())
    roi = float(pl.mean())
    net = float(pl.sum())

    ci_lo, ci_hi = bca_bootstrap_roi(pl)
    p_perm = permutation_sign(pl)
    mdd = max_drawdown(pl, tarih)

    return {
        "Bolme": etiket,
        "N": n,
        "Win": win,
        "Win_pct": round(win / n * 100, 2),
        "Ort_oran": round(float(oran.mean()), 4),
        "Ort_max_res": round(float(max_res.mean()), 6),
        "Net_PL": round(net, 4),
        "ROI": float(roi),
        "ROI_GA_lo": float(ci_lo) if not np.isnan(ci_lo) else None,
        "ROI_GA_hi": float(ci_hi) if not np.isnan(ci_hi) else None,
        "Perm_p": float(p_perm) if not np.isnan(p_perm) else None,
        "MDD": float(mdd),
    }


# ==================================================================
# 8. KARAR
# ==================================================================
def karar_uygula(d_oos):
    if d_oos is None or d_oos["N"] < 5:
        return "YETERSIZ_VERI", {}

    roi = d_oos["ROI"]
    ga_lo = d_oos["ROI_GA_lo"]
    n = d_oos["N"]
    p = d_oos["Perm_p"]
    mdd = d_oos["MDD"]

    k_roi = roi is not None and roi > 0
    k_ga = ga_lo is not None and ga_lo > 0
    k_n = n >= N_MIN
    k_p = p is not None and p < ALPHA
    k_mdd = mdd is not None and mdd <= MDD_ESIK
    # Tek test olduğu için BH-FDR q = p (raporlama amaçlı)
    k_q = k_p

    k_detay = {
        "K_ROI": k_roi, "K_GA": k_ga, "K_N": k_n,
        "K_P": k_p, "K_MDD": k_mdd, "K_Q": k_q,
    }

    if k_roi and k_ga and k_n and k_p and k_mdd and k_q:
        return "SUPPORTED", k_detay
    if not k_roi or not k_mdd:
        return "NOT SUPPORTED", k_detay
    return "WEAK / UNCERTAIN", k_detay


# ==================================================================
# 9. ANA
# ==================================================================
def main():
    ortam_bilgisi()

    df = ham_veri_yukle()
    train, val, oos = bolmeleri_ayir(df)

    model, classes = model_egit(train)

    print("\n--- Feature importance (top 10) ---")
    try:
        fi = model.feature_importances_
        fi_df = pd.DataFrame({
            "Feature": FEATURES,
            "Importance": fi,
        }).sort_values("Importance", ascending=False).head(10)
        print(fi_df.to_string(index=False))
    except Exception as e:
        print(f"  Feature importance alınamadı: {e}")
        fi_df = pd.DataFrame()

    print("\n--- Tahmin + Residual (Train / Val / OOS) ---")
    b_train = tahmin_ve_bahis(train, model, classes)
    b_val = tahmin_ve_bahis(val, model, classes)
    b_oos = tahmin_ve_bahis(oos, model, classes)

    print(f"  Train bahis: {b_train['n_bahis']} / {len(train)}")
    print(f"  Val bahis:   {b_val['n_bahis']} / {len(val)}")
    print(f"  OOS bahis:   {b_oos['n_bahis']} / {len(oos)}")

    ozet_train = bolme_ozet(b_train, "Train")
    ozet_val = bolme_ozet(b_val, "Validation")
    ozet_oos = bolme_ozet(b_oos, "OOS")

    ozet_df = pd.DataFrame([ozet_train, ozet_val, ozet_oos])
    print("\n--- Bölme Özet ---")
    print(ozet_df.to_string(index=False))

    # Karar
    print("\n--- KARAR ---")
    karar, k_detay = karar_uygula(ozet_oos)
    print(f"  {karar}")

    train_roi = ozet_train["ROI"]
    oos_roi = ozet_oos["ROI"]
    kirmizi = (train_roi is not None and oos_roi is not None
               and train_roi > 0 and oos_roi < 0)
    if kirmizi:
        print(f"  ⚠ KIRMIZI BAYRAK: Train ROI={train_roi} > 0, OOS ROI={oos_roi} < 0")

    print("\n  Kriter detayı (OOS):")
    for k, v in k_detay.items():
        print(f"    {k}: {v}")

    # Excel
    print(f"\n--- {CIKTI} yazılıyor ---")
    import lightgbm as lgb

    with pd.ExcelWriter(CIKTI, engine="openpyxl") as w:
        ozet_df.to_excel(w, sheet_name="Ozet", index=False)

        pd.DataFrame([{
            "Protokol": "H17-F2",
            "Tarih": "2026-10-08",
            "Python": sys.version.split()[0],
            "LightGBM": lgb.__version__,
            "Model": "LightGBM Multiclass",
            "num_leaves": 31,
            "learning_rate": 0.05,
            "n_estimators": 300,
            "min_child_samples": 20,
            "random_state": 20261008,
            "Classes": str(classes),
            "Features": len(FEATURES),
            "NaN_strategy": "Native LightGBM",
            "Esik": ESIK,
            "Market_prob": "1/B365_acilis (overround yok)",
            "Residual": "P_model - P_market",
            "Bet_rule": "max residual > 0.02, max 1 bet",
            "Stake": 1,
            "Settlement": "Dogru: +(oran-1); Yanlis: -1",
            "BCa": "10.000, seed=20261008",
            "Permutation": "10.000, iki tarafli, seed=20261008",
            "MDD_bankroll": 100,
            "N_MIN": N_MIN, "ALPHA": ALPHA, "MDD_ESIK": MDD_ESIK,
            "Train": "2015/16 - 2022/23 (3040)",
            "Validation": "2023/24 (380)",
            "OOS": "2024/25 (380)",
            "2026_27": "KILITLI - okunmadi",
            "Karar": karar,
            "Kirmizi_bayrak": kirmizi,
            "Train_ROI": train_roi,
            "OOS_ROI": oos_roi,
        }]).to_excel(w, sheet_name="Notlar", index=False)

        if len(fi_df) > 0:
            fi_df.to_excel(w, sheet_name="Feature_Importance", index=False)

    print(f"\n{CIKTI} yazıldı.")

    print("\n" + "=" * 80)
    print("VERİ BÜTÜNLÜĞÜ VE KANIT")
    print("=" * 80)
    print(f"  Toplam: {len(df)}")
    print(f"  Train: {len(train)}, Val: {len(val)}, OOS: {len(oos)}")
    print(f"  Okuma sayacı: {dict(_okuma_sayaci)}")
    print(f"  Yasaklılardan hiçbiri okunmadı: "
          f"{all(d not in _okuma_sayaci for d in YASAKLI_DOSYALAR)}")
    print("=" * 80)


if __name__ == "__main__":
    main()