import pygame
import numpy as np
import sys
import matplotlib.pyplot as plt

# ==========================================
# YARDIMCI FONKSİYONLAR
# ==========================================
def normalize(v):
    """
    Bir vektörün yönünü değiştirmeden uzunluğunu 1 birim yapar (Birim Vektör).
    Çarpışma normalleri ve yön hesaplamalarında kullanılır.
    Ayrıca vektörün orijinal uzunluğunu (norm) da döndürür.
    """
    norm = np.linalg.norm(v)
    if norm == 0: 
       return v, 0 # Sıfıra bölme hatasını (ZeroDivisionError) engeller
    return v / norm, norm

# ==========================================
# 1. TEMEL DURUM VE FİZİKSEL CİSİM (BODY)
# ==========================================
class Body:
    def __init__(self, x, y, mass, radius, color=(200, 50, 50), is_static=False):
        """
        Her bir cisim için ödevde istenen temel durum değişkenlerini tanımlıyoruz[cite: 1].
        NumPy array (dizi) kullanmak, x ve y bileşenlerini tek satırda hesaplamamızı sağlar.
        """
        # Dinamik özellikler: Konum, Hız, İvme[cite: 1]
        self.position = np.array([x, y], dtype=float)
        self.velocity = np.array([0.0, 0.0], dtype=float)
        self.acceleration = np.array([0.0, 0.0], dtype=float)
        
        # Cisme o anki karede etki eden toplam kuvvet
        self.force = np.array([0.0, 0.0], dtype=float)
        
        # Fiziksel özellikler
        self.mass = mass
        self.radius = radius
        self.color = color
        self.is_static = is_static # Cisim sabit mi? (Örn: duvara çakılı bir nokta)
        
        # Restitüsyon (e): Çarpışma sonrası enerjinin ne kadarının korunacağı (1=Tam elastik, 0=Yapışır)[cite: 1]
        self.restitution = 0.8 
        
        # Ters Kütle (Inverse Mass) Mantığı:
        # Fizikte F = m*a formülünü a = F * (1/m) olarak kullanırız.
        # Eğer bir cisim statikse veya sonsuz kütleliyse (zemin gibi) 1/m = 0 kabul edilir[cite: 1].
        # Bu sayede ağır işlemler veya sonsuza bölme hataları yapmadan cismi "hareketsiz" kılarız.
        if self.is_static or self.mass == 0.0:
            self.inv_mass = 0.0
        else:
            self.inv_mass = 1.0 / self.mass

    def apply_force(self, force_vector):
        """
        Cisme kuvvet ekler (Örn: Yerçekimi). Statik cisimler kuvvetten etkilenmez.
        """
        if not self.is_static:
            self.force += force_vector

    def clear_forces(self):
        """
        Her zaman adımı (At) başında birikmiş kuvvetleri sıfırlarız ki sürekli üst üste binmesinler.
        """
        self.force = np.array([0.0, 0.0], dtype=float)

# ==========================================
# 2. MESAFE KISITI (DISTANCE CONSTRAINT)
# ==========================================
class DistanceConstraint:
    def __init__(self, body_a, body_b, length):
        """
        İki cismi görünmez bir çubukla (veya çok sert bir yayla) birbirine bağlar[cite: 1].
        """
        self.body_a = body_a
        self.body_b = body_b
        self.rest_length = length # Korunması gereken orijinal mesafe

    def solve(self):
        """
        Constraint Solver (Pozisyon Düzeltmesi)
        İki cisim arasındaki mevcut mesafeyi ölçer ve olması gereken mesafeyle kıyaslar.
        Eğer fark (hata) varsa, cisimleri kütleleriyle ters orantılı olarak çeker veya iter.
        """
        # Cisimler arası vektör ve anlık mesafe (current_length)
        delta = self.body_b.position - self.body_a.position
        normal, current_length = normalize(delta)
        
        if current_length == 0:
            return

        # İhlal (hata) miktarı: Anlık mesafe - Olması gereken mesafe
        error = current_length - self.rest_length
        total_inv_mass = self.body_a.inv_mass + self.body_b.inv_mass
        
        if total_inv_mass == 0:
            return # İkisi de statikse işlem yapma
        
        # Hata payını cisimlerin (1/m) değerlerine göre paylaştır.
        # Hafif olan daha çok itilir/çekilir, ağır olan daha az etkilenir.
        correction_scalar = error / total_inv_mass
        
        # Pozisyonları direkt olarak düzelt (Baumgarte stabilizasyonu benzeri doğrudan müdahale)[cite: 1]
        if not self.body_a.is_static:
            self.body_a.position += normal * correction_scalar * self.body_a.inv_mass
        if not self.body_b.is_static:
            self.body_b.position -= normal * correction_scalar * self.body_b.inv_mass

    def get_violation(self):
        """ 
        Analiz grafikleri için mesafe kısıtının o anki karede ne kadar ihlal edildiğini döndürür[cite: 1].
        """
        delta = self.body_b.position - self.body_a.position
        current_length = np.linalg.norm(delta)
        return abs(current_length - self.rest_length)

# ==========================================
# 3. FİZİK MOTORU DÜNYASI (WORLD)
# ==========================================
class PhysicsWorld:
    def __init__(self):
        self.bodies = []
        self.constraints = []
        
        # Yerçekimi vektörü (Y ekseninde aşağı doğru -9.81 m/s^2)[cite: 1]
        self.gravity = np.array([0.0, -9.81]) 
        
        # Zaman adımı (Delta t). Saniyede 60 kare (60 FPS) için 1/60 sabit zaman adımı[cite: 1]
        self.dt = 1.0 / 60.0 
        
        # Varsayılan integrasyon yöntemi
        self.method = "Verlet" 
        self.ground_y = 50.0 # Zeminin Y koordinatındaki yeri

    def add_body(self, body):
        self.bodies.append(body)

    def add_constraint(self, constraint):
        self.constraints.append(constraint)

    def step(self):
        """
        Fizik motorunun ana boru hattı (Pipeline)[cite: 1]. Her karede sırasıyla çalışır:
        1. Kuvvetler -> 2. İntegrasyon -> 3. Kısıtlar -> 4. Çarpışmalar
        """
        # 1. Kuvvetleri Uygula (F = m*g)[cite: 1]
        for body in self.bodies:
            body.clear_forces()
            body.apply_force(self.gravity * body.mass)

        # 2. Sayısal İntegrasyon (Diferansiyel denklemlerin zamana göre çözümü)[cite: 1]
        for body in self.bodies:
            if body.is_static: continue

            # Newton'un 2. Yasası: a = F / m (veya F * inv_mass)
            body.acceleration = body.force * body.inv_mass

            if self.method == "Euler":
                # Semi-Implicit Euler Yöntemi[cite: 1]
                # Önce hız güncellenir, sonra yeni hız kullanılarak konum güncellenir.
                # v_new = v_old + a * dt
                # x_new = x_old + v_new * dt
                body.velocity += body.acceleration * self.dt
                body.position += body.velocity * self.dt
                
            elif self.method == "Verlet":
                # Velocity Verlet Yöntemi[cite: 1]
                # Konum hem hız hem de ivme dikkate alınarak güncellenir (2. mertebeden doğruluk).
                # x_new = x_old + v * dt + 0.5 * a * dt^2
                body.position += body.velocity * self.dt + 0.5 * body.acceleration * (self.dt ** 2)
                
                # Kuvvetlerimiz (yerçekimi) sabit olduğu için basit hız güncellemesi yeterlidir.
                body.velocity += body.acceleration * self.dt

        # 3. Kısıtları Çöz (Constraint Solver)[cite: 1]
        # Kısıtlar birbirini etkileyebileceği için iteratif (döngüsel) çözülür (örn: PGS yaklaşımı).
        # İterasyon sayısı arttıkça kısıtlar daha "sert" (stiff) davranır[cite: 1].
        iterations = 3
        for _ in range(iterations):
            for constraint in self.constraints:
                constraint.solve()

        # 4. Çarpışma Tespiti ve Tepkisi[cite: 1]
        self.solve_collisions()

    def solve_collisions(self):
        """
        Narrow-phase (Dar Aşama) Çarpışma tespiti ve Impuls tabanlı tepki[cite: 1].
        """
        # A. Zemin Çarpışması[cite: 1]
        for body in self.bodies:
            # Cismin alt kısmı zeminin altındaysa (y - r < zemin_y)
            if body.position[1] - body.radius < self.ground_y:
                
                # Sinking (Batma) Etkisini Çözme: Cismi doğrudan zeminin üstüne taşı
                body.position[1] = self.ground_y + body.radius
                
                # Sekme (Restitution): Hızın Y bileşeni zemin yönündeyse tersine çevir ve e ile çarp[cite: 1]
                if body.velocity[1] < 0:
                    body.velocity[1] = -body.velocity[1] * body.restitution

        # B. Daire-Daire Çarpışması[cite: 1]
        for i in range(len(self.bodies)):
            for j in range(i + 1, len(self.bodies)):
                b1, b2 = self.bodies[i], self.bodies[j]
                
                # Merkezler arası mesafe vektörü ve uzunluğu
                delta = b2.position - b1.position
                normal, dist = normalize(delta)
                min_dist = b1.radius + b2.radius

                # Penetrasyon (İç içe geçme) var mı?[cite: 1]
                if dist < min_dist:
                    depth = min_dist - dist # Ne kadar iç içe geçmişler?
                    total_inv = b1.inv_mass + b2.inv_mass
                    if total_inv == 0: continue

                    # 1. Pozisyon Düzeltmesi (Penetrasyonu giderme)[cite: 1]
                    # Cisimleri kütlelerine ters orantılı olarak normal yönünde dışarı iteriz.
                    correction = depth / total_inv
                    if not b1.is_static: b1.position -= normal * correction * b1.inv_mass
                    if not b2.is_static: b2.position += normal * correction * b2.inv_mass

                    # 2. İmpuls (Ani Hız Değişimi) Tepkisi[cite: 1]
                    # Bağıl hız (relative velocity) hesaplanır.
                    rel_vel = b2.velocity - b1.velocity
                    
                    # Bağıl hızın çarpışma normali yönündeki iz düşümü
                    vel_along_normal = np.dot(rel_vel, normal)

                    # Eğer cisimler zaten birbirinden uzaklaşıyorsa impuls uygulama (yapışmayı önler)
                    if vel_along_normal > 0:
                        continue

                    # İki cismin sekme katsayısından küçük olanı seçilir.
                    e = min(b1.restitution, b2.restitution)
                    
                    # Ödev dokümanındaki Impulse büyüklüğü (j) formülü:[cite: 1]
                    # j = -(1 + e) * (Vrel . N) / (1/m1 + 1/m2)
                    j = -(1 + e) * vel_along_normal / total_inv
                    
                    # Normal vektörü ile j'yi çarparak impuls vektörünü elde ederiz
                    impulse = j * normal

                    # İmpulsu uygulayarak hızları güncelle (J = Delta_P = m*Delta_v -> Delta_v = J/m)[cite: 1]
                    if not b1.is_static: b1.velocity -= impulse * b1.inv_mass
                    if not b2.is_static: b2.velocity += impulse * b2.inv_mass

    def get_total_energy(self):
        """
        Analiz için sistemin toplam mekanik enerjisini hesaplar[cite: 1].
        Enerji = Kinetik Enerji (0.5 * m * v^2) + Potansiyel Enerji (m * g * h)
        """
        total_energy = 0.0
        for body in self.bodies:
            if not body.is_static:
                # np.dot(v, v) işlemi v^2 'yi yani hızın karesini verir.
                speed_sq = np.dot(body.velocity, body.velocity)
                kinetic = 0.5 * body.mass * speed_sq
                
                # h yüksekliğini zemine göre hesaplıyoruz.
                potential = body.mass * 9.81 * (body.position[1] - self.ground_y)
                
                total_energy += (kinetic + potential)
        return total_energy

# ==========================================
# 4. GRAFİK RAPORLAMA FONKSİYONU
# ==========================================
def plot_results(time_data, energy_data, violation_data, method_name):
    """
    Simülasyon bitiminde toplanan verileri matplotlib ile grafiğe dönüştürür.
    Raporlamadaki analiz ihtiyacını (Enerji Drifti ve Constraint Violation) karşılar[cite: 1].
    """
    plt.figure(figsize=(12, 5))

    # 1. Grafik: Toplam Enerjinin Zamanla Değişimi (Enerji Drifti Analizi)[cite: 1]
    plt.subplot(1, 2, 1)
    plt.plot(time_data, energy_data, color='blue', label=f'Toplam Enerji ({method_name})')
    plt.title("Zaman - Toplam Enerji Grafiği")
    plt.xlabel("Zaman (s)")
    plt.ylabel("Enerji (Joule)")
    plt.grid(True)
    plt.legend()

    # 2. Grafik: Mesafe Kısıtı Hata Miktarı (Constraint Violation)[cite: 1]
    plt.subplot(1, 2, 2)
    plt.plot(time_data, violation_data, color='red', label='Mesafe Kısıtı Hatası')
    plt.title("Zaman - Constraint Violation Grafiği")
    plt.xlabel("Zaman (s)")
    plt.ylabel("Hata (Mesafe Farkı)")
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.savefig("simulasyon_analiz_raporu.png") # Çıktıyı raporun için klasöre kaydeder[cite: 1]
    plt.show() # Grafiği kullanıcıya gösterir

# ==========================================
# 5. GÖRSELLEŞTİRME VE ANA DÖNGÜ (PYGAME)
# ==========================================
def main():
    # Pygame pencere ve temel ayarları
    pygame.init()
    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("2D Fizik Motoru Vize Ödevi")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 18)

    world = PhysicsWorld()

    # --- Sahne Kurulumu ---
    # Serbest Düşen Cisim
    b1 = Body(400, 500, mass=5.0, radius=20, color=(50, 150, 250))
    world.add_body(b1)

    # Sarkaç (Pendulum) Sistemi[cite: 1]
    # Anchor (çivi) statik bir cisimdir, pendulum ise hareketlidir.
    anchor = Body(200, 400, mass=0.0, radius=10, color=(100, 100, 100), is_static=True)
    pendulum = Body(300, 400, mass=2.0, radius=15, color=(250, 150, 50))
    dist_constraint = DistanceConstraint(anchor, pendulum, 150)
    
    world.add_body(anchor)
    world.add_body(pendulum)
    world.add_constraint(dist_constraint)

    def to_screen(pos):
        """
        Matematiksel Koordinat Çevirici:
        Bilgisayar ekranlarında orijin (0,0) sol üsttedir ve Y ekseni aşağı doğru artar.
        Fizikte ise Y ekseni yukarı doğru artar. Fizik hesaplarımızın doğruluğunu bozmamak için
        çizim yaparken Y koordinatını ekran yüksekliğinden çıkararak ters çeviriyoruz.
        """
        return (int(pos[0]), int(HEIGHT - pos[1]))

    running = True
    initial_energy = world.get_total_energy() # Başlangıç enerjisi (Drift hesabı için)
    
    # --- Raporlama İçin Veri Toplama Listeleri ---
    sim_time = 0.0
    time_history = []
    energy_history = []
    violation_history = []

    # OYUN DÖNGÜSÜ
    while running:
        screen.fill((30, 30, 30)) # Arka planı koyu gri yap
        
        # Etkileşim: Klavye ve Mouse Olayları[cite: 1]
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # Klavyeden tuşa basılarak Entegrasyon Yöntemi Değiştirilebilir
                if event.key == pygame.K_e:
                    world.method = "Euler"
                    initial_energy = world.get_total_energy() # Enerji referansını sıfırla
                elif event.key == pygame.K_v:
                    world.method = "Verlet"
                    initial_energy = world.get_total_energy()

        # 1. Fiziği bir zaman adımı (dt) kadar ilerlet
        world.step()
        sim_time += world.dt

        # 2. Analiz grafikleri için o anki durumu kaydet
        time_history.append(sim_time)
        energy_history.append(world.get_total_energy())
        violation_history.append(dist_constraint.get_violation())

        # 3. ÇİZİM İŞLEMLERİ
        # Zemini çiz
        pygame.draw.line(screen, (100, 200, 100), (0, HEIGHT - world.ground_y), (WIDTH, HEIGHT - world.ground_y), 4)

        # Kısıtları (Beyaz çizgiler) çiz
        for constraint in world.constraints:
            p1 = to_screen(constraint.body_a.position)
            p2 = to_screen(constraint.body_b.position)
            pygame.draw.line(screen, (255, 255, 255), p1, p2, 2)

        # Cisimleri (Daireler) ve Hız Vektörlerini çiz
        for body in world.bodies:
            # Cisim çizimi
            pygame.draw.circle(screen, body.color, to_screen(body.position), body.radius)
            
            # Gelişmiş Görselleştirme (Bonus): Hız Vektörü Çizimi[cite: 1]
            if not body.is_static and np.linalg.norm(body.velocity) > 0.1:
                # Hız okunun ucunu hesapla (Çok uzun olmasın diye 0.2 ile ölçeklendirdik)
                vel_end_pos = body.position + body.velocity * 0.2 
                start_p = to_screen(body.position)
                end_p = to_screen(vel_end_pos)
                pygame.draw.line(screen, (0, 255, 0), start_p, end_p, 2) # Yeşil renkli hız çizgisi

        # 4. ARAYÜZ (UI) BİLGİ METİNLERİ
        current_energy = world.get_total_energy()
        
        # Enerji Drift Formülü: |Şu anki Enerji - Başlangıç| / |Başlangıç| * 100[cite: 1]
        if initial_energy != 0:
            energy_drift = abs(current_energy - initial_energy) / abs(initial_energy) * 100 
        else:
            energy_drift = 0.0

        # Ekrana yazdırılacak metinler
        info_texts = [
            f"Metot: {world.method} ('E' veya 'V' ile degistir)",
            f"Toplam Enerji: {current_energy:.2f} J",
            f"Enerji Drift (Hata payi): %{energy_drift:.4f}",
            "Simulasyonu kapatinca (X), Rapor Grafikleri cizilecektir."
        ]

        # Metinleri sol üste sırayla alt alta çizdir
        for i, text in enumerate(info_texts):
            surf = font.render(text, True, (200, 200, 200))
            screen.blit(surf, (10, 10 + i * 25))

        pygame.display.flip() # Çizimleri ekrana yansıt
        clock.tick(60) # Döngüyü saniyede 60 kare olacak şekilde sınırla

    pygame.quit() # Pygame penceresini kapat
    
    # 5. SİMÜLASYON BİTTİĞİNDE GRAFİKLERİ ÇİZ (Rapor İçin)[cite: 1]
    print("Simülasyon bitti. Analiz grafikleri hazırlanıyor...")
    plot_results(time_history, energy_history, violation_history, world.method)
    
    sys.exit()

if __name__ == "__main__":
    main()