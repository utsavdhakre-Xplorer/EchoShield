# EchoShield Backend Security & Reliability Notes

## Runtime configuration
- Set ECHOSHIELD_ENV=production for deployments. The backend refuses to start if JWT_SECRET_KEY is shorter than 32 characters.
- Production startup now fails closed unless MongoDB is connected; mock persistence is prohibited in production.
- Set a unique random JWT secret in hosting secret storage; never commit .env or secrets.
- Set CORS_ORIGINS to exact trusted HTTPS frontend origins. Production rejects missing origins and wildcard origins.
- Production disables interactive Swagger and ReDoc docs endpoints.
- Production responses include defensive headers and HSTS. TLS must be configured at the trusted hosting proxy/load balancer.
- Configure MONGO_URI and restrict database network access and privileges.
- Configure DEEPFAKE_MODEL_PATH only with a trained checkpoint. Without a checkpoint detector reports unverified status.
- Treat transcripts and call logs as sensitive data; do not log their content.

## API resilience
- Authentication and storage paths distinguish temporarily unavailable storage from invalid credentials/accounts.
- Audio upload endpoints read bounded chunks and reject payloads exceeding 15 MiB with HTTP 413.
- Transcript analysis bounds transcript size at 10,000 characters.
- Long-running analysis tasks use timeouts.
- WebSocket audio frames are capped at 1 MiB.

## Run tests locally (Windows PowerShell)
From backend directory:
```powershell
.\\setup.ps1
.\\test.ps1
```
Tests use Python unittest. CI executes backend suite on pushes, relevant pull requests and manual dispatch.

## Production operator checklist
See docs/PHASE_7_SECURITY_PRIVACY.md. External hosting, TLS, secret store, database backups, gateway rate limiting, retention policy, and legal/privacy approval require operator configuration and validation.
