FROM python:3.11-slim

# -------------------------
# System setup
# -------------------------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# -------------------------
# Install uv
# -------------------------
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# -------------------------
# Copy dependency metadata first (for caching)
# -------------------------
COPY pyproject.toml uv.lock ./

# -------------------------
# Install dependencies (locked, prod-only)
# -------------------------
RUN uv sync --frozen --no-dev

# -------------------------
# Copy application code
# -------------------------
COPY src/ ./src/
COPY config/ ./config/
COPY app.py ./

# -------------------------
# Security: non-root user
# -------------------------
RUN useradd -m appuser
USER appuser

# -------------------------
# Streamlit config
# -------------------------
EXPOSE 8501

CMD ["uv", "run", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
