FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Environment variables for production-locked mode
# SECRETS MUST BE INJECTED AT RUNTIME. Defaults provided for CI/Sim only.
ENV NEXGEN_SECRET=${NEXGEN_SECRET:-NATIONAL_SECRET_2024}
ENV MNOS_INTEGRATION_SECRET=${MNOS_INTEGRATION_SECRET:-NATIONAL_SECRET_2024}
ENV PYTHONPATH=/app

EXPOSE 8000 8001 8002

CMD ["./run_engine.sh"]
