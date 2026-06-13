FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Données persistantes (SQLite) : monter un volume sur /app/data en prod.
ENV RAID_COACH_DB=/app/data/raid_coach.db
RUN mkdir -p /app/data
EXPOSE 8000

# $PORT est fourni par l'hébergeur (Railway/Render) ; 8000 en local.
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
