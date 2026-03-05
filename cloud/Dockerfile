# Gebruik een Python image
FROM python:3.12-slim

# Install MySQL server en client
RUN apt-get update && \
    apt-get install -y default-mysql-server default-mysql-client curl && \
    rm -rf /var/lib/apt/lists/*

# Werkdirectory
WORKDIR /app

# Kopieer bestanden
COPY init.sql .
COPY requirements.txt .

# Download python script van GitHub
RUN curl -o script.py https://raw.githubusercontent.com/coconutsRhealthy/image_openai/refs/heads/main/cloud/script.py

# Installeer Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose MySQL poort
EXPOSE 3306

# Voeg entrypoint script toe
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Start alles via entrypoint
ENTRYPOINT ["./entrypoint.sh"]