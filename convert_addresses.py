import csv
import re
import sys
import os

def expand_numbers(house_numbers_str, side=None):
    """Expand '1-13, 17, 2A, 6-8' into individual house numbers.

    Args:
        house_numbers_str: Comma-separated house numbers/ranges (e.g. "1-13, 17").
        side: Optional side filter — "páratlan" keeps only odd numbers,
              "páros" keeps only even numbers. Non-numeric entries (e.g. "2A")
              are always kept regardless of side.
    """
    if not house_numbers_str or not house_numbers_str.strip():
        return []
    results = []
    parts = [p.strip() for p in house_numbers_str.split(',')]
    for part in parts:
        if not part:
            continue
        range_match = re.match(r'^(\d+)-(\d+)$', part)
        if range_match:
            start, end = int(range_match.group(1)), int(range_match.group(2))
            for n in range(start, end + 1):
                if side == 'páratlan' and n % 2 == 0:
                    continue
                if side == 'páros' and n % 2 == 1:
                    continue
                results.append(str(n))
        else:
            results.append(part)
    return results


# Hungarian alphabet order (digraphs are single letters in Hungarian).
# Each entry maps to a sort key that preserves correct order.
_HU_ORDER = [
    'a', 'á', 'b', 'c', 'cs', 'd', 'dz', 'dzs', 'e', 'é',
    'f', 'g', 'gy', 'h', 'i', 'í', 'j', 'k', 'l', 'ly',
    'm', 'n', 'ny', 'o', 'ó', 'ö', 'ő', 'p', 'q', 'r',
    's', 'sz', 't', 'ty', 'u', 'ú', 'ü', 'ű', 'v', 'w',
    'x', 'y', 'z', 'zs',
]
_HU_MAP = {ch: f"{i:02d}" for i, ch in enumerate(_HU_ORDER)}


def hungarian_sort_key(s):
    """Convert a string to a sort key respecting Hungarian alphabetical order."""
    result = []
    i = 0
    low = s.lower()
    while i < len(low):
        matched = False
        # Try 3-char then 2-char digraphs first (dzs before dz, sz before s, etc.)
        for length in (3, 2):
            chunk = low[i:i+length]
            if chunk in _HU_MAP:
                result.append(_HU_MAP[chunk])
                i += length
                matched = True
                break
        if not matched:
            ch = low[i]
            if ch in _HU_MAP:
                result.append(_HU_MAP[ch])
            else:
                # Non-letter characters (spaces, digits, punctuation) sort by ordinal
                result.append(ch)
            i += 1
    return ''.join(result)


ROMAN_VALUES = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}


def roman_to_int(s):
    """Convert a Roman numeral string to an integer. Returns 0 if invalid."""
    total = 0
    prev = 0
    for ch in reversed(s):
        val = ROMAN_VALUES.get(ch, 0)
        if not val:
            return 0
        if val < prev:
            total -= val
        else:
            total += val
        prev = val
    return total


def sort_key(row):
    """Sort by Település, then Utca (with Roman numerals as numbers), then Házszám numerically."""
    utca = row["Utca"]

    # Sort order: digit-prefixed (-1) < Roman numeral (0) < alphabetical (1)
    digit_m = re.match(r'^(\d+)(.*)', utca)
    if digit_m:
        # "56-os forradalom tere" → sort by leading number, then suffix
        utca_key = (-1, int(digit_m.group(1)), hungarian_sort_key(digit_m.group(2).strip()))
    else:
        m = re.match(r'^([IVXLCDM]+)\.\s*(.*)', utca)
        if m:
            # Prefix pattern: "III. utca" → sort by numeric value, then suffix
            utca_key = (0, roman_to_int(m.group(1)), hungarian_sort_key(m.group(2) or ''))
        else:
            m2 = re.search(r'\b([IVXLCDM]+)\.$', utca)
            if m2:
                # Suffix pattern: "Pincesor III." → sort by prefix, then numeric value
                prefix = utca[:m2.start()].strip()
                utca_key = (1, hungarian_sort_key(prefix), roman_to_int(m2.group(1)))
            else:
                utca_key = (1, hungarian_sort_key(utca), 0)

    # Sort house number numerically (non-numeric like "2A" sorts after pure numbers)
    house_number = row["Házszám"]
    num_match = re.match(r'^(\d+)', house_number)
    house_number_num = int(num_match.group(1)) if num_match else float('inf')

    # páratlan (odd) sorts before páros (even)
    side_order = 0 if row.get("Oldal") == "páratlan" else 1

    return (hungarian_sort_key(row["Település"]), utca_key,
            side_order, house_number_num, house_number)


def expand_addresses(input_file, output_file):
    rows_out = []

    with open(input_file, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            house_numbers = row.get("Házszámok", "").strip()
            if not house_numbers:
                continue
            side = row.get("Oldal", "").strip()
            for num in expand_numbers(house_numbers, side):
                rows_out.append({
                    "Település": row["Település"],
                    "Utca": row["Utca"],
                    "Oldal": side,
                    "Házszám": num,
                    "Teljes cím": f"{row['Utca']} {num}, {row['Település']}, Hungary",
                    "Megjegyzés": row.get("Megjegyzés", "")
                })

    rows_out.sort(key=sort_key)

    with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["Település", "Utca", "Oldal", "Házszám", "Teljes cím", "Megjegyzés"])
        writer.writeheader()
        writer.writerows(rows_out)

    print(f"Done! {len(rows_out)} addresses written to {output_file}")


if __name__ == "__main__":
    if len(sys.argv) == 3:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
    elif len(sys.argv) == 2:
        input_file = sys.argv[1]
        output_file = os.path.splitext(input_file)[0] + "_expanded.csv"
    else:
        input_file = "input.csv"
        output_file = "address_list.csv"

    if not os.path.exists(input_file):
        print(f"Error: input file '{input_file}' not found.")
        sys.exit(1)

    expand_addresses(input_file, output_file)
