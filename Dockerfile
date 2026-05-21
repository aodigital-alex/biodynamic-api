FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY biodynamic/ biodynamic/

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD uvicorn biodynamic.api.app:app --host 0.0.0.0 --port ${PORT:-8000}
