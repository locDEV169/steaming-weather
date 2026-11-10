FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Listen inside the container. Always override again at runtime if using
# --env-file .env (local .env often sets WEATHER_API_HOST=127.0.0.1).
ENV WEATHER_API_HOST=0.0.0.0
ENV WEATHER_API_PORT=5000
ENV CORS_ORIGINS=*

# Runtime secrets/config — do NOT COPY .env into the image.
# Pass via: docker run --env-file .env -e WEATHER_API_HOST=0.0.0.0
#   or:     docker compose up --build


# Runtime secrets/config — do NOT COPY .env into the image.
# Pass via: docker run --env-file .env -e WEATHER_API_HOST=0.0.0.0
#   or:     docker compose up --build
# Expected keys (see .env.example) — supply at runtime via --env-file / compose:
#   WEATHER_API_KEY
#   SUPABASE_URL
#   SUPABASE_SERVICE_ROLE_KEY
#   SUPABASE_LOCATION_KEY
#   TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID
# Do not bake secret values into the image.


WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY run.py ./run.py
COPY main.py ./main.py

EXPOSE 5000

# Default sync worker timeout (30s) is too low for Open-Meteo + Supabase + Telegram.
ENV GUNICORN_WORKERS=2
ENV GUNICORN_TIMEOUT=120

CMD ["sh", "-c", "gunicorn --bind ${WEATHER_API_HOST}:${WEATHER_API_PORT} --workers ${GUNICORN_WORKERS} --timeout ${GUNICORN_TIMEOUT} 'app:create_app()'"]
