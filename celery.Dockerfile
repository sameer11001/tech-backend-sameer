# celery.Dockerfile
FROM python:3.12-slim

WORKDIR /worker
COPY celery-requirements.txt .
RUN pip install --no-cache-dir -r celery-requirements.txt

COPY my_celery/ ./my_celery

CMD ["bash", "-c", "echo 'Specify celery worker or flower in docker-compose'"]