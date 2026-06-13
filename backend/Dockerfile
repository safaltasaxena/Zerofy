FROM python:3.11.9-slim

RUN adduser --disabled-password --gecos '' appuser

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

COPY . .

USER appuser

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
