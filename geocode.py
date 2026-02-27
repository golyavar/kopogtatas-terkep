import csv
import json
import os
import sys
import time
import urllib.request
import urllib.parse

ADDRESS_LIST = "address_list.csv"
CACHE_FILE = "geocoded_cache.json"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "kopogtatas-terkep/1.0"


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
    """Call Nominatim and return {lat, lon} or None if not found."""
    params = urllib.parse.urlencode({"q": address, "format": "json", "limit": 1})
    url = f"{NOMINATIM_URL}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    if data:
        return {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"])}
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
        time.sleep(1)

    print(f"\nDone. {len(cache)} addresses in cache.")
    if skipped:
        print(f"{len(skipped)} skipped (Nominatim could not resolve):")
        for addr in skipped:
            print(f"  - {addr}")


if __name__ == "__main__":
    main()
