import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import os

class GrafikSinifMotoru:
    def __init__(self, en, boy, yukseklik, resim_yolu):
        self.en = en
        self.boy = boy
        self.yukseklik = yukseklik
        self.resim_yolu = resim_yolu # Fotoğrafın dosya yolu eklendi
        
        self.blok_sayisi = 3
        self.blok_basi_sira = 8
        self.sira_basi_kapasite = 3

    def geometrik_hesaplama(self):
        hacim = self.en * self.boy * self.yukseklik
        yuzey_alani = 2 * (self.en * self.boy + self.en * self.yukseklik + self.boy * self.yukseklik)
        kapasite = self.blok_sayisi * self.blok_basi_sira * self.sira_basi_kapasite
        return hacim, yuzey_alani, kapasite

    def gorsellestir_yan_yana(self):
        """
        Sol tarafta orijinal fotoğrafı, sağ tarafta 3D modeli gösterir.
        """
        hacim, alan, kapasite = self.geometrik_hesaplama()
        
        # 1x2'lik bir grid (yan yana iki panel) oluşturuyoruz
        fig = plt.figure(figsize=(15, 6))

        # --- SOL PANEL: ORİJİNAL FOTOĞRAF ---
        ax1 = fig.add_subplot(1, 2, 1) # 1 satır, 2 sütun, 1. panel
        
        # Dosyanın var olup olmadığını kontrol et
        if os.path.exists(self.resim_yolu):
            img = mpimg.imread(self.resim_yolu)
            ax1.imshow(img)
            ax1.set_title("Referans Görüntü\n(Senin Yüklediğin Fotoğraf)")
            ax1.axis('off') # Eksen çizgilerini kapat
        else:
            ax1.text(0.5, 0.5, "Fotoğraf Bulunamadı!\nDosya adını kontrol edin.", 
                     horizontalalignment='center', verticalalignment='center')
            ax1.axis('off')

        # --- SAĞ PANEL: 3D GRAFİK MODELİ ---
        ax2 = fig.add_subplot(1, 2, 2, projection='3d') # 1 satır, 2 sütun, 2. panel
        
        x_corners = [0, self.en, self.en, 0, 0]
        y_corners = [0, 0, self.boy, self.boy, 0]
        
        ax2.plot(x_corners, y_corners, 0, color='blue', linewidth=2)
        ax2.plot(x_corners, y_corners, self.yukseklik, color='blue', linewidth=2, linestyle='--')
        
        for i in range(4):
            ax2.plot([x_corners[i], x_corners[i]], [y_corners[i], y_corners[i]], 
                    [0, self.yukseklik], color='black', alpha=0.3)

        xs = np.random.uniform(0.5, self.en - 0.5, kapasite)
        ys = np.random.uniform(0.5, self.boy - 0.5, kapasite)
        zs = np.zeros(kapasite) + 0.5 

        ax2.scatter(xs, ys, zs, c='orange', marker='o', s=30, label=f'Kapasite ({kapasite} Öğrenci)')

        ax2.set_xlabel('Genişlik (X - Metre)')
        ax2.set_ylabel('Derinlik (Y - Metre)')
        ax2.set_zlabel('Yükseklik (Z - Metre)')
        ax2.set_title(f'3D Sınıf Projeksiyonu\nHacim: {hacim}m3 | Alan: {alan}m2')
        ax2.legend()
        
        plt.tight_layout()
        print("[!] Görselleştirme paneli açılıyor...")
        plt.show()

# --- ANA UYGULAMA ---
if __name__ == "__main__":
    # DİKKAT: Python dosyan ile fotoğrafın aynı klasörde olması gerekir!
    dosya_adi = "WhatsApp Image 2026-04-27 at 9.45.15 AM (1).jpeg"
    
    derslik_motoru = GrafikSinifMotoru(en=7.0, boy=10.0, yukseklik=3.2, resim_yolu=dosya_adi)
    
    h, a, k = derslik_motoru.geometrik_hesaplama()
    print(f"Hesaplanan Kapasite: {k} Kişi | Hacim: {h:.2f} m3")
    
    derslik_motoru.gorsellestir_yan_yana()