import pygame
import math

# ==========================================
# --- AYARLAR VE SABİTLER ---
# ==========================================
GENISLIK, YUKSEKLIK = 800, 600
# Ekranın merkez noktası koordinatları (Matematiksel (0,0) noktası olarak kullanılacak)
MERKEZ_X, MERKEZ_Y = GENISLIK // 2, YUKSEKLIK // 2

# Kullanıcının seçebileceği renklerin RGB (Red, Green, Blue) formatında tanımlanması
RENKLER = {
    "1": ("Kırmızı", (255, 0, 0)),
    "2": ("Yeşil", (0, 255, 0)),
    "3": ("Mavi", (0, 0, 255)),
    "4": ("Sarı", (255, 255, 0)),
    "5": ("Beyaz", (255, 255, 255))
}

# ==========================================
# --- YARDIMCI FONKSİYONLAR ---
# ==========================================

def donusum(math_x, math_y):
    """
    Matematiksel (Kartezyen) koordinatları, bilgisayar ekranı koordinatlarına çevirir.
    Pygame'de (0,0) noktası sol üst köşedir ve Y ekseni aşağı doğru artar.
    Bu fonksiyon ile (0,0) noktası ekranın tam merkezine (400, 300) taşınır ve Y ekseni tersine çevrilir.
    """
    ekran_x = MERKEZ_X + math_x
    ekran_y = MERKEZ_Y - math_y # Matematiksel Y eksenini bilgisayar ekranına uydurmak için çıkarıyoruz
    return (ekran_x, ekran_y)

def ciz_ekran(noktalar, renk, baslik, dolu_mu=False):
    """
    Hesaplanan koordinat noktalarını Pygame penceresinde görselleştirir.
    Pencere açılır, şekil çizilir ve kullanıcı pencereyi kapatana kadar ekranda kalır.
    """
    pygame.init() # Pygame motorunu başlat
    ekran = pygame.display.set_mode((GENISLIK, YUKSEKLIK)) # Pencereyi oluştur
    pygame.display.set_caption(baslik) # Pencere başlığını ayarla
    
    ekran.fill((30, 30, 30)) # Arkaplanı koyu gri renge boya
    
    # Koordinat düzlemini (X ve Y eksenlerini) referans olarak ince, gri çizgilerle çiz
    pygame.draw.line(ekran, (100, 100, 100), (0, MERKEZ_Y), (GENISLIK, MERKEZ_Y), 1)
    pygame.draw.line(ekran, (100, 100, 100), (MERKEZ_X, 0), (MERKEZ_X, YUKSEKLIK), 1)

    # Şeklin çizim mantığı:
    # Eğer şekil içi dolu istenmişse ve en az 3 nokta varsa 'polygon' (çokgen dolgusu) kullan.
    # Aksi halde noktaları sadece dış hat olarak 'lines' (çizgiler) ile birleştir.
    if len(noktalar) > 2 and dolu_mu:
        pygame.draw.polygon(ekran, renk, noktalar)
    elif len(noktalar) > 1:
        pygame.draw.lines(ekran, renk, False, noktalar, 2) # 2 piksel kalınlığında çizgi

    pygame.display.flip() # Çizilenleri ekrana yansıt (Güncelle)

    # Pygame olay (event) döngüsü: Pencere kapanana kadar programı açık tut
    calisiyor = True
    while calisiyor:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: # Çarpı tuşuna basılırsa
                calisiyor = False
                
    pygame.display.quit() # Menüye dönebilmek için ekranı güvenlice kapat

# ==========================================
# --- PARAMETRİK ŞEKİL HESAPLAMA FONKSİYONLARI ---
# ==========================================

def hesapla_daire(r):
    noktalar = []
    t = 0
    # t (açı) 0'dan 2*pi'ye (360 derece) kadar 0.05 adımlarla artırılır
    while t <= 2 * math.pi:
        x = r * math.cos(t) # Dairenin parametrik X denklemi
        y = r * math.sin(t) # Dairenin parametrik Y denklemi
        noktalar.append(donusum(x, y)) # Noktayı ekran koordinatına çevir ve listeye ekle
        t += 0.05
    # Çizginin tam kapanması için döngü sonu ilk noktaya (t=0) manuel olarak bağlanır
    noktalar.append(donusum(r * math.cos(0), r * math.sin(0))) 
    return noktalar

def hesapla_elips(a, b):
    noktalar = []
    t = 0
    while t <= 2 * math.pi:
        x = a * math.cos(t) # Yatay yarıçap 'a' ile çarpılır
        y = b * math.sin(t) # Düşey yarıçap 'b' ile çarpılır
        noktalar.append(donusum(x, y))
        t += 0.05
    noktalar.append(donusum(a * math.cos(0), b * math.sin(0)))
    return noktalar

def hesapla_spiral(a, b, donus_sayisi):
    noktalar = []
    t = 0
    # Spiral için t, dönüş sayısı kadar 2*pi ile çarpılarak maksimum açı bulunur
    maksimum_t = 2 * math.pi * donus_sayisi
    while t <= maksimum_t:
        x = (a + b * t) * math.cos(t) # Arşimet spirali x denklemi
        y = (a + b * t) * math.sin(t) # Arşimet spirali y denklemi
        noktalar.append(donusum(x, y))
        t += 0.05
    return noktalar

def hesapla_kare(a):
    noktalar = []
    # Karenin merkezi orijin kabul edilerek 4 köşesinin kartezyen koordinatları belirlenir
    kose_koordinatlari = [
        (-a/2, -a/2), (a/2, -a/2), (a/2, a/2), (-a/2, a/2), (-a/2, -a/2) 
    ]
    for x, y in kose_koordinatlari:
        noktalar.append(donusum(x, y))
    return noktalar

def hesapla_cokgen(R, n):
    noktalar = []
    # Düzgün çokgenin n adet köşesi çember üzerinde eşit açılarla dağıtılır
    for k in range(n + 1): 
        aci = (2 * math.pi * k / n) - (math.pi / 2) # -pi/2 ile şeklin tepeden başlaması sağlanır
        x = R * math.cos(aci)
        y = R * math.sin(aci)
        noktalar.append(donusum(x, y))
    return noktalar

def hesapla_yildiz(R, r, n):
    noktalar = []
    # Yıldız şekli, iç (r) ve dış (R) çemberler arasında zikzak çizilerek oluşturulur
    for k in range(2 * n + 1): 
        aci = (math.pi * k / n) - (math.pi / 2)
        if k % 2 == 0: # Çift sayılarda dış çember
            x = R * math.cos(aci)
            y = R * math.sin(aci)
        else: # Tek sayılarda iç çember noktası alınır
            x = r * math.cos(aci)
            y = r * math.sin(aci)
        noktalar.append(donusum(x, y))
    return noktalar

def hesapla_kardioid(a):
    noktalar = []
    t = 0
    while t <= 2 * math.pi:
        # Kardioid eğrisi (Kalp şekli) parametrik denklemleri
        x = a * (2 * math.cos(t) - math.cos(2 * t))
        y = a * (2 * math.sin(t) - math.sin(2 * t))
        noktalar.append(donusum(x, y))
        t += 0.05
    # Şekli tam kapatmak için t=2*pi anındaki nokta manuel eklenir
    x = a * (2 * math.cos(2*math.pi) - math.cos(4*math.pi))
    y = a * (2 * math.sin(2*math.pi) - math.sin(4*math.pi))
    noktalar.append(donusum(x, y))
    return noktalar

def hesapla_dikdortgen(w, h):
    noktalar = []
    # Dikdörtgen köşe koordinatları (w=genişlik, h=yükseklik)
    kose_koordinatlari = [
        (-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2), (-w/2, -h/2)
    ]
    for x, y in kose_koordinatlari:
        noktalar.append(donusum(x, y))
    return noktalar

def hesapla_eskenar_ucgen(a):
    noktalar = []
    # Eşkenar üçgen yüksekliği formülü: h = a * kök(3) / 2
    h = a * math.sqrt(3) / 2
    kose_koordinatlari = [
        (0, h/2), (-a/2, -h/2), (a/2, -h/2), (0, h/2) # Tepe noktası, sol alt, sağ alt, tepe noktası
    ]
    for x, y in kose_koordinatlari:
        noktalar.append(donusum(x, y))
    return noktalar

def hesapla_rozet(a, n):
    noktalar = []
    t = 0
    # Rozet (Rose) eğrisinde yaprak sayısı tek ise [0, 2*pi], çift ise [0, 4*pi] aralığı gerekir
    maksimum_t = 2 * math.pi if n % 2 != 0 else 4 * math.pi
    
    while t <= maksimum_t:
        r = a * math.cos(n * t) # Polar formülü
        x = r * math.cos(t)     # Kartezyene çevirme (X)
        y = r * math.sin(t)     # Kartezyene çevirme (Y)
        noktalar.append(donusum(x, y))
        t += 0.05
        
    noktalar.append(donusum(a * math.cos(n * maksimum_t) * math.cos(maksimum_t), 
                            a * math.cos(n * maksimum_t) * math.sin(maksimum_t)))
    return noktalar

# ==========================================
# --- KONSOL MENÜSÜ VE GİRDİ İŞLEMLERİ ---
# ==========================================

def renk_secimi():
    """Kullanıcıya renk seçeneklerini sunar ve seçilen rengin RGB değerini döndürür."""
    print("\nRenk Seçenekleri:")
    for key, (isim, _) in RENKLER.items():
        print(f"{key}. {isim}")
    secim = input("Renk seçiniz (1-5): ")
    # Eğer geçersiz bir seçim yapılırsa varsayılan olarak "5" (Beyaz) döndürür
    return RENKLER.get(secim, RENKLER["5"])[1]

def dolgu_secimi():
    """Şeklin içinin doldurulup doldurulmayacağını kullanıcıya sorar."""
    while True:
        secim = input("Şekil içi dolu çizilsin mi? (E/H): ").strip().upper()
        if secim == 'E':
            return True
        elif secim == 'H':
            return False
        else:
            print("Lütfen 'E' (Evet) veya 'H' (Hayır) giriniz.")

def ana_menu():
    """Programın ana döngüsünü barındıran menü fonksiyonu."""
    while True:
        print("\n" + "="*30)
        print(" PARAMETRİK GRAFİK ÇİZİCİ")
        print("="*30)
        print("1. Daire")
        print("2. Elips")
        print("3. Archimedean Spiral")
        print("4. Kare")
        print("5. Düzgün Çokgen")
        print("6. Yıldız")
        print("7. Kardioid")
        print("8. Dikdörtgen")
        print("9. Eşkenar Üçgen")
        print("10. Rozet (Rose)")
        print("0. Çıkış")
        
        secim = input("Lütfen çizmek istediğiniz şekli seçin: ")

        if secim == "0":
            print("Programdan çıkılıyor...")
            break # 0 girilirse sonsuz döngüden çık ve programı bitir
            
        # Kullanıcının harf veya yanlış sembol girmesine karşı Hata Yönetimi (Try-Except)
        try:
            if secim == "1":
                r = float(input("Yarıçap değerini (r) giriniz (örn: 100): "))
                renk = renk_secimi()
                dolu = dolgu_secimi()
                noktalar = hesapla_daire(r)
                ciz_ekran(noktalar, renk, f"Daire (r={r})", dolu_mu=dolu)
                
            elif secim == "2":
                a = float(input("Yatay yarıçap (a) değerini giriniz (örn: 150): "))
                b = float(input("Düşey yarıçap (b) değerini giriniz (örn: 80): "))
                renk = renk_secimi()
                dolu = dolgu_secimi()
                noktalar = hesapla_elips(a, b)
                ciz_ekran(noktalar, renk, f"Elips (a={a}, b={b})", dolu_mu=dolu)
                
            elif secim == "3":
                a = float(input("Başlangıç değeri (a) giriniz (örn: 0): "))
                b = float(input("Artış miktarı (b) giriniz (örn: 5): "))
                donus = int(input("Dönüş sayısı giriniz (örn: 4): "))
                renk = renk_secimi()
                dolu = dolgu_secimi() 
                noktalar = hesapla_spiral(a, b, donus)
                ciz_ekran(noktalar, renk, "Archimedean Spiral", dolu_mu=dolu)
                
            elif secim == "4":
                a = float(input("Kenar uzunluğunu (a) giriniz (örn: 200): "))
                renk = renk_secimi()
                dolu = dolgu_secimi()
                noktalar = hesapla_kare(a)
                ciz_ekran(noktalar, renk, f"Kare (a={a})", dolu_mu=dolu)
                
            elif secim == "5":
                r = float(input("Yarıçap (R) değerini giriniz (örn: 120): "))
                n = int(input("Kenar sayısını (n) giriniz (örn: 6): "))
                renk = renk_secimi()
                dolu = dolgu_secimi()
                noktalar = hesapla_cokgen(r, n)
                ciz_ekran(noktalar, renk, f"Düzgün Çokgen (n={n})", dolu_mu=dolu)
                
            elif secim == "6":
                R = float(input("Dış yarıçap (R) giriniz (örn: 150): "))
                r = float(input("İç yarıçap (r) giriniz (örn: 60): "))
                n = int(input("Uç sayısını (n) giriniz (örn: 5): "))
                renk = renk_secimi()
                dolu = dolgu_secimi()
                noktalar = hesapla_yildiz(R, r, n)
                ciz_ekran(noktalar, renk, f"Yıldız (n={n})", dolu_mu=dolu)
                
            elif secim == "7":
                a = float(input("Ölçek faktörü (a) giriniz (örn: 60): "))
                renk = renk_secimi()
                dolu = dolgu_secimi()
                noktalar = hesapla_kardioid(a)
                ciz_ekran(noktalar, renk, f"Kardioid (a={a})", dolu_mu=dolu)

            elif secim == "8":
                w = float(input("Genişlik (w) giriniz (örn: 200): "))
                h = float(input("Yükseklik (h) giriniz (örn: 100): "))
                renk = renk_secimi()
                dolu = dolgu_secimi()
                noktalar = hesapla_dikdortgen(w, h)
                ciz_ekran(noktalar, renk, f"Dikdörtgen (w={w}, h={h})", dolu_mu=dolu)

            elif secim == "9":
                a = float(input("Kenar uzunluğunu (a) giriniz (örn: 150): "))
                renk = renk_secimi()
                dolu = dolgu_secimi()
                noktalar = hesapla_eskenar_ucgen(a)
                ciz_ekran(noktalar, renk, f"Eşkenar Üçgen (a={a})", dolu_mu=dolu)

            elif secim == "10":
                a = float(input("Yarıçap (a) giriniz (örn: 150): "))
                n = int(input("Yaprak sayısını (n) giriniz (örn: 4 veya 5): "))
                renk = renk_secimi()
                dolu = dolgu_secimi()
                noktalar = hesapla_rozet(a, n)
                ciz_ekran(noktalar, renk, f"Rozet (a={a}, n={n})", dolu_mu=dolu)
                
            else:
                print("Geçersiz seçim, lütfen 0 ile 10 arasında bir rakam girin.")
                
        except ValueError:
            # Kullanıcı sayı yerine harf girerse programın çökmesini engeller
            print("\n[HATA] Geçersiz giriş yaptınız! Lütfen harf veya sembol yerine sadece sayısal değerler giriniz.")

# Eğer dosya doğrudan çalıştırılıyorsa ana menüyü başlat
if __name__ == "__main__":
    ana_menu()