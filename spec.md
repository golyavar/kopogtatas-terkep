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

## Phase 2 — Cloud deployment (GitHub Actions + Netlify)

### Overview
- Google Sheet is the data source (shared as "Anyone with the link can view")
- Google Apps Script `onEdit` trigger sends a webhook to GitHub Actions
- GitHub Actions downloads the sheet as CSV, runs the Python pipeline, deploys to Netlify
- Map is publicly accessible at the Netlify site URL (no login needed)
- GitHub repo stays **private** (Netlify works with private repos, unlike GitHub Pages free tier)

### GitHub Actions workflow (`.github/workflows/deploy.yml`)
- Triggers: `repository_dispatch` (from Apps Script webhook) + `workflow_dispatch` (manual)
- Downloads Google Sheet as CSV: `https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv`
- Runs: `convert_addresses.py` → `geocode.py` → `generate_map.py`
- Commits updated `geocoded_cache.json` to main (cache persists across runs)
- Commits updated `index.html` to main → Netlify auto-deploys on push

### Google Apps Script (bound to the Google Sheet)
```javascript
function onEdit(e) {
  var token = PropertiesService.getScriptProperties().getProperty('GITHUB_PAT');
  UrlFetchApp.fetch(
    'https://api.github.com/repos/davidpalfi/kopogtatas-terkep/dispatches',
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
Note: Use an **installable** onChange trigger for edits by other users.

### Required secrets
| Secret | Where | Purpose |
|--------|-------|---------|
| `GOOGLE_MAPS_API_KEY` | GitHub repo secret | Geocoding + Maps JS API |
| `GOOGLE_SHEET_ID` | GitHub repo secret | Identifies the source sheet |
| `GITHUB_PAT` | Google Apps Script property | Auth for webhook |

### Setup steps
1. Create a free Netlify account and connect the GitHub repo (Netlify auto-deploys on push)
2. GitHub repo → Settings → Secrets → add `GOOGLE_MAPS_API_KEY` and `GOOGLE_SHEET_ID`
3. Create a GitHub PAT (fine-grained, repo scope for this repo only)
4. Google Sheet → Extensions → Apps Script → paste the onEdit function above
5. Apps Script → Project Settings → Script Properties → add `GITHUB_PAT`
6. Apps Script → Triggers → Add → onChange (installable, catches all edits)
7. Restrict Google Maps API key to the Netlify site domain in Google Cloud Console
8. Run workflow manually once (`workflow_dispatch`) to verify

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
- Library: Google Maps JavaScript API (loaded from CDN)
- Map ID: kopogtat_s_t_rk_p (custom styled map)
- Custom house icon (SVG path, dark blue #1a237e)
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
- .github/workflows/deploy.yml       — GitHub Actions: download sheet → pipeline → deploy to Netlify
- .env                               — local env vars (GOOGLE_MAPS_API_KEY) [gitignored]
- spec.md                            — project specification (this file)
- progress.txt                       — detailed progress tracking, architecture notes, and changelog
