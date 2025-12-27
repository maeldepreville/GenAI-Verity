FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Dépendances
COPY pyproject.toml uv.lock app.py ./

# Initialiser les fichiers de dép
RUN uv sync --frozen --no-cache

COPY src/ ./src/
COPY config/ ./config/
COPY ui/ ./ui/

# Ajout au PYTHONPATH pour les imports
ENV PYTHONPATH=/app

CMD ["/app/.venv/bin/streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]