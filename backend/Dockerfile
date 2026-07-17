# Optional: a container image for the backend. Render can run this repo natively (see render.yaml),
# but this Dockerfile makes the backend portable to any container host and reproducible locally.
FROM python:3.13-slim

WORKDIR /app

# Install deps first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# $PORT is provided by the host (Render/Fly/etc). Default to 8000 for local `docker run`.
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
