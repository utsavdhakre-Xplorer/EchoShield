# Phase 6 — Protection UX and Safety

Implemented in this phase:
- Added a consent/disclosure dialog before app monitoring is enabled. It describes microphone/phone permission needs, audio chunk upload to the configured backend, limits on cellular call-audio capture, and the absence of guaranteed system-wide blocking.
- Renamed the monitor state label to explicitly say **APP MONITOR ON/OFF**, avoiding a blanket protection claim.
- Added a visible active audio-analysis banner with a STOP control. STOP awaits recorder/timer teardown and the WebSocket stream shutdown and exits the app monitor session.
- Added a risk limitation notice: scores are estimates, not proof, and false positives/false negatives are possible.
- Reworked threat alert detail to show transcript evidence and urgency phrases, plus practical anti-fraud steps. It no longer presents an AI negotiator strategy as an instruction to engage with a suspected scammer.
- Removed transcript snippets from lock-screen notifications; notifications contain risk level and score only.

Owner/device validation still required in Phase 8:
- Verify disclosure presentation, microphone session lifecycle, stop behavior, and notification privacy on supported Android devices.
- Verify permissions-denied paths, background/foreground transitions, notification delivery, and capture session start/end timing.
- Confirm actual audio data capture boundaries and retention behavior on the configured backend. UI disclosures describe intended behavior; they are not a legal/privacy-policy substitute.

Safety boundaries:
- The app monitor toggle does not represent universal caller protection or automatic call blocking.
- Audio capture is not guaranteed to capture both sides of a cellular call.
- Users are advised not to share OTPs, PINs, passwords, or transfer funds under pressure; verify claims through independently sourced official contact details.
- No autonomous caller engagement or blocking is performed.
