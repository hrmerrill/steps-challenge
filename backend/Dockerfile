FROM python:3.11-slim

WORKDIR /app

# Install dependencies (apt) if psycopg2 needs it
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

ENV PYTHONPATH=/app

# Run alembic migrations and then start the server
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
