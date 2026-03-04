import json
import os
import sys

CACHE_FILE = "geocoded_cache.json"
OUTPUT_HTML = "index.html"
API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "YOUR_API_KEY")

# Tighter bounding box for Dombóvár centre
DOMBOVAR_SOUTH = 46.370
DOMBOVAR_NORTH = 46.389
DOMBOVAR_WEST = 18.121
DOMBOVAR_EAST = 18.166


def main():
    if not os.path.exists(CACHE_FILE):
        print(f"Error: {CACHE_FILE} not found. Run geocode.py first.")
        sys.exit(1)

    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        cache = json.load(f)

    if not cache:
        print(f"Error: {CACHE_FILE} is empty. Run geocode.py first.")
        sys.exit(1)

    pins = [
        {"lat": coords["lat"], "lon": coords["lon"], "address": address}
        for address, coords in cache.items()
    ]

    pins_json = json.dumps(pins, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="hu">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Kopogtatás térkép</title>
  <style>
    html, body, #map {{ height: 100%; margin: 0; padding: 0; }}
  </style>
</head>
<body>
  <div id="map"></div>
  <script>
    function initMap() {{
      var bounds = new google.maps.LatLngBounds(
        new google.maps.LatLng({DOMBOVAR_SOUTH}, {DOMBOVAR_WEST}),
        new google.maps.LatLng({DOMBOVAR_NORTH}, {DOMBOVAR_EAST})
      );

      var map = new google.maps.Map(document.getElementById('map'), {{
        mapId: 'kopogtat_s_t_rk_p',
      }});
      map.fitBounds(bounds);

      var houseIcon = {{
        path: 'M12 3L2 12h3v8h6v-6h2v6h6v-8h3L12 3z',
        fillColor: '#1a237e',
        fillOpacity: 1,
        strokeColor: '#0d1442',
        strokeWeight: 1,
        scale: 0.5,
        anchor: new google.maps.Point(12, 22),
      }};

      var pins = {pins_json};
      var infoWindow = new google.maps.InfoWindow();

      pins.forEach(function(pin) {{
        var marker = new google.maps.Marker({{
          position: {{ lat: pin.lat, lng: pin.lon }},
          map: map,
          icon: houseIcon,
          optimized: true,
        }});
        marker.addListener('click', function() {{
          infoWindow.setContent(pin.address);
          infoWindow.open(map, marker);
        }});
      }});
    }}
  </script>
  <script src="https://maps.googleapis.com/maps/api/js?key={API_KEY}&callback=initMap" async defer></script>
</body>
</html>"""

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Generated {OUTPUT_HTML} with {len(pins)} pins.")


if __name__ == "__main__":
    main()
