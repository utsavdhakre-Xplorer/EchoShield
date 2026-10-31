import asyncio

from app.services.scam_detector import detect_scam_tactics
from app.services.threat_classifier import classify_threat


async def main():

    messages = [
        "Your bank account will be blocked. Share your OTP immediately.",
        "Hey, are you coming to college tomorrow?",
        "Congratulations! Pay processing fees to claim your prize."
    ]

    for message in messages:

        scam_result = await detect_scam_tactics(message)

        threat_result = classify_threat(
            deepfake_confidence=0.0,
            is_deepfake=False,
            urgency_score=scam_result["urgency_score"],
            urgency_detected=scam_result["urgency_detected"],
            deepfake_verified=False,
            tactics_detected=scam_result["tactics_detected"]
        )

        print("\nMessage:", message)
        print("Scam Score:", scam_result["urgency_score"])
        print("Threat Level:", threat_result["threat_level"])
        print("Overall Score:", threat_result["overall_score"])
        print("Alert Required:", threat_result["alert_required"])
        print("Threat Factors:", threat_result["threat_factors"])


if __name__ == "__main__":
    asyncio.run(main())