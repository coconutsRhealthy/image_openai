# Promotion detector — long-running container running the Telegram bot and the
# hourly pipeline side by side (see cloud/entrypoint.sh). Built from local files,
# NOT a git clone, so a redeploy ships exactly what's on disk. See cloud/DEPLOY.txt.
# Build (from repo root):  docker build -t eije2 .
FROM python:3.12-slim

WORKDIR /app

# requirements first so this pip layer is cached and only rebuilds when
# requirements.txt itself changes, not on every code edit.
COPY cloud/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime code only (.dockerignore keeps data/secrets/notes out of the context).
COPY config.py pipeline.py dedup_sweep.py ./
COPY ai ./ai
COPY bot ./bot
COPY util ./util
COPY cloud/entrypoint.sh ./cloud/entrypoint.sh
RUN chmod +x cloud/entrypoint.sh

# bot.main + pipeline.py write state to /data — mount a named volume there so it
# survives restarts/redeploys:  docker run -v promotions-json:/data ...
# Unbuffered stdout so `docker logs` shows each line live.
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["./cloud/entrypoint.sh"]
