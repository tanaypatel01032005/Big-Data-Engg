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

# Set model cache path to ensure it's preserved
ENV SENTENCE_TRANSFORMERS_HOME=/app/model_cache

# Pre-download the model to avoid runtime timeout & connection issues
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

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

# Use pure Uvicorn to save memory (Gunicorn overhead can cause OOM on 512MB RAM)
# Workers=1 is implicit via single process
CMD ["sh", "-c", "python -m uvicorn API.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
