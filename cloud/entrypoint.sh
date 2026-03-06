#!/bin/bash
set -e

echo "Starting MySQL..."
mysqld_safe &

echo "Wachten tot MySQL opstart..."
while ! mysqladmin ping --silent; do
    sleep 1
done

echo "Creating database and app user..."
mysql -u root <<EOF
CREATE DATABASE IF NOT EXISTS py_diski_webshops;
CREATE USER IF NOT EXISTS 'appuser'@'localhost' IDENTIFIED BY 'app_password';
GRANT ALL PRIVILEGES ON py_diski_webshops.* TO 'appuser'@'localhost';
FLUSH PRIVILEGES;
EOF

echo "Downloading R2 dump..."
curl -L -o dump.sql https://pub-bf3c129fe9d64e8695d474075e0dfcc6.r2.dev/py_diski_webshops_test_container.sql

echo "Importing dump into MySQL..."
mysql -u root py_diski_webshops < dump.sql

echo "Running Python scripts..."
python run_pipeline_screenshot_analysis.py

# Keep container alive (optioneel)
tail -f /dev/null