#!/bin/bash
set -e

mysqld_safe &

echo "Wachten tot MySQL opstart..."
while ! mysqladmin ping --silent; do
    sleep 1
done

echo "Database configureren..."

# Database aanmaken
mysql -u root <<EOF
CREATE DATABASE IF NOT EXISTS mydb;
CREATE USER IF NOT EXISTS 'appuser'@'localhost' IDENTIFIED BY 'app_password';
GRANT ALL PRIVILEGES ON mydb.* TO 'appuser'@'localhost';
FLUSH PRIVILEGES;
EOF

# Init SQL uitvoeren
mysql -u root mydb < init.sql

echo "Start Python script..."
python script.py