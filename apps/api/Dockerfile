FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /workspace
COPY apps/api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
COPY apps/api/app /workspace/apps/api/app
COPY config /workspace/config

RUN useradd --create-home --uid 10001 still
USER still
EXPOSE 8080
CMD ["python", "-m", "uvicorn", "app.main:app", "--app-dir", "/workspace/apps/api", "--host", "0.0.0.0", "--port", "8080"]
