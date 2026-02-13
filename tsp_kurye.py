"""
Kurye Rota Optimizasyonu - Gezgin Satıcı Problemi (TSP)
========================================================
Senaryo: Bir kargo/lojistik firmasının İstanbul'daki merkez deposundan
çıkarak Türkiye genelinde 9 farklı şehirdeki dağıtım adreslerine
uğraması ve depoya geri dönmesi gerekiyor.

Amaç: En kısa ve en az yakıt harcayan iller arası rotayı bulmak.

Tech Stack:
- Python
- Google OR-Tools (TSP çözücü)
- Folium (Harita görselleştirme)
- Gerçek Türkiye şehir koordinatları
"""

import math
import folium
from ortools.constraint_solver import routing_enums_pb2, pywrapcp


# ============================================================
# 1. GERÇEK VERİ — Türkiye şehirleri, depo ve dağıtım noktaları
# ============================================================

# Gerçek GPS koordinatları (enlem, boylam) ve adres bilgileri
NOKTALAR = [
    {
        "ad": "Merkez Depo",
        "sehir": "İstanbul",
        "adres": "Tuzla Organize Sanayi Bölgesi, Lojistik Merkezi",
        "koordinat": (40.8190, 29.3005),
        "tip": "depo",
    },
    {
        "ad": "Ankara Dağıtım Merkezi",
        "sehir": "Ankara",
        "adres": "Ostim OSB, 100. Yıl Bulvarı No:52",
        "koordinat": (39.9708, 32.6227),
        "tip": "dagitim",
    },
    {
        "ad": "İzmir Şubesi",
        "sehir": "İzmir",
        "adres": "Alsancak, Kıbrıs Şehitleri Cad. No:118",
        "koordinat": (38.4362, 27.1428),
        "tip": "dagitim",
    },
    {
        "ad": "Bursa Teslim Noktası",
        "sehir": "Bursa",
        "adres": "Nilüfer, DOSAB Organize Sanayi",
        "koordinat": (40.2225, 28.8640),
        "tip": "dagitim",
    },
    {
        "ad": "Antalya Mağaza",
        "sehir": "Antalya",
        "adres": "Konyaaltı, Liman Cad. No:45",
        "koordinat": (36.8841, 30.6927),
        "tip": "dagitim",
    },
    {
        "ad": "Konya Deposu",
        "sehir": "Konya",
        "adres": "Selçuklu, Büsan Organize Sanayi No:78",
        "koordinat": (37.8746, 32.4932),
        "tip": "dagitim",
    },
    {
        "ad": "Denizli Müşterisi",
        "sehir": "Denizli",
        "adres": "Merkezefendi, Organize Sanayi Bölgesi No:14",
        "koordinat": (37.7765, 29.0864),
        "tip": "dagitim",
    },
    {
        "ad": "Eskişehir Teslimat",
        "sehir": "Eskişehir",
        "adres": "Tepebaşı, Organize Sanayi Bölgesi 11. Cad.",
        "koordinat": (39.7668, 30.5256),
        "tip": "dagitim",
    },
    {
        "ad": "Kayseri Dağıtım",
        "sehir": "Kayseri",
        "adres": "Melikgazi, Kayseri OSB 3. Cadde No:22",
        "koordinat": (38.7205, 35.4826),
        "tip": "dagitim",
    },
    {
        "ad": "Afyon Aktarma Noktası",
        "sehir": "Afyonkarahisar",
        "adres": "Merkez, Afyon-Kütahya Karayolu 5. km",
        "koordinat": (38.7507, 30.5387),
        "tip": "dagitim",
    },
]

NOKTA_ADLARI = [n["ad"] for n in NOKTALAR]
KOORDINATLAR = [n["koordinat"] for n in NOKTALAR]


# ============================================================
# 2. MESAFELERİ HESAPLA — Haversine formülü (km)
# ============================================================

def haversine(coord1: tuple, coord2: tuple) -> float:
    """İki GPS koordinatı arasındaki kuş uçuşu mesafeyi km cinsinden hesaplar."""
    R = 6371  # Dünya yarıçapı (km)
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    return R * c


def karayolu_mesafesi(kus_ucusu_km: float) -> float:
    """
    Kuş uçuşu mesafeyi gerçekçi karayolu mesafesine dönüştürür.
    Türkiye karayolları için ortalama düzeltme katsayısı: 1.35
    (dağlık ve kıvrımlı yollar göz önüne alınarak)
    """
    return kus_ucusu_km * 1.35


def mesafe_matrisi_olustur(koordinatlar: list) -> list[list[int]]:
    """
    Tüm noktalar arasındaki tahmini karayolu mesafe matrisini oluşturur.
    OR-Tools tam sayı beklediği için mesafeler metre cinsine çevrilir.
    """
    n = len(koordinatlar)
    matris = []
    for i in range(n):
        satir = []
        for j in range(n):
            if i == j:
                satir.append(0)
            else:
                kus_ucusu = haversine(koordinatlar[i], koordinatlar[j])
                karayolu = karayolu_mesafesi(kus_ucusu)
                satir.append(int(karayolu * 1000))  # metre cinsinden
        matris.append(satir)
    return matris


# ============================================================
# 3. TSP ÇÖZÜCÜ — Google OR-Tools
# ============================================================

def tsp_coz(mesafe_matrisi: list[list[int]]) -> tuple[list[int], int]:
    """
    Google OR-Tools ile TSP'yi çözer.
    Returns:
        rota: Sıralı indeks listesi (depoya dönüş dahil)
        toplam_mesafe: Toplam mesafe (metre)
    """
    n = len(mesafe_matrisi)

    # Veri modeli: n nokta, 1 araç, depo indeksi = 0
    manager = pywrapcp.RoutingIndexManager(n, 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    # Mesafe callback
    def mesafe_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return mesafe_matrisi[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(mesafe_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Arama parametreleri — Guided Local Search metaheuristic
    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_params.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_params.time_limit.FromSeconds(10)  # 10 saniyelik arama

    # Çöz
    solution = routing.SolveWithParameters(search_params)

    if not solution:
        raise RuntimeError("TSP çözümü bulunamadı!")

    # Rotayı oku
    rota = []
    index = routing.Start(0)
    while not routing.IsEnd(index):
        rota.append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))
    rota.append(manager.IndexToNode(index))  # Depoya geri dönüş

    toplam_mesafe = solution.ObjectiveValue()
    return rota, toplam_mesafe


# ============================================================
# 4. SONUÇLARI YAZDIRMA
# ============================================================

def sonuclari_yazdir(rota: list[int], toplam_mesafe_m: int, mesafe_matrisi: list[list[int]]):
    """Optimum rotayı detaylı şekilde konsola yazdırır."""
    toplam_km = toplam_mesafe_m / 1000
    yakit_lt_100km = 12  # Ticari araç yakıt tüketimi (lt/100 km)
    yakit_fiyat_tl = 43.50  # ₺/lt (güncel ortalama motorin)

    toplam_yakit = toplam_km * yakit_lt_100km / 100
    toplam_maliyet = toplam_yakit * yakit_fiyat_tl

    print()
    print("╔" + "═" * 62 + "╗")
    print("║   🚛  KURYE ROTA OPTİMİZASYONU — Türkiye İller Arası       ║")
    print("╠" + "═" * 62 + "╣")
    print(f"║   📍 Toplam nokta sayısı  : {len(NOKTALAR):>3} (1 depo + {len(NOKTALAR)-1} dağıtım)    ║")
    print(f"║   📏 Toplam rota mesafesi : {toplam_km:>8.1f} km                    ║")
    print(f"║   ⛽ Tahmini yakıt        : {toplam_yakit:>8.1f} lt                    ║")
    print(f"║   💰 Tahmini yakıt maliyeti: {toplam_maliyet:>7.0f} ₺                     ║")
    print(f"║      ({yakit_lt_100km} lt/100km, motorin {yakit_fiyat_tl}₺/lt)            ║")
    print("╚" + "═" * 62 + "╝")
    print()
    print("   ╔══════════════════════════════════════════════════════╗")
    print("   ║              OPTİMUM ROTA SIRASI                    ║")
    print("   ╠══════════════════════════════════════════════════════╣")

    for sira, nokta_idx in enumerate(rota):
        nokta = NOKTALAR[nokta_idx]
        tip_ikon = "🏭" if nokta["tip"] == "depo" else "📦"

        print(f"   ║  {sira + 1:2d}. {tip_ikon} {nokta['ad']:<36s}   ║")
        print(f"   ║      📍 {nokta['sehir']:<20s}                     ║")
        print(f"   ║      🏠 {nokta['adres'][:42]:<42s} ║")

        if sira < len(rota) - 1:
            sonraki = rota[sira + 1]
            etap_mesafe = mesafe_matrisi[nokta_idx][sonraki] / 1000
            print(f"   ║      ↓  {etap_mesafe:>6.1f} km                                ║")
            print(f"   ║{'─' * 54}║")

    print("   ╚══════════════════════════════════════════════════════╝")
    print()


# ============================================================
# 5. HARİTA GÖRSELLEŞTİRME — Folium
# ============================================================

def harita_olustur(rota: list[int], toplam_mesafe_m: int, mesafe_matrisi: list[list[int]],
                   dosya_adi: str = "kurye_rota_haritasi.html"):
    """Optimum rotayı Türkiye haritası üzerinde interaktif olarak görselleştirir."""

    # Harita merkezi — Türkiye ortası civarı
    merkez_lat = sum(k[0] for k in KOORDINATLAR) / len(KOORDINATLAR)
    merkez_lng = sum(k[1] for k in KOORDINATLAR) / len(KOORDINATLAR)

    harita = folium.Map(
        location=[merkez_lat, merkez_lng],
        zoom_start=6,
        tiles=None,
    )

    # Birden fazla harita katmanı
    folium.TileLayer("OpenStreetMap", name="Sokak Haritası").add_to(harita)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Uydu Görüntüsü",
    ).add_to(harita)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB", name="Koyu Tema",
    ).add_to(harita)

    # Katman kontrolü
    folium.LayerControl(position="topright").add_to(harita)

    # ── Başlık paneli ──
    toplam_km = toplam_mesafe_m / 1000
    yakit = toplam_km * 12 / 100
    maliyet = yakit * 43.50

    baslik_html = f"""
    <div style="
        position: fixed; top: 10px; left: 50%; transform: translateX(-50%);
        z-index: 9999;
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        padding: 18px 35px; border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.5);
        color: white; font-family: 'Segoe UI', system-ui, sans-serif;
        text-align: center; border: 1px solid rgba(255,255,255,0.1);
    ">
        <div style="font-size: 20px; font-weight: 700; letter-spacing: 0.5px;">
            🚛 Kurye Rota Optimizasyonu — Türkiye
        </div>
        <div style="font-size: 13px; margin-top: 8px; opacity: 0.85; display: flex; gap: 15px; justify-content: center;">
            <span>📍 {len(NOKTALAR)} nokta</span>
            <span>📏 {toplam_km:.0f} km</span>
            <span>⛽ ~{yakit:.0f} lt</span>
            <span>💰 ~{maliyet:,.0f} ₺</span>
        </div>
        <div style="font-size: 11px; margin-top: 4px; opacity: 0.6;">
            Gezgin Satıcı Problemi (TSP) — Google OR-Tools ile çözüldü
        </div>
    </div>
    """
    harita.get_root().html.add_child(folium.Element(baslik_html))

    # ── Rota bilgi paneli (sol alt) ──
    rota_satirlari = ""
    for sira, idx in enumerate(rota):
        nokta = NOKTALAR[idx]
        renk = "#FFD700" if nokta["tip"] == "depo" else "#00E5FF"
        ikon = "🏭" if nokta["tip"] == "depo" else "📦"

        mesafe_str = ""
        if sira < len(rota) - 1:
            sonraki = rota[sira + 1]
            etap_km = mesafe_matrisi[idx][sonraki] / 1000
            mesafe_str = f"<span style='color:#aaa; font-size:10px;'> → {etap_km:.0f} km</span>"

        rota_satirlari += f"""
        <div style="margin: 4px 0; display: flex; align-items: center; gap: 6px;">
            <span style="
                background: {renk}; color: #000; font-weight: 700;
                width: 20px; height: 20px; border-radius: 50%;
                display: inline-flex; align-items: center; justify-content: center;
                font-size: 10px; flex-shrink: 0;
            ">{sira+1}</span>
            <span>{ikon} {nokta['sehir']}{mesafe_str}</span>
        </div>
        """

    bilgi_html = f"""
    <div style="
        position: fixed; bottom: 20px; left: 20px; z-index: 9999;
        background: rgba(15, 12, 41, 0.94); padding: 16px 20px;
        border-radius: 14px; color: white; font-size: 12px;
        font-family: 'Segoe UI', system-ui, sans-serif;
        box-shadow: 0 8px 32px rgba(0,0,0,0.5);
        max-height: 380px; overflow-y: auto;
        border: 1px solid rgba(255,255,255,0.08);
        backdrop-filter: blur(10px);
    ">
        <div style="font-size: 14px; font-weight: 700; margin-bottom: 10px; color: #FFD700;">
            📋 Optimum Rota Sırası
        </div>
        {rota_satirlari}
    </div>
    """
    harita.get_root().html.add_child(folium.Element(bilgi_html))

    # ── Noktaları işaretle ──
    for i, nokta in enumerate(NOKTALAR):
        lat, lng = nokta["koordinat"]
        is_depo = nokta["tip"] == "depo"

        # Rota sırasını bul
        rota_sirasi = rota.index(i) + 1 if i in rota else "—"

        popup_html = f"""
        <div style="font-family: 'Segoe UI', system-ui; min-width: 220px; padding: 5px;">
            <div style="font-weight: 700; font-size: 15px; color: #1a1a2e;">
                {'🏭' if is_depo else '📦'} {nokta['ad']}
            </div>
            <hr style="margin: 6px 0; border-color: #e0e0e0;">
            <div style="font-size: 12px; color: #555; line-height: 1.6;">
                🏙️ <b>Şehir:</b> {nokta['sehir']}<br>
                🏠 <b>Adres:</b> {nokta['adres']}<br>
                📍 <b>Koordinat:</b> {lat:.4f}°N, {lng:.4f}°E<br>
                🔢 <b>Rota sırası:</b> <span style="color:#e74c3c; font-weight:700;">{rota_sirasi}</span><br>
                🏷️ <b>Tip:</b> {"Merkez Depo" if is_depo else "Dağıtım Noktası"}
            </div>
        </div>
        """

        # Ana marker
        folium.Marker(
            location=[lat, lng],
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{rota_sirasi}. {nokta['sehir']} — {nokta['ad']}",
            icon=folium.Icon(
                color="red" if is_depo else "blue",
                icon="industry" if is_depo else "cube",
                prefix="fa",
            ),
        ).add_to(harita)

        # Sıra numarası etiketi
        etiket_renk = "#FF4444" if is_depo else "#00B4D8"
        folium.Marker(
            location=[lat, lng],
            icon=folium.DivIcon(
                html=f"""
                <div style="
                    background: {etiket_renk}; color: white; font-weight: 800;
                    width: 26px; height: 26px; border-radius: 50%;
                    display: flex; align-items: center; justify-content: center;
                    font-size: 12px; border: 2px solid white;
                    box-shadow: 0 3px 10px rgba(0,0,0,0.4);
                    transform: translate(-13px, -35px);
                    font-family: 'Segoe UI', system-ui, sans-serif;
                ">{rota_sirasi}</div>
                """,
                icon_size=(26, 26),
                icon_anchor=(0, 0),
            ),
        ).add_to(harita)

    # ── Optimum rota çizgisi ──
    rota_koordinatlari = [KOORDINATLAR[i] for i in rota]

    # Gölge çizgisi
    folium.PolyLine(
        locations=rota_koordinatlari,
        weight=10,
        color="#0f0c29",
        opacity=0.3,
    ).add_to(harita)

    # Her segment için farklı renkte çizgi
    segment_renkleri = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4",
        "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F",
        "#BB8FCE", "#85C1E9", "#FF6B6B",
    ]

    for seg_idx in range(len(rota) - 1):
        baslangic = KOORDINATLAR[rota[seg_idx]]
        bitis = KOORDINATLAR[rota[seg_idx + 1]]
        renk = segment_renkleri[seg_idx % len(segment_renkleri)]
        etap_km = mesafe_matrisi[rota[seg_idx]][rota[seg_idx + 1]] / 1000

        # Rota çizgisi
        folium.PolyLine(
            locations=[baslangic, bitis],
            weight=4,
            color=renk,
            opacity=0.85,
            dash_array="12 6",
            tooltip=f"{NOKTALAR[rota[seg_idx]]['sehir']} → {NOKTALAR[rota[seg_idx+1]]['sehir']}: {etap_km:.0f} km",
        ).add_to(harita)

        # Segment ortasına mesafe etiketi
        orta_lat = (baslangic[0] + bitis[0]) / 2
        orta_lng = (baslangic[1] + bitis[1]) / 2

        folium.Marker(
            location=[orta_lat, orta_lng],
            icon=folium.DivIcon(
                html=f"""
                <div style="
                    background: rgba(15,12,41,0.88); color: {renk};
                    padding: 3px 8px; border-radius: 10px;
                    font-size: 11px; font-weight: 700;
                    font-family: 'Segoe UI', system-ui, sans-serif;
                    white-space: nowrap; transform: translate(-25px, -12px);
                    box-shadow: 0 2px 8px rgba(0,0,0,0.4);
                    border: 1px solid {renk}40;
                ">{etap_km:.0f} km</div>
                """,
                icon_size=(70, 24),
                icon_anchor=(0, 0),
            ),
        ).add_to(harita)

    # ── Kaydet ──
    harita.save(dosya_adi)
    print(f"   🗺️  Harita kaydedildi: {dosya_adi}")
    print(f"   📂 Tarayıcıda açarak interaktif rotayı inceleyebilirsiniz.\n")


# ============================================================
# 6. MESAFE MATRİSİ TABLOSU
# ============================================================

def mesafe_tablosu_yazdir(mesafe_matrisi: list[list[int]]):
    """Noktalar arası mesafe matrisini tablo olarak yazdırır."""
    n = len(mesafe_matrisi)
    print("   ╔══════════════════════════════════════════════════════════════╗")
    print("   ║              MESAFE MATRİSİ (km — tahmini karayolu)        ║")
    print("   ╚══════════════════════════════════════════════════════════════╝")
    print()

    # Başlık satırı — kısa şehir isimleri
    kisaltmalar = [n["sehir"][:5] for n in NOKTALAR]
    baslik = "         " + "".join(f"{k:>8s}" for k in kisaltmalar)
    print(baslik)
    print("         " + "─" * (8 * n))

    for i in range(n):
        satir = f"   {kisaltmalar[i]:>5s} │"
        for j in range(n):
            km = mesafe_matrisi[i][j] / 1000
            if i == j:
                satir += "     — "
            else:
                satir += f" {km:>6.0f}"
        print(satir)

    print()


# ============================================================
# 7. ANA PROGRAM
# ============================================================

def main():
    print()
    print("   ╔══════════════════════════════════════════════════════════╗")
    print("   ║   🚛 Gezgin Satıcı Problemi (TSP) — Türkiye Rotası     ║")
    print("   ║   📦 Google OR-Tools ile Optimum Rota Hesaplama         ║")
    print("   ╚══════════════════════════════════════════════════════════╝")
    print()

    # Noktaları listele
    print("   📍 Teslimat Noktaları:")
    print("   " + "─" * 50)
    for i, nokta in enumerate(NOKTALAR):
        tip = "🏭 DEPO" if nokta["tip"] == "depo" else "📦 DAĞ."
        print(f"   {i:2d}. [{tip}] {nokta['sehir']:15s} — {nokta['ad']}")
    print()

    # Mesafe matrisi
    print("   ⏳ Mesafe matrisi hesaplanıyor (Haversine + karayolu katsayısı)...")
    matris = mesafe_matrisi_olustur(KOORDINATLAR)
    mesafe_tablosu_yazdir(matris)

    # TSP çöz
    print("   ⏳ TSP çözülüyor (Google OR-Tools — Guided Local Search)...")
    print("   ⏳ 10 saniyelik optimizasyon süresi...")
    rota, toplam_mesafe = tsp_coz(matris)

    # Sonuçları yazdır
    sonuclari_yazdir(rota, toplam_mesafe, matris)

    # Haritayı oluştur
    harita_olustur(rota, toplam_mesafe, matris)


if __name__ == "__main__":
    main()
