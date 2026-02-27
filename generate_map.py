import json
import os
import sys

CACHE_FILE = "geocoded_cache.json"
OUTPUT_HTML = "index.html"

MAP_CENTER_LAT = 46.37
MAP_CENTER_LON = 18.14
MAP_ZOOM = 12


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
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />
  <style>
    html, body, #map {{ height: 100%; margin: 0; padding: 0; }}
  </style>
</head>
<body>
  <div id="map"></div>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
  <script>
    var map = L.map('map').setView([{MAP_CENTER_LAT}, {MAP_CENTER_LON}], {MAP_ZOOM});

    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }}).addTo(map);

    var pins = {pins_json};

    var markers = L.markerClusterGroup();
    pins.forEach(function(pin) {{
      var el = document.createElement('span');
      el.textContent = pin.address;
      L.marker([pin.lat, pin.lon])
        .bindPopup(el)
        .addTo(markers);
    }});
    map.addLayer(markers);
  </script>
</body>
</html>"""

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Generated {OUTPUT_HTML} with {len(pins)} pins.")


if __name__ == "__main__":
    main()
