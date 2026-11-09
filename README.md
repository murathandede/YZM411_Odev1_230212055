# YZM 411 Bilgisayarlı Görü — Ödev 1: Renk, Aydınlatma ve Örnekleme

Öğrenci No: 230212055

Kendi kurulan bir masaüstü sahnesinde (renkli nesne + beyaz kâğıt + küçük yazı/çizgili doku) üç aydınlatma koşulunda:
- **H1** görüntünün sayısal yapısı (shape, dtype, `img[y, x, kanal]`, BGR→RGB),
- **H2** sabit (dondurulmuş) RGB ve HSV eşikleriyle maske karşılaştırması,
- **H3** parlaklık kaydırması (b=+40) ve gama (γ=0,5 / 2,0) — tahmin vs. ölçüm, kırpma analizi,
- **H4** 1/4 küçültmede `INTER_NEAREST` vs `INTER_AREA` bilgi kaybı.

## Klasör yapısı
```
odev1.py            # tüm deneyler
rapor_olustur.py    # 2 sayfalık PDF rapor
ayarlar.json        # fotoğraf yolları, ROI'ler, 3 piksel, kamera notları
tahminler.json      # deneyden ÖNCE yazılan tahminler (boşsa kod çalışmaz)
yorumlar.json       # ölçümden sonra: ne gördüm / neden / nasıl kontrol ederim, sorular, YZ beyanı
esikler.json        # ilk çalıştırmada normal ışıktan belirlenip DONDURULAN eşikler
fotograflar/ham/    # kendi çekimim, değiştirilmemiş ham fotoğraflar
fotograflar/        # hizalanmış normal.jpg, golge.jpg, lamba.jpg
hizala.py           # ORB+RANSAC homografi ile hizalama (kadraj kaydığı için)
ciktilar/           # maskeler, şekiller, sonuclar.json, sonuc_tablosu.csv
rapor/              # YZM411_Odev1_230212055.pdf
```

## Çalıştırma sırası
```bash
pip install -r requirements.txt
# 0) fotoğrafları fotograflar/ altına koy; ayarlar.json'da kamera ve oto pozlama/beyaz dengesi notunu doldur
python hizala.py           # 0b) gölge/lamba -> normal'e hizalama (ham fotoğraflar fotograflar/ham/)
python odev1.py --sec      # 1) nesne ROI, yazı ROI ve 3 piksel seçimi (yerel pencere açar; Colab'da değil)
#                            2) tahminler.json'u doldur (deneyden önce!)
python odev1.py            # 3) deneyler -> ciktilar/
#                            4) yorumlar.json'u ölçümlere bakarak doldur
python odev1.py --rapor    # 5) rapor/YZM411_Odev1_230212055.pdf
```

## Parametreler
- Eşikler: normal ışıklı ROI'nin %2–%98 yüzdelikleri ± pay (RGB ±15; HSV: H ±4, S −30, V −40). OpenCV 8 bit HSV: H 0–179, S/V 0–255. Kırmızı tonlarda H sarmalanması için +90 kaydırma.
- Parlaklık: `J = clip(I + 40, 0, 255)`; gama: `J = 255 · (I/255)^γ` (γ formüldeki üs), float üzerinde.
- Küçültme: genişlik/yükseklik 1/4; büyütme yalnızca gösterim için `INTER_NEAREST`.
- Maske alan oranı bir doğruluk ölçütü değildir.
