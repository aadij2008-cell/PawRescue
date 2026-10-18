import requests

from fastapi import APIRouter, HTTPException
from schemas import AIAidRequest
from config import GEMINI_API_KEY

router = APIRouter(
    prefix="/api/ai",
    tags=["AI First-Aid"]
)


@router.post("/first-aid")
async def get_first_aid(data: AIAidRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="AI service is not configured."
        )

    description = data.injury_description.strip()

    if not description:
        raise HTTPException(
            status_code=400,
            detail="Please describe the animal's condition."
        )

    prompt = f"""
You are an animal first-aid information assistant.

The user describes this animal-related situation:

{description}

Provide clear, concise, situation-specific first-aid guidance.

Requirements:
1. Start with the most important immediate action.
2. Give numbered, practical stabilization steps.
3. Explain what the person should avoid doing.
4. Identify signs that require urgent veterinary attention.
5. Do not invent a diagnosis.
6. Do not recommend human medicines or unsupported treatments.
7. If the animal may be seriously injured, emphasize urgent
   professional veterinary care.
8. Use simple language that an ordinary person can understand.
9. Never suggest delaying emergency veterinary treatment.

Clearly state that your guidance is not a veterinary diagnosis
and that a qualified veterinarian should assess the animal.
"""

    try:
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/"
            "models/gemini-3.8-flash:generateContent",
            headers={
                "x-goog-api-key": GEMINI_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 1200
                }
            },
            timeout=30
        )

        if not response.ok:
            print(
                "Gemini API error:",
                response.status_code,
                response.text
            )

            raise HTTPException(
                status_code=502,
                detail="The AI service could not generate guidance."
            )

        result = response.json()

        guidance = (
            result.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        

        if not guidance:
            raise HTTPException(
                status_code=502,
                detail="The AI returned an empty response."
            )

        return {
            "success": True,
            "injury_reported": description,
            "guidance": guidance,
            "disclaimer": (
                "This is general first-aid information, not a "
                "veterinary diagnosis. Seek professional veterinary "
                "care, especially for serious injuries."
            )
        }

    except requests.RequestException:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to the AI service. Please retry."
        )