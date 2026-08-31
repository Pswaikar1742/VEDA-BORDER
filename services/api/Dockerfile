# syntax=docker/dockerfile:1

# Stage 1: Build Dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY services/api/requirements.txt .

RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime Production Image
FROM python:3.11-slim AS runner

WORKDIR /app

# Install runtime system libraries (Tesseract OCR engine, Poppler PDF utilities, OpenCV GL libs, curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app/services/api" \
    PYTHONUNBUFFERED=1 \
    MOCK_BORDER_INTELLIGENCE_ENABLED=true \
    THREAT_INTELLIGENCE_MANDATORY=true \
    VISUAL_FORENSICS_ENABLED=true \
    BIOMETRICS_ENABLED=true \
    CASE_DATABASE_PATH="data/runtime/veda_border.db"

# Create non-root user
RUN groupadd -g 1001 veda && \
    useradd -u 1001 -g veda -s /bin/bash -m veda && \
    mkdir -p /app/data/runtime /app/data/integrated_fixtures /app/services/api/assets/models && \
    chown -R veda:veda /app

# Copy application assets and source
COPY --chown=veda:veda services/api /app/services/api
COPY --chown=veda:veda data/integrated_fixtures /app/data/integrated_fixtures

USER veda

EXPOSE 8000

HEALTHCHECK --interval=5s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--app-dir", "services/api", "--host", "0.0.0.0", "--port", "8000"]