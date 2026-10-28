import os
import logging
from typing import Optional
import random

logger = logging.getLogger(__name__)

# Pre-built negotiator strategies for different threat levels
STRATEGIES = {
    "CRITICAL": [
        "Act extremely confused and say: 'Wait, I need to find my reading glasses. Can you repeat everything from the beginning? I'm also a bit hard of hearing.'",
        "Pretend you can't find your bank card: 'I know I put it somewhere safe... let me check every drawer in the house. This might take a while.'",
        "Claim your internet is down: 'My wifi keeps cutting out. Could you hold on? My grandson is usually the one who fixes these things but he's at school.'",
        "Pretend to be very elderly and confused: 'Now, which bank did you say this was? I have accounts at four different banks you see. Which account number exactly?'",
        "Say your printer is broken: 'I always write these things down. Let me find a pen. Oh, the pen is out of ink. Let me find another one...'",
        
        # New Enhanced Strategies
        "Tech Support Counter: 'I don't know how to turn on the computer. I'm pressing the screen but nothing happens. Wait, is the screen the computer?'",
        "Gift Card Counter: 'You want target gift cards? Oh, I love Target! I have a 20% off coupon. Should I buy some socks while I'm there?'",
        "Crypto Counter: 'What is a Bitcoin ATM? Do they take quarters? I only have a jar of loose change in my house right now.'",
        "Agent Verification: 'Before I do anything, I need your badge number. Hold on, my police officer neighbor is right here, let me put him on the phone to verify your badge...'",
    ],
    "HIGH": [
        "Stall by asking for verification: 'Before I do anything, I need you to verify you're legitimate. What's the full address of your company's registered office?'",
        "Request a callback number and say you'll call back after consulting your financial advisor.",
        "Ask them to repeat all information multiple times claiming you're writing everything down slowly.",
        "Tell them your spouse handles all financial matters and they won't be home until later tonight.",
        "Pretend poor phone reception: 'Sorry, you're breaking up. Can you... can you repeat that? You said don't do what exactly?'",
        "Language barrier stall: Repeatedly ask them to explain terms very slowly. 'I don't understand what remote access means, can you explain it like I'm five?'",
    ],
    "MEDIUM": [
        "Ask for a reference number and say you'll verify through official channels before proceeding.",
        "Request all information in writing via official mail before taking any action.",
        "Tell them you need to speak with your bank directly using the number on the back of your card.",
        "Say you are driving right now and ask them to call back in two hours.",
    ],
    "LOW": [
        "Politely ask for their name, company, and a callback number for verification.",
        "Thank them for calling and say you'll look into this through official channels.",
        "Request written confirmation before taking any steps.",
    ],
}


async def generate_negotiator_strategy(transcript: str, threat_level) -> str:
    """
    Generate an AI negotiator strategy to waste scammer time.
    Uses Claude API if available, falls back to curated strategies.
    """
    threat_str = str(threat_level).replace("ThreatLevel.", "")

    # Try to use the Anthropic API for dynamic strategy generation if valid key is set
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if api_key and not api_key.startswith("your-") and threat_str in ["HIGH", "CRITICAL"]:
        try:
            strategy = await _generate_with_claude(transcript, threat_str, api_key)
            if strategy:
                return strategy
        except Exception as e:
            logger.warning(f"Claude API unavailable for negotiator: {e}")

    # Fallback to curated strategies
    strategies = STRATEGIES.get(threat_str, STRATEGIES["LOW"])
    return random.choice(strategies)


async def _generate_with_claude(transcript: str, threat_level: str, api_key: str) -> Optional[str]:
    """Generate a custom strategy using Claude API."""
    import httpx
    import asyncio

    prompt = f"""You are an anti-scam negotiator AI. A user is on a call with a suspected scammer.
    
Threat Level: {threat_level}
Transcript snippet: "{transcript[:500]}"

Generate ONE specific strategy (2-3 sentences) to waste the scammer's time and protect the user.
Be creative, realistic, and slightly humorous. The strategy should cause maximum time waste.
Do NOT use bullet points. Just return the strategy text directly."""

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await asyncio.wait_for(
                client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-sonnet-4-20250514",
                        "max_tokens": 200,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                ),
                timeout=5.0
            )
            data = response.json()
            if "content" in data and data["content"]:
                return data["content"][0]["text"].strip()
    except asyncio.TimeoutError:
        logger.warning("Claude API timeout")
    except Exception as e:
        logger.warning(f"Claude API error: {e}")
    return None
