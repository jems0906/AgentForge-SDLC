FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 AGENTFORGE_ROOT=/app
WORKDIR /app
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY backend/app /app/app
COPY sample_repo /app/sample_repo
COPY worker /app/worker
CMD ["python", "-m", "worker.task_runner"]
