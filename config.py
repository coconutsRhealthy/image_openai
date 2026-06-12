import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4.1-mini"

R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")

SCREENSHOTS_BUCKET = "screenshots"
PROMOTIONS_BUCKET = "promotions"

# Duplicate sweep: a separate loop (dedup_sweep.py) periodically scans the newest
# DEDUP_RECENT_COUNT entries of spotted_promotions.json, asks the model to cluster
# same-offer promotions per webshop, and removes the later copy of any duplicate whose
# original was recorded less than DEDUP_WINDOW_DAYS before it.
DEDUP_ENABLED = True
DEDUP_RECENT_COUNT = 100
DEDUP_WINDOW_DAYS = 7
DEDUP_SWEEP_INTERVAL_HOURS = 8  # ~3x per day

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
