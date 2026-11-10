# Phase 8 — Testing & Deployment

## CI automation
- Backend unittest suite runs on pull requests targeting main and pushes to main/utsav when backend files change.
- Flutter analyze and test run in the Android APK workflow.
- GitHub Actions builds a debug APK and uploads it as a workflow artifact for 14 days.
- This artifact is for QA/internal installation, not a production-signed Play Store release.

## CI test commands
Backend (from backend folder):
```powershell
.\\setup.ps1
.\\test.ps1
```
Flutter (from flutter-app folder):
```powershell
flutter pub get
flutter analyze
flutter test
flutter build apk --debug
```

## Physical Android QA checklist — execute on the target phone before release
Record device model, Android version, app build SHA, backend URL, date, result, and issue IDs. Do not use real sensitive conversations or credentials during testing.

- [ ] Install APK; app launches and no crash on cold start.
- [ ] Login / invalid credentials / logout paths behave safely.
- [ ] Microphone permission: allow, deny, and revoke from system settings.
- [ ] Consent disclosure appears before monitoring; stop action terminates session.
- [ ] Confirm app's visible active-monitoring state is accurate.
- [ ] Test backend unavailable, slow network, reconnect, and WebSocket disconnect.
- [ ] Confirm alert UX, transcript display limits, and no transcript in lock-screen notification.
- [ ] Verify normal call is not blocked by call-screening service.
- [ ] Grant Android call-screening role (if device OS offers it); test known safe caller and unknown caller; confirm no call auto-blocking behavior.
- [ ] Test incoming/outgoing calls, speaker/earpiece, Bluetooth if available, backgrounding, screen lock, and battery saver.
- [ ] Confirm permissions and monitoring state after app restart.
- [ ] Inspect logs for credentials, bearer tokens, or sensitive transcript leakage.
- [ ] Test API over HTTPS/WSS with production-like deployment configuration.

## Release blockers / known boundaries
- Phone-level QA is manual and must be performed on the target handset; CI runner cannot validate carrier calls, OEM permissions, Bluetooth, background execution, or battery behavior.
- Current Android Gradle release configuration uses debug signing. Do not publish a release APK/AAB until release signing keys are configured securely.
- The Android manifest currently allows cleartext traffic for development; deployment must switch to HTTPS/WSS and remove cleartext allowance before public release.
- Hosting setup, TLS, production secrets, MongoDB backup/restore, gateway rate limiting, retention policy and legal privacy approval remain operator responsibilities (see Phase 7 security checklist).
- CallScreeningService integration is a feasibility scaffold, not a certified or guaranteed real-time scam call interception product.
