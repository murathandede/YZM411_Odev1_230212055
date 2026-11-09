"""Kamera/telefon yazilimi kadraji degistirdigi icin golge ve lamba fotograflari
normal fotografa hizalanir. Ham fotograflar fotograflar/ham/ altinda DEGISTIRILMEDEN
durur; hizalanmis kopyalar fotograflar/ altina yazilir. Homografi matrisleri ve
hizalama kalitesi ciktilar/hizalama.json'a kaydedilir (raporda sinirlama olarak).

Yontem: ORB (8000 nokta) + Lowe oran testi + RANSAC homografi -> ECC ile ince ayar.
Not: warpPerspective yeniden ornekleme (INTER_LINEAR) yapar; piksel degerleri
hafif yumusar. Bu, olcumlerde bir sinirlamadir.
"""
import json
import os

import cv2
import numpy as np

KOK = os.path.dirname(os.path.abspath(__file__))
HAM = os.path.join(KOK, "fotograflar", "ham")
CIK = os.path.join(KOK, "fotograflar")
ESLESME = {"normal": "normal.jpg", "golge": "golge.jpg", "lamba": "lamba.jpg"}


def oku(yol):
    return cv2.imdecode(np.fromfile(yol, np.uint8), cv2.IMREAD_COLOR)


def gri(x):
    # Isik cok farkli oldugu icin yerel kontrast esitleme ile ozellik bul
    return cv2.createCLAHE(3.0, (8, 8)).apply(cv2.cvtColor(x, cv2.COLOR_BGR2GRAY))


def orb_homografi(ref, hedef):
    orb = cv2.ORB_create(8000)
    k0, d0 = orb.detectAndCompute(gri(ref), None)
    k1, d1 = orb.detectAndCompute(gri(hedef), None)
    eslesmeler = cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(d1, d0, k=2)
    iyi = [a for a, b in eslesmeler if a.distance < 0.75 * b.distance]
    src = np.float32([k1[m.queryIdx].pt for m in iyi])
    dst = np.float32([k0[m.trainIdx].pt for m in iyi])
    H, inl = cv2.findHomography(src, dst, cv2.RANSAC, 3.0)
    return H, len(iyi), int(inl.sum())


def ecc_ince_ayar(ref, hedef, H0, olcek=0.25):
    """Kucuk olcekte ECC homografi; ORB sonucunu baslangic alir."""
    S = np.diag([olcek, olcek, 1.0])
    Hs = (S @ H0 @ np.linalg.inv(S)).astype(np.float32)
    r = cv2.resize(gri(ref), None, fx=olcek, fy=olcek).astype(np.float32)
    h = cv2.resize(gri(hedef), None, fx=olcek, fy=olcek).astype(np.float32)
    kriter = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 300, 1e-6)
    # ECC hedef->ref yonunu tersten tanimlar: warp, ref koordinatindan hedefe esler
    W = np.linalg.inv(Hs).astype(np.float32)
    cc, W = cv2.findTransformECC(r, h, W, cv2.MOTION_HOMOGRAPHY, kriter, None, 5)
    Hs2 = np.linalg.inv(W)
    return (np.linalg.inv(S) @ Hs2 @ S), float(cc)


def kenar_uyumu(a, b):
    """Iki goruntunun kenar haritalarinin ortusme orani (0-1), hizalama kalitesi icin."""
    ea = cv2.dilate(cv2.Canny(cv2.GaussianBlur(gri(a), (5, 5), 0), 40, 120), np.ones((3, 3), np.uint8)) > 0
    eb = cv2.Canny(cv2.GaussianBlur(gri(b), (5, 5), 0), 40, 120) > 0
    return round(float((ea & eb).sum() / max(1, eb.sum())), 3)


def main():
    ref = oku(os.path.join(HAM, ESLESME["normal"]))
    H_, W_ = ref.shape[:2]
    cv2.imencode(".jpg", ref, [cv2.IMWRITE_JPEG_QUALITY, 100])[1].tofile(os.path.join(CIK, "normal.jpg"))
    rapor = {"yontem": "ORB+RANSAC homografi, ECC ince ayar, warpPerspective INTER_LINEAR",
             "referans": "normal", "boyut": [H_, W_]}
    for k in ["golge", "lamba"]:
        hedef = oku(os.path.join(HAM, ESLESME[k]))
        H0, n, inl = orb_homografi(ref, hedef)
        once = kenar_uyumu(ref, cv2.warpPerspective(hedef, H0, (W_, H_)))
        try:
            H1, cc = ecc_ince_ayar(ref, hedef, H0)
            sonra = kenar_uyumu(ref, cv2.warpPerspective(hedef, H1, (W_, H_)))
        except cv2.error:
            H1, cc, sonra = H0, None, once
        Hs = H1 if sonra >= once else H0
        hiz = cv2.warpPerspective(hedef, Hs, (W_, H_), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        cv2.imencode(".jpg", hiz, [cv2.IMWRITE_JPEG_QUALITY, 100])[1].tofile(os.path.join(CIK, ESLESME[k]))
        rapor[k] = {
            "orb_eslesme": n, "ransac_inlier": inl, "ecc_cc": cc,
            "kenar_uyumu_ham": kenar_uyumu(ref, hedef),
            "kenar_uyumu_orb": once, "kenar_uyumu_ecc": sonra,
            "secilen": "ecc" if Hs is H1 and H1 is not H0 else "orb",
            "homografi": np.round(Hs, 5).tolist(),
            "olcek_yaklasik": round(float(np.sqrt(abs(np.linalg.det(Hs[:2, :2])))), 3),
        }
        print(k, rapor[k])
    os.makedirs(os.path.join(KOK, "ciktilar"), exist_ok=True)
    with open(os.path.join(KOK, "ciktilar", "hizalama.json"), "w", encoding="utf-8") as f:
        json.dump(rapor, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
