#!/bin/bash
set -e

mkdir -p /data

echo "$(date '+%Y-%m-%d %H:%M:%S') | Starting pipeline..."
python pipeline.py
