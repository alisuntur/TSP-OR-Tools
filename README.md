# 🚚 Eco-Route: Çoklu Nokta Dağıtım Optimizasyonu (TSP)

Bu proje, İstanbul’daki bir depodan çıkan bir kargo kuryesinin gün içinde Türkiye’deki **9 farklı şehre** teslimat yapıp tekrar İstanbul’a döndüğü senaryoda, **en kısa (en düşük maliyetli) rotayı** bulmayı amaçlar.

Problem, bilgisayar biliminde **Gezgin Satıcı Problemi (Travelling Salesman Problem — TSP)** olarak bilinir ve **NP-Hard** sınıfındadır. Bu nedenle tüm olasılıkları tek tek denemek yerine, Google’ın geliştirdiği **OR-Tools** kütüphanesi ile akıllı sezgisel arama yöntemleri kullanılmıştır.

---

## 🎯 Proje Amacı

- İstanbul (depo) + 9 şehir için **en kısa turu** bulmak  
- Toplam mesafeye göre **yakıt tüketimi** ve **yakıt maliyeti** tahmini yapmak  
- Bulunan rotayı **Folium** ile interaktif harita üzerinde görselleştirmek  

---

## 🧩 Senaryo

Kurye sabah İstanbul’dan (Tuzla) çıkıyor ve şu şehirleri **tam 1 kez** ziyaret ediyor:

- Ankara  
- İzmir  
- Bursa  
- Antalya  
- Konya  
- Denizli  
- Eskişehir  
- Kayseri  
- Afyonkarahisar  

Ardından tekrar İstanbul’a dönüyor.

---

## 🛠️ Kullanılan Teknolojiler

- **Python 3**
- **Google OR-Tools** (TSP çözümü)
- **Folium** (harita görselleştirme)

---

## ⚙️ Çözüm Yaklaşımı

### 1) Mesafe Matrisi Oluşturma
Şehirler arası mesafeler **Haversine** formülü ile kuş uçuşu hesaplanır.

Gerçek hayatta karayolu daha uzun olduğu için proje içinde:
- `karayolu_mesafesi ≈ kus_ucusu_mesafe × 1.35`

katsayısı kullanılmıştır.

OR-Tools maliyetleri tam sayı ile daha stabil çalıştırdığı için:
- km → metre çevrilip `int()` olarak solver’a verilir.

---

### 2) OR-Tools ile TSP Çözümü
OR-Tools, başlangıç için hızlı bir rota üretir ve ardından Local Search ile sürekli iyileştirir.

Kullanılan yöntemler:
- **First Solution Strategy:** `PATH_CHEAPEST_ARC`
- **Local Search Metaheuristic:** `GUIDED_LOCAL_SEARCH`
- **Time Limit:** 10 saniye

---

### 3) Yakıt ve Maliyet Hesabı
Toplam mesafe üzerinden basit bir yakıt modeli kullanılmıştır:

- Yakıt tüketimi: **12 L / 100 km**
- Yakıt fiyatı: **43.50 ₺ / L**

Bu sayede toplam rota için:
- Tahmini yakıt (L)
- Tahmini maliyet (₺)

hesaplanır.

---

### 4) Harita Çıktısı
Sonuç rota, Folium ile interaktif bir harita üzerinde:
- Şehir marker’ları
- Rota çizgisi (polyline)
- Rota sırası paneli
- Özet metrikler (km, yakıt, ₺)

şeklinde gösterilir.

---

## 📌 Örnek Çıktı

Çalıştırma sonucunda örnek bir optimum rota şu şekilde olabilir:

```
İstanbul → Bursa → İzmir → Denizli → Antalya → Konya → Kayseri → Ankara → Afyonkarahisar → Eskişehir → İstanbul
```

Çıktılar:
- Toplam mesafe (km)
- Tahmini yakıt (L)
- Yakıt maliyeti (₺)
- Etap etap mesafe bilgisi
- Interaktif HTML harita

---

## 📂 Proje Dosyaları

- `tsp_kurye.py` → Ana Python dosyası (solver + hesaplar + harita üretimi)
- `kurye_rota_haritasi.html` → Oluşturulan interaktif harita çıktısı
- `requirements.txt` → Gerekli kütüphaneler

---

## ▶️ Kurulum

### 1) Ortam Oluşturma (Önerilir)
```bash
python -m venv venv
```

Windows:
```bash
venv\Scripts\activate
```

Mac/Linux:
```bash
source venv/bin/activate
```

---

### 2) Bağımlılıkları Kurma
```bash
pip install -r requirements.txt
```

---

## 🚀 Çalıştırma

```bash
python tsp_kurye.py
```

Çalıştırınca:
- Terminale rota ve metrikler yazdırılır
- Aynı klasöre `rota.html` dosyası üretilir

---

## 🗺️ Haritayı Açma

Çalıştırma sonrası oluşan dosyayı tarayıcıda açabilirsiniz:

- `kurye_rota_haritasi.html`

---

## 🔍 Notlar ve Geliştirme Fikirleri

Bu proje bir **MVP** niteliğindedir. Aşağıdaki geliştirmelerle daha “gerçek lojistik” seviyesine taşınabilir:

- **VRP (Vehicle Routing Problem):** Çoklu kurye
- **Kapasite kısıtı:** Araç kapasitesi / paket sayısı
- **Zaman penceresi:** Teslimat saat aralığı (VRPTW)
- **Gerçek yol mesafesi:** OSRM veya Google Directions API entegrasyonu
- **CO2 emisyonu tahmini:** Yakıt üzerinden karbon hesabı

---

## 👤 Proje Sahibi

Bu proje,Veri Madenciliği / Optimizasyon derslerinde öğrenilen kavramların gerçek bir lojistik problemine uygulanması amacıyla geliştirilmiştir.

---

## 📜 Lisans

Bu proje eğitim amaçlıdır. MIT lisansı ile açık kaynak olarak paylaşılmıştır.
