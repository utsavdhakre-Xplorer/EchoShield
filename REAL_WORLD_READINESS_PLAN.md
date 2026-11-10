# EchoShield Real-World Readiness Plan

Status date: 2026-11-10  
Working branch: `utsav` (do not merge into `main` until review and device validation).

This is an implementation and validation plan, not a claim that the app is already production-ready. A feature is "done" only after code review, tests, and a real-device check.

## Current audit snapshot

- Flutter Android app builds and launches on RMX3999.
- Backend FastAPI entry point includes the auth, audio, analysis, and WebSocket routers.
- Dashboard requests `GET /stats` and `GET /call-logs`; these routes are present in the checked-in analysis router. The observed 404s therefore need a reproducible runtime check (the running server may be loading different/stale code or a different app instance).
- Login is a real API call, but MongoDB startup previously failed and the backend fell back to an in-memory mock store. Mock users disappear on process restart, so this is not acceptable for real accounts.
- Flutter API helpers currently suppress errors for dashboard requests; the UI can only show an unavailable state, not the actual HTTP/network cause.
- Audio capture currently has two competing paths: the call monitor starts WebSocket microphone capture and also starts periodic chunk recording. They must be unified and tested; concurrent microphone capture can produce silence or contention.
- The Android manifest includes legacy `PROCESS_OUTGOING_CALLS`; policy and platform restrictions must be checked before retaining restricted permissions.
- The UI's Monitoring switch currently means only local app monitoring state/permission flow. It must not be presented as guaranteed system-wide call protection.

## Phase 1 — Stabilize local development and reproducible builds

- Pin a supported Python runtime for the backend (Python 3.11 is already installed on the developer machine).
- Recreate and activate a clean backend virtual environment; install the locked requirements; add a tested lock/constraints strategy.
- Make startup fail loudly in production when required configuration or database is unavailable; keep mock mode explicitly development-only.
- Add a single documented Windows PowerShell setup/run script and verify `/health` and OpenAPI route registration.
- Ensure local-device API URL is supplied at build/run time rather than hard-coded to a laptop Wi-Fi IP.

Acceptance: clean setup from README; backend starts with an explicit database status; app connects from emulator and physical phone; no unexplained 404/401/connection errors.

## Phase 2 — Backend and database correctness

- Verify MongoDB Atlas/local MongoDB configuration, DNS/network access, credentials, database name, and Beanie initialization.
- Add typed request/response schemas, input validation, consistent error responses, and API versioning.
- Verify signup, login, JWT expiry, /auth/me, per-user authorization, call-log ownership, stats, and history.
- Remove production seed/sample records from user-facing metrics; seed data only in an explicit demo/test command.
- Fix audio call-log lifecycle (create once per call, append chunks safely, close on call end, enforce ownership).
- Add health/readiness endpoints that distinguish API availability from DB readiness.

Acceptance: data survives backend restarts; two users cannot read one another's records; all routes have automated tests; production never silently changes to mock persistence.

## Phase 3 — Flutter app reliability

- Centralize API configuration, timeouts, token handling, error parsing, and retry rules.
- Stop swallowing HTTP errors; show human-readable offline/auth/server/database states.
- Add session restoration at app startup, expired-token handling, logout cleanup, and signup/login validation.
- Make dashboard/history/analyzer refresh predictable, loading states accessible, and empty states truthful.
- Ensure analyzer errors and server responses are rendered accurately; never show fabricated stats or detections.
- Add app-level tests for auth, refresh, analysis, history, and offline behavior.

Acceptance: no hard-coded personal LAN address; API failures are visible; all app screens behave correctly on slow/offline network and expired sessions.

## Phase 4 — Audio analysis pipeline

- Pick one supported capture pipeline (chunked upload or WebSocket streaming); remove duplicate recorder ownership.
- Agree and validate audio format, sample rate, channels, framing, authentication, reconnect, backpressure, and call/session IDs.
- Verify transcription, trained scam text model, deepfake model, threat scoring, and negotiator outputs independently.
- Add model artifact/version metadata, confidence calibration, thresholds, and a clear "inconclusive" result.
- Do not call a result "deepfake detected" unless the trained detector actually ran successfully; expose model unavailable/error states.
- Add audio fixtures and integration tests for normal speech, scam speech, noisy/short audio, corrupt audio, and model failure.

Acceptance: documented inference path, repeatable metrics on a held-out test set, no false claim that an unavailable model ran, and correct saved analysis records.

## Phase 5 — Android call-related features (platform feasibility gate)

- Replace the current broadcast-receiver assumption with a supported Android Telecom design where appropriate.
- Evaluate `CallScreeningService` for caller identification/screening and user-granted call-screening role. Do not promise automatic blocking until this is implemented and tested.
- Do not attempt hidden/system call-audio capture. Ordinary third-party apps generally cannot capture cellular call audio; Android restricts call audio input to privileged/system situations. A microphone recording of nearby speaker audio is not equivalent to capturing both sides of the call.
- If user-consented recording is offered, make it explicit, foreground, visible, stoppable, and legally reviewed; test supported devices and call types.
- Review Android 14+ microphone foreground-service requirements and background-start limitations.
- Remove permissions that are not essential or not policy-eligible, including legacy call-log/outgoing-call permissions unless the app qualifies for the relevant role/policy.
- Add device/OEM compatibility checks and explain unsupported behaviors in-app.

Acceptance: only advertise capabilities that the selected Android APIs and the tested device can actually provide. No silent call recording, hidden monitoring, or unsupported interception claims.

## Phase 6 — Protection UX and safety

- Separate "Protection enabled" (supported caller screening/alerts) from "Audio analysis session" (user starts an explicit capture session).
- Add clear onboarding disclosures for microphone, phone state, notifications, data upload, retention, and consent.
- Add a visible recording indicator and immediate stop action wherever audio capture is active.
- Use a conservative risk display: evidence, confidence, detected signals, limitations, and safe next steps.
- The app must advise users not to transfer money/share OTPs and to verify with the organization using an independently sourced contact channel; it must not autonomously engage a caller or block a legitimate call without user/system-authorized action.

Acceptance: users understand exactly what is captured, when, where it is sent, and what protection does/does not do.

## Phase 7 — Security, privacy, and operational readiness

- Replace default JWT secret; load secrets only from environment/secret manager; never commit real .env files.
- Use HTTPS/WSS for deployed environments; restrict CORS; protect endpoints with auth, rate limits, upload size limits, and request timeouts.
- Validate file types/content, clean temporary audio files, prevent path/filename abuse, and limit audio retention.
- Add user data deletion/export, retention policy, audit-safe logging without passwords/tokens/raw transcripts.
- Review dependency vulnerabilities, password hashing compatibility, token storage, and platform permissions.
- Add production monitoring, structured logs, database backups, crash reporting, and incident response instructions.

Acceptance: security checklist reviewed; secrets absent from repository/logs; transport encrypted in deployment; retention and deletion tested.

## Phase 8 — Test, release, and deployment

- Backend unit/integration tests and Flutter widget/integration tests in CI.
- Build Android debug and release APK/AAB; test on RMX3999 plus at least one other Android version/device.
- Test Wi-Fi loss, mobile data, backend restart, expired tokens, denied permissions, battery saver, incoming/outgoing calls, Bluetooth/headsets, and device reboot.
- Deploy backend and MongoDB securely; configure production base URL; smoke-test from an external network.
- Prepare privacy policy, terms, store disclosures, screenshots, release notes, signing key backup, and staged rollout.

Acceptance: release candidate passes test matrix; production URL works independently of the developer laptop; rollback/backup process documented.

## Phase 9 — Final handoff

- Update README with verified capabilities, setup, configuration, deployment, troubleshooting, and known limitations.
- Provide a feature-by-feature evidence checklist and list every remaining manual account/device/legal action.
- Do not merge `utsav` into `main` until the release acceptance checklist passes.

## Tasks that require the project owner

These cannot be completed solely through repository edits:
1. Provide/configure MongoDB Atlas (or approve another persistent database) and securely add connection credentials as deployment/local environment secrets.
2. Create/configure a hosting account and production domain for the backend, then add secrets/variables in that provider.
3. Physically test permission prompts, calls, microphone/headset behavior, battery settings, and notifications on the target Android phone.
4. Decide whether to pursue default dialer/call-screening role and accept the Android UX/policy requirements; this changes the product scope.
5. Approve privacy policy, consent wording, data-retention period, and legal compliance for audio processing in intended countries.
6. Keep signing credentials private and complete Play Console ownership/declarations if publishing.

## Non-negotiable scope boundary

EchoShield can provide real transcript/audio-file analysis, persistent history, alerts, and supported caller-screening features once implemented and validated. It cannot honestly promise universal silent cellular-call recording, guaranteed deepfake detection, or automatic scam-call interception on ordinary Android devices. Android platform rules, OEM behavior, consent, and app-store policy constrain those capabilities. The implementation must communicate those limits rather than bypass them.
