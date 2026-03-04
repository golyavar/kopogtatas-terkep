# Knocking Map (Kopogtatás térkép)

Interactive map showing door-to-door canvassing addresses in Dombóvár, Hungary. Auto-updates from a Google Sheet via GitHub Actions.

**View the map:** https://golyavar.github.io/kopogtatas-terkep/

**Google Sheet:** https://docs.google.com/spreadsheets/d/1N6Pv3u-4E8ZwFY6aySRjl4i0qtVu5IAgLrHLxN1Hww4/edit?gid=1244607183#gid=1244607183

## How it works

1. An address is edited in the Google Sheet
2. Google Apps Script sends a webhook to GitHub
3. GitHub Actions downloads the sheet and runs the processing pipeline
4. The updated map is automatically deployed to GitHub Pages

## Local setup

```
cp .env.example .env  # Set GOOGLE_MAPS_API_KEY
./run.sh
```

## Pipeline

- `convert_addresses.py` — Expand address ranges, filter by side (odd/even)
- `geocode.py` — Geocode addresses via Google Maps API (cached)
- `generate_map.py` — Generate `index.html` with all map markers
