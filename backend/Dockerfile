FROM python:3.11-slim

WORKDIR /app

# Install system deps (basic)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . /app

# Render provides PORT env var
CMD ["bash", "-lc", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]
