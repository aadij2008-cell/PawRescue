import json
import re

from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder

from schemas import RoutineRequest
from tinyfish import AsyncTinyFish
from config import TINYFISH_API_KEY


router = APIRouter(
    prefix="/api/routine",
    tags=["Routine Allocation"]
)

tinyfish_client = AsyncTinyFish(
    api_key=TINYFISH_API_KEY,
    timeout=120.0
) if TINYFISH_API_KEY else None


def extract_json(text):
    """Extract a JSON array or object from an agent response."""
    if not isinstance(text, str):
        return None

    text = text.strip()

    # Handle JSON returned directly.
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Handle JSON surrounded by explanatory text or code fences.
    for pattern in (r"\[[\s\S]*\]", r"\{[\s\S]*\}"):
        match = re.search(pattern, text)

        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                continue

    return None


def normalize_facilities(raw, location):
    """Convert common TinyFish response formats into facility cards."""

    facilities = []

    def inspect(value):
        if isinstance(value, list):
            for item in value:
                inspect(item)
            return

        if not isinstance(value, dict):
            return

        # Recognize common names for lists of search results.
        for key in (
            "allocated_facilities",
            "facilities",
            "results",
            "places",
            "clinics",
            "organizations",
            "organisations"
        ):
            nested = value.get(key)

            if isinstance(nested, (list, dict)):
                inspect(nested)

        name = (
            value.get("name")
            or value.get("facility_name")
            or value.get("business_name")
        )

        if name:
            facilities.append({
                "name": str(name),
                "type": str(
                    value.get("type")
                    or value.get("category")
                    or "Veterinary / Animal Welfare Facility"
                ),
                "location": str(
                    value.get("address")
                    or value.get("location")
                    or location
                ),
                "contact": str(
                    value.get("phone")
                    or value.get("contact")
                    or ""
                ),
                "status": "Verify directly",
                "source_url": str(
                    value.get("source_url")
                    or value.get("website")
                    or value.get("url")
                    or ""
                ),
                "details": str(
                    value.get("details")
                    or value.get("description")
                    or ""
                )
            })

        # Search nested objects, including SDK response wrappers.
        for key, nested in value.items():
            if key not in (
                "allocated_facilities",
                "facilities",
                "results",
                "places",
                "clinics",
                "organizations",
                "organisations"
            ):
                if isinstance(nested, (dict, list)):
                    inspect(nested)
                elif isinstance(nested, str) and (
                    nested.strip().startswith("[")
                    or nested.strip().startswith("{")
                ):
                    parsed = extract_json(nested)

                    if parsed is not None:
                        inspect(parsed)

    inspect(raw)

    # Remove duplicates and limit the results to five.
    unique = []
    seen = set()

    for facility in facilities:
        key = (
            facility["name"].strip().lower(),
            facility["location"].strip().lower()
        )

        if key not in seen:
            seen.add(key)
            unique.append(facility)

        if len(unique) == 5:
            break

    return unique


@router.post("/allocate")
async def allocate_vet_or_ngo(data: RoutineRequest):
    if not tinyfish_client:
        raise HTTPException(
            status_code=503,
            detail="TinyFish is not configured. Check TINYFISH_API_KEY."
        )

    location = data.location_name.strip()

    goal_text = f"""
Find up to five REAL veterinary clinics, veterinary hospitals,
animal rescue NGOs, or animal welfare organisations near:
{location}

Animal type: {data.pet_type}
Help required: {data.condition}

Search for facilities relevant to this location and request.

Return the results as a JSON array. For each facility, include:
- name
- type
- address
- phone
- website or source_url
- description

Use only information found in your search results.
Do not invent names, phone numbers, addresses, websites, or opening hours.
If a detail is unavailable, leave it empty.
Do not claim a facility is open or available unless the search evidence
supports that claim.

Return no more than five distinct facilities.
"""

    try:
        response = await tinyfish_client.agent.run(
            goal=goal_text,
            url="https://www.google.com/maps"
        )

        raw = jsonable_encoder(response)

        facilities = normalize_facilities(raw, location)

        if not facilities:
            # Preserve the actual response for troubleshooting instead
            # of returning fabricated facility details.
            raw_text = (
                raw
                if isinstance(raw, str)
                else json.dumps(raw, ensure_ascii=False, indent=2)
            )

            return {
                "success": True,
                "query": data.dict(),
                "allocated_facilities": [],
                "search_details": raw_text,
                "message": (
                    "TinyFish returned a response, but facility details "
                    "could not be extracted. Review the search response."
                )
            }

        return {
            "success": True,
            "query": data.dict(),
            "allocated_facilities": facilities,
            "message": (
                "Search results found. Verify contact details and "
                "availability directly before travelling."
            )
        }

    except Exception as e:
        print("ROUTINE TINYFISH ERROR:", repr(e))

        raise HTTPException(
            status_code=502,
            detail=(
                "The facility search failed. Check the TinyFish account, "
                "API key, available credits, and backend logs."
            )
        )
