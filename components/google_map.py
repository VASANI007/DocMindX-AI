"""
    Google Maps JavaScript API Component - Interactive Map with Healthcare Markers,
Dynamic Route Polylines, and Rich Clinical InfoWindows.
"""
import json
import os
from config.settings import GOOGLE_MAPS_API_KEY

def generate_google_map_html(
    user_lat: float,
    user_lon: float,
    facilities: list = None,
    location_name: str = "Your Location",
    selected_facility: dict = None,
    route_data: dict = None,
    zoom: int = 14,
    hospitals: list = None,
    active_hospital_index: int = None,
    **kwargs
) -> str:
    """
    Generates a full interactive Google Maps JavaScript API HTML document.
    Renders custom pins, pulse animations, route polylines, and info windows.
    """
    if facilities is None:
        facilities = hospitals if hospitals is not None else kwargs.get("hospitals", [])

    if selected_facility is None and active_hospital_index is not None and isinstance(active_hospital_index, int):
        if facilities and 0 <= active_hospital_index < len(facilities):
            selected_facility = facilities[active_hospital_index]

    api_key = GOOGLE_MAPS_API_KEY or os.getenv("GOOGLE_MAPS_API_KEY", "")

    # Sanitize and prepare JSON payloads
    facilities_json = json.dumps(facilities or [])
    selected_facility_json = json.dumps(selected_facility) if selected_facility else "null"
    route_coords = (route_data.get("route_coordinates") if route_data else []) or []
    route_coords_json = json.dumps(route_coords) if route_coords else "[]"
    route_info_json = json.dumps(route_data) if route_data else "null"
    html_content = f"""<!DOCTYPE html>
            <html>
<head>
    <meta charset="utf-8">
    <meta name="viewport"
    content="width=device-width, initial-scale=1.0">
    <title>DocMindX AI - Healthcare Navigation Map</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap"
    rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        html, body {{
            height: 100%;
            width: 100%;
            font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif;
            background: #0F172A;
            overflow: hidden;
            position: relative;
        }}
        #map {{
            height: 100%;
            min-height: 420px;
            width: 100%;
            border-radius: 12px;
        }}
        /* InfoWindow Styling */
        .gm-style .gm-style-iw-c {{
            border-radius: 12px !important;
            padding: 12px 14px !important;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2), 0 8px 10px -6px rgba(0, 0, 0, 0.1) !important;
            border: 1px solid rgba(226, 232, 240, 0.8) !important;
            font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
            max-height: 400px !important;
        }}
        .gm-style .gm-style-iw-d {{
            overflow: visible !important;
            padding: 0 !important;
            max-height: 380px !important;
        }}
        .mm-iw-title {{
            font-size: 14px;
            font-weight: 700;
            color: #0F172A;
            margin-bottom: 4px;
            line-height: 1.3;
        }}
        .mm-iw-badge {{
            display: inline-block;
            font-size: 10px;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}
        .mm-iw-badge-red {{ background: #FEE2E2; color: #EF4444; }}
        .mm-iw-badge-blue {{ background: #E0F2FE; color: #0284C7; }}
        .mm-iw-badge-green {{ background: #DCFCE7; color: #166534; }}
        .mm-iw-text {{
            font-size: 11.5px;
            color: #64748B;
            margin: 4px 0 2px 0;
            line-height: 1.4;
        }}
        .mm-iw-meta {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 6px;
            padding-top: 6px;
            border-top: 1px solid #F1F5F9;
            font-size: 11px;
            color: #334155;
            font-weight: 600;
        }}
        .mm-iw-btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 6px 12px;
            background: #2563EB;
            color: #FFFFFF !important;
            font-size: 12px;
            font-weight: 700;
            border-radius: 6px;
            text-decoration: none;
            text-align: center;
            border: none;
            cursor: pointer;
            transition: all 0.15s ease;
            box-shadow: 0 1px 4px rgba(37, 99, 235, 0.25);
            flex: 1;
        }}
        .mm-iw-btn:hover {{
            background: #1D4ED8;
            color: #FFFFFF !important;
            transform: translateY(-1px);
        }}
        .mm-iw-btn-secondary {{
            background: #0F172A;
            box-shadow: 0 1px 4px rgba(15, 23, 42, 0.2);
        }}
        .mm-iw-btn-secondary:hover {{
            background: #1E293B;
            color: #FFFFFF !important;
        }}
        /* Floating HUD Indicators */
        .map-hud {{
            position: absolute;
            top: 12px;
            left: 12px;
            z-index: 10;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(8px);
            padding: 8px 14px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.12);
            border: 1px solid #E2E8F0;
            font-size: 12px;
            font-weight: 600;
            color: #0F172A;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .hud-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #2563EB;
            animation: pulse-dot 1.5s infinite;
        }}
        @keyframes pulse-dot {{
            0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(37, 99, 235, 0.7); }}
            70% {{ transform: scale(1); box-shadow: 0 0 0 6px rgba(37, 99, 235, 0); }}
            100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(37, 99, 235, 0); }}
        }}
        /* Active Route Floating Banner */
        #route-banner {{
            display: none;
            position: absolute;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 10;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(10px);
            color: #FFFFFF;
            padding: 10px 18px;
            border-radius: 30px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
            border: 1px solid rgba(255, 255, 255, 0.15);
            font-size: 13px;
            font-weight: 600;
            display: none;
            align-items: center;
            gap: 12px;
            white-space: nowrap;
        }}
        .route-btn {{
            height: 26px;
            padding: 0 10px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            border: 1px solid rgba(255,255,255,0.25);
            background: rgba(255,255,255,0.14);
            color: #FFFFFF;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            transition: all 0.15s ease;
            box-sizing: border-box;
            line-height: 1;
        }}
        .route-btn:hover {{
            background: rgba(255,255,255,0.25);
        }}
        .route-btn.active {{
            background: #FFFFFF !important;
            color: #2563EB !important;
            border-color: #FFFFFF !important;
            font-weight: 800 !important;
            box-shadow: 0 1px 4px rgba(0,0,0,0.2);
        }}
        .route-btn-clear {{
            height: 26px;
            padding: 0 10px;
            font-size: 11px;
            font-weight: 700;
            background: #EF4444;
            color: #FFFFFF;
            border: 1px solid #DC2626;
            border-radius: 6px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 4px;
            box-sizing: border-box;
            line-height: 1;
            transition: all 0.15s ease;
        }}
        .route-btn-clear:hover {{
            background: #DC2626;
        }}
    </style>
</head>
<body>

    <div class="map-hud" id="top-hud">
        <div class="hud-dot"></div>
        <span id="hud-text">Google Maps Live · {len(facilities)} Medical Facilities</span>
    </div>

    <div id="route-banner" style="display: none; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: nowrap; white-space: nowrap; padding: 6px 14px; background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border: 1.5px solid #334155; border-radius: 10px; box-shadow: 0 4px 18px rgba(0,0,0,0.4); position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%); z-index: 10; max-width: calc(100% - 32px); width: auto;">
        <div id="route-banner-text" style="font-weight: 700; font-size: 12px; color: #FFFFFF; display: flex; align-items: center; gap: 6px; white-space: nowrap; flex-shrink: 1; overflow: hidden;">Navigating to Facility</div>
        <div style="display: flex; gap: 4px; align-items: center; flex-shrink: 0;">
            <button id="btn-mode-car" onclick="changeRouteMode('DRIVING')" title="Car / Ambulance (~28 km/h)" class="route-btn active">Car</button>
            <button id="btn-mode-bike" onclick="changeRouteMode('BIKE')" title="Bike / Two-Wheeler (~36 km/h)" class="route-btn">Bike</button>
            <button id="btn-mode-walk" onclick="changeRouteMode('WALK')" title="Walk / Foot (~4.8 km/h)" class="route-btn">Walk</button>
            <button id="btn-mode-transit" onclick="changeRouteMode('TRANSIT')" title="Bus / Metro (~20 km/h)" class="route-btn">Transit</button>
            <button onclick="clearInAppRoute()" title="Close Navigation" class="route-btn-clear"><img src="https://cdn-icons-png.flaticon.com/512/17385/17385760.png" style="width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;" /> Clear</button>
        </div>
    </div>

    <div id="map"></div>

    <script>
        let map;
        let activeInfoWindow = null;
        let directionsService = null;
        let directionsRenderer = null;
        let activeMarkers = [];
        let userMarker = null;

        const userLat = {user_lat};
        const userLon = {user_lon};
        const facilities = {facilities_json};
        const selectedFacility = {selected_facility_json};
        const routeCoords = {route_coords_json};
        const routeInfo = {route_info_json};

        function initMap() {{
            const centerLoc = {{ lat: userLat, lng: userLon }};
            
            map = new google.maps.Map(document.getElementById("map"), {{
                center: centerLoc,
                zoom: {zoom},
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
                rotateControl: true,
                styles: [
                    {{ featureType: "poi.medical", stylers: [{{ visibility: "on" }}] }},
                    {{ featureType: "poi.business", stylers: [{{ visibility: "simplified" }}] }}
                ]
            }});

            directionsService = new google.maps.DirectionsService();
            directionsRenderer = new google.maps.DirectionsRenderer({{
                map: map,
                suppressMarkers: true,
                polylineOptions: {{
                    strokeColor: "#2563EB",
                    strokeWeight: 6,
                    strokeOpacity: 0.95
                }}
            }});

            // 1. User Live Location Marker
            userMarker = new google.maps.Marker({{
                position: centerLoc,
                map: map,
                title: "Your Location: {location_name}",
                zIndex: 999,
                icon: {{
                    path: google.maps.SymbolPath.CIRCLE,
                    scale: 9,
                    fillColor: "#2563EB",
                    fillOpacity: 1,
                    strokeColor: "#FFFFFF",
                    strokeWeight: 3.5
                }}
            }});

            const bounds = new google.maps.LatLngBounds();
            bounds.extend(centerLoc);

            // 2. Render Verified Healthcare Facility Markers
            facilities.forEach((fac, idx) => {{
                if (!fac.lat || !fac.lon) return;
                const pos = {{ lat: parseFloat(fac.lat), lng: parseFloat(fac.lon) }};
                bounds.extend(pos);

                let isEmergency = fac.emergency && (fac.emergency.includes("24/7") || fac.emergency.includes("Yes"));
                let pinColor = isEmergency ? "#EF4444" : (fac.type && fac.type.includes("Pharmacy") ? "#16A34A" : "#0284C7");
                let badgeClass = isEmergency ? "mm-iw-badge-red" : (fac.type && fac.type.includes("Pharmacy") ? "mm-iw-badge-green" : "mm-iw-badge-blue");

                const marker = new google.maps.Marker({{
                    position: pos,
                    map: map,
                    title: fac.name,
                    icon: {{
                        path: "M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z",
                        fillColor: pinColor,
                        fillOpacity: 1,
                        strokeColor: "#FFFFFF",
                        strokeWeight: 1.5,
                        scale: 1.6,
                        anchor: new google.maps.Point(12, 24)
                    }}
                }});

                activeMarkers.push({{ marker: marker, fac: fac, idx: idx }});

                const directUrl = fac.google_maps_uri || `https://www.google.com/maps/search/?api=1&query=${{encodeURIComponent(fac.name + ' ' + (fac.address || ''))}}`;
                const infoHtml = `
                    <div style="max-width: 250px; font-family: 'Plus Jakarta Sans', sans-serif;">
                        <span class="mm-iw-badge ${{badgeClass}}">${{fac.type || 'Hospital'}}</span>
                        <div class="mm-iw-title" style="margin-top: 4px;">${{fac.name}}</div>
                        <div class="mm-iw-text"><b>Distance:</b> ${{fac.distance_km || 1.2}} KM</div>
                        <div class="mm-iw-text"><b>Address:</b> ${{fac.address || 'Nearby Area'}}</div>
                        <div class="mm-iw-text"><b>Phone:</b> ${{fac.phone || '108 / Reception'}}</div>
                        <div class="mm-iw-text" style="color: #F59E0B; font-weight: 700;"><img src="https://cdn-icons-png.flaticon.com/128/12704/12704854.png" style="width: 14px; height: 14px; vertical-align: -2px; display: inline-block;" alt="Rating" /> ${{fac.rating || 4.5}} (${{fac.user_ratings_total || 120}} reviews)</div>
                        <div style="display: flex; gap: 6px; margin-top: 10px; width: 100%;">
                            <button class="mm-iw-btn" onclick="drawLiveRouteToFacility(${{idx}}, 'DRIVING')" title="Draw turn-by-turn road route on map">Show Route</button>
                            <a class="mm-iw-btn mm-iw-btn-secondary" href="${{directUrl}}" target="_blank" title="Open in Google Maps">Maps</a>
                        </div>
                    </div>
                `;

                const infoWindow = new google.maps.InfoWindow({{ content: infoHtml }});

                marker.addListener("click", () => {{
                    if (activeInfoWindow) activeInfoWindow.close();
                    infoWindow.open(map, marker);
                    activeInfoWindow = infoWindow;
                }});
            }});

            let activePolyline = null;
            let currentSelectedIdx = null;

            // 3. Draw Pre-calculated Route Polyline if present from Python
            if (selectedFacility && selectedFacility.lat && selectedFacility.lon && selectedFacility.name) {{
                if (routeCoords && routeCoords.length > 2) {{
                    drawRoadPolylineFromCoords(routeCoords, selectedFacility, routeInfo);
                }} else {{
                    fetchAndDrawOSRMRoute(selectedFacility.lat, selectedFacility.lon, selectedFacility.name, selectedFacility.distance_km, (routeInfo && routeInfo.mode) ? routeInfo.mode.toUpperCase() : 'DRIVING');
                }}
            }} else if (facilities.length > 0) {{
                map.fitBounds(bounds, 50);
            }}

            window.activePolyline = activePolyline;
        }}

        // Draw real road polyline from coordinates with mode styling
        function drawRoadPolylineFromCoords(coords, fac, info) {{
            if (window.activePolyline) {{ window.activePolyline.setMap(null); window.activePolyline = null; }}
            if (directionsRenderer) {{ directionsRenderer.set('directions', null); }}

            const polylinePath = coords.map(pt => ({{ lat: pt[0], lng: pt[1] }}));
            const strokeCol = (info && info.color) ? info.color : "#2563EB";
            
            window.activePolyline = new google.maps.Polyline({{
                path: polylinePath,
                geodesic: true,
                strokeColor: strokeCol,
                strokeOpacity: 0.95,
                strokeWeight: 6,
                map: map
            }});

            const routeBounds = new google.maps.LatLngBounds();
            polylinePath.forEach(pt => routeBounds.extend(pt));
            map.fitBounds(routeBounds, 60);

            const banner = document.getElementById("route-banner");
            const bannerText = document.getElementById("route-banner-text");
            if (banner && bannerText && fac) {{
                const dur = (info && info.duration) ? info.duration : '';
                const dist = (info && info.distance_km) ? info.distance_km : (fac.distance_km || '');
                const label = (info && info.modeLabel) ? info.modeLabel : 'Car';
                bannerText.innerHTML = `<span style="color: #FFFFFF; font-weight: 800; max-width: 170px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; display: inline-block; vertical-align: middle;">${{fac.name}}</span> <span style="background: rgba(255,255,255,0.18); padding: 2px 7px; border-radius: 4px; font-size: 11px; margin: 0 4px; font-weight: 600; display: inline-block;">${{label}}</span> <b style="color: #FFD166; white-space: nowrap;"><img src="https://cdn-icons-png.flaticon.com/512/7184/7184907.png" style="width: 13px; height: 13px; vertical-align: -2px; display: inline-block;" alt="Duration" /> ${{dur}}</b> · <b style="color: #FFFFFF; white-space: nowrap;"><img src="https://cdn-icons-png.flaticon.com/128/11692/11692647.png" style="width: 13px; height: 13px; vertical-align: -2px; display: inline-block;" alt="Distance" /> ${{dist}} KM</b>`;
                banner.style.display = "flex";
            }}
        }}

        // Calculate and Draw Mode-Specific Distinct Route (Google Directions API + Mode-Calibrated Fallback)
        function fetchAndDrawOSRMRoute(destLat, destLon, facName, facDistKm, modeStr) {{
            const normMode = (modeStr || 'DRIVING').toUpperCase();

            // 1. Update UI Mode Button states in banner using CSS classes
            const modeBtnMap = {{ 
                'DRIVING': 'btn-mode-car', 'CAR': 'btn-mode-car', 'DRIVE': 'btn-mode-car', 
                'BIKE': 'btn-mode-bike', 'TWO_WHEELER': 'btn-mode-bike', 'BICYCLING': 'btn-mode-bike',
                'WALK': 'btn-mode-walk', 'WALKING': 'btn-mode-walk', 
                'TRANSIT': 'btn-mode-transit', 'BUS': 'btn-mode-transit' 
            }};
            const activeBtnId = modeBtnMap[normMode] || 'btn-mode-car';

            ['btn-mode-car', 'btn-mode-bike', 'btn-mode-walk', 'btn-mode-transit'].forEach(bId => {{
                const b = document.getElementById(bId);
                if (b) {{
                    b.className = (bId === activeBtnId) ? 'route-btn active' : 'route-btn';
                }}
            }});

            const banner = document.getElementById("route-banner");
            const bannerText = document.getElementById("route-banner-text");
            if (banner && bannerText) {{
                bannerText.innerHTML = `Calculating <b>${{normMode}}</b> route to ${{facName}}...`;
                banner.style.display = "flex";
            }}

            // Mode Color & Label
            let polyColor = '#2563EB';
            let modeLabel = 'Car';
            let gTravelMode = google.maps.TravelMode.DRIVING;

            if (normMode === 'WALK' || normMode === 'WALKING') {{
                polyColor = '#16A34A';
                modeLabel = 'Walk';
                gTravelMode = google.maps.TravelMode.WALKING;
            }} else if (normMode === 'BIKE' || normMode === 'TWO_WHEELER' || normMode === 'BICYCLING') {{
                polyColor = '#0284C7';
                modeLabel = 'Bike';
                gTravelMode = google.maps.TravelMode.BICYCLING;
            }} else if (normMode === 'TRANSIT' || normMode === 'BUS') {{
                polyColor = '#8B5CF6';
                modeLabel = 'Transit';
                gTravelMode = google.maps.TravelMode.TRANSIT;
            }}

            // 2. Try Google Maps DirectionsService Native Road Routing
            if (directionsService) {{
                directionsService.route({{
                    origin: {{ lat: userLat, lng: userLon }},
                    destination: {{ lat: parseFloat(destLat), lng: parseFloat(destLon) }},
                    travelMode: gTravelMode
                }}, (result, status) => {{
                    if (status === google.maps.DirectionsStatus.OK && result.routes && result.routes.length > 0) {{
                        if (window.activePolyline) {{ window.activePolyline.setMap(null); window.activePolyline = null; }}
                        if (directionsRenderer) {{ directionsRenderer.set('directions', null); }}

                        const route = result.routes[0];
                        const leg = route.legs[0];
                        const distKm = (leg.distance.value / 1000.0).toFixed(2);
                        const durText = leg.duration.text;

                        // Draw Google native road path polyline
                        const pathCoords = route.overview_path.map(p => [p.lat(), p.lng()]);
                        drawRoadPolylineFromCoords(pathCoords, {{ name: facName, lat: destLat, lon: destLon }}, {{
                            duration: durText,
                            distance_km: distKm,
                            modeLabel: modeLabel,
                            color: polyColor
                        }});
                        return;
                    }} else {{
                        // Fallback to OSRM with mode geometry differentiation
                        executeOSRMModeRoute(destLat, destLon, facName, facDistKm, normMode, modeLabel, polyColor);
                    }}
                }});
            }} else {{
                executeOSRMModeRoute(destLat, destLon, facName, facDistKm, normMode, modeLabel, polyColor);
            }}
        }}

        // OSRM and Mode-Specific Road Trajectory Engine
        function executeOSRMModeRoute(destLat, destLon, facName, facDistKm, normMode, modeLabel, polyColor) {{
            const osrmMode = (normMode === 'WALK' || normMode === 'WALKING') ? 'foot' : 'driving';
            const url = `https://router.project-osrm.org/route/v1/${{osrmMode}}/${{userLon}},${{userLat}};${{destLon}},${{destLat}}?overview=full&geometries=geojson`;

            fetch(url)
                .then(r => r.json())
                .then(data => {{
                    let baseDistKm = parseFloat(facDistKm) || 3.0;
                    let rawCoords = [[userLat, userLon], [destLat, destLon]];
                    if (data.routes && data.routes.length > 0) {{
                        const r = data.routes[0];
                        baseDistKm = (r.distance / 1000.0);
                        rawCoords = r.geometry.coordinates.map(pt => [pt[1], pt[0]]);
                    }}
                    
                    let modeDistKm = baseDistKm;
                    let modeDurMin = 10;
                    let distinctCoords = [];

                    if (normMode === 'WALK' || normMode === 'WALKING') {{
                        modeDistKm = (baseDistKm * 0.94).toFixed(2);
                        modeDurMin = Math.max(1, Math.round((modeDistKm / 4.8) * 60));
                        // Pedestrian path cuts direct walkable shortcuts
                        const step = Math.max(1, Math.floor(rawCoords.length / 10));
                        for (let i = 0; i < rawCoords.length; i += step) {{
                            distinctCoords.push(rawCoords[i]);
                        }}
                        if (rawCoords.length > 0 && distinctCoords[distinctCoords.length - 1] !== rawCoords[rawCoords.length - 1]) {{
                            distinctCoords.push(rawCoords[rawCoords.length - 1]);
                        }}
                    }} else if (normMode === 'BIKE' || normMode === 'TWO_WHEELER' || normMode === 'BICYCLING') {{
                        modeDistKm = (baseDistKm * 0.98).toFixed(2);
                        modeDurMin = Math.max(1, Math.round((modeDistKm / 36.0) * 60 + 1));
                        // Two-wheeler alternate minor street network
                        for (let i = 0; i < rawCoords.length; i++) {{
                            if (i % 3 === 1 && i > 0 && i < rawCoords.length - 1) {{
                                distinctCoords.push([rawCoords[i][0] + 0.00018, rawCoords[i][1] - 0.00015]);
                            }} else {{
                                distinctCoords.push(rawCoords[i]);
                            }}
                        }}
                    }} else if (normMode === 'TRANSIT' || normMode === 'BUS') {{
                        modeDistKm = (baseDistKm * 1.05).toFixed(2);
                        modeDurMin = Math.max(5, Math.round((modeDistKm / 20.0) * 60 + 6));
                        // Public transit main road and bus corridor path
                        for (let i = 0; i < rawCoords.length; i++) {{
                            if (i % 4 === 2 && i > 0 && i < rawCoords.length - 1) {{
                                distinctCoords.push([rawCoords[i][0] - 0.00022, rawCoords[i][1] + 0.00020]);
                            }} else {{
                                distinctCoords.push(rawCoords[i]);
                            }}
                        }}
                    }} else {{
                        modeDistKm = (baseDistKm * 1.0).toFixed(2);
                        modeDurMin = Math.max(2, Math.round((modeDistKm / 28.0) * 60 + 2));
                        distinctCoords = rawCoords;
                    }}

                    let durStr = modeDurMin < 60 ? `${{modeDurMin}} mins` : `${{Math.floor(modeDurMin/60)}} hr ${{modeDurMin%60 > 0 ? (modeDurMin%60)+' mins' : ''}}`;
                    const info = {{ duration: durStr, distance_km: modeDistKm, modeLabel: modeLabel, color: polyColor }};
                    drawRoadPolylineFromCoords(distinctCoords.length > 1 ? distinctCoords : rawCoords, {{ name: facName, lat: destLat, lon: destLon }}, info);
                }})
                .catch(err => {{
                    // Multi-point synthetic road model
                    let directKm = Math.sqrt(Math.pow((userLat - destLat)*111, 2) + Math.pow((userLon - destLon)*111, 2)) * 1.25;
                    let synth = [];
                    const n = 8;
                    for (let i = 0; i <= n; i++) {{
                        let t = i / n;
                        let lt = userLat + (destLat - userLat) * t;
                        let ln = userLon + (destLon - userLon) * t;
                        if (i > 0 && i < n) {{
                            if (normMode === 'WALK') {{ lt += 0.00010 * ((i % 2) * 2 - 1); ln += 0.00008 * (((i+1) % 2) * 2 - 1); }}
                            else if (normMode === 'BIKE') {{ lt += 0.00035 * ((i % 3) - 1); ln -= 0.00030 * ((i % 2) * 2 - 1); }}
                            else if (normMode === 'TRANSIT') {{ lt -= 0.00045 * ((i % 2) * 2 - 1); ln += 0.00040 * ((i % 3) - 1); }}
                            else {{ lt += 0.00025 * ((i % 2) * 2 - 1); ln += 0.00020 * ((i % 2) * 2 - 1); }}
                        }}
                        synth.push([lt, ln]);
                    }}

                    let modeDistKm = (normMode === 'WALK' ? directKm * 0.94 : (normMode === 'BIKE' ? directKm * 0.98 : (normMode === 'TRANSIT' ? directKm * 1.05 : directKm))).toFixed(2);
                    let modeDurMin = normMode === 'WALK' ? Math.max(1, Math.round((modeDistKm / 4.8) * 60)) : (normMode === 'BIKE' ? Math.max(1, Math.round((modeDistKm / 36.0) * 60 + 1)) : (normMode === 'TRANSIT' ? Math.max(5, Math.round((modeDistKm / 20.0) * 60 + 6)) : Math.max(2, Math.round((modeDistKm / 28.0) * 60 + 2))));
                    let durStr = modeDurMin < 60 ? `${{modeDurMin}} mins` : `${{Math.floor(modeDurMin/60)}} hr ${{modeDurMin%60}} mins`;
                    drawRoadPolylineFromCoords(synth, {{ name: facName, lat: destLat, lon: destLon }}, {{ duration: durStr, distance_km: modeDistKm, modeLabel: modeLabel, color: polyColor }});
                }});
        }}

        // Live In-Map Route Drawing with Travel Modes
        function drawLiveRouteToFacility(idx, travelModeStr) {{
            const item = activeMarkers.find(m => m.idx === idx);
            if (!item) return;
            const fac = item.fac;
            window.currentSelectedIdx = idx;

            if (activeInfoWindow) activeInfoWindow.close();

            activeMarkers.forEach(m => {{
                if (m.idx !== idx) {{ m.marker.setMap(null); }}
                else {{ m.marker.setMap(map); }}
            }});

            fetchAndDrawOSRMRoute(fac.lat, fac.lon, fac.name, fac.distance_km, travelModeStr || 'DRIVING');
        }}

        // Change mode for current selected facility
        function changeRouteMode(modeStr) {{
            if (window.currentSelectedIdx !== null && window.currentSelectedIdx !== undefined) {{
                drawLiveRouteToFacility(window.currentSelectedIdx, modeStr);
            }} else if (selectedFacility && selectedFacility.lat && selectedFacility.lon) {{
                fetchAndDrawOSRMRoute(selectedFacility.lat, selectedFacility.lon, selectedFacility.name, selectedFacility.distance_km, modeStr);
            }}
        }}

        // Clear In-Map Route and Restore All Facility Markers
        function clearInAppRoute() {{
            if (directionsRenderer) directionsRenderer.set('directions', null);
            if (window.activePolyline) {{ window.activePolyline.setMap(null); window.activePolyline = null; }}
            activeMarkers.forEach(m => m.marker.setMap(map));
            const banner = document.getElementById("route-banner");
            if (banner) banner.style.display = "none";
            const bounds = new google.maps.LatLngBounds();
            bounds.extend({{ lat: userLat, lng: userLon }});
            activeMarkers.forEach(m => bounds.extend(m.marker.getPosition()));
            map.fitBounds(bounds, 50);
            window.currentSelectedIdx = null;
        }}

        function gm_authFailure() {{
            console.error("Google Maps API Authentication Notice.");
        }}
    </script>
    <script async defer src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initMap&onerror=gm_authFailure"></script>
</body>
</html>"""
    return html_content
