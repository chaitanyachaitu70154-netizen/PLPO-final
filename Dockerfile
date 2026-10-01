# ==============================================================================
# Dockerfile: Production Multi-Stage Build for PLPO Phase 4
# ==============================================================================
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final Minimal Runtime Image
FROM python:3.11-slim AS runner

WORKDIR /app

# Install runtime libpq for PostgreSQL connectivity
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged application user
RUN useradd -m -u 1001 -s /bin/bash plpo_user

# Copy installed Python packages from builder
COPY --from=builder /root/.local /home/plpo_user/.local
ENV PATH=/home/plpo_user/.local/bin:$PATH

# Copy application source code
COPY --chown=plpo_user:plpo_user . /app

# Switch to non-root user
USER plpo_user

# Production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8501

# Production Container Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; sys_exit = 0 if urllib.request.urlopen('http://localhost:8501/_stcore/health').getcode() == 200 else 1; exit(sys_exit)"

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
