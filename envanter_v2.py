# envanter_v2.py
# Sadece veri yapısı envanteri. Hiçbir edge/ROI/threshold/strateji testi yok.

import glob
import os
import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
# 1. Dosya -> sezon haritası (kesinleşti)
# ----------------------------------------------------------------------
DOSYA_SEZON = {
    "E0.csv":       "2015/16",
    "E0 (1).csv":   "2016/17",
    "E0 (2).csv":   "2017/18",
    "E0 (3).csv":   "2018/19",
    "E0 (4).csv":   "2019/20",
    "E0 (5).csv":   "2020/21",
    "E0 (6).csv":   "2021/22",
    "E0 (7).csv":   "2022/23",
    "E0 (8).csv":   "2023/24",
    "E0 (9).csv":   "2024/25",
    "E0 (10).csv":  "2026/27",
}

ROL = {
    "2019/20": "Discovery",
    "2020/21": "Discovery",
    "2021/22": "Validation",
    "2022/23": "Validation",
    "2023/24": "Confirmation",
    "2024/25": "Blind OOS-1",
    "2025/26": "Beklemede",
    "2015/16": "Hariç",
    "2016/17": "Hariç",
    "2017/18": "Hariç",
    "2018/19": "Hariç",
    "2026/27": "Hariç",
}

# ----------------------------------------------------------------------
# 2. Her dosyayı oku, sezon etiketi ekle, hepsini birleştir
# ----------------------------------------------------------------------
print("Dosyalar okunuyor...")
df_list = []
for f in sorted(glob.glob("E0*.csv")):
    sezon = DOSYA_SEZON.get(os.path.basename(f), "?")
    d = pd.read_csv(f, encoding="utf-8-sig")
    d["Season"] = sezon
    d["Rol"] = ROL.get(sezon, "?")
    df_list.append(d)
    print(f"  {os.path.basename(f):15s} -> {sezon} ({len(d)} satır)")

df = pd.concat(df_list, ignore_index=True)

# Tarih
df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")

# ----------------------------------------------------------------------
# 3. Kullanılabilir sütunları tespit et
# ----------------------------------------------------------------------
print("\n" + "=" * 110)
print("KOLON VARLIK KONTROLÜ")
print("=" * 110)

# O/U line kolonu var mı?
ou_line_kolonlari = [c for c in df.columns
                     if c.upper().startswith("OU")
                     or "OU_" in c.upper()
                     or c.upper() in ("OU", "OUH", "OUA", "LINE_OU")]
print(f"Gerçek O/U line kolonu adayları: {ou_line_kolonlari if ou_line_kolonlari else 'YOK'}")

# AH line kolonu
ah_line_kolonlari = [c for c in df.columns
                     if c.upper() in ("AHH", "AHCH", "AH_LINE", "AHLINE")]
print(f"Gerçek AH line kolonu: {ah_line_kolonlari if ah_line_kolonlari else 'YOK'}")

# Mevcut O/U ve AH sütunlarını listele
print("\nMevcut O/U oran sütunları:")
for c in ["B365>2.5","B365<2.5","P>2.5","P<2.5","Max>2.5","Max<2.5","Avg>2.5","Avg<2.5",
          "B365C>2.5","B365C<2.5","PC>2.5","PC<2.5","MaxC>2.5","MaxC<2.5","AvgC>2.5","AvgC<2.5"]:
    print(f"  {c:15s} -> {'VAR' if c in df.columns else 'YOK'}")

print("\nMevcut AH sütunları:")
for c in ["AHh","B365AHH","B365AHA","PAHH","PAHA","MaxAHH","MaxAHA","AvgAHH","AvgAHA",
          "AHCh","B365CAHH","B365CAHA","PCAHH","PCAHA","MaxCAHH","MaxCAHA","AvgCAHH","AvgCAHA"]:
    print(f"  {c:15s} -> {'VAR' if c in df.columns else 'YOK'}")

# ----------------------------------------------------------------------
# 4. Sezon bazında kullanılabilir satır + eksik maç listesi
# ----------------------------------------------------------------------
print("\n" + "=" * 110)
print("SEZON BAZINDA KULLANILABİLİRLİK")
print("=" * 110)

OU_TUM = ["B365>2.5","B365<2.5","P>2.5","P<2.5","Max>2.5","Max<2.5","Avg>2.5","Avg<2.5",
          "B365C>2.5","B365C<2.5","PC>2.5","PC<2.5","MaxC>2.5","MaxC<2.5","AvgC>2.5","AvgC<2.5"]
AH_TUM = ["AHh","B365AHH","B365AHA","PAHH","PAHA","MaxAHH","MaxAHA","AvgAHH","AvgAHA",
          "AHCh","B365CAHH","B365CAHA","PCAHH","PCAHA","MaxCAHH","MaxCAHA","AvgCAHH","AvgCAHA"]

ozet = []
for s in sorted(df["Season"].unique()):
    g = df[df["Season"] == s]
    rol = g["Rol"].iloc[0]

    ou_tam = g[OU_TUM].notna().all(axis=1).sum()
    ah_tam = g[AH_TUM].notna().all(axis=1).sum()

    ozet.append({
        "Sezon": s,
        "Rol": rol,
        "Mac": len(g),
        "OU_Tam": ou_tam,
        "OU_Eksik": len(g) - ou_tam,
        "AH_Tam": ah_tam,
        "AH_Eksik": len(g) - ah_tam,
    })

ozet_df = pd.DataFrame(ozet)
print(ozet_df.to_string(index=False))

# ----------------------------------------------------------------------
# 5. Eksik maçların kimlikleri (sadece kullanılabilir sezonlar için)
# ----------------------------------------------------------------------
print("\n" + "=" * 110)
print("EKSİK MAÇ LİSTELERİ (kullanılabilir sezonlar)")
print("=" * 110)

KULLANILABILIR = ["2019/20","2020/21","2021/22","2022/23","2023/24","2024/25"]

eksik_df_list = []
for s in KULLANILABILIR:
    g = df[df["Season"] == s]
    ou_mask = g[OU_TUM].notna().all(axis=1)
    ah_mask = g[AH_TUM].notna().all(axis=1)
    eksik_mask = ~(ou_mask & ah_mask)
    if eksik_mask.any():
        eksik = g.loc[eksik_mask, ["Season","Date","HomeTeam","AwayTeam"]].copy()
        eksik["OU_Eksik"] = ~ou_mask[eksik_mask].values
        eksik["AH_Eksik"] = ~ah_mask[eksik_mask].values
        eksik_df_list.append(eksik)

if eksik_df_list:
    eksik_df = pd.concat(eksik_df_list, ignore_index=True)
    print(eksik_df.to_string(index=False))
else:
    eksik_df = pd.DataFrame()
    print("Eksik maç yok.")

# ----------------------------------------------------------------------
# 6. O/U ve AH fiyat hareketi (kesin ölçülebilen)
# ----------------------------------------------------------------------
print("\n" + "=" * 110)
print("FİYAT HAREKETİ (açılış -> kapanış)")
print("=" * 110)

def fiyat_hareket_ozet(g, acilis, kapanis, etiket):
    m = g[[acilis, kapanis]].notna().all(axis=1)
    dustu = ((g[kapanis] < g[acilis]) & m).sum()
    yukseldi = ((g[kapanis] > g[acilis]) & m).sum()
    ayni = ((g[kapanis] == g[acilis]) & m).sum()
    ort_fark = (g.loc[m, kapanis] - g.loc[m, acilis]).mean()
    return {
        f"{etiket}_Toplam": int(m.sum()),
        f"{etiket}_Dustu": int(dustu),
        f"{etiket}_Yukseldi": int(yukseldi),
        f"{etiket}_Ayni": int(ayni),
        f"{etiket}_OrtFark": round(float(ort_fark), 4) if m.any() else np.nan,
    }

hareket_satirlar = []
for s in sorted(df["Season"].unique()):
    g = df[df["Season"] == s]
    rol = g["Rol"].iloc[0]
    satir = {"Sezon": s, "Rol": rol}
    satir.update(fiyat_hareket_ozet(g, "B365>2.5", "B365C>2.5", "OU_Over"))
    satir.update(fiyat_hareket_ozet(g, "B365<2.5", "B365C<2.5", "OU_Under"))
    satir.update(fiyat_hareket_ozet(g, "B365AHH", "B365CAHH", "AH_Home"))
    satir.update(fiyat_hareket_ozet(g, "B365AHA", "B365CAHA", "AH_Away"))
    hareket_satirlar.append(satir)

hareket_df = pd.DataFrame(hareket_satirlar)
print(hareket_df.to_string(index=False))

# ----------------------------------------------------------------------
# 7. B365 - Pinnacle ve Max - Avg farkları (her iki taraf)
# ----------------------------------------------------------------------
print("\n" + "=" * 110)
print("B365 - PINNACLE VE MAX - AVG FARKLARI (her iki taraf)")
print("=" * 110)

def fark_ozet(g, a, b, etiket):
    m = g[[a, b]].notna().all(axis=1)
    if not m.any():
        return {f"{etiket}_Ort": np.nan, f"{etiket}_Std": np.nan, f"{etiket}_N": 0}
    f = g.loc[m, a] - g.loc[m, b]
    return {
        f"{etiket}_Ort": round(float(f.mean()), 4),
        f"{etiket}_Std": round(float(f.std()), 4),
        f"{etiket}_N": int(m.sum()),
    }

fark_satirlar = []
for s in sorted(df["Season"].unique()):
    g = df[df["Season"] == s]
    rol = g["Rol"].iloc[0]
    satir = {"Sezon": s, "Rol": rol}
    satir.update(fark_ozet(g, "B365>2.5", "P>2.5",  "B365P_OU_Over_Ac"))
    satir.update(fark_ozet(g, "B365<2.5", "P<2.5",  "B365P_OU_Under_Ac"))
    satir.update(fark_ozet(g, "B365C>2.5","PC>2.5", "B365P_OU_Over_Kp"))
    satir.update(fark_ozet(g, "B365C<2.5","PC<2.5", "B365P_OU_Under_Kp"))
    satir.update(fark_ozet(g, "B365AHH", "PAHH",   "B365P_AH_Home_Ac"))
    satir.update(fark_ozet(g, "B365AHA", "PAHA",   "B365P_AH_Away_Ac"))
    satir.update(fark_ozet(g, "B365CAHH","PCAHH",  "B365P_AH_Home_Kp"))
    satir.update(fark_ozet(g, "B365CAHA","PCAHA",  "B365P_AH_Away_Kp"))
    satir.update(fark_ozet(g, "Max>2.5", "Avg>2.5", "MaxAvg_OU_Over_Ac"))
    satir.update(fark_ozet(g, "Max<2.5", "Avg<2.5", "MaxAvg_OU_Under_Ac"))
    satir.update(fark_ozet(g, "MaxC>2.5","AvgC>2.5","MaxAvg_OU_Over_Kp"))
    satir.update(fark_ozet(g, "MaxC<2.5","AvgC<2.5","MaxAvg_OU_Under_Kp"))
    fark_satirlar.append(satir)

fark_df = pd.DataFrame(fark_satirlar)
print(fark_df.to_string(index=False))

# ----------------------------------------------------------------------
# 8. Gerçek O/U line movement tespiti
# ----------------------------------------------------------------------
print("\n" + "=" * 110)
print("GERÇEK O/U LINE MOVEMENT TESPİTİ")
print("=" * 110)

if not ou_line_kolonlari:
    print("Veri setinde gerçek O/U line kolonu YOK.")
    print("Bu nedenle 'line movement' ölçülemeyecek.")
    print("Over/Under fiyat hareketi ayrı raporlandı (yukarıda).")
else:
    print(f"Gerçek O/U line kolonu bulundu: {ou_line_kolonlari}")
    print("Line movement doğrudan ölçülebilir.")

# ----------------------------------------------------------------------
# 9. Excel'e yaz
# ----------------------------------------------------------------------
cikti = "envanter_v2.xlsx"
with pd.ExcelWriter(cikti, engine="openpyxl") as w:
    ozet_df.to_excel(w, sheet_name="Sezon_Ozet", index=False)
    if not eksik_df.empty:
        eksik_df.to_excel(w, sheet_name="Eksik_Maclar", index=False)
    hareket_df.to_excel(w, sheet_name="Fiyat_Hareketi", index=False)
    fark_df.to_excel(w, sheet_name="Fark_Analizleri", index=False)
    pd.DataFrame({
        "OU_Line_Kolonu_Var_Mi": ["EVET" if ou_line_kolonlari else "HAYIR"],
        "OU_Line_Kolonlari": [",".join(ou_line_kolonlari) if ou_line_kolonlari else ""],
    }).to_excel(w, sheet_name="OU_Line_Kontrol", index=False)

print(f"\nKaydedildi: {cikti}")
print("Hiçbir edge/ROI/threshold/strateji testi yapılmadı.")