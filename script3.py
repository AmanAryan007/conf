import folium
import requests
import json
import time

# Define start and end coordinates
start_coords = (52.52, 13.405)  # Berlin start point
end_coords = (52.5159, 13.3777)  # Berlin end point

def fetch_route_coordinates(start, end):
    """Fetch route data from local OSRM server and return coordinates."""
    osrm_url = f"http://localhost:5000/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full&geometries=geojson"
    try:
        response = requests.get(osrm_url)
        response.raise_for_status()
        data = response.json()
        return data['routes'][0]['geometry']['coordinates']
    except requests.RequestException as e:
        print(f"Error fetching route data: {e}")
        return []

def update_map_with_coordinates(coordinates):
    """Create and save a Folium map with the given route coordinates."""
    # Create a Folium map centered between start and end points
    midpoint = ((start_coords[0] + end_coords[0]) / 2, (start_coords[1] + end_coords[1]) / 2)
    m = folium.Map(location=midpoint, zoom_start=15, tiles=None)
    folium.TileLayer(tiles="http://localhost:8080/styles/klokantech-basic/{z}/{x}/{y}.png", attr='offline map').add_to(m)
    folium.Marker(start_coords, tooltip='Start Point', icon=folium.Icon(color='green')).add_to(m)
    folium.Marker(end_coords, tooltip='End Point', icon=folium.Icon(color='red')).add_to(m)

    # Add a polyline for the route
    if coordinates:
        folium.PolyLine(locations=[(coord[1], coord[0]) for coord in coordinates], color='blue').add_to(m)

    # Add JavaScript to move a marker from start to end
    move_script = """
    <script>
        var map = L.map('map').setView([52.52, 13.405], 15);
        L.tileLayer('http://localhost:8080/styles/klokantech-basic/{z}/{x}/{y}.png', {
            attribution: 'offline map'
        }).addTo(map);

        var startCoords = [52.52, 13.405];
        var endCoords = [52.5159, 13.3777];
        var path = %s;
        var marker = L.marker(startCoords).addTo(map);
        var i = 0;

        function moveMarker() {
            if (i < path.length) {
                marker.setLatLng([path[i][1], path[i][0]]);
                i++;
            } else {
                i = 0; // Loop back to start
            }
            setTimeout(moveMarker, 1000); // Move marker every second
        }

        moveMarker();
    </script>
    """ % json.dumps(coordinates)

    # Save the map to an HTML file
    map_html_file = 'map.html'
    m.save(map_html_file)

    # Add meta tag for auto-refresh and JavaScript code
    with open(map_html_file, 'r') as file:
        html_content = file.read()

    # Inject meta tag for auto-refresh every second and JavaScript for moving marker
    meta_refresh = '<meta http-equiv="refresh" content="1">\n'
    script_tag = f'<script>{move_script}</script>\n'
    if '<head>' in html_content:
        html_content = html_content.replace('<head>', f'<head>\n{meta_refresh}')
    else:
        html_content = html_content.replace('<html>', f'<html>\n<head>\n{meta_refresh}</head>\n')

    # Inject JavaScript before the closing </body> tag
    if '</body>' in html_content:
        html_content = html_content.replace('</body>', f'{script_tag}</body>')
    else:
        html_content = html_content.replace('</html>', f'{script_tag}</html>')

    # Write the modified HTML back to the file
    with open(map_html_file, 'w') as file:
        file.write(html_content)

    print(f"Map has been saved to {map_html_file}")

def main_loop():
    global end_coords  # Declare end_coords as global
    while True:
        coordinates = fetch_route_coordinates(start_coords, end_coords)
        update_map_with_coordinates(coordinates)
        # Update coordinates slightly to simulate changes for demonstration
        end_coords = (end_coords[0] + 0.001, end_coords[1] + 0.001)
        time.sleep(5)  # Wait for 5 seconds before the next update

if __name__ == "__main__":
    main_loop()
