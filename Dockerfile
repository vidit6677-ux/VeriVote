FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --uid 10001 verivote \
    && chown -R verivote:verivote /app
USER verivote

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/ready')"

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
