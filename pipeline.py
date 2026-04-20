import logging
import time

from ai.analyzer import analyze_images
from util.new_promotion_exporter import export_new_promotion
from util.r2_image_utils import get_files_with_metadata_per_shop, download_image_bytes
from util.webshops_info_manager import load_webshop_info, update_webshops

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

FILESIZE_THRESHOLD = 15


def run():
    update_webshops()
    webshop_urls = load_webshop_info()

    files_per_shop = get_files_with_metadata_per_shop()
    logger.info(f"{len(files_per_shop)} shops found in R2")

    for shop, files in files_per_shop.items():
        if len(files) < 2:
            continue

        prev_dt, prev_filename, prev_size = files[-2]
        curr_dt, curr_filename, curr_size = files[-1]

        if prev_size > 0:
            change_pct = abs(curr_size - prev_size) / prev_size * 100
            if change_pct < FILESIZE_THRESHOLD:
                continue

        logger.info(f"Analyzing {shop} ({curr_filename})")
        try:
            today_bytes = download_image_bytes(curr_filename)
            yesterday_bytes = download_image_bytes(prev_filename)
        except Exception as e:
            logger.warning(f"Could not download images for {shop}: {e}")
            continue

        result = analyze_images(today_bytes, yesterday_bytes)

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
