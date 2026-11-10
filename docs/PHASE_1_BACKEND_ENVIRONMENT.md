# Phase 1 — Backend Environment Setup

**Goal:** Establish a repeatable local backend environment for EchoShield.  
**Scope:** Python runtime, dependency installation, environment variables, server startup, health/readiness checks, tests, and Docker option.

## 1. Prerequisites

- Python 3.11 (the repository targets Python 3.11 for reproducible setup).
- PowerShell on Windows, or a shell with Python and pip on Linux/macOS.
- Git.
- MongoDB local or MongoDB Atlas connection for database-backed readiness and runtime.
- Optional: Docker Desktop and Docker Compose for container-based local setup.
- Optional audio stack dependencies such as ffmpeg / Whisper / PyTorch are governed by backend requirements and model configuration.

Verify Python:

```powershell
python --version
```

Expected major/minor version: Python 3.11.x.

## 2. One-step Windows setup

From repository root:

```powershell
cd backend
.\setup.ps1
```

The setup helper provisions a local virtual environment, installs dependencies from `requirements.txt`, and creates `.env` from `.env.example` only if `.env` does not already exist. Existing environment settings are not overwritten.

Edit `backend/.env` and set at least:
- `MONGO_URI`: your local or Atlas MongoDB connection string.
- `JWT_SECRET_KEY`: a unique strong random secret (do not use the sample placeholder).

Start server after setup:

```powershell
.\setup.ps1 -SkipInstall -RunServer
```

## 3. Manual virtual environment alternative

Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env -ErrorAction SilentlyContinue
python run.py
```

Linux/macOS:

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp -n .env.example .env
python run.py
```

Review `.env` before launching; configure secrets and the database URI. Never commit the local `.env` file.

## 4. Runtime verification

When the backend is running at the default local address:

- Liveness: `GET http://localhost:8000/health`
- Readiness: `GET http://localhost:8000/ready` (readiness includes database connectivity)
- Development OpenAPI docs: `http://localhost:8000/openapi.json` if enabled for the current environment.

A successful liveness response alone does not mean MongoDB is connected. Confirm readiness separately.

## 5. Test the environment

From PowerShell:

```powershell
cd backend
.\test.ps1
```

Or activate the virtual environment and invoke the project's Python unittest suite directly as configured by the test helper. Check the command output for actual test results; setup completion does not imply the tests have passed.

## 6. Docker Compose option

From the repository root:

```powershell
Copy-Item backend/.env.example backend/.env -ErrorAction SilentlyContinue
# Edit backend/.env: set the JWT secret and any environment-specific values.
docker compose up --build
```

Compose brings up MongoDB, the FastAPI backend, and the static web dashboard. Stop services:

```powershell
docker compose down
```

For persistence, Compose defines a named MongoDB data volume. Do not use this local development arrangement as a substitute for a production backup/restore plan.

## 7. Configuration and safety

Configuration template: `backend/.env.example`.

- Generate a strong random `JWT_SECRET_KEY` for each environment.
- Keep `.env`, API keys, database credentials, tokens, and signing material out of version control.
- Use separate credentials and database instances for development and production.
- In production, configure persistent MongoDB, exact CORS origins, HTTPS/WSS, secret storage, backups, and monitoring as described in the Phase 7 security checklist.
- Mock/fallback behavior is development-only; production configuration is designed to fail closed when persistent database requirements are not met.

## Phase 1 completion checklist

- [x] Python 3.11 target documented.
- [x] Repeatable Windows setup helper and manual venv commands documented.
- [x] Dependency installation and environment-file configuration documented.
- [x] Backend startup and health/readiness checks documented.
- [x] Test helper and Docker Compose workflow documented.
- [x] Secret hygiene and development-vs-production boundaries documented.

**Outcome:** A single consolidated environment setup guide is available for developers to bootstrap and validate the EchoShield backend locally. This documentation is not itself a claim that a specific machine's setup, database, or test suite was executed.
