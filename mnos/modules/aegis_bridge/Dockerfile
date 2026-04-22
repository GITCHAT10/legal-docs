FROM python:3.11-slim

WORKDIR /app

RUN pip install paho-mqtt

# Copy the entire mnos directory to satisfy imports
COPY mnos /app/mnos
COPY mnos/modules/aegis_bridge/bridge.py /app/bridge.py

ENV PYTHONPATH=/app
ENV NEXGEN_SECRET=hardened_secret_placeholder

CMD ["python", "bridge.py"]
