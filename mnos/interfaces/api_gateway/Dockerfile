FROM python:3.11-slim

WORKDIR /app

# Copy requirements from root
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source
COPY . .

CMD ["uvicorn", "mnos.interfaces.api_gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
