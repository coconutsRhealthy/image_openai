import json
import logging
import re
import statistics
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

from ai.analyzer import analyze_images
from util.new_promotion_exporter import export_new_promotion
from util.r2_image_utils import get_files_with_metadata_per_shop, make_image_url

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

FILESIZE_THRESHOLD = 15
ZSCORE_ENABLED = False
ZSCORE_THRESHOLD = 2.0
ZSCORE_WINDOW_DAYS = 7

ANALYZED_FILE = Path("/data/analyzed.json")
ANALYZED_RETENTION_DAYS = 10
FILENAME_DATE_REGEX = re.compile(r"_(\d{8})_\d{6}\.")

SPOTTED_PROMOTIONS_URL = "https://pub-a3be569620e4415b916e737210363aee.r2.dev/spotted_promotions.json"
SPOTTED_PROMOTIONS_WINDOW_DAYS = 7


def _load_spotted_promotions() -> dict:
    """Returns dict of lowercase shop name -> list of recent korting_text_nl strings."""
    try:
        response = requests.get(SPOTTED_PROMOTIONS_URL, timeout=10)
        response.raise_for_status()
        entries = response.json()
    except Exception as e:
        logger.warning(f"Could not load spotted_promotions.json: {e}")
        return {}

    cutoff = datetime.now() - timedelta(days=SPOTTED_PROMOTIONS_WINDOW_DAYS)
    result = {}
    for entry in entries:
        try:
            entry_date = datetime.strptime(entry["date"], "%Y-%m-%d %H:%M:%S")
        except (KeyError, ValueError):
            continue
        if entry_date < cutoff:
            continue
        shop = entry.get("webshop_name", "").lower()
        text = entry.get("korting_text_nl") or entry.get("korting_text")
        if shop and text:
            result.setdefault(shop, []).append(text)

    return result


def _load_analyzed() -> set:
    if not ANALYZED_FILE.exists():
        return set()
    try:
        return set(json.loads(ANALYZED_FILE.read_text()))
    except Exception:
        return set()


def _save_analyzed(analyzed: set):
    cutoff = datetime.now() - timedelta(days=ANALYZED_RETENTION_DAYS)
    pruned = {
        f for f in analyzed
        if (m := FILENAME_DATE_REGEX.search(f)) and datetime.strptime(m.group(1), "%Y%m%d") >= cutoff
    }
    ANALYZED_FILE.write_text(json.dumps(list(pruned), ensure_ascii=False))


def _z_score(files) -> "float | None":
    """Z-score of the latest file's size against the previous 7 days. Returns None if insufficient data."""
    if len(files) < 2:
        return None

    curr_dt, _, curr_size = files[-1]
    cutoff = curr_dt - timedelta(days=ZSCORE_WINDOW_DAYS)
    baseline = [size for dt, _, size in files[:-1] if dt >= cutoff]

    if len(baseline) < 3:
        return None

    mean = statistics.mean(baseline)
    stdev = statistics.stdev(baseline)

    if stdev == 0:
        return None

    return (curr_size - mean) / stdev


def _should_analyze(files, shop: str) -> bool:
    curr_dt, curr_filename, curr_size = files[-1]
    prev_dt, prev_filename, prev_size = files[-2]

    change_pct = abs(curr_size - prev_size) / prev_size * 100 if prev_size > 0 else None
    filesize_triggered = change_pct is not None and change_pct >= FILESIZE_THRESHOLD

    z = _z_score(files) if ZSCORE_ENABLED else None
    zscore_triggered = z is not None and abs(z) > ZSCORE_THRESHOLD

    if filesize_triggered or zscore_triggered:
        reasons = []
        if filesize_triggered:
            reasons.append(f"filesize +{change_pct:.1f}% (threshold {FILESIZE_THRESHOLD}%)")
        if zscore_triggered:
            reasons.append(f"z-score {z:.2f} (threshold ±{ZSCORE_THRESHOLD})")
        logger.info(f"[{shop}] Gating passed — {' | '.join(reasons)}")
        logger.info(f"  prev: {prev_filename} ({prev_size} bytes)")
        logger.info(f"  curr: {curr_filename} ({curr_size} bytes)")
        return True

    return False


def run():
    response = requests.get("https://pub-a3be569620e4415b916e737210363aee.r2.dev/webshops_info/webshop_info_export.json", timeout=10)
    response.raise_for_status()
    webshop_urls = {w["name"].lower(): w["url"] for w in response.json() if w.get("name") and w.get("url")}
    analyzed = _load_analyzed()
    spotted = _load_spotted_promotions()

    files_per_shop = get_files_with_metadata_per_shop()
    logger.info(f"{len(files_per_shop)} shops found in R2")

    for shop, files in files_per_shop.items():
        if len(files) < 2:
            continue

        _, curr_filename, _ = files[-1]

        if curr_filename in analyzed:
            continue

        if not _should_analyze(files, shop):
            continue

        _, prev_filename, _ = files[-2]

        recent = spotted.get(shop.lower(), [])
        logger.info(f"Analyzing {shop} ({curr_filename}) — {len(recent)} recent promotion(s) in context")
        result = analyze_images(make_image_url(prev_filename), make_image_url(curr_filename), recent)

        analyzed.add(curr_filename)
        _save_analyzed(analyzed)

        if result.get("has_new_promotion"):
            url = webshop_urls.get(shop.lower(), "-")
            export_new_promotion(shop, url, result)
            logger.info(f"New promotion at {shop}: {result.get('promo_nl_summ')}")


if __name__ == "__main__":
    while True:
        logger.info("Starting pipeline run")
        try:
            run()
        except Exception as e:
            logger.error(f"Pipeline run failed: {e}")
        logger.info("Sleeping 1 hour")
        time.sleep(3600)
