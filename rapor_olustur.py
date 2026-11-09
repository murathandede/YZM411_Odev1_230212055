"""2 sayfalik PDF rapor. Olcumler ciktilar/sonuclar.json'dan, tahminler ve yorumlar
ogrencinin kendi yazdigi tahminler.json / yorumlar.json'dan gelir. Bos alanlar
kirmizi [DOLDURULACAK] olarak basilir; hicbir yorum otomatik uydurulmaz."""
import json
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

KOK = os.path.dirname(os.path.abspath(__file__))
CIKTI = os.path.join(KOK, "ciktilar")
ISIKLAR = ["normal", "golge", "lamba"]


def font_kaydet():
    adaylar = [
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
        ("/Library/Fonts/Arial Unicode.ttf", "/Library/Fonts/Arial Unicode.ttf"),
    ]
    for n, b in adaylar:
        if os.path.exists(n) and os.path.exists(b):
            pdfmetrics.registerFont(TTFont("TR", n))
            pdfmetrics.registerFont(TTFont("TRB", b))
            return
    raise SystemExit("Turkce karakter destekli TTF bulunamadi; font_kaydet() icine yol ekle.")


def main():
    font_kaydet()
    s = json.load(open(os.path.join(CIKTI, "sonuclar.json"), encoding="utf-8"))
    t = json.load(open(os.path.join(KOK, "tahminler.json"), encoding="utf-8"))
    y = json.load(open(os.path.join(KOK, "yorumlar.json"), encoding="utf-8"))
    ayar = s["ayarlar"]

    N = ParagraphStyle("n", fontName="TR", fontSize=7.4, leading=9.1)
    K = ParagraphStyle("k", parent=N, fontName="TRB", fontSize=8.6, leading=10.5, spaceBefore=3)
    BAS = ParagraphStyle("b", parent=N, fontName="TRB", fontSize=11, leading=13)

    def v(d, k):
        x = str(d.get(k, "")).strip()
        return x if x else '<font color="red">[DOLDURULACAK]</font>'

    def tablo(veri, gen):
        tb = Table(veri, colWidths=gen)
        tb.setStyle(TableStyle([
            ("FONT", (0, 0), (-1, -1), "TR", 6.8),
            ("FONT", (0, 0), (-1, 0), "TRB", 6.8),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
            ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]))
        return tb

    def resim(ad, gen):
        yol = os.path.join(CIKTI, ad)
        from PIL import Image as PI
        w, h = PI.open(yol).size
        return Image(yol, width=gen, height=gen * h / w)

    def deney(baslik, tk, yk):
        return [
            Paragraph(f"<b>Tahmin (önce):</b> {v(t, tk)}", N),
            Paragraph(f"<b>Ne gördüm:</b> {v(y, yk + '_gordum')} <b>Neden olabilir:</b> {v(y, yk + '_neden')} "
                      f"<b>Nasıl kontrol ederim:</b> {v(y, yk + '_kontrol')}", N),
        ]

    a4 = s["adim4"]
    e = s["esikler"]
    a5, a6, a7 = s["adim5"], s["adim6"], s["adim7"]
    W = A4[0] - 24 * mm
    h = []
    h.append(Paragraph("YZM 411 Ödev 1 — Renk, Aydınlatma ve Örnekleme", BAS))
    h.append(Paragraph(f"{v(ayar, 'ogrenci_adi')} · {ayar.get('ogrenci_no', '')} · Kamera: {v(ayar, 'kamera')} · "
                       f"Otomatik pozlama/beyaz dengesi: {v(ayar, 'oto_pozlama_beyaz_dengesi')}", N))
    h.append(Paragraph(f"<b>Sahne:</b> {v(ayar, 'sahne_aciklamasi')}", N))

    h.append(Paragraph("1. Sayısal yapı (H1)", K))
    n = a4["normal"]
    h.append(Paragraph(
        f"img.shape = {tuple(n['shape'])} (H×W×C), dtype = {n['dtype']}, aralık {n['min']}–{n['max']}. "
        f"Erişim img[y, x, kanal]; cv2 BGR okur, cv2.cvtColor(..., COLOR_BGR2RGB) ile RGB'ye çevrildi "
        f"(kodda bgr[y,x][::-1] == rgb[y,x] doğrulanır).", N))
    satir = [["piksel (x, y)"] + [f"{k} RGB" for k in ISIKLAR]]
    for i, p in enumerate(a4["normal"]["pikseller"]):
        satir.append([f"({p['x']}, {p['y']})"] + [str(tuple(a4[k]["pikseller"][i]["rgb"])) for k in ISIKLAR])
    h.append(tablo(satir, [W * 0.22] + [W * 0.26] * 3))
    hz_yol = os.path.join(CIKTI, "hizalama.json")
    if os.path.exists(hz_yol):
        hz = json.load(open(hz_yol, encoding="utf-8"))
        h.append(Paragraph(
            "<b>Hizalama (sınırlama):</b> Telefon kadrajı çekimler arasında değişti; gölge ve lamba fotoğrafları "
            "ORB+RANSAC homografi ile normal fotoğrafa hizalandı (hizala.py). Ölçek: gölge "
            f"{hz['golge']['olcek_yaklasik']}, lamba {hz['lamba']['olcek_yaklasik']}; kenar uyumu ham → hizalı: "
            f"gölge {hz['golge']['kenar_uyumu_ham']} → {max(hz['golge']['kenar_uyumu_orb'], hz['golge']['kenar_uyumu_ecc'])}, "
            f"lamba {hz['lamba']['kenar_uyumu_ham']} → {max(hz['lamba']['kenar_uyumu_orb'], hz['lamba']['kenar_uyumu_ecc'])}. "
            "Yeniden örnekleme (INTER_LINEAR) piksel değerlerini hafif yumuşatır.", N))

    h.append(Paragraph("2. Sabit eşikli renk maskeleri (H2)", K))
    h.append(Paragraph(
        f"Eşikler yalnızca normal ışıklı fotoğraftaki nesne ROI'sinden bir kez belirlenip donduruldu (esikler.json): "
        f"RGB {e['rgb_alt']}–{e['rgb_ust']}; HSV H {e['h_alt']}–{e['h_ust']}"
        f"{' (+90 kaydırmalı)' if e['h_kaydirma'] else ''}, S ≥ {e['s_alt']}, V ≥ {e['v_alt']} (OpenCV H 0–179). "
        f"Oran = seçilen piksel / görüntü alanı; doğruluk ölçütü <b>değildir</b>.", N))
    h.append(resim("adim5_maskeler.png", W * 0.66))
    satir = [["ışık", "RGB alan %", "HSV alan %", "RGB: nesne kutusu içi %", "HSV: nesne kutusu içi %"]]
    for k in ISIKLAR:
        d = a5[k]
        satir.append([k, d["rgb_oran_%"], d["hsv_oran_%"], d["rgb_roi_ici_%"], d["hsv_roi_ici_%"]])
    h.append(tablo(satir, [W * 0.12, W * 0.17, W * 0.17, W * 0.27, W * 0.27]))
    h += deney("maske", "adim5_maske", "adim5")

    h.append(Paragraph("3. Parlaklık kaydırması ve gama (H3)", K))
    h.append(resim("adim6_donusumler.png", W * 0.72))
    p = a6["parlaklik_b+40"]
    satir = [["dönüşüm", "naif beklenti f(ort)", "ölçülen ort", "fark"],
             ["orijinal", "-", a6["orijinal_ort"], "-"]]
    for k in ["parlaklik_b+40", "gama_0.5", "gama_2.0"]:
        d = a6[k]
        satir.append([k, d["naif_beklenti_f(ort)"], d["olculen_ort"],
                      round(d["olculen_ort"] - d["naif_beklenti_f(ort)"], 2)])
    h.append(tablo(satir, [W * 0.25] * 4))
    h.append(Paragraph(
        f"b=+40'ta değerlerin %{p['255te_kirpilan_deger_%']}'i 255'te kırpıldı (ortalamaya etkisi −{p['kirpma_kaybi']}). "
        f"Kontrol: 64 → γ0,5: {a6['kontrol_64']['g0.5']}, γ2,0: {a6['kontrol_64']['g2.0']}. "
        f"Gama doğrusal olmadığı için ort(f(I)) ≠ f(ort(I)).", N))
    h += deney("parlaklık", "adim6_parlaklik", "adim6_parlaklik")
    h.append(Paragraph(f"<b>Gama tahminleri:</b> γ=0,5: {v(t, 'adim6_gama05')} γ=2,0: {v(t, 'adim6_gama20')}", N))
    h.append(Paragraph(f"<b>Gama yorumu:</b> {v(y, 'adim6_gama')}", N))

    h.append(Paragraph("4. Küçültme (H4)", K))
    h.append(resim("adim7_kucultme.png", W * 0.92))
    satir = [["yöntem", "MAE", "kontrast P95−P5", "kenar enerjisi"],
             ["orijinal", "-", a7["orijinal"]["kontrast_P95-P5"], a7["orijinal"]["kenar_enerjisi"]]]
    for k in ["INTER_NEAREST", "INTER_AREA"]:
        satir.append([k, a7[k]["MAE"], a7[k]["kontrast_P95-P5"], a7[k]["kenar_enerjisi"]])
    h.append(tablo(satir, [W * 0.25] * 4))
    h.append(Paragraph(f"Kesit {a7['kesit_boyut'][1]}×{a7['kesit_boyut'][0]} → {a7['kucuk_boyut'][1]}×"
                       f"{a7['kucuk_boyut'][0]}; büyütme yalnızca göstermek için en yakın komşu.", N))
    h += deney("küçültme", "adim7_kucultme", "adim7")

    h.append(Paragraph("5. Sorular, tutmayan tahmin, sınırlar", K))
    h.append(Paragraph(f"<b>Sarı bir arka plan neden hedef gibi seçildi?</b> {v(y, 'soru_sari_arkaplan')}", N))
    h.append(Paragraph(f"<b>Büyütme kaybolan yazıyı neden geri getirmedi?</b> {v(y, 'soru_buyutme')}", N))
    h.append(Paragraph(f"<b>Tutmayan tahminim:</b> {v(y, 'tutmayan_tahmin')}", N))
    h.append(Paragraph(f"<b>Sınırlar:</b> {v(y, 'sinirlar')}", N))
    h.append(Paragraph(f"<b>Yapay zekâ beyanı:</b> {v(y, 'yapay_zeka_beyani')}", N))
    sv = s["surumler"]
    h.append(Paragraph(f"<b>Yeniden çalıştırma:</b> Python {sv['python']}, OpenCV {sv['opencv']}, NumPy {sv['numpy']}, "
                       f"Matplotlib {sv['matplotlib']}. Sıra: odev1.py --sec → tahminler.json → odev1.py → "
                       f"yorumlar.json → odev1.py --rapor. Girdi: {', '.join(ayar['fotograflar'].values())}.", N))

    os.makedirs(os.path.join(KOK, "rapor"), exist_ok=True)
    cikis = os.path.join(KOK, "rapor", f"YZM411_Odev1_{ayar.get('ogrenci_no', 'OgrenciNo')}.pdf")
    doc = SimpleDocTemplate(cikis, pagesize=A4, leftMargin=12 * mm, rightMargin=12 * mm,
                            topMargin=10 * mm, bottomMargin=10 * mm)
    doc.build(h)
    from pypdf import PdfReader
    sayfa = len(PdfReader(cikis).pages)
    print(f"Rapor: {cikis} ({sayfa} sayfa)")
    if sayfa > 2:
        print("UYARI: 2 sayfa sınırı aşıldı — yorumları kısalt ya da rapor_olustur.py'de resim genişliklerini küçült.")


if __name__ == "__main__":
    main()
