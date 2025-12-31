FROM python:3.11-slim

# -------------------------
# System setup
# -------------------------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# -------------------------
# Create user EARLY so we can use it for permissions later
# -------------------------
RUN useradd -m appuser

# -------------------------
# Install uv
# -------------------------
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# -------------------------
# Copy dependency metadata
# -------------------------
COPY --chown=appuser:appuser pyproject.toml uv.lock ./

# -------------------------
# Install dependencies (locked, prod-only)
# -------------------------
RUN uv sync --frozen --no-dev --no-install-project

# -------------------------
# Copy application code WITH OWNERSHIP
# -------------------------
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser config/ ./config/
COPY --chown=appuser:appuser app.py ./

COPY --chown=appuser:appuser README.md ./

# -------------------------
# Install the project itself
# -------------------------
RUN uv sync --frozen --no-dev

# -------------------------
# Security: non-root user
# -------------------------
USER appuser

# -------------------------
# Streamlit config
# -------------------------
EXPOSE 8501


CMD ["uv", "run", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]