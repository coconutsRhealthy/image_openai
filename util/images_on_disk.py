import os
from datetime import datetime
from collections import defaultdict

# ======================
# CONFIG
# ======================
ROOT_DIR = "/Users/lennartmac/Documents/ubuntu_mac_shared/screenshots"
START_DATE = "2026-01-01"
OUTPUT_FILE = "output_aaa_03.txt"

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")

# ======================
# HELPERS
# ======================
def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")


def extract_date_from_path(path):
    """
    Verwacht pad: webshop/jaar/maand/dag/filename.png
    """
    parts = path.split(os.sep)
    try:
        return datetime(int(parts[1]), int(parts[2]), int(parts[3]))
    except (IndexError, ValueError):
        return None


def extract_webshop_name(path):
    return path.split(os.sep)[0]


# ======================
# MAIN
# ======================
def main():
    start_date = parse_date(START_DATE)

    # webshop -> list van (datum, pad)
    webshop_files = defaultdict(list)

    for root, _, files in os.walk(ROOT_DIR):
        for filename in files:
            if not filename.lower().endswith(IMAGE_EXTENSIONS):
                continue

            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, ROOT_DIR)

            file_date = extract_date_from_path(rel_path)
            if not file_date or file_date < start_date:
                continue

            webshop = extract_webshop_name(rel_path)
            webshop_files[webshop].append((file_date, full_path))

    # schrijf output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for webshop in sorted(webshop_files.keys()):
            # sorteer chronologisch per webshop
            webshop_files[webshop].sort(key=lambda x: x[0])

            for file_date, path in webshop_files[webshop]:
                f.write(f"{webshop} - {path}\n")

    print(f"Klaar! {sum(len(v) for v in webshop_files.values())} regels geschreven naar {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
