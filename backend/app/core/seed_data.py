"""Production-safe seed behavior.

EchoShield must not fabricate call history for real users. Sample data belongs in
explicit development fixtures/tests, never auto-inserted during API reads.
"""


async def ensure_seed_logs(call_log_cls, user_id: str):
    """Compatibility no-op; real call logs are created only from actual analysis."""
    return None
