"""
    Map visualization with OpenStreetMap and Folium
Supports interactive routing polylines, selected single-facility view, and multi-facility exploration.
"""
import folium

def render_healthcare_map(user_lat, user_lon, facilities, location_name="Your Location", selected_facility=None, route_data=None):
    """
    Generate a Folium interactive map with:
      - High-visibility user location marker & radar radius
      - Nearby healthcare markers
      - Dynamic turn-by-turn road route polyline (when a single facility is selected)
    """
    # Determine map center
    if selected_facility:
        dest_lat = selected_facility.get("lat", user_lat)
        dest_lon = selected_facility.get("lon", user_lon)
        center_lat = (user_lat + dest_lat) / 2.0
        center_lon = (user_lon + dest_lon) / 2.0
        zoom = 14
    else:
        center_lat = user_lat
        center_lon = user_lon
        zoom = 14

    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, tiles="OpenStreetMap")

    # User Marker (High-Visibility Red Pin)
    folium.Marker(
        location=[user_lat, user_lon],
        popup=f"<b>Your Location</b><br/>{location_name}",
        tooltip=f"You Are Here ({user_lat:.4f}, {user_lon:.4f})",
        icon=folium.Icon(color="red", icon="dot-circle-o", prefix="fa")
    ).add_to(m)

    # Facility Icons & Colors
    icon_map = {
        "Hospital": ("blue", "hospital-o"),
        "24/7 Emergency Hospital": ("red", "ambulance"),
        "Pharmacy": ("green", "plus-square"),
        "Clinic": ("orange", "medkit"),
        "Diagnostic": ("purple", "flask"),
        "Blood_bank": ("darkred", "tint"),
        "Blood bank": ("darkred", "tint")
    }

    # If a specific facility is selected for routing
    if selected_facility:
        ftype = selected_facility.get("type", "Hospital")
        color, icon_name = icon_map.get(ftype, ("blue", "hospital-o"))
        dist = selected_facility.get("distance_km", 0)
        phone = selected_facility.get("phone", "108 / Local Desk")
        address = selected_facility.get("address", "")
        name = selected_facility.get("name", "Healthcare Facility")

        popup_html = f"""
        <div style="font-family: sans-serif; min-width: 190px;">
            <h4 style="margin: 0 0 5px 0; color: #2563EB;"> {name}</h4>
            <span style="background: #E0F2FE; color: #2563EB; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold;">{ftype}</span>
            <p style="margin: 6px 0 3px 0; font-size: 12px; color: #475569;"> {address}</p>
            <p style="margin: 3px 0; font-size: 12px; color: #0284c7;"><b>Distance:</b> {dist} km</p>
            <p style="margin: 3px 0; font-size: 12px; color: #16a34a;"><b>Phone:</b> {phone}</p>
        </div>
        """
        folium.Marker(
            location=[selected_facility["lat"], selected_facility["lon"]],
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"Destination: {name} ({dist} km)",
            icon=folium.Icon(color=color, icon=icon_name, prefix="fa")
        ).add_to(m)

        # Draw road navigation polyline if route data is available
        if route_data and route_data.get("route_coordinates"):
            folium.PolyLine(
                locations=route_data["route_coordinates"],
                color="#2563EB",
                weight=6,
                opacity=0.85,
                tooltip=f"{route_data.get('mode', 'driving').capitalize()} Route: {route_data.get('distance_km')} km (~{route_data.get('duration_min')} mins)"
            ).add_to(m)

    else:
        # Show all facilities within radius
        folium.Circle(
            location=[user_lat, user_lon],
            radius=1500,
            color="#2563EB",
            fill=True,
            fill_color="#2563EB",
            fill_opacity=0.06,
            tooltip="Nearby Care Radius (1.5 km)"
        ).add_to(m)

        for fac in facilities:
            ftype = fac.get("type", "Hospital")
            color, icon_name = icon_map.get(ftype, ("blue", "hospital-o"))
            dist = fac.get("distance_km", 0)
            phone = fac.get("phone", "108 / Desk")
            address = fac.get("address", "")
            name = fac.get("name", "Healthcare Facility")

            popup_html = f"""
            <div style="font-family: sans-serif; min-width: 190px;">
                <h4 style="margin: 0 0 5px 0; color: #0f172a;">{name}</h4>
                <span style="background: #e2e8f0; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold;">{ftype}</span>
                <p style="margin: 6px 0 3px 0; font-size: 12px; color: #475569;"> {address}</p>
                <p style="margin: 3px 0; font-size: 12px; color: #0284c7;"><b>Distance:</b> {dist} km</p>
                <p style="margin: 3px 0; font-size: 12px; color: #16a34a;"><b>Phone:</b> {phone}</p>
            </div>
            """
            folium.Marker(
                location=[fac["lat"], fac["lon"]],
                popup=folium.Popup(popup_html, max_width=260),
                tooltip=f"{name} ({dist} km)",
                icon=folium.Icon(color=color, icon=icon_name, prefix="fa")
            ).add_to(m)

    return m
