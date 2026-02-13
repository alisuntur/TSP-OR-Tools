"""
Kurye Rota Optimizasyonu - TSP
------------------------------
Bir kargo firmasının İstanbul'daki merkez deposundan çıkıp
Türkiye'deki farklı şehirlerdeki dağıtım noktalarına uğrayarak
tekrar depoya dönmesini sağlayan en kısa rotayı bulur.

Kullanılanlar:
- Python
- Google OR-Tools
- Folium
"""

import math
import folium
from ortools.constraint_solver import routing_enums_pb2, pywrapcp


# ============================================================
# 1. Şehirler ve koordinatlar
# ============================================================

# Merkez depo ve dağıtım noktaları
NOKTALAR = [
    {
        "ad": "Merkez Depo",
        "sehir": "İstanbul",
        "adres": "Tuzla OSB",
        "koordinat": (40.8190, 29.3005),
        "tip": "depo",
    },
    {
        "ad": "Ankara Dağıtım",
        "sehir": "Ankara",
        "adres": "Ostim OSB",
        "koordinat": (39.9708, 32.6227),
        "tip": "dagitim",
    },
    {
        "ad": "İzmir Şube",
        "sehir": "İzmir",
        "adres": "Alsancak",
        "koordinat": (38.4362, 27.1428),
        "tip": "dagitim",
    },
    {
        "ad": "Bursa Noktası",
        "sehir": "Bursa",
        "adres": "Nilüfer OSB",
        "koordinat": (40.2225, 28.8640),
        "tip": "dagitim",
    },
    {
        "ad": "Antalya Mağaza",
        "sehir": "Antalya",
        "adres": "Konyaaltı",
        "koordinat": (36.8841, 30.6927),
        "tip": "dagitim",
    },
    {
        "ad": "Konya Depo",
        "sehir": "Konya",
        "adres": "Büsan OSB",
        "koordinat": (37.8746, 32.4932),
        "tip": "dagitim",
    },
    {
        "ad": "Denizli Müşteri",
        "sehir": "Denizli",
        "adres": "OSB",
        "koordinat": (37.7765, 29.0864),
        "tip": "dagitim",
    },
    {
        "ad": "Eskişehir Teslimat",
        "sehir": "Eskişehir",
        "adres": "Tepebaşı OSB",
        "koordinat": (39.7668, 30.5256),
        "tip": "dagitim",
    },
    {
        "ad": "Kayseri Dağıtım",
        "sehir": "Kayseri",
        "adres": "Kayseri OSB",
        "koordinat": (38.7205, 35.4826),
        "tip": "dagitim",
    },
    {
        "ad": "Afyon Aktarma",
        "sehir": "Afyon",
        "adres": "Merkez",
        "koordinat": (38.7507, 30.5387),
        "tip": "dagitim",
    },
]

KOORDINATLAR = [n["koordinat"] for n in NOKTALAR]


# ============================================================
# 2. Mesafe hesaplama
# ============================================================

def haversine(coord1, coord2):
    """İki nokta arasındaki kuş uçuşu mesafeyi hesaplar."""
    R = 6371
    lat1, lon1 = map(math.radians, coord1)
    lat2, lon2 = map(math.radians, coord2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    return R * 2 * math.asin(math.sqrt(a))


def karayolu_mesafesi(km):
    """Kuş uçuşu mesafeyi tahmini karayolu mesafesine çevirir."""
    return km * 1.35


def mesafe_matrisi_olustur(koordinatlar):
    """Tüm noktalar arası mesafe matrisini oluşturur."""
    n = len(koordinatlar)
    matris = []

    for i in range(n):
        satir = []
        for j in range(n):
            if i == j:
                satir.append(0)
            else:
                kus_ucusu = haversine(koordinatlar[i], koordinatlar[j])
                yol = karayolu_mesafesi(kus_ucusu)
                satir.append(int(yol * 1000))  # metre
        matris.append(satir)

    return matris


# ============================================================
# 3. TSP çözümü (OR-Tools)
# ============================================================

def tsp_coz(mesafe_matrisi):
    """OR-Tools ile en kısa rotayı bulur."""
    n = len(mesafe_matrisi)

    manager = pywrapcp.RoutingIndexManager(n, 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def mesafe_callback(i, j):
        return mesafe_matrisi[
            manager.IndexToNode(i)
        ][
            manager.IndexToNode(j)
        ]

    transit_cb = routing.RegisterTransitCallback(mesafe_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_cb)

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.FromSeconds(10)

    solution = routing.SolveWithParameters(params)

    rota = []
    index = routing.Start(0)
    while not routing.IsEnd(index):
        rota.append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))
    rota.append(manager.IndexToNode(index))

    return rota, solution.ObjectiveValue()


# ============================================================
# 4. Harita çizimi
# ============================================================

def harita_olustur(rota, toplam_mesafe=None):
    """Rotayı harita üzerinde detaylı şekilde gösterir."""
    merkez_lat = sum(k[0] for k in KOORDINATLAR) / len(KOORDINATLAR)
    merkez_lng = sum(k[1] for k in KOORDINATLAR) / len(KOORDINATLAR)

    harita = folium.Map([merkez_lat, merkez_lng], zoom_start=6, tiles=None)

    # Harita katmanları
    folium.TileLayer("OpenStreetMap", name="Sokak Haritası").add_to(harita)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB", name="Koyu Tema",
    ).add_to(harita)
    folium.LayerControl(position="topright").add_to(harita)

    # Başlık
    km = toplam_mesafe / 1000 if toplam_mesafe else 0
    baslik = f"""
    <div style="position:fixed; top:10px; left:50%; transform:translateX(-50%);
        z-index:9999; background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);
        padding:14px 28px; border-radius:14px; color:white;
        font-family:'Segoe UI',system-ui,sans-serif; text-align:center;
        box-shadow:0 6px 24px rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.1);">
        <div style="font-size:18px; font-weight:700;">🚛 Kurye Rota Optimizasyonu — TSP</div>
        <div style="font-size:12px; margin-top:6px; opacity:0.85;">
            📍 {len(NOKTALAR)} nokta &nbsp;|&nbsp; 📏 {km:.0f} km &nbsp;|&nbsp;
            ⛽ ~{km*0.12:.0f} lt &nbsp;|&nbsp; 💰 ~{km*0.12*43.5:,.0f} ₺
        </div>
    </div>"""
    harita.get_root().html.add_child(folium.Element(baslik))

    # Rota bilgi paneli (sol alt)
    rota_html = ""
    for sira, idx in enumerate(rota):
        n = NOKTALAR[idx]
        renk = "#FF4444" if n["tip"] == "depo" else "#4FC3F7"
        ikon = "🏭" if n["tip"] == "depo" else "📦"
        mesafe_str = ""
        if sira < len(rota) - 1:
            sonraki = rota[sira + 1]
            etap = karayolu_mesafesi(haversine(KOORDINATLAR[idx], KOORDINATLAR[sonraki]))
            mesafe_str = f" <span style='color:#888;font-size:10px;'>→ {etap:.0f} km</span>"
        rota_html += f"""<div style="margin:3px 0; display:flex; align-items:center; gap:5px;">
            <span style="background:{renk}; color:#fff; font-weight:700;
                width:20px; height:20px; border-radius:50%; display:inline-flex;
                align-items:center; justify-content:center; font-size:10px;
                flex-shrink:0;">{sira+1}</span>
            <span>{ikon} {n['sehir']}{mesafe_str}</span></div>"""

    panel = f"""
    <div style="position:fixed; bottom:20px; left:20px; z-index:9999;
        background:rgba(15,12,41,0.93); padding:14px 18px; border-radius:12px;
        color:white; font-size:12px; font-family:'Segoe UI',system-ui,sans-serif;
        box-shadow:0 6px 24px rgba(0,0,0,0.5); max-height:360px; overflow-y:auto;
        border:1px solid rgba(255,255,255,0.08);">
        <div style="font-size:13px; font-weight:700; margin-bottom:8px; color:#FFD700;">
            📋 Optimum Rota</div>
        {rota_html}
    </div>"""
    harita.get_root().html.add_child(folium.Element(panel))

    # Renkli segment çizgileri
    segment_renkleri = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
        "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9", "#FF6B6B",
    ]

    for seg in range(len(rota) - 1):
        p1 = KOORDINATLAR[rota[seg]]
        p2 = KOORDINATLAR[rota[seg + 1]]
        renk = segment_renkleri[seg % len(segment_renkleri)]
        etap = karayolu_mesafesi(haversine(p1, p2))

        # Gölge
        folium.PolyLine([p1, p2], weight=8, color="#1a1a2e", opacity=0.3).add_to(harita)
        # Ana çizgi
        folium.PolyLine(
            [p1, p2], weight=4, color=renk, opacity=0.9, dash_array="10 5",
            tooltip=f"{NOKTALAR[rota[seg]]['sehir']} → {NOKTALAR[rota[seg+1]]['sehir']}: {etap:.0f} km",
        ).add_to(harita)

        # Mesafe etiketi
        orta = ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2)
        folium.Marker(orta, icon=folium.DivIcon(html=f"""
            <div style="background:rgba(15,12,41,0.88); color:{renk};
                padding:2px 7px; border-radius:8px; font-size:10px; font-weight:700;
                font-family:'Segoe UI',sans-serif; white-space:nowrap;
                transform:translate(-22px,-10px); box-shadow:0 2px 6px rgba(0,0,0,0.3);
                border:1px solid {renk}40;">{etap:.0f} km</div>""",
            icon_size=(60, 20), icon_anchor=(0, 0),
        )).add_to(harita)

    # Noktaları işaretle
    for i, nokta in enumerate(NOKTALAR):
        lat, lng = nokta["koordinat"]
        is_depo = nokta["tip"] == "depo"
        sira = rota.index(i) + 1 if i in rota else "—"

        # Popup
        popup = f"""
        <div style="font-family:'Segoe UI',sans-serif; min-width:200px;">
            <div style="font-weight:700; font-size:14px; color:#1a1a2e;">
                {'🏭' if is_depo else '📦'} {nokta['ad']}</div>
            <hr style="margin:5px 0; border-color:#eee;">
            <div style="font-size:12px; color:#555; line-height:1.6;">
                🏙️ {nokta['sehir']}<br>
                🏠 {nokta['adres']}<br>
                📍 {lat:.4f}°N, {lng:.4f}°E<br>
                🔢 Sıra: <b style="color:#e74c3c;">{sira}</b>
            </div>
        </div>"""

        folium.Marker(
            [lat, lng],
            popup=folium.Popup(popup, max_width=260),
            tooltip=f"{sira}. {nokta['sehir']} — {nokta['ad']}",
            icon=folium.Icon(
                color="red" if is_depo else "blue",
                icon="industry" if is_depo else "cube",
                prefix="fa",
            ),
        ).add_to(harita)

        # Numara etiketi
        etiket_renk = "#FF4444" if is_depo else "#1E88E5"
        folium.Marker([lat, lng], icon=folium.DivIcon(html=f"""
            <div style="background:{etiket_renk}; color:white; font-weight:800;
                width:24px; height:24px; border-radius:50%; display:flex;
                align-items:center; justify-content:center; font-size:11px;
                border:2px solid white; box-shadow:0 2px 8px rgba(0,0,0,0.4);
                transform:translate(-12px,-32px);
                font-family:'Segoe UI',sans-serif;">{sira}</div>""",
            icon_size=(24, 24), icon_anchor=(0, 0),
        )).add_to(harita)

    harita.save("rota.html")


# ============================================================
# 5. Ana program
# ============================================================

def main():
    matris = mesafe_matrisi_olustur(KOORDINATLAR)
    rota, mesafe = tsp_coz(matris)
    harita_olustur(rota, mesafe)

    print("Optimum rota:")
    for i in rota:
        print("-", NOKTALAR[i]["sehir"])
    print(f"Toplam mesafe: {mesafe / 1000:.0f} km")


if __name__ == "__main__":
    main()
