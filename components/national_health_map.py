"""
DocMindX AI — National Health Resource Geospatial Map Component
Powered by Google Maps JavaScript API (Track 03 - Google Cloud Hackathon)
Renders interactive maps of Primary Health Centres, supply bottlenecks, and regional hubs.
"""
import json
import os
from config.settings import GOOGLE_MAPS_API_KEY

def generate_health_resource_map_html(facilities: list, dark_mode: bool = False, center_lat: float = 22.5, center_lon: float = 78.9, zoom: int = 5) -> str:
    """
    Generates high-performance interactive Google Maps JavaScript API map for health resources.
    Renders custom pins, clinical InfoWindows, supply triage colors, and responsive bounds fitting.
    """
    api_key = GOOGLE_MAPS_API_KEY or os.getenv("GOOGLE_MAPS_API_KEY", "")
    bg_color = "#0B1120" if dark_mode else "#F8FAFC"

    markers_data = []
    for fac in facilities:
        worst_status = "HEALTHY"
        critical_count = 0
        warning_count = 0
        critical_items = []
        for med_id, inv in fac["inventory"].items():
            st = inv.get("status", "HEALTHY")
            if st == "CRITICAL":
                critical_count += 1
                worst_status = "CRITICAL"
                critical_items.append(inv.get("med_name", med_id))
            elif st == "WARNING":
                warning_count += 1
                if worst_status != "CRITICAL":
                    worst_status = "WARNING"

        color = "#EF4444" if worst_status == "CRITICAL" else ("#F59E0B" if worst_status == "WARNING" else "#10B981")
        if fac.get("type") == "CHC":
            color = "#3B82F6" if worst_status == "HEALTHY" else color

        bed_total = fac.get("bed_capacity", fac.get("beds", {}).get("total", 30))
        bed_occ = int(bed_total * 0.75) if isinstance(bed_total, (int, float)) else 20
        doc_pres = fac.get("doctors", fac.get("staff", {}).get("doctors_pres", 2))
        nurse_pres = fac.get("nurses", fac.get("staff", {}).get("nurses_pres", 4))

        markers_data.append({
            "id": fac["id"],
            "name": fac["name"],
            "state": fac["state"],
            "district": fac["district"],
            "type": fac["type"],
            "lat": fac["lat"],
            "lon": fac["lon"],
            "color": color,
            "status": worst_status,
            "critical_count": critical_count,
            "warning_count": warning_count,
            "critical_items": ", ".join(critical_items[:3]) if critical_items else "None",
            "beds_occupied": bed_occ,
            "beds_total": bed_total,
            "staff_doc": f"{doc_pres} Doctors",
            "staff_nurse": f"{nurse_pres} Nurses",
            "provenance": fac.get("provenance", "OBSERVED")
        })

    markers_json = json.dumps(markers_data)

    # Google Maps Dark Mode Styling Vector
    dark_style = """[
        {"elementType": "geometry", "stylers": [{"color": "#182030"}]},
        {"elementType": "labels.text.stroke", "stylers": [{"color": "#182030"}]},
        {"elementType": "labels.text.fill", "stylers": [{"color": "#94A3B8"}]},
        {"featureType": "administrative.locality", "elementType": "labels.text.fill", "stylers": [{"color": "#E2E8F0"}]},
        {"featureType": "poi", "elementType": "labels.text.fill", "stylers": [{"color": "#94A3B8"}]},
        {"featureType": "poi.park", "elementType": "geometry", "stylers": [{"color": "#152E28"}]},
        {"featureType": "road", "elementType": "geometry", "stylers": [{"color": "#24324D"}]},
        {"featureType": "road", "elementType": "geometry.stroke", "stylers": [{"color": "#1B273E"}]},
        {"featureType": "road", "elementType": "labels.text.fill", "stylers": [{"color": "#94A3B8"}]},
        {"featureType": "road.highway", "elementType": "geometry", "stylers": [{"color": "#3B4D71"}]},
        {"featureType": "water", "elementType": "geometry", "stylers": [{"color": "#0D1929"}]},
        {"featureType": "water", "elementType": "labels.text.fill", "stylers": [{"color": "#475569"}]}
    ]""" if dark_mode else "[]"

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DocMindX AI - Google Maps Health Geospatial Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        html, body {{ height: 100%; width: 100%; margin: 0; padding: 0; background: {bg_color}; font-family: 'Inter', -apple-system, sans-serif; overflow: hidden; }}
        #map {{ height: 100%; width: 100%; border-radius: 12px; }}
        
        .gm-style .gm-style-iw-c {{
            background: {('#1E293B' if dark_mode else '#FFFFFF')} !important;
            color: {('#F8FAFC' if dark_mode else '#0F172A')} !important;
            border-radius: 12px !important;
            box-shadow: 0 12px 30px rgba(0,0,0,0.35) !important;
            padding: 14px 16px !important;
            border: 1px solid {('#334155' if dark_mode else '#E2E8F0')} !important;
            max-width: 88vw !important;
            box-sizing: border-box !important;
        }}
        .gm-style .gm-style-iw-tc::after {{
            background: {('#1E293B' if dark_mode else '#FFFFFF')} !important;
        }}
        .gm-style-iw-d {{
            overflow: visible !important;
            max-height: none !important;
            max-width: 85vw !important;
            box-sizing: border-box !important;
        }}
        
        .legend {{
            position: absolute;
            top: 18px;
            left: 18px;
            z-index: 1000;
            background: {('rgba(15, 23, 42, 0.92)' if dark_mode else 'rgba(255, 255, 255, 0.95)')};
            backdrop-filter: blur(8px);
            padding: 12px 16px;
            border-radius: 10px;
            border: 1px solid {('#334155' if dark_mode else '#E2E8F0')};
            color: {('#F8FAFC' if dark_mode else '#0F172A')};
            font-size: 11.5px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.22);
        }}
        .legend-title {{
            font-weight: 800;
            margin-bottom: 8px;
            text-transform: uppercase;
            font-size: 10px;
            letter-spacing: 0.6px;
            color: {('#94A3B8' if dark_mode else '#64748B')};
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .legend-item {{ display: flex; align-items: center; gap: 8px; margin-bottom: 5px; font-weight: 500; }}
        .legend-dot {{ width: 11px; height: 11px; border-radius: 50%; display: inline-block; box-shadow: 0 0 4px rgba(0,0,0,0.2); }}

        @media (max-width: 480px) {{
            .legend {{
                top: 10px;
                left: 10px;
                padding: 8px 10px;
                font-size: 10px;
                max-width: calc(100vw - 20px);
            }}
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="legend">
        <div class="legend-title">Facility Status [Google Maps]</div>
        <div class="legend-item"><span class="legend-dot" style="background: #10B981;"></span> Healthy (&gt; 14 Days Stock)</div>
        <div class="legend-item"><span class="legend-dot" style="background: #F59E0B;"></span> Warning (5–14 Days Stock)</div>
        <div class="legend-item"><span class="legend-dot" style="background: #EF4444;"></span> Critical Shortage (&lt; 5 Days)</div>
        <div class="legend-item"><span class="legend-dot" style="background: #3B82F6;"></span> Community Health Centre (CHC)</div>
        <div class="legend-item"><span style="color: #DC2626; font-size: 13px; line-height: 1; font-weight: 900; margin-right: 2px;">✚</span> District Hospital</div>
        <div class="legend-item"><span style="color: #8B5CF6; font-size: 13px; line-height: 1; font-weight: 900; margin-right: 2px;">✚</span> Medical College</div>
        <div class="legend-item"><span class="legend-dot" style="background: #64748B;"></span> Other Facility</div>
    </div>

    <script>
        function initGoogleHealthMap() {{
            const centerPos = {{ lat: {center_lat}, lng: {center_lon} }};
            const mapOptions = {{
                zoom: {zoom},
                center: centerPos,
                styles: {dark_style},
                mapTypeControl: true,
                mapTypeControlOptions: {{
                    style: google.maps.MapTypeControlStyle.HORIZONTAL_BAR,
                    position: google.maps.ControlPosition.TOP_RIGHT,
                    mapTypeIds: ['roadmap', 'satellite', 'hybrid', 'terrain']
                }},
                streetViewControl: true,
                streetViewControlOptions: {{
                    position: google.maps.ControlPosition.RIGHT_BOTTOM
                }},
                fullscreenControl: true,
                zoomControl: true,
                scaleControl: true,
                rotateControl: true
            }};

            const map = new google.maps.Map(document.getElementById('map'), mapOptions);
            const facilities = {markers_json};
            const bounds = new google.maps.LatLngBounds();
            let activeInfoWindow = null;

            facilities.forEach((f) => {{
                const pos = {{ lat: f.lat, lng: f.lon }};
                bounds.extend(pos);

                // Custom SVG Marker Pin
                const pinSymbol = {{
                    path: "M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z",
                    fillColor: f.color,
                    fillOpacity: 1,
                    strokeColor: '#FFFFFF',
                    strokeWeight: 1.5,
                    scale: 1.4,
                    anchor: new google.maps.Point(12, 22)
                }};

                const marker = new google.maps.Marker({{
                    position: pos,
                    map: map,
                    title: f.name,
                    icon: pinSymbol
                }});

                const contentHtml = `
                    <div style="font-family: 'Inter', sans-serif; font-size: 12px; line-height: 1.55; min-width: 180px; max-width: 82vw; box-sizing: border-box; word-break: break-word;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <span style="font-weight: 800; font-size: 13.5px; color: ${{f.color}};">${{f.name}}</span>
                            <span style="background: ${{f.color}}20; color: ${{f.color}}; border: 1px solid ${{f.color}}50; font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px;">${{f.type}}</span>
                        </div>
                        <div style="opacity: 0.75; font-size: 11px; margin-bottom: 6px;">${{f.district}}, ${{f.state}} • ID: ${{f.id}}</div>
                        <hr style="margin: 6px 0 8px 0; border: 0; border-top: 1px solid rgba(128,128,128,0.2);">
                        <div style="margin-bottom: 3px;"><b>Supply Status:</b> <span style="color: ${{f.color}}; font-weight: 700;">${{f.status}}</span></div>
                        <div style="margin-bottom: 3px;"><b>Critical Deficits:</b> <span style="color: ${{f.critical_count > 0 ? '#EF4444' : '#10B981'}}; font-weight: 600;">${{f.critical_count}} Items (${{f.critical_items}})</span></div>
                        <div style="margin-bottom: 3px;"><b>Bed Occupancy:</b> ${{f.beds_occupied}} / ${{f.beds_total}} Beds</div>
                        <div style="margin-bottom: 3px;"><b>Medical Staff:</b> ${{f.staff_doc}} Docs | ${{f.staff_nurse}} Nurses</div>
                    </div>
                `;

                const infoWindow = new google.maps.InfoWindow({{
                    content: contentHtml
                }});

                marker.addListener("click", () => {{
                    if (activeInfoWindow) activeInfoWindow.close();
                    infoWindow.open(map, marker);
                    activeInfoWindow = infoWindow;
                }});
            }});

            if (facilities.length > 1) {{
                map.fitBounds(bounds, {{ top: 40, right: 40, bottom: 40, left: 40 }});
            }} else if (facilities.length === 1) {{
                map.setCenter({{ lat: facilities[0].lat, lng: facilities[0].lon }});
                map.setZoom(11);
            }}
        }}
    </script>
    <script async defer src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initGoogleHealthMap"></script>
</body>
</html>
"""
    return html_content
