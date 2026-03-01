FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5010

CMD ["gunicorn", "--bind", "0.0.0.0:5010", "--timeout", "120", "--workers", "2", "app:app"]
