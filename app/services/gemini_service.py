import os
import time
import google.generativeai as genai


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)


GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]


def call_gemini_with_fallback(prompt: str) -> dict:
    """
    Calls Gemini with retries and fallback models.
    Never raises raw Gemini errors to the frontend.
    """

    if not GOOGLE_API_KEY:
        return {
            "answer": "AI wording is unavailable because the Google API key is not configured.",
            "source": "local_fallback",
            "model_used": None,
            "ai_status": "missing_api_key",
        }

    last_error = None

    for model_name in GEMINI_MODELS:
        for attempt in range(3):
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)

                text = getattr(response, "text", None)

                if text and text.strip():
                    return {
                        "answer": text.strip(),
                        "source": "gemini",
                        "model_used": model_name,
                        "ai_status": "available",
                    }

                last_error = "Gemini returned an empty response."

            except Exception as e:
                last_error = str(e)

                # Retry on temporary failures
                if "503" in last_error or "429" in last_error or "UNAVAILABLE" in last_error:
                    time.sleep(2 * (attempt + 1))
                    continue

                # For other errors, try the next model
                break

    return {
        "answer": "AI-generated wording is temporarily unavailable, so this answer was calculated from your uploaded product and review data instead.",
        "source": "local_fallback",
        "model_used": None,
        "ai_status": "busy",
        "error_summary": last_error,
    }