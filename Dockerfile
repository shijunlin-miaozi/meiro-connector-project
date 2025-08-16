FROM python:3.11-slim

# Create non-root user early
RUN useradd -ms /bin/bash appuser

WORKDIR /app

# System deps (TLS certs) and clean up
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Install Python deps first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code with correct ownership so non-root can write under /app
COPY --chown=appuser:appuser . .

# Ensure /app/out exists and is writable (covers cases where code needs to create it)
RUN mkdir -p /app/out && chown -R appuser:appuser /app

USER appuser

# Quieter/faster Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Default: run the pipeline (scripts can override this to run uvicorn)
CMD ["python", "main.py"]
