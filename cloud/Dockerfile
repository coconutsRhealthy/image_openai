FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y git curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

ARG CACHEBUST=1
ARG BRANCH=main
RUN git clone --depth 1 -b ${BRANCH} https://github.com/coconutsRhealthy/image_openai.git .

RUN pip install --no-cache-dir -r cloud/requirements.txt

RUN chmod +x cloud/entrypoint.sh

ENTRYPOINT ["./cloud/entrypoint.sh"]
