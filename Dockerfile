# ── Build stage ───────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.11-slim

# Create non-root user (HF Spaces requirement)
RUN useradd -m -u 1000 appuser
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser . .

USER appuser

# Expose port (HF Spaces default)
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/health')"

# Environment variables with defaults
ENV PORT=7860
ENV API_BASE_URL=https://api.openai.com/v1
ENV MODEL_NAME=gpt-4o-mini

CMD ["python", "app.py"]
