FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV WEATHER_API_HOST=0.0.0.0
ENV WEATHER_API_PORT=5000

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY weather ./weather
COPY run.py ./run.py
COPY main.py ./main.py

EXPOSE 5000

CMD ["sh", "-c", "gunicorn --bind ${WEATHER_API_HOST}:${WEATHER_API_PORT} 'src:create_app()'"]