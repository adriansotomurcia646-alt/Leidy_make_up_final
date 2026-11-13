FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python -m compileall -q .
EXPOSE 8000
# En producción utilice un servidor WSGI/ASGI y un proxy HTTPS (no runserver).
CMD ["python","manage.py","runserver","0.0.0.0:8000"]
