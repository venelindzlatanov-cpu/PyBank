# syntax=docker/dockerfile:1
FROM python:3.12-slim

# OS deps (includes netcat for the wait script)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first for better layer caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . /app

# Tiny wait-for-db helper
RUN printf '#!/bin/sh\nset -e\nhost=$1\nshift\nuntil nc -z $host 5432; do echo "waiting for db..."; sleep 1; done\nexec "$@"\n' \
    > /usr/local/bin/wait-for-db && chmod +x /usr/local/bin/wait-for-db

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
