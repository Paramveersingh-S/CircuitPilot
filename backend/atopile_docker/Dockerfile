FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    cmake \
    kicad \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir atopile

WORKDIR /workspace

ENTRYPOINT ["ato"]
