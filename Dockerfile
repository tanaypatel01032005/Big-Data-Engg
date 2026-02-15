# -------- Stage 1: Build React frontend --------
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --production=false
COPY frontend ./
RUN npm run build

# -------- Stage 2: Python backend --------
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python dependencies (CPU-only torch for smaller image)
COPY requirements.txt ./
RUN pip install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt

# Copy project files
COPY API ./API
COPY Database ./Database
COPY scripts ./scripts
COPY cli_helper.py ./

# Copy pre-built embeddings (built locally, committed to repo)
COPY embeddings ./embeddings

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Render sets PORT env var; default to 8000
EXPOSE 8000
CMD ["sh", "-c", "gunicorn -k uvicorn.workers.UvicornWorker -w 1 API.api:app --bind 0.0.0.0:${PORT:-8000}"]
