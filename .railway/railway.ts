import { defineRailway, postgres, project, service } from "railway/iac";

export default defineRailway(() => {
  const database = postgres("postgres");
  const api = service("api", {
    build: { builder: "DOCKERFILE", dockerfilePath: "backend/Dockerfile" },
    deploy: {
      preDeployCommand: ["alembic -c /app/alembic.ini upgrade head"],
      startCommand: "python -m app.serve",
      healthcheckPath: "/api/health",
      healthcheckTimeout: 100,
      restartPolicyType: "ON_FAILURE",
      restartPolicyMaxRetries: 10,
    },
    env: {
      APP_ENV: "production",
      SANDBOX_MODE: "railway",
      CORS_ORIGINS: "https://frontend-production-a97b.up.railway.app",
      DATABASE_URL: database.env.DATABASE_URL,
      GITHUB_REPOSITORY: "jems0906/AgentForge-SDLC",
      GITHUB_BASE_BRANCH: "main",
      GITHUB_TOKEN: { value: "", isOptional: true, isSealed: true },
      RAILWAY_PROJECT_TOKEN: { value: process.env.AGENTFORGE_BOOTSTRAP_PROJECT_TOKEN || "", isOptional: true, isSealed: true },
      RAILWAY_ENVIRONMENT_ID: "a7dd5f81-7a57-4582-a3be-1eddf8325bc4",
    },
  });
  const worker = service("worker", {
    build: { builder: "DOCKERFILE", dockerfilePath: "worker/Dockerfile" },
    deploy: {
      startCommand: "python -m worker.task_runner",
      restartPolicyType: "ON_FAILURE",
      restartPolicyMaxRetries: 10,
    },
    env: {
      APP_ENV: "production",
      SANDBOX_MODE: "railway",
      DATABASE_URL: database.env.DATABASE_URL,
      GITHUB_REPOSITORY: "jems0906/AgentForge-SDLC",
      GITHUB_BASE_BRANCH: "main",
      GITHUB_TOKEN: { value: "", isOptional: true, isSealed: true },
      RAILWAY_PROJECT_TOKEN: { value: process.env.AGENTFORGE_BOOTSTRAP_PROJECT_TOKEN || "", isOptional: true, isSealed: true },
      RAILWAY_ENVIRONMENT_ID: "a7dd5f81-7a57-4582-a3be-1eddf8325bc4",
    },
  });
  const frontend = service("frontend", {
    build: { builder: "DOCKERFILE", dockerfilePath: "frontend/Dockerfile" },
    deploy: {
      healthcheckPath: "/",
      healthcheckTimeout: 100,
      restartPolicyType: "ON_FAILURE",
      restartPolicyMaxRetries: 10,
    },
    env: { VITE_API_URL: "" },
  });

  return project("AgentForge SDLC", {
    resources: [database, api, worker, frontend],
  });
});
