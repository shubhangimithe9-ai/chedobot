# Production Dockerfile for Hugging Face Spaces (Chedo Tech AI Assistant)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=7860 \
    GRADIO_SERVER_NAME=0.0.0.0 \
    MODEL_PATH=/app/models/gamma-2b-chedotech-q4_k_m.gguf \
    MAKEFLAGS="-j2"

WORKDIR /app

# Install build dependencies, curl, and Node.js 20 for Jev AI (@receptron/laya)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    curl \
    gnupg \
    ca-certificates \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy package and install Node.js dependencies for Jev AI / Laya
COPY package*.json ./
RUN npm install --omit=dev

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and OKF knowledge base
COPY app.py chedobot.py main.py laya_classifier.py laya_bridge.mjs ./
COPY okf/ ./okf/

# Copy Gamma 2B GGUF model binary
COPY models/ ./models/

EXPOSE 7860

# Container health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# Automatically start the application
CMD ["python", "app.py"]
