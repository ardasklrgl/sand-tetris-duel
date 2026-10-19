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

COPY sandtris_c_core.c .
RUN gcc -O3 -std=c99 -shared -fPIC sandtris_c_core.c -o sandtris_c_core.so

COPY sandtris_env_v10.py sandtris_parameterized_bot.py sandtris_lookahead_bot.py \
     web_physics.py web_game.py web_demo.py web_flow.py web_accounts.py best_clipped_weights_run2.npy ./
COPY web/ ./web/
COPY design/beach/assets/ ./design/beach/assets/
RUN mkdir -p /app/data

EXPOSE 10000
CMD ["sh", "-c", "exec python web_flow.py --host 0.0.0.0 --port ${PORT}"]
