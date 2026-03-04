# Kopogtatas Terkep — Project Spec

## Goal
Visualize all addresses from a Google Sheet on an interactive map, delivered as
a single shareable link that a non-technical person can click to view.
The map must auto-update whenever the input Google Sheet is edited.

---

## Phase 1 — Local (DONE)

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
- Digit-prefixed street names (e.g. "56-os forradalom tere") sort numerically before all others
- Roman numeral street names (e.g. "III. utca") sort numerically after digit-prefixed, before alphabetical streets

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

## Phase 2 — Cloud deployment (DONE — GitHub Actions + GitHub Pages)

### Status: FULLY OPERATIONAL
The end-to-end auto-update flow is working:
1. User edits Google Sheet
2. Apps Script onChange trigger fires → sends webhook to GitHub
3. GitHub Actions downloads sheet, runs pipeline, commits results
4. Push to main → GitHub Pages auto-deploys updated map

### Map URL
https://golyavar.github.io/kopogtatas-terkep/

### Overview
- Google Sheet is the data source (shared as "Anyone with the link can view")
- Google Apps Script installable `onChange` trigger sends a webhook to GitHub Actions
- GitHub Actions downloads the sheet as CSV, runs the Python pipeline, commits to main
- GitHub Pages auto-deploys on push to main
- Map is publicly accessible at the GitHub Pages URL (no login needed)
- Repo hosted under the `golyavar` GitHub organization (separate from personal profile)
- Any editor of the Google Sheet triggers an update (not just the owner)

### GitHub Actions workflow (`.github/workflows/deploy.yml`)
- Triggers: `repository_dispatch` (from Apps Script webhook) + `workflow_dispatch` (manual)
- Downloads Google Sheet as CSV: `https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv`
- Runs: `convert_addresses.py` → `geocode.py` → `generate_map.py`
- Commits updated `geocoded_cache.json` and `index.html` to main
- Cleans up intermediate files (input.csv, address_list.csv) before pull to avoid rebase conflicts
- GitHub Pages auto-deploys on push to main

### Google Apps Script (bound to the Google Sheet)
```javascript
function onEdit(e) {
  var token = PropertiesService.getScriptProperties().getProperty('GITHUB_PAT');
  UrlFetchApp.fetch(
    'https://api.github.com/repos/golyavar/kopogtatas-terkep/dispatches',
    {
      method: 'post',
      headers: {
        'Authorization': 'token ' + token,
        'Accept': 'application/vnd.github.v3+json'
      },
      payload: JSON.stringify({ event_type: 'sheet-updated' }),
      contentType: 'application/json'
    }
  );
}
```
Note: Must use an **installable** onChange trigger (not simple onEdit) so it fires
for all editors, not just the script owner. Set up via Apps Script → Triggers → Add Trigger.

### Required secrets
| Secret | Where | Purpose |
|--------|-------|---------|
| `GOOGLE_MAPS_API_KEY` | GitHub repo secret | Geocoding + Maps JS API |
| `GOOGLE_SHEET_ID` | GitHub repo secret | Identifies the source sheet |
| `GITHUB_PAT` | Google Apps Script property | Auth for webhook |

### Setup steps
1. Create a GitHub organization (e.g. `golyavar`) and transfer the repo to it
2. Make the repo public and enable GitHub Pages (Settings → Pages → main branch, root)
3. GitHub repo → Settings → Secrets → add `GOOGLE_MAPS_API_KEY` and `GOOGLE_SHEET_ID`
4. Create a GitHub PAT (fine-grained, scoped to the org repo)
5. Google Sheet → Extensions → Apps Script → paste the onEdit function above
6. Apps Script → Project Settings → Script Properties → add `GITHUB_PAT`
7. Apps Script → Triggers → Add → onChange (installable, catches all edits)
8. Restrict Google Maps API key to the GitHub Pages domain in Google Cloud Console
9. Run workflow manually once (`workflow_dispatch`) to verify

---

## Data

### input.csv columns
- Település — city (Dombóvár only — other cities were removed from the source sheet)
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
- Library: Google Maps JavaScript API (loaded from CDN)
- Map ID: kopogtat_s_t_rk_p (custom styled map)
- Custom house icon (SVG path, dark blue #1a237e, scale 0.5, optimized: true for canvas rendering)
- Geocoding API: Google Geocoding API (build-time only)
- Pin popup content: full address (Megjegyzés not shown for now)
- All pin data embedded as a JS array in the HTML (no runtime geocoding calls)
- Must be a single self-contained file a non-technical user can open via one link
- Initial view: fitted to Dombóvár bounding box (46.370–46.389°N, 18.121–18.166°E)

---

## Existing files
- input.csv                          — source address data [gitignored, downloaded from Sheet in CI]
- convert_addresses.py               — Step 1: expands ranges, respects Oldal, produces address_list.csv
- address_list.csv                   — expanded address list
- geocode.py                         — Step 2: reads address_list.csv, geocodes via Google API, produces cache
- geocoded_cache.json                — persistent geocoding cache (committed for CI persistence)
- generate_map.py                    — Step 3: reads cache, produces index.html
- index.html                         — output map (created by generate_map.py)
- run.sh                             — runs all 3 steps in sequence (local use)
- .github/workflows/deploy.yml       — GitHub Actions: download sheet → pipeline → commit → GitHub Pages auto-deploys
- .env                               — local env vars (GOOGLE_MAPS_API_KEY) [gitignored]
- spec.md                            — project specification (this file)
- progress.txt                       — detailed progress tracking, architecture notes, and changelog
