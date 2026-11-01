# One container for the whole app: FastAPI serves both the API (/api/...) and the
# built React app (/). Used by Render (render.yaml); also runs locally with Docker.

# --- Stage 1: build the React frontend ---
FROM node:20.18.1-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Python API + built frontend ---
FROM python:3.12.8-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.1 /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FRONTEND_DIST=/app/frontend-dist

WORKDIR /app/backend

# Install only the dependencies listed in pyproject.toml (cached unless they change)
COPY backend/pyproject.toml ./
RUN uv pip install --system --no-cache -r pyproject.toml

COPY backend/src ./src
COPY backend/config ./config
COPY backend/db ./db
COPY backend/data/indian_dishes.csv ./data/indian_dishes.csv
COPY --from=frontend /app/frontend/dist /app/frontend-dist

# Run as a non-root user; it only needs to write the SQLite file in data/
RUN useradd --create-home appuser && chown -R appuser /app/backend/data
USER appuser

# Render sets $PORT; default 8000 for local runs
EXPOSE 8000
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
