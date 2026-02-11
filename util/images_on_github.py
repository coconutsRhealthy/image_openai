import requests
from datetime import datetime

# ======================
# CONFIG
# ======================
OWNER = "wgknl"
REPO = "screenshots"
BRANCH = "main"
START_DATE = "2026-01-01"
OUTPUT_FILE = "output_03.txt"

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")

BASE_API_URL = "https://api.github.com"

# ======================
# HELPERS
# ======================
def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")


def get_repo_tree():
    url = f"{BASE_API_URL}/repos/{OWNER}/{REPO}/git/trees/{BRANCH}?recursive=1"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()["tree"]


def extract_date_from_path(path):
    """
    Verwacht pad: webshop/jaar/maand/dag/filename.png
    Geeft datetime object terug
    """
    parts = path.split("/")
    try:
        year = int(parts[1])
        month = int(parts[2])
        day = int(parts[3])
        return datetime(year, month, day)
    except (IndexError, ValueError):
        return None  # pad volgt niet de verwachte structuur


def extract_webshop_name(path):
    return path.split("/")[0]


def build_raw_image_url(path):
    return f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/{path}"


# ======================
# MAIN
# ======================
def main():
    start_date = parse_date(START_DATE)
    tree = get_repo_tree()
    results = []

    for item in tree:
        if item["type"] != "blob":
            continue

        path = item["path"]
        if not path.lower().endswith(IMAGE_EXTENSIONS):
            continue

        file_date = extract_date_from_path(path)
        if not file_date:
            continue  # skip bestanden die niet in de juiste folderstructuur zitten

        if file_date >= start_date:
            webshop = extract_webshop_name(path)
            image_url = build_raw_image_url(path)
            results.append(f"{webshop} - {image_url}")

    # schrijf output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for line in results:
            f.write(line + "\n")

    print(f"Klaar! {len(results)} regels geschreven naar {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
