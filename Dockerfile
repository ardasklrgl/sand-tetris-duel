FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000 \
    SANDTRIS_DB_PATH=/app/data/accounts.sqlite3

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt

COPY native/sandtris_c_core.c ./native/
RUN gcc -O3 -std=c99 -shared -fPIC native/sandtris_c_core.c -o native/sandtris_c_core.so

COPY app/ ./app/
COPY models/ ./models/
COPY web/ ./web/
COPY design/beach/assets/ ./design/beach/assets/
RUN mkdir -p /app/data

EXPOSE 10000
CMD ["sh", "-c", "exec python -m app.web_flow --host 0.0.0.0 --port ${PORT}"]
