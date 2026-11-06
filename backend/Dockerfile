FROM python:3.11-slim

WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements for layer caching
COPY backend/requirements.txt /app/backend/requirements.txt
COPY ai-models/requirements.txt /app/ai-models/requirements.txt

# Install python dependencies including tensorflow, wfdb, shap, and python-dotenv
# Ensure numpy remains pinned to 1.26.4 compatible with tensorflow-cpu 2.16.1
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt && \
    pip install --no-cache-dir -r /app/ai-models/requirements.txt && \
    pip install --no-cache-dir python-dotenv shap && \
    pip install --no-cache-dir "numpy==1.26.4"

# Copy all project files into the container
COPY . /app

ENV PYTHONPATH="/app/backend:/app"
WORKDIR /app/backend

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head || true; uvicorn app.main:app --host 0.0.0.0 --port 8000"]
