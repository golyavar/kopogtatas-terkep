import csv
import re
import sys
import os

def expand_numbers(házszámok_str, oldal=None):
    """Expand '1-13, 17, 2A, 6-8' into individual house numbers.

    Args:
        házszámok_str: Comma-separated house numbers/ranges (e.g. "1-13, 17").
        oldal: Optional side filter — "páratlan" keeps only odd numbers,
               "páros" keeps only even numbers. Non-numeric entries (e.g. "2A")
               are always kept regardless of oldal.
    """
    if not házszámok_str or not házszámok_str.strip():
        return []
    results = []
    parts = [p.strip() for p in házszámok_str.split(',')]
    for part in parts:
        if not part:
            continue
        range_match = re.match(r'^(\d+)-(\d+)$', part)
        if range_match:
            start, end = int(range_match.group(1)), int(range_match.group(2))
            for n in range(start, end + 1):
                if oldal == 'páratlan' and n % 2 == 0:
                    continue
                if oldal == 'páros' and n % 2 == 1:
                    continue
                results.append(str(n))
        else:
            results.append(part)
    return results


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
    # Replace Roman numeral tokens with their numeric value for sorting.
    # Handles both "III. utca" and "Pincesor III." patterns.
    def replace_roman(m):
        return str(roman_to_int(m.group(1))).zfill(4)
    utca_sort = re.sub(r'\b([IVXLCDM]+)\.', replace_roman, utca)

    # Sort house number numerically (non-numeric like "2A" sorts after pure numbers)
    házszám = row["Házszám"]
    num_match = re.match(r'^(\d+)', házszám)
    házszám_num = int(num_match.group(1)) if num_match else float('inf')

    # páratlan (odd) sorts before páros (even)
    oldal_order = 0 if row.get("Oldal") == "páratlan" else 1

    return (row["Település"], utca_sort, oldal_order, házszám_num, házszám)


def expand_addresses(input_file, output_file):
    rows_out = []

    with open(input_file, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            házszámok = row.get("Házszámok", "").strip()
            if not házszámok:
                continue
            oldal = row.get("Oldal", "").strip()
            for num in expand_numbers(házszámok, oldal):
                rows_out.append({
                    "Település": row["Település"],
                    "Utca": row["Utca"],
                    "Oldal": oldal,
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
