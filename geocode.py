import csv
import json
import os
import sys
import urllib.request
import urllib.parse

ADDRESS_LIST = "address_list.csv"
CACHE_FILE = "geocoded_cache.json"
GOOGLE_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")


def load_addresses(address_list_csv):
    """Read address_list.csv (produced by convert_addresses.py) and return
    a deduplicated list of full address strings from the 'Teljes cím' column."""
    if not os.path.exists(address_list_csv):
        print(f"Error: {address_list_csv} not found. Run convert_addresses.py first.")
        sys.exit(1)
    seen = set()
    addresses = []
    with open(address_list_csv, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            addr = row["Teljes cím"]
            if addr not in seen:
                seen.add(addr)
                addresses.append(addr)
    return addresses


def geocode_address(address):
    """Call Google Geocoding API and return {lat, lon} or None if not found."""
    if not API_KEY:
        print("Error: GOOGLE_MAPS_API_KEY not set.")
        sys.exit(1)
    params = urllib.parse.urlencode({"address": address, "key": API_KEY})
    url = f"{GOOGLE_GEOCODE_URL}?{params}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    if data["status"] == "OK" and data["results"]:
        loc = data["results"][0]["geometry"]["location"]
        return {"lat": loc["lat"], "lon": loc["lng"]}
    return None


def load_cache():
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def main():
    addresses = load_addresses(ADDRESS_LIST)
    print(f"Total addresses: {len(addresses)}")

    cache = load_cache()
    pending = [a for a in addresses if a not in cache]
    print(f"Already cached: {len(cache)}  |  To geocode: {len(pending)}")

    if not pending:
        print("Nothing to do.")
        return

    skipped = []
    for i, address in enumerate(pending, 1):
        print(f"[{i}/{len(pending)}] {address}", end=" ... ", flush=True)
        try:
            result = geocode_address(address)
            if result:
                cache[address] = result
                print(f"OK ({result['lat']:.5f}, {result['lon']:.5f})")
            else:
                skipped.append(address)
                print("NOT FOUND (skipped)")
        except Exception as e:
            skipped.append(address)
            print(f"ERROR: {e} (skipped)")

        save_cache(cache)

    print(f"\nDone. {len(cache)} addresses in cache.")
    if skipped:
        print(f"{len(skipped)} skipped (Google could not resolve):")
        for addr in skipped:
            print(f"  - {addr}")


if __name__ == "__main__":
    main()
