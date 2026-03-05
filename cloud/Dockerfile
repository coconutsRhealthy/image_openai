root@ubuntu-s-1vcpu-1gb-ams3-01:~/db# cat Dockerfile
# Gebruik een Python image
FROM python:3.12-slim

# Install MySQL server en client
RUN apt-get update && \
    apt-get install -y default-mysql-server default-mysql-client && \
    rm -rf /var/lib/apt/lists/*

# Werkdirectory
WORKDIR /app

# Kopieer bestanden
COPY init.sql .
COPY script.py .
COPY requirements.txt .

# Installeer Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose MySQL poort
EXPOSE 3306

# Voeg entrypoint script toe
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Start alles via entrypoint
ENTRYPOINT ["./entrypoint.sh"]