# Gebruik een Python image
FROM python:3.12-slim

# Install MySQL server, client en git/curl
RUN apt-get update && \
    apt-get install -y default-mysql-server default-mysql-client git curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Clone hele GitHub repo (alle scripts en requirements)
RUN git clone --depth 1 https://github.com/coconutsRhealthy/image_openai.git .

# Installeer Python dependencies (requirements.txt zit in cloud folder)
RUN pip install --no-cache-dir -r cloud/requirements.txt

# Entrypoint script executable maken
RUN chmod +x cloud/entrypoint.sh

# Expose MySQL poort
EXPOSE 3306

ENTRYPOINT ["./cloud/entrypoint.sh"]