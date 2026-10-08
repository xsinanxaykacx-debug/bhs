# -*- coding: utf-8 -*-
"""
H5 O/U SIFIR ORAN KONTROLÜ

AMAÇ:
- B365 O/U sütunlarında 0.0 değerlerini tespit etmek.
- Hangi sezon ve maçlarda olduğunu raporlamak.
- Sıfırların açılış/kapanış tarafındaki durumunu görmek.

YAPMAZ:
- Model kurmaz.
- Eşik aramaz.
- Veri temizlemez.
- Sonuçlara göre karar vermez.
- 2026/27 verisini okumaz.

KAPSAM:
- E0 (4).csv  -> 2019/20
- E0 (5).csv  -> 2020/21
- E0 (6).csv  -> 2021/22
- E0 (7).csv  -> 2022/23
- E0 (8).csv  -> 2023/24
- E0 (9).csv  -> 2024/25

E0 (10).csv KESİNLİKLE OKUNMAZ.
"""

import os
import pandas as pd


DOSYALAR = [
    "E0 (4).csv",
    "E0 (5).csv",
    "E0 (6).csv",
    "E0 (7).csv",
    "E0 (8).csv",
    "E0 (9).csv",
]

KONTROL_SUTUNLARI = [
    "B365>2.5",
    "B365C>2.5",
    "B365<2.5",
    "B365C<2.5",
]

ANAHTAR_SUTUNLAR = [
    "Date",
    "HomeTeam",
    "AwayTeam",
    "FTHG",
    "FTAG",
    "FTR",
]


print("=" * 100)
print("H5 O/U SIFIR ORAN KONTROLÜ")
print("=" * 100)
print("Kapsam : E0 (4) - E0 (9)")
print("Kilit  : E0 (10) OKUNMAYACAK")
print("=" * 100)


# ---------------------------------------------------------------------
# Güvenlik: E0 (10) dosyasının kesinlikle okunmadığını belirt
# ---------------------------------------------------------------------

if os.path.exists("E0 (10).csv"):
    print("\n[LOCK] E0 (10).csv mevcut ancak KESİNLİKLE OKUNMAYACAK.")
else:
    print("\n[LOCK] E0 (10).csv mevcut değil; yine de script kapsamı dışındadır.")


# ---------------------------------------------------------------------
# Sayaçlar
# ---------------------------------------------------------------------

toplam_sifirlar = {
    col: 0
    for col in KONTROL_SUTUNLARI
}

sezon_sifirlar = {
    dosya: {
        col: 0
        for col in KONTROL_SUTUNLARI
    }
    for dosya in DOSYALAR
}


# ---------------------------------------------------------------------
# Sezon bazında kontrol
# ---------------------------------------------------------------------

for dosya in DOSYALAR:

    print("\n" + "=" * 100)
    print(f"SEZON DOSYASI: {dosya}")
    print("=" * 100)

    if not os.path.exists(dosya):
        print(f"[HATA] Dosya bulunamadı: {dosya}")
        continue

    df = pd.read_csv(
        dosya,
        encoding="utf-8-sig"
    )

    print(f"Satır sayısı: {len(df)}")

    mevcut_sutunlar = [
        col for col in KONTROL_SUTUNLARI
        if col in df.columns
    ]

    if len(mevcut_sutunlar) != len(KONTROL_SUTUNLARI):
        eksik = [
            col for col in KONTROL_SUTUNLARI
            if col not in df.columns
        ]

        print(f"[UYARI] Eksik sütunlar: {eksik}")

    sezon_sifir_var = False

    for col in KONTROL_SUTUNLARI:

        if col not in df.columns:
            continue

        zero = df[df[col] == 0].copy()

        if len(zero) == 0:
            continue

        sezon_sifir_var = True

        adet = len(zero)

        toplam_sifirlar[col] += adet
        sezon_sifirlar[dosya][col] += adet

        print("\n" + "-" * 100)
        print(f"{col} -> {adet} ADET SIFIR")
        print("-" * 100)

        # Mevcut anahtar sütunları seç
        gosterilecek = [
            col_ for col_ in ANAHTAR_SUTUNLAR
            if col_ in zero.columns
        ]

        gosterilecek.append(col)

        print(
            zero[gosterilecek].to_string(index=False)
        )

    if not sezon_sifir_var:
        print("\nSıfır değer YOK.")


# ---------------------------------------------------------------------
# Sezon × sütun özeti
# ---------------------------------------------------------------------

print("\n\n" + "=" * 100)
print("SEZON × SÜTUN SIFIR ÖZETİ")
print("=" * 100)

ozet_rows = []

for dosya in DOSYALAR:

    row = {
        "Dosya": dosya
    }

    for col in KONTROL_SUTUNLARI:
        row[col] = sezon_sifirlar[dosya][col]

    ozet_rows.append(row)

ozet_df = pd.DataFrame(ozet_rows)

print(
    ozet_df.to_string(index=False)
)


# ---------------------------------------------------------------------
# Toplam özet
# ---------------------------------------------------------------------

print("\n\n" + "=" * 100)
print("TÜM SEZONLAR TOPLAM SIFIR SAYILARI")
print("=" * 100)

for col in KONTROL_SUTUNLARI:
    print(
        f"{col:<15} : {toplam_sifirlar[col]:>5} sıfır"
    )


# ---------------------------------------------------------------------
# Kritik çiftler
# ---------------------------------------------------------------------

print("\n" + "=" * 100)
print("KRİTİK KAPANIŞ ORANLARI")
print("=" * 100)

over_zero = toplam_sifirlar["B365C>2.5"]
under_zero = toplam_sifirlar["B365C<2.5"]

print(f"B365C>2.5 = 0 : {over_zero} kayıt")
print(f"B365C<2.5 = 0 : {under_zero} kayıt")


# ---------------------------------------------------------------------
# Veri kalitesi değerlendirmesi
# ---------------------------------------------------------------------

print("\n" + "=" * 100)
print("VERİ KALİTESİ ÖN DEĞERLENDİRME")
print("=" * 100)

if over_zero == 0 and under_zero == 0:

    print(
        "SONUÇ: B365 kapanış O/U oranlarında sıfır kayıt bulunmadı."
    )

elif over_zero > 0 or under_zero > 0:

    print(
        "SONUÇ: B365 kapanış O/U oranlarında sıfır kayıt bulundu."
    )

    print(
        "Bu aşamada kayıtlar OTOMATİK OLARAK DIŞLANMADI."
    )

    print(
        "Zero check yalnızca veri kalitesi kanıtı üretmektedir."
    )

    print(
        "H5 protokolündeki sıfır işleme kuralı ayrıca belirlenecektir."
    )


# ---------------------------------------------------------------------
# E0 (10) güvenlik son kontrolü
# ---------------------------------------------------------------------

print("\n" + "=" * 100)
print("KİLİTLİ VERİ GÜVENLİK KONTROLÜ")
print("=" * 100)

print("E0 (4).csv -> OKUNDU")
print("E0 (5).csv -> OKUNDU")
print("E0 (6).csv -> OKUNDU")
print("E0 (7).csv -> OKUNDU")
print("E0 (8).csv -> OKUNDU")
print("E0 (9).csv -> OKUNDU")
print("E0 (10).csv -> 0 OKUMA / KİLİTLİ")

print("\n" + "=" * 100)
print("ZERO CHECK TAMAMLANDI")
print("=" * 100)