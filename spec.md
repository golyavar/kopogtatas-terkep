# Kopogtatas Terkep — Project Spec

## Goal
Visualize all addresses from a Google Sheet on an interactive map, delivered as
a single shareable link that a non-technical person can click to view.
The map must auto-update whenever the input Google Sheet is edited.

---

## Phase 1 — Local (current focus)

Build and test the full pipeline locally using input.csv as the data source.

### Step 1: convert_addresses.py
- Read input.csv
- Expand house number ranges into individual addresses
- Respect the Oldal column: páratlan → only odd numbers, páros → only even numbers
- Non-numeric entries (e.g. "2A") are always kept regardless of Oldal
- Rows with empty Házszámok are skipped
- Output includes Oldal column (páratlan/páros) carried over from input
- Output sorted by Település → Utca → Oldal (páratlan first) → Házszám (numerically)
- Sorting respects Hungarian alphabet (Á after A, É after E, digraphs CS/SZ/GY etc.)
- Roman numeral street names (e.g. "III. utca") sort numerically before alphabetical streets

Input:  input.csv
Output: address_list.csv (the expanded address list — becomes a Google Sheet in Phase 2)

### Step 2: geocode.py
- Read address_list.csv (produced by Step 1)
- Deduplicate addresses
- Load geocoded_cache.json (create if missing)
- For each address not already in the cache: call Nominatim API to get lat/lon
- Save the updated geocoded_cache.json after each address (so progress isn't lost on crash)
- Skip addresses Nominatim cannot resolve (log them, don't crash)
- Respect Nominatim's rate limit: 1 request/second, include a User-Agent header

Input:  address_list.csv
Output: geocoded_cache.json

### Step 3: generate_map.py
- Read geocoded_cache.json
- Generate a single self-contained index.html

Input:  geocoded_cache.json
Output: index.html

### Run order
```
./run.sh
```
or individually:
```
python convert_addresses.py
python geocode.py
python generate_map.py
```

---

## Phase 2 — Cloud (backlog, do not build yet)

Once Phase 1 is tested and working, port to Google Apps Script:
- Trigger: onEdit / onChange on the Google Sheet
- Cache stored as geocoded_cache.json on Google Drive
- Output index.html written to Google Drive (public share link)
- Chunked geocoding to handle Apps Script's 6-minute execution limit:
  - Save pending address queue + progress in PropertiesService
  - Geocode ~50 addresses per run (~50 sec)
  - Self-schedule a 1-minute time trigger to continue until done
  - On final chunk: regenerate HTML, delete trigger, clear state
  - If sheet is edited mid-process: merge new addresses into queue, don't restart

---

## Data

### input.csv columns
- Település — city (e.g. Dombóvár, Alsónána), all in Hungary
- Utca — street name
- Oldal — side of street (páros = even, páratlan = odd)
- Házszámok — house numbers; may be ranges like "1-13, 17" or empty (skip if empty)
- Megjegyzés — notes

### Address expansion
Ranges like "1-13, 17" on a páratlan (odd) row expand to: 1, 3, 5, 7, 9, 11, 13, 17.
The Oldal column filters which numbers are kept:
- páratlan → only odd house numbers from ranges
- páros → only even house numbers from ranges
- Non-numeric entries (e.g. "2A") are always kept regardless of Oldal.
Full address string format: "{Utca} {Házszám}, {Település}, Hungary"
~1,906 input rows (55 with house numbers) → **618 unique addresses** after expansion.
Rows with empty Házszámok are skipped (these are streets without specific house data).

### geocoded_cache.json format
```json
{
  "Ady Endre utca 1, Dombóvár, Hungary": { "lat": 46.123, "lon": 18.456 },
  ...
}
```

---

## Map (index.html) spec
- Library: Leaflet.js (loaded from CDN)
- Tiles: OpenStreetMap (no API key needed)
- Clustering: Leaflet.markercluster plugin (pins cluster when zoomed out)
- Pin popup content: full address (Megjegyzés not shown for now)
- All pin data embedded as a JS array in the HTML (no runtime API calls)
- Must be a single self-contained file a non-technical user can open via one link
- Initial view: fixed center 46.37°N 18.14°E (Dombóvár area), zoom 12

---

## Existing files
- input.csv             — source address data
- convert_addresses.py  — Step 1: expands ranges, respects Oldal, produces address_list.csv
- address_list.csv      — expanded address list (output of Step 1; becomes a Google Sheet in Phase 2)
- geocode.py            — Step 2: reads address_list.csv, geocodes via Nominatim, produces cache
- geocoded_cache.json   — persistent geocoding cache (created by geocode.py)
- generate_map.py       — Step 3: reads cache, produces index.html
- index.html            — output map (created by generate_map.py)
- run.sh                — runs all 3 steps in sequence
- spec.md               — project specification (this file)
- progress.txt          — detailed progress tracking, architecture notes, and changelog
