# PROJE HAFIZA NOTU — FUTBOL BAHİS YAPISI ARAŞTIRMASI (v15)

**Tarih:** 2026-10-08  
**Kullanıcı:** EPL (İngiltere Premier Lig) verisiyle çalışan araştırmacı  
**Ortam:** Windows, Python 3.14, `C:\Users\bzdye\Downloads\EPL\`  
**Veri:** E0.csv … E0 (10).csv (2015/16 – 2026/27)  
**Disiplin:** Önceden ilan → FROZEN → tek çalıştırma → post-hoc yasak

## KORUMA KURALLARI

- Bir hipotez sonuçlandığında yeni hipotez üretilebilir; yeni hipotez yine FROZEN ve tek çalıştırma protokolüne tabidir.
- Mevcut sonuçlar yeni hipotezi seçmek için post-hoc kanıt olarak kullanılamaz.
- Arşiv dosyaları değiştirilmez.
- 2026/27 `E0 (10).csv` KÖR OOS'tur ve hiçbir koşulda okunmaz.
- H17'yi sonradan leaves, threshold, feature veya model değiştirerek yeniden oynatmak yasaktır; bu ayrı bir hipotez olur.
- Yeni araştırma ancak yeni piyasa, yeni veri tipi veya baştan tanımlanmış yeni protokol ile açılabilir.

## VERİ ENVANTERİ

| Sezon | Dosya | Rol |
|---|---|---|
| 2015/16 | E0.csv | Train |
| 2016/17 | E0 (1).csv | Train |
| 2017/18 | E0 (2).csv | Train |
| 2018/19 | E0 (3).csv | Train |
| 2019/20 | E0 (4).csv | Train |
| 2020/21 | E0 (5).csv | Train |
| 2021/22 | E0 (6).csv | Train |
| 2022/23 | E0 (7).csv | Train |
| 2023/24 | E0 (8).csv | Validation |
| 2024/25 | E0 (9).csv | Blind OOS |
| 2025/26 | YOK | — |
| 2026/27 | E0 (10).csv | KİLİTLİ / KÖR OOS |

Toplam görülen 2015/16–2024/25: 3800 maç.  
2026/27 dosyası hiçbir deneyde okunmayacaktır.

# TAMAMLANMIŞ ARAŞTIRMA ZİNCİRLERİ

## 1. Yapısal Doğrulama — STRONG OOS

Discovery → Validation → Confirmation → Blind OOS.

Amaç: açılış→kapanış fiyat hareketi yapıları ile AH ve O/U arasında istatistiksel ilişki.

12 primary test:
- V-A1 AH_line_abs ↔ B365_Home_abs (+)
- V-A2 AH_line_abs ↔ B365_Away_abs (+)
- V-B1 Over_fark ↔ Under_fark (−)
- V-B2 Over_fark ↔ MaxAvg_Over_Kayma (+)
- V-B3 Over_fark ↔ MaxAvg_Under_Kayma (−)
- V-C1 Over_abs ↔ Under_abs (+)
- V-C2 Over_abs ↔ B365P_Over_Kayma_abs (+)
- V-C3 Over_abs ↔ MaxAvg_Over_Kayma_abs (+)
- V-D1..D4 yön → kapanış kayması KW testleri

Metodoloji: 8 korelasyon + 4 KW; tek 12'li BH-FDR; 10.000 BCa bootstrap; seed=20261008; Quarter-AH split-stake.

Sonuç:
- Validation 9/12 başarılı
- Confirmation 9/12 başarılı
- Blind OOS 10/12 başarılı
- **STRONG OOS**

Bu zincir yapısal ilişkinin gerçek olduğunu gösterdi; ancak bu ilişki ekonomik edge'e dönüştürülemedi.

## 2. ROI/EDGE v1.1 — NEGATİF

20 sinyal test edildi; 0 güçlü kanıt.  
3 zayıf pozitif, 3 belirgin negatif.  
2026/27'ye taşınacak sinyal yok.

## H1 Feature Engineering — PASS

`h1_features.csv`: 3800 × 56.

49 sayısal pre-match feature:
- Elo
- genel/home-away form
- gol ve gol-yeme ortalamaları
- rest
- maç sayısı

Kilitli Elo:
- başlangıç 1500
- K=20
- HA=+100
- Elo sezonlar arasında taşınır
- Form sezon başında sıfırlanır
- Gol özellikleri sezonlar arasında taşınır
- yetersiz geçmiş = NaN

Audit:
- 3800 satır
- E0 (10).csv okunmadı
- look-ahead 0
- self-reference 0
- same-day leakage 0
- deterministik

## H1 Edge v1.0 — INCONCLUSIVE

9 hipotez (3 Elo × 3 market movement).  
Hareketli maç yalnızca 41/2280 (%1.80); Validation'da 4 maç.  
Güçlü kanıt 0/9.  
Sonuç: **INCONCLUSIVE — yetersiz sinyal yoğunluğu.**

## H2 — WEAK / UNCERTAIN

GoalDiff modeli:
- M0 OOS R² 0.178627
- M1 OOS R² 0.179726
- M2 OOS R² 0.180171
- M3 OOS R² −0.004803

Movement/Elo katkısı çok küçük ve istikrarsız.

## H3 — WEAK / UNCERTAIN

Movement + Elo + AH fiyat seviyesi katkıları küçük:
- ΔR²(M3−M0)=+0.002390
- ΔR²(M3−M1)=+0.001291
- ΔR²(M2−M0)=+0.000117

## H4 — WEAK / UNCERTAIN

Cross-market disagreement sınıfı oluşmadı (0/0/0).  
Kırmızı bayrak görüldü; güvenilir ekonomik sinyal oluşmadı.

## H5 — WEAK / UNCERTAIN

O/U price movement:
- OOS ΔR² +0.006443
- ΔMAE −0.002021
- p=.0816

Kriterlerin çoğu geçse de p<.05 geçmedi.

## H6 — NOT SUPPORTED

AH bookmaker spread:
- OOS ΔR² −0.001340
- MAE kötüleşti
- katsayı p=.6840

## H7 — FAIL / VERİ UYGULANAMAZ

Gerekli B365HC (1X2 kapanış) verisi yok: 0/6.

# H9–H17: DOKUZ BAĞIMSIZ BAHİS MEKANİZMASI

## H9 — Multinomial Logistic Value Betting — NOT SUPPORTED / RED FLAG

Model: MLR, 49 pre-match feature.  
Value: P_model × odds − 1 > 0.

| Bölme | N | ROI | GA_lo | p | MDD |
|---|---:|---:|---:|---:|---:|
| Train | 2885 | +9.48% | +2.70% | 1.0000 | 85.34% |
| Val | 346 | −5.60% | −20.89% | .9935 | 35.67% |
| OOS | 346 | −3.80% | −19.66% | .9307 | 42.27% |

**NOT SUPPORTED / RED FLAG.**

## H10 — Opening→Closing Movement ROI — NOT SUPPORTED

2019/20–2024/25; 18 frozen hücre.  
0/18 supported, 5 weak, 13 not supported.  
OOS pozitif hücrelerde GA_lo>0 ve p<.05 birlikte oluşmadı.

## H11 — Draw Movement — NOT SUPPORTED / KIRMIZI

6 bant:
- 2 WEAK
- 4 NOT SUPPORTED
- 1 kırmızı bayrak
- BH-FDR 6/6 fail

Örnek:
- (-10%,-5%] OOS ROI +23.29%, N=58, GA_lo −21.33%, p=.937
- (-5%,0%] OOS ROI +16.34%, N=189, GA_lo −8.46%, p=.5455
- (0%,+5%] OOS ROI −24.87%, p=.0478 fakat BH-FDR q=.2862

## H12 — Favourite-Longshot Bias — NOT SUPPORTED / KIRMIZI

6 oran bandı.  
0 supported, 2 weak, 4 not supported, 1 kırmızı bayrak.  
BH-FDR 6/6 fail.

[1.00,1.20] OOS ROI +7.13%, ancak N=16 ve GA_lo −21.75%.

## H13 — Corner Market Inefficiency — NOT SUPPORTED

Son 5 maç korner ortalaması, 10.5 çizgisinin yönünü tahmin etti.

| Bölme | N | Win% | ROI | GA_lo | p | MDD |
|---|---:|---:|---:|---:|---:|---:|
| Train | 2560 | 50.78% | −3.52% | −7.30% | .0621 | 124.0% |
| Val | 375 | 50.13% | −4.75% | −14.37% | .3286 | 21.6% |
| OOS | 375 | 51.73% | −1.71% | −11.33% | .7219 | 17.7% |

Korner bahis oranları CSV'de olmadığı için yaklaşık 1.90 kullanıldı. Edge oluşmadı.

## H14 — Optimal Odds Band Discovery — NOT SUPPORTED

Train+Val discovery ile en iyi bant seçildi, OOS'a bakılmadı.

Seçilen bant: [2.60,2.65)
- Train N=138, ROI +6.02%
- Val N=9, ROI +103.22%
- OOS N=12, ROI −34.25%
- GA=[−100%, +9.58%]
- p=.3318
- MDD=5%
- q=.9424

Sonuç: discovery overfitting/sample instability.

## H15 — Cross-Bookmaker Mispricing — NOT SUPPORTED

Pinnacle açılışı referans; B365/BW/WH açılışları karşılaştırıldı.  
Eşik: retail implied probability − Pinnacle implied probability > .02.

Ortak evren: 3568.  
9 strateji:
- SUPPORTED 0
- WEAK 2
- NOT SUPPORTED 5
- YETERSİZ 2

Önemli:
- B365-H OOS N=9, ROI +91.44%, p=.0864 → yalnızca WEAK
- BW-A ROI −75.83%, q=.0434 → ters yönde güçlü negatif bulgu
- Kırmızı bayrak 0

## H16-E4 — Pinnacle Sharp vs Retail Lag — NOT SUPPORTED

Pinnacle kapanış referans; retail açılış.

Gap:
1/retail_opening − 1/pinnacle_close > .02.

Ortak evren frozen mask ile 3554.  
Train 2952, Val 368, OOS 234.

9 strateji:
- SUPPORTED 0
- WEAK 1 (WH-A)
- NOT SUPPORTED 8
- Kırmızı bayrak 0

WH-A:
- Train −15.91%
- Val −30.12%
- OOS +11.89%
- N=85
- GA_lo −20.02%
- p=.5081
- q=.6533
- MDD 12.92%

Sonuç: sinyal baştan yoktu; OOS pozitifliği anlamsız.

# H17 — CONTEXT-ADJUSTED MARKET RESIDUAL — NOT SUPPORTED

Dosyalar:
- h17_f2_model.py
- h17_f2_model_results.xlsx

Hipotez:
EPL'de maç öncesi takım/form bağlamından öğrenilen LightGBM model olasılığı ile B365 açılış piyasa olasılığı arasındaki residual, bağımsız ekonomik bahis sinyali içerir.

### F0
PASS:
- 3800/3800 merge
- leakage audit PASS
- 2026/27 okunmadı

### F1 FROZEN
- LightGBM Multiclass >=4.0 (kurulu 4.7.0)
- num_leaves=31
- learning_rate=.05
- n_estimators=300
- min_child_samples=20
- random_state=20261008
- 49 pre-match feature
- native NaN
- Train 2015/16–2022/23
- Validation 2023/24
- OOS 2024/25
- market prob = 1/B365 opening odds; overround normalization yok
- residual = P_model − P_market
- max residual > .02 → 1 bahis/maç
- stake 1
- BCa 10k / sign-permutation 10k, seed 20261008
- MDD bankroll 100
- BH-FDR tek aile
- N_MIN=100
- alpha=.05
- MDD limit=.20
- hyperparameter search yok
- early stopping yok

### F2 SONUÇ

| Bölme | N | Win% | Ort oran | Ort max residual | Net PL | ROI | GA_lo | GA_hi | p | MDD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Train | 3031 | 98.85% | 2.9284 | .3966 | +5635.38 | +185.92% | +179.83% | +193.05% | .0001 | 4.00% |
| Validation | 366 | 42.62% | 3.1385 | .1948 | −24.56 | −6.71% | −19.48% | +7.59% | .3426 | 31.08% |
| OOS | 365 | 46.58% | 2.8914 | .2119 | +14.01 | +3.84% | −9.05% | +18.71% | .5847 | 31.97% |

OOS kriterleri:
- K_ROI TRUE
- K_GA FALSE
- K_N TRUE
- K_P FALSE
- K_MDD FALSE
- K_Q FALSE

**KARAR: NOT SUPPORTED.**

Doğru ifade:
> Aşırı in-sample optimism / güçlü overfit belirtisi; ekonomik genelleme başarısız.

Yanlış ifade:
> LightGBM kesinlikle overfit oldu.

Sebep: Train performansı aynı veri üzerinde model seçimi/eğitimi sonrasında ölçüldüğü için güçlü in-sample iyimserlik beklenebilir; fakat %98.85 Train Win ve +185.92% ROI, Validation/OOS çöküşü ile birlikte güçlü overfit belirtisidir.

H9 vs H17:
- H9 MLR: Train +9.48% → OOS −3.80%, RED FLAG
- H17 LightGBM: Train +185.92% → OOS +3.84%, RED FLAG yok
- Ancak H17 OOS GA_lo −9.05%, p=.5847 ve MDD 31.97% → istatistiksel olarak güvenilir edge yok.

## xG / F18 KARARI

xG veri genişletmesi değerlendirildi ve RED edildi.

Gerekçe:
- Maç öncesi kullanılacak xG ancak önceki maçlardan kümülatif olarak üretilebilir.
- Bu, gol/form ailesinden farklı bir ölçüm olsa da bağımsız bir piyasa mekanizması değildir.
- Piyasanın xG benzeri takım kalite bilgisini kısmen fiyatlaması beklenir.
- Bu nedenle sırf feature sayısını artırmak için xG eklemek yeni ve bağımsız bir araştırma yolu sayılmadı.

**F18 açılmayacak.**

Bu karar, "xG kesinlikle işe yaramaz" iddiası değildir; yalnızca mevcut kapanış protokolü kapsamında yeni bir araştırma yolu olarak açılmamıştır.

# GÜNCEL DURUM — 20 ARAŞTIRMA YOLU

1. Zincir 1 (yapısal) — STRONG OOS
2. Zincir 2 (ROI/Edge) — NEGATİF
3. H1 Feature Engineering — PASS
4. H1 Edge v1.0 — INCONCLUSIVE
5. H2 Explore — WEAK
6. H3 Explore — WEAK
7. H4 Explore — WEAK
8. H5 Explore — WEAK
9. H6 Explore — NOT SUPPORTED
10. H7 Inventory — FAIL
11. H9 Value Betting — NOT SUPPORTED / RED
12. H10 Opening→Closing — NOT SUPPORTED
13. H11 Draw Movement — NOT SUPPORTED / KIRMIZI
14. H12 Favourite-Longshot — NOT SUPPORTED / KIRMIZI
15. H13 Corner — NOT SUPPORTED
16. H14 Optimal Odds — NOT SUPPORTED
17. H15 Cross-Bookmaker — NOT SUPPORTED
18. H16-E4 Pinnacle Sharp — NOT SUPPORTED
19. H17 LightGBM Context — NOT SUPPORTED

Not: "20 araştırma yolu" toplamı proje içindeki ayrı araştırma zincirleri/katmanları ile ifade edilmektedir; listelenen ana hipotez numaraları H1–H17 arasında boşluklar içerir.

## KRİTİK DESEN

H9–H17: 9 farklı bahis mekanizması, hiçbiri SUPPORTED olmadı:
- MLR value betting
- opening→closing movement
- draw movement
- favourite-longshot bias
- corner form
- optimal odds band discovery
- cross-bookmaker mispricing
- Pinnacle sharp vs retail lag
- LightGBM context residual

Ortak bulgu:
**İstatistiksel öngörülebilirlik ile ekonomik edge aynı şey değildir.**
Discovery'de görünen pozitif sonuçlar bağımsız kör OOS doğrulamasında güvenilir biçimde taşınmadı.

## NİHAİ, SAVUNULABİLİR İFADE

> İncelenen 2015/16–2024/25 EPL 1X2 veri evreninde, önceden dondurulmuş çoklu hipotezler ve kör OOS doğrulamaları altında sürdürülebilir, istatistiksel olarak güvenilir bir bahis edge'i tespit edilemedi.

Daha dar kapsam:
> İncelenen fiyat hareketi, oran seviyesi, favourite-longshot bias, ML/value, korner form, optimal odds band keşfi, cross-bookmaker mispricing, Pinnacle sharp vs retail lag ve LightGBM context residual yaklaşımları altında, kör OOS döneminde güvenilir ve tekrarlanabilir bir ekonomik edge gösterilememiştir.

**Kesinlikle söylenmeyecek ifade:**
> EPL 1X2 piyasası kesinlikle verimlidir.

Deney, piyasanın matematiksel/teorik verimliliğini kanıtlamaz. Yalnızca test edilen mekanizmaların güvenilir ekonomik edge üretmediğini gösterir.

# VERİ SINIRLILIĞI

CSV'de HT/Kart/Korner/Şut/Faul/Hakem gibi alanlar bulunuyor; ancak bu marketlerde bahis oranı olmadığı için doğrudan ROI testi yapılamaz.

Mevcut 1X2 bookmaker verileri:
- B365 açılış
- Betway açılış
- William Hill açılış
- Pinnacle açılış + kapanış

1X2 kapanış yalnız Pinnacle'da mevcut.

2015/16–2018/19 için AH, O/U ve bazı kapanış verileri yok.

# ARŞİV DURUMU

Arşivde korunan ana dosyalar:
- validation_v1.py + sonuçlar
- confirmation_v1.py + sonuçlar
- blind_oos_v1.py + sonuçlar
- roi_edge_v1.py + sonuçlar
- inventory_h1.py + inventory_h1.xlsx
- build_h1_features.py + h1_features.csv
- debug_h1_flow.py
- h1_edge_v1.py + sonuçlar
- h2_explore_v1.py + sonuçlar
- h3_inventory.py / h3_explore_v1.py
- h4_inventory.py / h4_explore_v1.py
- h5_inventory.py / h5_ou_zero_check.py / h5_explore_v1.py
- h6_inventory.py / h6_explore_v1.py
- h7_inventory.py
- h9_explore_v1.py + sonuçlar
- h10_opening_closing_roi.py + sonuçlar
- h11_explore_v1.py + sonuçlar
- h12_favourite_longshot.py + sonuçlar
- h13_corner_market.py + sonuçlar
- h14_optimal_odds_band.py + sonuçlar
- h15_cross_bookmaker.py + sonuçlar
- h16_e4_pinnacle_sharp.py + sonuçlar
- h17_f2_model.py + sonuçlar
- altyapı/diagnostic scriptleri
- E0.csv … E0 (10).csv

**Arşiv: AKTİF / DEĞİŞTİRİLMEZ.**

# NİHAİ DURUM

- ARAŞTIRMA ZİNCİRİ: KAPALI
- ARŞİV: AKTİF / DEĞİŞTİRİLMEZ
- EDGE: BULUNAMADI
- 2026/27: KİLİTLİ / KÖR OOS
- YENİ HİPOTEZ: DURDURULDU
- F18 xG: AÇILMAYACAK
- EPL 1X2'yi aynı veri ailesinde H21/H22 vb. ile kurcalamak: YASAK

Araştırma programı 2026-10-08 tarihinde kapatılmıştır.

> Yirmi araştırma yolu denedik. Fiyat hareketi yapılarının gerçek olduğunu gösterdik (STRONG OOS). Bunları güvenilir ekonomik edge'e dönüştüremedik. Negatif sonuç da bilimsel sonuçtur.

**KİLİT:** 2026/27 (E0 (10).csv) kör kalacak.  
**ARŞİV:** değiştirilmeyecek.  
**Yeni araştırma:** ancak yeni piyasa + yeni veri + baştan ilan edilmiş protokol ile açılabilir.
