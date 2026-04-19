FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Explicitly exclude local dev artifacts from image if present
RUN rm -f skyfarm.db mnos.db skyfarm.log mnos.log

EXPOSE 8001

CMD ["uvicorn", "skyfarm.main:app", "--host", "0.0.0.0", "--port", "8001"]
