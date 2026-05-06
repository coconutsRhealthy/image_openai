#!/bin/bash
set -e

mkdir -p /data

echo "$(date '+%Y-%m-%d %H:%M:%S') | Starting bot and pipeline..."

python -m bot.main &
BOT_PID=$!

python pipeline.py &
PIPELINE_PID=$!

# Exit container if either process dies → Docker restart policy brings it back
wait -n $BOT_PID $PIPELINE_PID
exit $?
