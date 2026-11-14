FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt requirements-postgresql.txt ./
RUN pip install --no-cache-dir -r requirements-postgresql.txt
COPY . .
RUN python -m compileall -q .
EXPOSE 8000
# Para ejecutar es necesario proporcionar .env/variables seguras, PostgreSQL y Gmail API (OAuth).
CMD ["sh", "-c", "python manage.py migrate && gunicorn Pr_makeupweb.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]
