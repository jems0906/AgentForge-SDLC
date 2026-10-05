FROM node:22-slim AS railway-sandbox
WORKDIR /sandbox-sdk
COPY backend/sandbox_runner/package.json backend/sandbox_runner/package-lock.json ./
RUN npm ci --omit=dev --no-audit
FROM docker:27-cli AS dockercli
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 AGENTFORGE_ROOT=/app
WORKDIR /app
COPY backend/requirements-runtime.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY --from=dockercli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=railway-sandbox /usr/local/bin/node /usr/local/bin/node
COPY --from=railway-sandbox /sandbox-sdk/node_modules /app/node_modules
COPY backend/app /app/app
COPY backend/sandbox_runner/execute.mjs /app/sandbox_runner/execute.mjs
COPY sample_repo /app/sample_repo
COPY worker /app/worker
CMD ["python", "-m", "worker.task_runner"]
