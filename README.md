# Kopogtatás térkép

Interaktív térkép, amely egy Google Sheet-ből származó címeket jelenít meg a térképen.

**Térkép megtekintése:** https://golyavar.github.io/kopogtatas-terkep/

**Google Sheet:** https://docs.google.com/spreadsheets/d/1N6Pv3u-4E8ZwFY6aySRjl4i0qtVu5IAgLrHLxN1Hww4/edit?gid=1244607183#gid=1244607183

## Működés

1. A Google Sheet-ben szerkesztés történik
2. Google Apps Script webhook-ot küld a GitHub-nak
3. GitHub Actions letölti a táblázatot, futtatja a feldolgozó pipeline-t
4. Az eredmény automatikusan megjelenik a térképen

## Helyi futtatás

```
cp .env.example .env  # GOOGLE_MAPS_API_KEY beállítása
./run.sh
```

## Pipeline

- `convert_addresses.py` — címek kibontása (házszámtartományok, páros/páratlan szűrés)
- `geocode.py` — geokódolás Google Maps API-val (cache-elve)
- `generate_map.py` — `index.html` generálása az összes jelölővel
