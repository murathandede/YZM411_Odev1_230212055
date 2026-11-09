"""
YZM 411 Bilgisayarli Goru - Odev 1: Renk, Aydinlatma ve Ornekleme
Ogrenci No: 230212055

Calistirma sirasi (README.md'de ayrintili):
  1) python odev1.py --sec          -> fotograflar uzerinde ROI / piksel secimi (pencere acar), ayarlar.json'a yazar
  2) tahminler.json dosyasini DENEYLERI CALISTIRMADAN ONCE doldur
  3) python odev1.py                -> tum deneyler, ciktilar/ klasoru, sonuc tablosu
  4) yorumlar.json dosyasini olcumlere bakarak doldur
  5) python odev1.py --rapor        -> rapor/YZM411_Odev1_230212055.pdf

Esikler ILK calistirmada normal isikli fotograftan belirlenir ve esikler.json'a
DONDURULUR. Sonraki calistirmalarda dosya varsa yeniden hesaplanmaz.
"""
import argparse
import csv
import json
import os
import platform
import sys

import cv2
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

KOK = os.path.dirname(os.path.abspath(__file__))
AYAR = os.path.join(KOK, "ayarlar.json")
ESIK = os.path.join(KOK, "esikler.json")
TAHMIN = os.path.join(KOK, "tahminler.json")
YORUM = os.path.join(KOK, "yorumlar.json")
CIKTI = os.path.join(KOK, "ciktilar")
ISIKLAR = ["normal", "golge", "lamba"]


# ----------------------------------------------------------------- yardimcilar
def jyukle(yol, varsayilan=None):
    if not os.path.exists(yol):
        return varsayilan
    with open(yol, encoding="utf-8") as f:
        return json.load(f)


def jyaz(yol, veri):
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)


def oku_bgr(yol):
    # cv2.imread Turkce karakterli Windows yollarinda sorun cikarabilir -> imdecode
    veri = np.fromfile(yol, dtype=np.uint8)
    img = cv2.imdecode(veri, cv2.IMREAD_COLOR)
    if img is None:
        sys.exit(f"Goruntu okunamadi: {yol}")
    return img


def fotolar(ayar):
    return {k: oku_bgr(os.path.join(KOK, ayar["fotograflar"][k])) for k in ISIKLAR}


def surumler():
    return {
        "python": platform.python_version(),
        "opencv": cv2.__version__,
        "numpy": np.__version__,
        "matplotlib": matplotlib.__version__,
    }


# ------------------------------------------------------ 0) etkilesimli secim
def sec(ayar):
    """ROI ve pikselleri fareyle sec. Windows/Mac'te yerel calistir (Colab'da pencere acilmaz)."""
    img = oku_bgr(os.path.join(KOK, ayar["fotograflar"]["normal"]))
    olcek = min(1.0, 1400 / max(img.shape[:2]))
    kucuk = cv2.resize(img, None, fx=olcek, fy=olcek, interpolation=cv2.INTER_AREA)

    def roi(baslik):
        print(f"\n{baslik}: fareyle dikdortgen ciz, ENTER/SPACE ile onayla.")
        x, y, w, h = cv2.selectROI(baslik, kucuk, showCrosshair=True)
        cv2.destroyWindow(baslik)
        return [int(x / olcek), int(y / olcek), int(w / olcek), int(h / olcek)]

    ayar["nesne_roi"] = roi("1-Nesnenin KUCUK bir bolgesi (esik icin)")
    ayar["yazi_roi"] = roi("2-Yazili/cizgili bolge (kucultme icin)")

    noktalar = []
    goster = kucuk.copy()

    def tik(olay, x, y, *_):
        if olay == cv2.EVENT_LBUTTONDOWN and len(noktalar) < 3:
            noktalar.append([int(x / olcek), int(y / olcek)])
            cv2.circle(goster, (x, y), 6, (0, 0, 255), 2)
            cv2.imshow(baslik, goster)

    baslik = "3-Ayni fiziksel bolgeden 3 piksel tikla, sonra herhangi bir tus"
    print(f"\n{baslik}")
    cv2.namedWindow(baslik)
    cv2.setMouseCallback(baslik, tik)
    cv2.imshow(baslik, goster)
    while len(noktalar) < 3:
        cv2.waitKey(50)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    ayar["pikseller_xy"] = noktalar
    jyaz(AYAR, ayar)
    print("\nayarlar.json guncellendi:", ayar["nesne_roi"], ayar["yazi_roi"], noktalar)


# ------------------------------------------------- 4) sayisal yapi (Hedef 1)
def adim4(imgs, ayar):
    sonuc = {}
    for k, bgr in imgs.items():
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        sonuc[k] = {
            "shape": list(bgr.shape),
            "dtype": str(bgr.dtype),
            "min": int(bgr.min()),
            "max": int(bgr.max()),
            "pikseller": [],
        }
        for (x, y) in ayar["pikseller_xy"]:
            # NumPy erisimi img[y, x, kanal]; OpenCV BGR okur
            b, g, r = (int(v) for v in bgr[y, x])
            rgb_deger = [int(v) for v in rgb[y, x]]
            assert rgb_deger == [r, g, b], "BGR->RGB donusumu tutarsiz"
            sonuc[k]["pikseller"].append({"x": x, "y": y, "bgr": [b, g, r], "rgb": rgb_deger})

    # Ayni piksel komsulugunun 5x5 ortalamasi (tek piksel gurultuye duyarli)
    for k, bgr in imgs.items():
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32)
        for p in sonuc[k]["pikseller"]:
            x, y = p["x"], p["y"]
            p["rgb_5x5_ort"] = [round(float(v), 1) for v in rgb[max(0, y-2):y+3, max(0, x-2):x+3].reshape(-1, 3).mean(0)]

    with open(os.path.join(CIKTI, "adim4_pikseller.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["isik", "x", "y", "R", "G", "B", "R_5x5", "G_5x5", "B_5x5"])
        for k in ISIKLAR:
            for p in sonuc[k]["pikseller"]:
                w.writerow([k, p["x"], p["y"], *p["rgb"], *p["rgb_5x5_ort"]])
    return sonuc


# --------------------------------------------- 5) sabit esik maskeler (Hedef 2)
def esik_belirle(bgr_normal, roi):
    """Normal isikli fotograftaki ROI'den yuzdelik tabanli aralik. Bir kez calisir, sonra dondurulur."""
    x, y, w, h = roi
    parca = bgr_normal[y:y+h, x:x+w]
    rgb = cv2.cvtColor(parca, cv2.COLOR_BGR2RGB).reshape(-1, 3).astype(np.float32)
    hsv = cv2.cvtColor(parca, cv2.COLOR_BGR2HSV).reshape(-1, 3).astype(np.float32)
    pay = 15
    rgb_alt = np.clip(np.percentile(rgb, 2, axis=0) - pay, 0, 255).astype(int).tolist()
    rgb_ust = np.clip(np.percentile(rgb, 98, axis=0) + pay, 0, 255).astype(int).tolist()

    # Ton dairesel (0-179). Kirmizi nesnede 0/179 sarmalanmasini yakalamak icin 90 kaydir.
    h_ = hsv[:, 0]
    yayilim = np.percentile(h_, 98) - np.percentile(h_, 2)
    kaydir = 0
    if yayilim > 90:
        kaydir = 90
        h_ = (h_ + 90) % 180
    h_lo = int(max(0, np.percentile(h_, 2) - 4))
    h_hi = int(min(179, np.percentile(h_, 98) + 4))
    s_lo = int(max(0, np.percentile(hsv[:, 1], 2) - 30))
    v_lo = int(max(0, np.percentile(hsv[:, 2], 2) - 40))
    return {
        "kaynak": "normal isik, nesne_roi, %2-%98 yuzdelik + pay",
        "rgb_alt": rgb_alt, "rgb_ust": rgb_ust,
        "h_alt": h_lo, "h_ust": h_hi, "h_kaydirma": kaydir,
        "s_alt": s_lo, "s_ust": 255, "v_alt": v_lo, "v_ust": 255,
    }


def maske_rgb(bgr, e):
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return cv2.inRange(rgb, np.array(e["rgb_alt"], np.uint8), np.array(e["rgb_ust"], np.uint8))


def maske_hsv(bgr, e):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    if e["h_kaydirma"]:
        hsv[..., 0] = ((hsv[..., 0].astype(np.int16) + e["h_kaydirma"]) % 180).astype(np.uint8)
    alt = np.array([e["h_alt"], e["s_alt"], e["v_alt"]], np.uint8)
    ust = np.array([e["h_ust"], e["s_ust"], e["v_ust"]], np.uint8)
    return cv2.inRange(hsv, alt, ust)


def adim5(imgs, ayar):
    e = jyukle(ESIK)
    if e is None:
        e = esik_belirle(imgs["normal"], ayar["nesne_roi"])
        jyaz(ESIK, e)
        print("Esikler belirlendi ve esikler.json'a donduruldu.")
    else:
        print("esikler.json bulundu -> dondurulmus esikler kullaniliyor (yeniden ayarlanmadi).")

    x, y, w, h = ayar["nesne_roi"]
    sonuc, maskeler = {}, {}
    for k, bgr in imgs.items():
        alan = bgr.shape[0] * bgr.shape[1]
        mr, mh = maske_rgb(bgr, e), maske_hsv(bgr, e)
        maskeler[k] = (mr, mh)
        roi_alan = w * h
        sonuc[k] = {
            "rgb_oran_%": round(100 * cv2.countNonZero(mr) / alan, 3),
            "hsv_oran_%": round(100 * cv2.countNonZero(mh) / alan, 3),
            # Ek tani: secilen piksellerin ne kadari nesne kutusunun DISINDA? (yanlis secim belirtisi)
            "rgb_roi_ici_%": round(100 * cv2.countNonZero(mr[y:y+h, x:x+w]) / roi_alan, 2),
            "hsv_roi_ici_%": round(100 * cv2.countNonZero(mh[y:y+h, x:x+w]) / roi_alan, 2),
        }
        cv2.imwrite(os.path.join(CIKTI, f"maske_rgb_{k}.png"), mr)
        cv2.imwrite(os.path.join(CIKTI, f"maske_hsv_{k}.png"), mh)

    fig, ax = plt.subplots(3, 3, figsize=(9, 6.6))
    for i, k in enumerate(ISIKLAR):
        ax[0, i].imshow(cv2.cvtColor(imgs[k], cv2.COLOR_BGR2RGB))
        ax[0, i].set_title(k, fontsize=9)
        ax[1, i].imshow(maskeler[k][0], cmap="gray")
        ax[1, i].set_title(f"RGB maske  %{sonuc[k]['rgb_oran_%']}", fontsize=8)
        ax[2, i].imshow(maskeler[k][1], cmap="gray")
        ax[2, i].set_title(f"HSV maske  %{sonuc[k]['hsv_oran_%']}", fontsize=8)
    for a in ax.ravel():
        a.axis("off")
    fig.tight_layout()
    fig.savefig(os.path.join(CIKTI, "adim5_maskeler.png"), dpi=130)
    plt.close(fig)
    return e, sonuc


# ----------------------------------------- 6) parlaklik ve gama (Hedef 3)
def parlaklik(I, b=40):
    return np.clip(I.astype(np.float32) + b, 0, 255)


def gama(I, g):
    # Bu odevde gama formuldeki ustur: J = 255 * (I/255)^g
    return np.clip(255.0 * (I.astype(np.float32) / 255.0) ** g, 0, 255)


def adim6(imgs):
    I = cv2.cvtColor(imgs["normal"], cv2.COLOR_BGR2RGB)
    If = I.astype(np.float32)
    ort0 = float(If.mean())
    # Kirpma olmasaydi beklenen ortalama: ort0 + 40. Gama icin piksel bazli beklenti = donusumun ortalamasi
    # (Jensen: mean(f(I)) != f(mean(I)), bu yuzden "f(ortalama)" ile "ortalama(f)" ayrica raporlanir)
    sonuc = {"orijinal_ort": round(ort0, 2)}
    donus = {
        "parlaklik_b+40": parlaklik(I, 40),
        "gama_0.5": gama(I, 0.5),
        "gama_2.0": gama(I, 2.0),
    }
    naif = {
        "parlaklik_b+40": ort0 + 40,
        "gama_0.5": 255 * (ort0 / 255) ** 0.5,
        "gama_2.0": 255 * (ort0 / 255) ** 2.0,
    }
    for k, J in donus.items():
        r = {
            "olculen_ort": round(float(J.mean()), 2),
            "naif_beklenti_f(ort)": round(naif[k], 2),
        }
        if k.startswith("parlaklik"):
            kirpilan = (If + 40) > 255
            r["255te_kirpilan_deger_%"] = round(100 * kirpilan.mean(), 3)
            r["kirpma_kaybi"] = round(float((If + 40 - 255)[kirpilan].sum() / If.size), 2)
            r["zaten_255_olan_%"] = round(100 * (I == 255).mean(), 3)
        sonuc[k] = r
        cv2.imwrite(os.path.join(CIKTI, f"adim6_{k}.jpg"),
                    cv2.cvtColor(J.round().astype(np.uint8), cv2.COLOR_RGB2BGR))
    # Kontrol: odevdeki ornek 64 -> ~128 / ~16
    sonuc["kontrol_64"] = {"g0.5": round(float(gama(np.array([64]), 0.5)[0]), 1),
                           "g2.0": round(float(gama(np.array([64]), 2.0)[0]), 1)}

    fig, ax = plt.subplots(2, 4, figsize=(11, 4.6), gridspec_kw={"height_ratios": [2.2, 1]})
    goster = {"orijinal": If, **donus}
    for i, (k, J) in enumerate(goster.items()):
        ax[0, i].imshow(J.round().astype(np.uint8))
        ax[0, i].set_title(f"{k}\nort={J.mean():.1f}", fontsize=8)
        ax[0, i].axis("off")
        ax[1, i].hist(J.ravel(), bins=64, range=(0, 255), color="0.35")
        ax[1, i].set_yticks([])
        ax[1, i].tick_params(labelsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(CIKTI, "adim6_donusumler.png"), dpi=130)
    plt.close(fig)
    return sonuc


# --------------------------------------------------- 7) kucultme (Hedef 4)
def adim7(imgs, ayar):
    x, y, w, h = ayar["yazi_roi"]
    parca = cv2.cvtColor(imgs["normal"][y:y+h, x:x+w], cv2.COLOR_BGR2RGB)
    H, W = parca.shape[:2]
    yeni = (max(1, W // 4), max(1, H // 4))
    sonuc, gorsel = {"kesit_boyut": [H, W], "kucuk_boyut": [yeni[1], yeni[0]]}, {"orijinal": parca}
    for ad, yontem in [("INTER_NEAREST", cv2.INTER_NEAREST), ("INTER_AREA", cv2.INTER_AREA)]:
        k = cv2.resize(parca, yeni, interpolation=yontem)
        # Yalnizca GOSTERMEK icin en yakin komsuyla geri buyut
        b = cv2.resize(k, (W, H), interpolation=cv2.INTER_NEAREST)
        gorsel[ad] = b
        fark = np.abs(b.astype(np.float32) - parca.astype(np.float32))
        g0 = cv2.cvtColor(parca, cv2.COLOR_RGB2GRAY).astype(np.float32)
        g1 = cv2.cvtColor(b, cv2.COLOR_RGB2GRAY).astype(np.float32)
        sonuc[ad] = {
            "MAE": round(float(fark.mean()), 2),
            # Kontrast: yazinin siyah-beyaz ayrimi ne kadar kaldi (P95-P5 gri)
            "kontrast_P95-P5": round(float(np.percentile(g1, 95) - np.percentile(g1, 5)), 1),
            # Kenar enerjisi: ince ayrinti miktari
            "kenar_enerjisi": round(float(np.abs(cv2.Laplacian(g1, cv2.CV_32F)).mean()), 2),
        }
        cv2.imwrite(os.path.join(CIKTI, f"adim7_{ad}_x4.png"), cv2.cvtColor(b, cv2.COLOR_RGB2BGR))
    g0 = cv2.cvtColor(parca, cv2.COLOR_RGB2GRAY).astype(np.float32)
    sonuc["orijinal"] = {
        "kontrast_P95-P5": round(float(np.percentile(g0, 95) - np.percentile(g0, 5)), 1),
        "kenar_enerjisi": round(float(np.abs(cv2.Laplacian(g0, cv2.CV_32F)).mean()), 2),
    }

    fig, ax = plt.subplots(1, 3, figsize=(11, 3.4))
    for a, (ad, im) in zip(ax, gorsel.items()):
        a.imshow(im, interpolation="nearest")
        a.set_title(ad if ad == "orijinal" else f"{ad} 1/4 -> NN ile geri", fontsize=9)
        a.axis("off")
    fig.tight_layout()
    fig.savefig(os.path.join(CIKTI, "adim7_kucultme.png"), dpi=150)
    plt.close(fig)
    return sonuc


# ---------------------------------------------------------------- calistir
def calistir():
    ayar = jyukle(AYAR)
    if not ayar or not ayar.get("nesne_roi"):
        sys.exit("Once ayarlar.json'u doldur ya da `python odev1.py --sec` calistir.")
    t = jyukle(TAHMIN, {})
    eksik = [k for k in ["adim5_maske", "adim6_parlaklik", "adim6_gama05", "adim6_gama20", "adim7_kucultme"]
             if not str(t.get(k, "")).strip()]
    if eksik:
        sys.exit("Odev kurali: deneyden ONCE tahmin yazilmali. tahminler.json'da bos: " + ", ".join(eksik))

    os.makedirs(CIKTI, exist_ok=True)
    imgs = fotolar(ayar)
    sonuc = {"surumler": surumler(), "ayarlar": ayar}
    sonuc["adim4"] = adim4(imgs, ayar)
    sonuc["esikler"], sonuc["adim5"] = adim5(imgs, ayar)
    sonuc["adim6"] = adim6(imgs)
    sonuc["adim7"] = adim7(imgs, ayar)
    jyaz(os.path.join(CIKTI, "sonuclar.json"), sonuc)

    with open(os.path.join(CIKTI, "sonuc_tablosu.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["deney", "olcum", "deger"])
        for k in ISIKLAR:
            for m, v in sonuc["adim5"][k].items():
                w.writerow([f"adim5_{k}", m, v])
        for k, d in sonuc["adim6"].items():
            if isinstance(d, dict):
                for m, v in d.items():
                    w.writerow([f"adim6_{k}", m, v])
            else:
                w.writerow(["adim6", k, d])
        for k, d in sonuc["adim7"].items():
            if isinstance(d, dict):
                for m, v in d.items():
                    w.writerow([f"adim7_{k}", m, v])
    print(json.dumps({k: sonuc[k] for k in ["adim5", "adim6", "adim7"]}, ensure_ascii=False, indent=1))
    print(f"\nCiktilar: {CIKTI}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--sec", action="store_true", help="ROI/piksel secimi (pencere acar)")
    p.add_argument("--rapor", action="store_true", help="PDF raporu uret (rapor_olustur.py)")
    a = p.parse_args()
    if a.sec:
        sec(jyukle(AYAR))
    elif a.rapor:
        import rapor_olustur
        rapor_olustur.main()
    else:
        calistir()
