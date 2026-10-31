import asyncio
from app.services.scam_detector import detect_scam_tactics


async def main():

    messages = [
        "Your bank account will be blocked. Share your OTP immediately.",
        "Hey, are you coming to college tomorrow?",
        "Congratulations! Pay processing fees to claim your prize."
    ]

    for message in messages:

        result = await detect_scam_tactics(message)

        print("\nMessage:", message)
        print("Urgency Detected:", result["urgency_detected"])
        print("Urgency Score:", result["urgency_score"])
        print("ML Scam Probability:", result["ml_scam_probability"])
        print("Tactics:", result["tactics_detected"])


if __name__ == "__main__":
    asyncio.run(main())