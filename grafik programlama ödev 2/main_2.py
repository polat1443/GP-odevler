import pygame
import math
import sys

# ==========================================
# 1. SABİTLER VE KONFİGÜRASYON
# ==========================================
# Pygame'de renkler RGB (Red, Green, Blue) formatında (0-255 arası) tanımlanır.
BEYAZ = (255, 255, 255)
SIYAH = (0, 0, 0)
ACIK_MAVI = (173, 216, 230) # Büret içindeki sıvının rengi
GRI = (200, 200, 200)       # Vananın normal rengi
KIRMIZI = (255, 0, 0)       # Vana kolu ve Metil Oranj'ın asidik rengi
YESIL = (0, 255, 0)         # Eşdeğerlik noktası ve vana tutulma efekti
PEMBE = (255, 200, 200)     # Fenolftalein bazik rengi
RENKSIZ = (240, 240, 240)   # Asidik ortamda şeffaf/beyazımsı görünüm
SARI = (255, 255, 0)        # Metil Oranj ve Bromotimol için geçiş rengi
KOYU_MAVI = (0, 0, 200)     # Bromotimol Mavisi bazik rengi
GRAFIK_RENK = (50, 50, 255) # Alt kısımdaki titrasyon eğrisinin çizgi rengi

# ==========================================
# 2. KİMYA MOTORU SINIFI (ARKA PLAN İŞLEMLERİ)
# ==========================================
class KimyaMotoru:
    """
    Simülasyonun görsel olmayan, tamamen matematiksel ve kimyasal 
    hesaplamalarının yapıldığı "Mantık" (Logic) katmanıdır.
    """
    def __init__(self, Ca, Va_ml, Cb):
        self.Ca = Ca       # Asit derişimi (Molar)
        self.Va_ml = Va_ml # Asit hacmi (mL)
        self.Cb = Cb       # Baz derişimi (Molar)
        
        # Eşdeğerlik hacmi formülü: M_asit * V_asit = M_baz * V_baz
        # Buradan V_eq (Eşdeğerlikte eklenmesi gereken baz hacmi) bulunur.
        self.V_eq = (Ca * Va_ml) / Cb
        
        # 1: Fenolftalein, 2: Metil Oranj, 3: Bromotimol Mavisi
        self.secili_indikator = 1 
        self.indikator_isimleri = {
            1: "Fenolftalein (pH 8.2 - 10.0)", 
            2: "Metil Oranj (pH 3.1 - 4.4)", 
            3: "Bromotimol Mavisi (pH 6.0 - 7.6)"
        }

    def ph_hesapla(self, Vb):
        """Eklenen baz hacmine (Vb) göre anlık pH değerini hesaplar."""
        if Vb < 0: Vb = 0
        
        # Mol sayısı hesaplamaları (Hacim mL olduğu için 1000'e bölerek Litreye çeviriyoruz)
        mol_asit = self.Ca * self.Va_ml / 1000.0
        mol_baz = self.Cb * Vb / 1000.0
        
        # Toplam hacim (Litre cinsinden)
        V_toplam_L = (self.Va_ml + Vb) / 1000.0

        # Durum 1: Hiç baz eklenmediyse, sadece asidin pH'ı
        if Vb == 0:
            return -math.log10(self.Ca)
            
        # Durum 2: Eşdeğerlik noktasına henüz ulaşılmadı (Ortam Asidik)
        elif mol_baz < mol_asit:
            H_der = (mol_asit - mol_baz) / V_toplam_L # Kalan [H+] derişimi
            return -math.log10(H_der)
            
        # Durum 3: Tam eşdeğerlik noktası (Güçlü Asit - Güçlü Baz titrasyonunda pH = 7)
        elif mol_baz == mol_asit:
            return 7.0
            
        # Durum 4: Eşdeğerlik noktası geçildi (Ortam Bazik)
        else:
            OH_der = (mol_baz - mol_asit) / V_toplam_L # Artan [OH-] derişimi
            return 14.0 - (-math.log10(OH_der)) # pH = 14 - pOH

    def _renk_karistir(self, renk1, renk2, oran):
        """
        Geçiş aralıklarında (örneğin pH 8.2 ile 10.0 arası) iki renk arasında 
        yumuşak bir görsel geçiş (gradient/interpolation) sağlar.
        """
        oran = max(0.0, min(1.0, oran)) # Oran 0 ile 1 aralığından dışarı çıkmasın
        r = int(renk1[0] * (1 - oran) + renk2[0] * oran)
        g = int(renk1[1] * (1 - oran) + renk2[1] * oran)
        b = int(renk1[2] * (1 - oran) + renk2[2] * oran)
        return (r, g, b)

    def indikator_rengi(self, pH):
        """Anlık pH değerine ve seçili indikatöre göre sıvının rengini belirler."""
        if self.secili_indikator == 1: # Fenolftalein
            if pH < 8.2: return RENKSIZ
            elif pH > 10.0: return PEMBE
            else: return self._renk_karistir(RENKSIZ, PEMBE, (pH - 8.2) / (10.0 - 8.2))
            
        elif self.secili_indikator == 2: # Metil Oranj
            if pH < 3.1: return KIRMIZI
            elif pH > 4.4: return SARI
            else: return self._renk_karistir(KIRMIZI, SARI, (pH - 3.1) / (4.4 - 3.1))
            
        elif self.secili_indikator == 3: # Bromotimol Mavisi
            if pH < 6.0: return SARI
            elif pH > 7.6: return KOYU_MAVI
            else: return self._renk_karistir(SARI, KOYU_MAVI, (pH - 6.0) / (7.6 - 6.0))


# ==========================================
# 3. ARAYÜZ BİLEŞENLERİ SINIFI (GÖRSEL ÇİZİMLER)
# ==========================================
class ArayuzBilesenleri:
    """Ekranda görünen fiziksel kapların ve objelerin çiziminden sorumludur."""
    
    @staticmethod
    def buret_ciz(pencere, x, y, gen, yuk):
        # Önce siyah dış çerçeve (kalınlık: 3), sonra içine mavi su rengi
        pygame.draw.rect(pencere, SIYAH, (x, y, gen, yuk), 3)
        pygame.draw.rect(pencere, ACIK_MAVI, (x + 2, y + 2, gen - 4, yuk - 4))

    @staticmethod
    def vana_ciz(pencere, merkez, damla_hizi, aktif_mi=False):
        # Vana fareyle tutuluyorsa (aktifse) yeşil, yoksa gri çizilir
        renk = YESIL if aktif_mi else GRI 
        pygame.draw.circle(pencere, renk, merkez, 15) # İç dolgu
        pygame.draw.circle(pencere, SIYAH, merkez, 15, 2) # Dış siyah çizgi
        
        # Vana kolunun açısı hıza göre (0'dan 5'e) hesaplanır. Her hız seviyesi 18 derece döndürür.
        kol_aci = damla_hizi * 18
        kol_uz = 20
        # Trigonometri ile açıyı x ve y koordinatlarına çevirerek kolun uç noktasını buluyoruz
        bitis = (merkez[0] + kol_uz * math.cos(math.radians(kol_aci)),
                 merkez[1] - kol_uz * math.sin(math.radians(kol_aci)))
        pygame.draw.line(pencere, KIRMIZI, merkez, bitis, 3)

    @staticmethod
    def erlen_ciz(pencere, x, y, gen, yuk, sivi_oran, renk):
        pygame.draw.rect(pencere, SIYAH, (x, y, gen, yuk), 3) # Erlen dış çerçevesi
        
        max_sivi = yuk - 10 # Taşıp dışarı çıkmaması için küçük bir pay bırakıyoruz
        sivi_yuk = int(min(max_sivi, max_sivi * sivi_oran)) # Sıvının doluluk yüzdesi
        
        if sivi_yuk > 0:
            # Sıvıyı erlenin altından başlayıp yukarı doğru çizeriz
            pygame.draw.rect(pencere, renk, (x + 5, y + yuk - sivi_yuk - 5, gen - 10, sivi_yuk))


# ==========================================
# 4. ANA SİMÜLASYON YÖNETİCİSİ SINIFI
# ==========================================
class TitrasyonSimulasyonu:
    """Tüm projenin çalışmasını, olay döngüsünü ve ekran yenilemeyi yöneten ana sınıftır."""
    def __init__(self, Ca, Va_ml, Cb):
        pygame.init() # Pygame kütüphanesini başlat
        self.genislik, self.yukseklik = 900, 700
        self.pencere = pygame.display.set_mode((self.genislik, self.yukseklik))
        pygame.display.set_caption("Modüler Asit-Baz Titrasyon Simülasyonu")
        self.saat = pygame.time.Clock() # FPS (kare hızı) kontrolü için saat objesi
        
        # Yazı tipleri
        self.font = pygame.font.Font(None, 26)
        self.font_kucuk = pygame.font.Font(None, 20)

        # Kimya motorunu başlatıyoruz
        self.kimya = KimyaMotoru(Ca, Va_ml, Cb)
        
        # Başlangıç değişkenleri
        self.damla_hizi = 0
        self.damla_hacim = 0.1 # Her bir damlanın ml cinsi
        self.Vb_toplam = 0.0   # Erlende biriken toplam baz
        self.veri_listesi = [(0, self.kimya.ph_hesapla(0))] # Grafiğe çizilecek [Hacim, pH] noktaları
        
        self.calisiyor = True
        self.vana_surukleniyor = False # Fare ile vananın tutulup tutulmadığını takip eder

        # Ekranda çizilecek objelerin koordinatları ve boyutları
        self.buret_x, self.buret_y = 200, 150
        self.buret_gen, self.buret_yuk = 60, 300
        self.vana_merkez = (self.buret_x + self.buret_gen//2, self.buret_y + self.buret_yuk - 20)
        self.erlen_x, self.erlen_y = 500, 250
        self.erlen_gen, self.erlen_yuk = 150, 200

    def olaylari_isle(self):
        """Klavye tuş vuruşları ve fare tıklamaları/sürüklemelerini algılar."""
        for event in pygame.event.get():
            # Pencere kapatılma (X) tuşuna basıldıysa
            if event.type == pygame.QUIT:
                self.calisiyor = False
                
            # Tuş algılama: İndikatör Seçimi
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: self.kimya.secili_indikator = 1
                elif event.key == pygame.K_2: self.kimya.secili_indikator = 2
                elif event.key == pygame.K_3: self.kimya.secili_indikator = 3

            # Fare Tıklaması Başlangıcı
            elif event.type == pygame.MOUSEBUTTONDOWN:
                fare_x, fare_y = event.pos
                # İki nokta arası uzaklık formülü (hipotenüs) ile vananın içine tıklanıp tıklanmadığını buluyoruz
                mesafe = math.hypot(fare_x - self.vana_merkez[0], fare_y - self.vana_merkez[1])
                
                if mesafe <= 25: # Vanaya yeterince yakın tıklandıysa
                    self.vana_surukleniyor = True
                    # Geleneksel tıklama (Sol tık: 1, Sağ tık: 3)
                    if event.button == 1: self.damla_hizi = min(5, self.damla_hizi + 1)
                    elif event.button == 3: self.damla_hizi = max(0, self.damla_hizi - 1)
            
            # Fare tuşu bırakıldığında sürükleme iptal edilir
            elif event.type == pygame.MOUSEBUTTONUP:
                self.vana_surukleniyor = False

            # Fare Sürükleme (Motion) İle Vana Hızı Ayarlama (BONUS ÖZELLİK)
            elif event.type == pygame.MOUSEMOTION:
                if self.vana_surukleniyor:
                    # Fare vana merkezinden x ekseninde (sağa/sola) ne kadar uzaklaştı?
                    fark_x = event.pos[0] - self.vana_merkez[0]
                    # Koordinatlara göre hızı dinamik hesaplama
                    if fark_x < -30: 
                        self.damla_hizi = 0
                    elif fark_x > 30: 
                        self.damla_hizi = 5
                    else:
                        self.damla_hizi = int(((fark_x + 30) / 60) * 5)

    def mantik_guncelle(self):
        """Her bir döngüde (frame) kimyasal değerleri ve sıvı miktarını günceller."""
        for _ in range(self.damla_hizi): # Hız ne kadarsa o kadar damla (hacim) ekle
            self.Vb_toplam += self.damla_hacim
            
            # Aşırı taşmayı engellemek için maksimum hacim (Eşdeğerliğin 2 katı) limiti koyuyoruz
            if self.Vb_toplam > 2 * self.kimya.V_eq:
                self.Vb_toplam = 2 * self.kimya.V_eq
                break
                
            # Yeni eklenen hacimle yeni pH'ı hesaplayıp grafik listesine ekle
            yeni_pH = self.kimya.ph_hesapla(self.Vb_toplam)
            self.veri_listesi.append((self.Vb_toplam, yeni_pH))

    def grafik_ciz(self):
        """Pencerenin alt kısmına dinamik titrasyon (Hacim-pH) grafiği çizer."""
        x, y, gen, yuk = 50, 450, 800, 200 # Grafiğin konum ve boyutları
        if len(self.veri_listesi) < 2: return # En az 2 nokta yoksa çizim yapma

        pygame.draw.rect(self.pencere, BEYAZ, (x, y, gen, yuk)) # Grafik arka planı
        pygame.draw.rect(self.pencere, SIYAH, (x, y, gen, yuk), 2) # Grafik çerçevesi

        # Hacim skalasını dinamik ayarlamak için şu ana kadarki en büyük hacmi buluyoruz
        max_hacim = max([v for v, p in self.veri_listesi]) if self.veri_listesi else 1.0
        
        noktalar = []
        for hacim, pH in self.veri_listesi:
            # Hacmi x eksenine, pH değerini (0-14 arası) y eksenine oranlayarak piksellere dönüştürüyoruz
            gx = x + 10 + (hacim / max_hacim) * (gen - 20) if max_hacim > 0 else x + 10
            gy = y + yuk - 10 - (pH / 14.0) * (yuk - 20)
            noktalar.append((gx, gy))

        # Hesaplanan noktaları çizgiyle birleştir
        if len(noktalar) > 1:
            pygame.draw.lines(self.pencere, GRAFIK_RENK, False, noktalar, 2)

        # Teorik eşdeğerlik noktasını (pH=7) grafikte yeşil bir nokta olarak işaretle
        eq_x = x + 10 + (self.kimya.V_eq / max_hacim) * (gen - 20) if max_hacim > 0 else x + 10
        eq_y = y + yuk - 10 - (7.0 / 14.0) * (yuk - 20)
        pygame.draw.circle(self.pencere, YESIL, (int(eq_x), int(eq_y)), 4)

    def ekrani_ciz(self):
        """Tüm objeleri (Büret, Erlen, Yazılar, Grafik) ekrana basar."""
        self.pencere.fill(BEYAZ) # Önceki kareyi temizlemek için ekranı beyaza boya
        
        # Büret ve Vanayı çiz
        ArayuzBilesenleri.buret_ciz(self.pencere, self.buret_x, self.buret_y, self.buret_gen, self.buret_yuk)
        ArayuzBilesenleri.vana_ciz(self.pencere, self.vana_merkez, self.damla_hizi, self.vana_surukleniyor)

        # Damla animasyonu (Eğer musluk açıksa büretin altına inen mavi bir yuvarlak çizer)
        if self.damla_hizi > 0:
            pygame.draw.circle(self.pencere, ACIK_MAVI, 
                               (self.buret_x + self.buret_gen//2, self.buret_y + self.buret_yuk - 10 + (pygame.time.get_ticks() % 15)), 5)

        # Erlen ve içindeki sıvıyı çiz
        guncel_pH = self.kimya.ph_hesapla(self.Vb_toplam)
        renk = self.kimya.indikator_rengi(guncel_pH)
        sivi_oran = self.Vb_toplam / (2 * self.kimya.V_eq) if self.kimya.V_eq > 0 else 0
        ArayuzBilesenleri.erlen_ciz(self.pencere, self.erlen_x, self.erlen_y, self.erlen_gen, self.erlen_yuk, sivi_oran, renk)

        # Ekrana yazdırılacak bilgi metinlerini hazırla
        ind_isim = self.kimya.indikator_isimleri[self.kimya.secili_indikator]
        metinler = [
            f"Anlik pH = {guncel_pH:.2f}",
            f"Eklenen Baz = {self.Vb_toplam:.1f} mL",
            f"Damla Hizi = {self.damla_hizi}",
            f"Secili Indikator: {ind_isim}",
            " ",
            "--- KONTROLLER ---",
            "Vanayi Tut ve Saga/Sola Surukle",
            "veya Sol Tik (+) / Sag Tik (-)",
            "Indikator Degistir: Klavyeden 1, 2 veya 3"
        ]
        
        # Metinleri alt alta ekrana bas
        for i, metin in enumerate(metinler):
            yazi = self.font.render(metin, True, SIYAH)
            self.pencere.blit(yazi, (30, 30 + (i * 28)))

        self.grafik_ciz() # Alt taraftaki grafiği çağır
        pygame.display.flip() # Çizilen her şeyi ekranda (display) güncelle

    def calistir(self):
        """Simülasyonun sonsuz ana döngüsü."""
        while self.calisiyor:
            self.olaylari_isle()
            self.mantik_guncelle()
            self.ekrani_ciz()
            self.saat.tick(15) # Saniyede 15 kere çalıştır (FPS ayarı)
        
        pygame.quit() # Çıkış yapıldığında pygame'i güvenle kapat
        sys.exit()

# ==========================================
# 5. PROGRAMIN BAŞLANGIÇ NOKTASI (MAIN)
# ==========================================
if __name__ == "__main__":
    print("--- GELISMIS ASIT-BAZ TITRASYON SIMULASYONU ---")
    
    # Kullanıcıdan konsol üzerinden başlangıç parametrelerini alıyoruz
    try:
        Ca = float(input("Asit derisimini girin (M) [orn: 0.1]: "))
        Va = float(input("Asit hacmini girin (mL) [orn: 50]: "))
        Cb = float(input("Baz derisimini girin (M) [orn: 0.1]: "))
    except ValueError:
        # Yanlış değer girilirse çökmeyi önlemek için varsayılan değerleri ata
        print("Hatali giris! Varsayilan degerler ataniyor (Ca=0.1, Va=50, Cb=0.1).")
        Ca, Va, Cb = 0.1, 50.0, 0.1

    # Simülasyon objesini oluştur ve çalıştır
    simulasyon = TitrasyonSimulasyonu(Ca, Va, Cb)
    simulasyon.calistir()