# Dockerfile for Qoder Creator & Auto-Claim on Ubuntu
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies, Python, Curl, and required libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    ca-certificates \
    git \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2t64 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt && \
    /opt/venv/bin/playwright install chromium --with-deps

ENV PATH="/opt/venv/bin:$PATH"

# Install Qoder CLI binary
RUN curl -fsSL https://qoder.sh/install.sh | bash || true

COPY . .

CMD ["python3", "main.py"]
