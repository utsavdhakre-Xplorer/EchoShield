# Phase 7 — Security, Privacy & Operational Readiness

## Implemented safeguards
- Production startup requires a persistent MongoDB connection; startup fails closed when database initialization is unavailable.
- Production configuration requires explicit trusted CORS origins and rejects wildcard origins.
- Production cannot run with ENABLE_MOCK_DB enabled.
- Swagger and ReDoc endpoints are disabled in production.
- HTTP responses receive defensive headers: content-type sniffing disabled, framing denied, referrer policy, microphone permissions policy, and no-store cache policy.
- HSTS is emitted only in production; the deployment must terminate TLS using HTTPS/WSS at a trusted proxy or hosting platform.
- Existing security module requires a 32+ character JWT secret in production. Secrets belong in hosting secret storage, not repository files.

## Deployment checklist (operator-owned)
- [ ] Set ECHOSHIELD_ENV=production.
- [ ] Store JWT_SECRET_KEY (32+ random characters) and MONGO_URI in secret manager.
- [ ] Set ENABLE_MOCK_DB=false.
- [ ] Set CORS_ORIGINS to exact HTTPS frontend origins (no wildcard).
- [ ] Configure HTTPS/WSS and confirm certificate renewal.
- [ ] Restrict MongoDB network access, credentials, and database privileges.
- [ ] Review provider logs/monitoring so passwords, bearer tokens, and raw transcripts are never logged.
- [ ] Define and approve audio/transcript retention, deletion, and export policy.
- [ ] Configure backups and test restore procedure.
- [ ] Review dependencies for known vulnerabilities before each release.
- [ ] Run backend integration and mobile device tests from Phase 8.

## Boundaries / pending
Repository code cannot configure external hosting, secret-manager values, TLS certificates, database backups, provider monitoring, or legal privacy policy approval. These remain explicit release-owner actions. In-memory rate limiting is intentionally not represented as a production safeguard; configure rate limits at a trusted API gateway/reverse proxy before public deployment.
