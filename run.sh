#!/bin/bash
set -e
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi
echo "=== Step 1: Expanding addresses ==="
python3 convert_addresses.py
echo ""
echo "=== Step 2: Geocoding addresses ==="
python3 geocode.py
echo ""
echo "=== Step 3: Generating map ==="
python3 generate_map.py
echo ""
echo "=== Done! Open index.html to view the map ==="
