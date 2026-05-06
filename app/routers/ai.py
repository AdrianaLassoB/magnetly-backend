from fastapi import APIRouter
from pydantic import BaseModel
import os
from google import genai

router = APIRouter()

class ChatRequest(BaseModel):
    question: str

@router.post("/ai/chat")
def ai_chat(payload: ChatRequest):
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        return {
            "answer": "AI chat is unavailable because the Gemini API key is not configured."
        }

    try:
        client = genai.Client(api_key=api_key)

        prompt = f"""
You are Magnetly's AI assistant for a D2C home goods brand.
Answer the user's question clearly and briefly.
If the question asks about products, reviews, marketing, or investment priorities,
respond as a marketing intelligence assistant.

User question: {payload.question}
""".strip()

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )

        return {
            "answer": response.text if response.text else "No answer returned."
        }
    except Exception as e:
        return {
            "answer": f"AI chat failed: {str(e)}"
        }