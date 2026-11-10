# EchoShield Backend Security & Reliability Notes

## Runtime configuration

- Set `ECHOSHIELD_ENV=production` for deployments. The backend refuses to start if `JWT_SECRET_KEY` is shorter than 32 characters.
- Use a unique, randomly generated JWT secret and keep it in the hosting provider's secret store. Do not commit `.env` files or secrets.
- Keep `ENABLE_MOCK_DB=false` in production. Mock persistence is volatile and intended only for local development/tests.
- Set `MONGO_URI` to the deployment's MongoDB connection string and restrict database network access.
- Set `CORS_ORIGINS` to the exact trusted frontend origins. Do not use wildcard origins with credentialed requests.
- Configure `DEEPFAKE_MODEL_PATH` only with a trained checkpoint. Without a checkpoint the detector explicitly reports unverified status, not an authoritative deepfake result.
- Set `DEEPFAKE_THRESHOLD` within the range 0.0–1.0. Invalid values fall back to 0.6.
- Treat transcripts and call logs as sensitive user data; avoid putting their content in application logs.

## API resilience

- Authentication, signup, login, call history, analysis statistics and WebSocket authentication distinguish temporarily unavailable storage from invalid credentials/accounts.
- Audio upload endpoints read in bounded chunks and reject payloads exceeding 15 MiB with HTTP 413.
- Transcript analysis validates input types and bounds transcript size at 10,000 characters.
- Long-running scam-analysis and negotiator tasks use timeouts and return HTTP 504 when they exceed their configured limits.
- WebSocket audio frames are capped at 1 MiB; a database availability issue during user verification uses close code 1013 (retryable).

## Run tests locally (Windows PowerShell)

From the `backend` directory:

```powershell
.\setup.ps1
.\test.ps1
```

To install/update dependencies before executing the test suite:

```powershell
.\test.ps1 -InstallDependencies
```

Tests use Python's built-in `unittest` runner. GitHub Actions also executes the backend suite on pushes to `utsav`, relevant pull requests, and manual workflow dispatch.

## Test coverage focus

- Password hashing, UTF-8 byte limits, JWT decoding/expiration and current-user dependency.
- Transcript request validation and bounded audio upload behavior.
- Database initialization/cleanup and service-unavailable behavior across auth, analysis and WebSocket paths.
- API endpoint behavior with explicitly enabled mock storage.
- Scam tactic detection, threat scoring, audio feature handling and deepfake checkpoint loading.

## Release caveats

A green unit-test workflow is not a substitute for deployment integration testing. Before production release, validate MongoDB connectivity, JWT secret configuration, CORS origins, model checkpoint provenance, audio inference latency, and end-to-end Flutter client behavior in the target environment.
