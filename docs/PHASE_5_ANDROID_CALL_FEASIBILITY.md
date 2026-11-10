# Phase 5 — Android call-related features: feasibility scaffold

## Implemented in repository
- Removed the legacy `PROCESS_OUTGOING_CALLS` permission and PHONE_STATE/NEW_OUTGOING_CALL broadcast receiver declaration from the Android manifest.
- Removed unused phone-state and boot-completed permissions from the manifest.
- Registered an Android Telecom `CallScreeningService` protected by `BIND_CALL_SCREENING`.
- The service currently responds by allowing calls unchanged. This is a deliberate safe scaffold, not caller identification, scam detection, or automatic blocking.

## Platform boundary
A user must explicitly grant the Android call-screening role (via system role settings) for this service to be eligible. Cellular call audio capture is not provided by this service and is not implemented here. Do not represent microphone recording of nearby speaker audio as capture of both call parties.

## Owner/device validation required
- Confirm service appears and can be granted as the call-screening role on supported Android versions.
- Test incoming call behavior and OEM/Telecom compatibility on target devices.
- Review any future caller-identification/scoring action, consent/disclosures, and app-store policy before rejecting or silencing calls.
- Microphone foreground service capture must be separately designed, permissioned, foreground-visible, stoppable, and tested; this phase does not add it.

## Acceptance boundary
This phase establishes the supported Android service declaration and removes legacy receiver assumption. Real-device role validation and any actual screening policy remain manual and unverified.
