FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Environment variables for production-locked mode
ENV PATENTE_HASH=464e8e0c804f8087928236102be8d12260f8f30999516348606c4b223010731a
ENV NEXGEN_SECRET=MALDIVES_SITA_2024
ENV PYTHONPATH=/app

EXPOSE 8000 8001 8002

CMD ["./run_engine.sh"]
