FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set PYTHONPATH to root for module resolution
ENV PYTHONPATH=/app

EXPOSE 8001

CMD ["uvicorn", "admiralda_pbx.apps.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
