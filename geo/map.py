import folium

def build_plan_trip_map(locations):
    if not locations:
        return "<p>No locations to map</p>"
        
    start_lat = locations[0]["estimated_coordinates"]["latitude"]
    start_lon = locations[0]["estimated_coordinates"]["longitude"]
    
    m = folium.Map(location=[start_lat, start_lon], zoom_start=13)
    
    for loc in locations:
        folium.Marker(
            location=[loc["estimated_coordinates"]["latitude"], loc["estimated_coordinates"]["longitude"]], # Comma added!
            popup=loc['name'],
            tooltip="Click for more info",
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)
        
    map_html = m._repr_html_()
    return map_html