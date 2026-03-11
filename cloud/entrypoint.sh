#!/bin/bash
set -e

echo "$(date '+%Y-%m-%d %H:%M:%S') | Starting MySQL..."
mysqld_safe &

echo "$(date '+%Y-%m-%d %H:%M:%S') | Wachten tot MySQL opstart..."
while ! mysqladmin ping --silent; do
    sleep 1
done

echo "$(date '+%Y-%m-%d %H:%M:%S') | Creating database and app user..."
mysql -u root <<EOF
CREATE DATABASE IF NOT EXISTS py_diski_webshops;
CREATE USER IF NOT EXISTS 'appuser'@'localhost' IDENTIFIED BY 'app_password';
GRANT ALL PRIVILEGES ON py_diski_webshops.* TO 'appuser'@'localhost';
FLUSH PRIVILEGES;
EOF

echo "$(date '+%Y-%m-%d %H:%M:%S') | Starting hourly Python scripts..."
while true; do
    echo "$(date '+%Y-%m-%d %H:%M:%S') | Running run_pipeline_screenshot_analysis.py..."
    python run_pipeline_screenshot_analysis.py || echo "$(date '+%Y-%m-%d %H:%M:%S') | ERROR in run_pipeline_screenshot_analysis.py"

    echo "$(date '+%Y-%m-%d %H:%M:%S') | Running cool_new_pipeline.py..."
    python cool_new_pipeline.py || echo "$(date '+%Y-%m-%d %H:%M:%S') | ERROR in cool_new_pipeline.py"

    echo "$(date '+%Y-%m-%d %H:%M:%S') | Running cool_new_printer.py..."
    python cool_new_printer.py || echo "$(date '+%Y-%m-%d %H:%M:%S') | ERROR in cool_new_printer.py"

    echo "$(date '+%Y-%m-%d %H:%M:%S') | Waiting 1 hour before next run..."
    sleep 3600
done