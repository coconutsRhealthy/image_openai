import logging
import time

import config
from util.dedup import run_sweep

logging.basicConfig(level=logging.INFO, format="%(asctime)s | [dedup] %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    interval = config.DEDUP_SWEEP_INTERVAL_HOURS * 3600
    while True:
        logger.info("Starting dedup sweep")
        try:
            run_sweep()
        except Exception as e:
            logger.error(f"Dedup sweep failed: {e}")
        logger.info(f"Sleeping {config.DEDUP_SWEEP_INTERVAL_HOURS} hour(s)")
        time.sleep(interval)
