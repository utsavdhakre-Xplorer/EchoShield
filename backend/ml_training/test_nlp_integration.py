import asyncio
from app.ml.nlp_classifier import classify_scam


async def main():

    messages = [
        "Your bank account will be blocked. Share your OTP immediately.",
        "Hey, are you coming to college tomorrow?",
        "Congratulations! Pay processing fees to claim your prize."
    ]

    for message in messages:
        result = await classify_scam(message)

        print("\nMessage:", message)
        print("Prediction:", result["label"])
        print("Scam Probability:", result["scam_probability"])
        print("Trained Model Probability:",
              result.get("trained_model_probability"))
        print("Contextual Probability:",
              result.get("contextual_probability"))
        print("ML Available:", result["ml_available"])


if __name__ == "__main__":
    asyncio.run(main())