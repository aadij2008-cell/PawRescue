import json
import re
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from schemas import EmergencyRequest
from database import get_db
from models import IncidentModel
from tinyfish import AsyncTinyFish
from config import TINYFISH_API_KEY

router = APIRouter(
    prefix="/api/emergency",
    tags=["Emergency Operations"]
)
tinyfish_client = AsyncTinyFish(
    api_key=TINYFISH_API_KEY,
    timeout=120.0
) if TINYFISH_API_KEY else None

# In-memory storage for active search results
vet_search_results = {}

async def search_vets_in_background(
    incident_id: int,
    latitude: float,
    longitude: float,
    db_session_factory
):
    """Search for nearby emergency veterinary clinics using a fast, optimized TinyFish goal."""
    vet_search_results[incident_id] = {
        "status": "searching",
        "results": None,
        "error": None
    }

    if not tinyfish_client:
        vet_search_results[incident_id] = {
            "status": "not_configured",
            "results": None,
            "error": "TinyFish API key is not configured."
        }
        return

    # OPTIMIZED GOAL: Shorter and more direct for faster browser execution
    goal_text = (
        f"Find 24/7 emergency vets near coordinates {latitude}, {longitude}. "
        "List names, addresses, and phone numbers."
    )

    try:
        agent_response = await tinyfish_client.agent.run(
            goal=goal_text,
            url="https://www.google.com/maps"
        )

        encoded_results = jsonable_encoder(agent_response)

        vet_search_results[incident_id] = {
            "status": "completed",
            "results": encoded_results,
            "error": None
        }

        # Save cached results into database incident record for future speedups
        db = db_session_factory()
        try:
            incident = db.query(IncidentModel).filter(IncidentModel.id == incident_id).first()
            if incident:
                # Store encoded response string/json in database if your model supports it
                # (Assuming you added or use a text column, otherwise safely ignored)
                db=db_session_factory()
                try:
                    incident=(db.query(IncidentModel).filter(IncidentModel.id==incident_id).first())
                    if incident:
                        incident.scraped_clinics=json.dumps(encoded_results)
                        db.commit()
                except Exception as db_err:
                    db.rollback()
                    print("Database save error:", db_err)
                finally:
                    db.close()
        except Exception as db_err:
            print("Cache save error:", db_err)
        finally:
            db.close()

        print(f"TinyFish search completed quickly for incident {incident_id}")

    except Exception as e:
        print(f"TINYFISH ERROR for incident {incident_id}:", repr(e))
        vet_search_results[incident_id] = {
            "status": "failed",
            "results": None,
            "error": "The veterinary search could not be completed."
        }


@router.post("/broadcast")
async def broadcast_emergency(
    data: EmergencyRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # CACHING CHECK: Look for a recent incident with nearly identical coordinates (within ~100 meters)
    recent_threshold = datetime.utcnow() - timedelta(minutes=30)
    cached_incident = db.query(IncidentModel).filter(
        IncidentModel.latitude.between(data.latitude - 0.001, data.latitude + 0.001),
        IncidentModel.longitude.between(data.longitude - 0.001, data.longitude + 0.001),
        IncidentModel.created_at>=recent_threshold
    ).order_by(IncidentModel.id.desc()).first()
    

    # STEP 1: Save the new emergency report.
    try:
        new_incident = IncidentModel(
            latitude=data.latitude,
            longitude=data.longitude,
            animal_type=data.animal_type,
            injury_description=data.injury_description
        )

        db.add(new_incident)
        db.commit()
        db.refresh(new_incident)
        incident_id = new_incident.id

    except SQLAlchemyError as e:
        db.rollback()
        print("DATABASE ERROR:", repr(e))
        raise HTTPException(
            status_code=503,
            detail="The emergency report could not be saved. Please retry."
        )

    # If we have a recent successful search nearby, copy its results to make it INSTANT
    if cached_incident and cached_incident.id in vet_search_results and vet_search_results[cached_incident.id]["status"] == "completed":
        vet_search_results[incident_id] = vet_search_results[cached_incident.id]
        return {
            "success": True,
            "incident_id": incident_id,
            "message": "Emergency report saved. Loaded cached nearby vet results instantly.",
            "vet_search_status": "completed",
            "live_vets_scraped": vet_search_results[incident_id]["results"]
        }

    # STEP 2: Start the optimized clinic search in the background.
    vet_search_results[incident_id] = {
        "status": "queued",
        "results": None,
        "error": None
    }

    from database import SessionLocal
    background_tasks.add_task(
        search_vets_in_background,
        incident_id,
        data.latitude,
        data.longitude,
        SessionLocal
    )

    # STEP 3: Return immediately.
    return {
        "success": True,
        "incident_id": incident_id,
        "message": "Emergency report saved successfully.",
        "vet_search_status": "searching",
        "live_vets_scraped": None
    }


@router.get("/search/{incident_id}")
async def get_vet_search_results(incident_id: int):
    """Check the progress and results of a veterinary clinic search."""
    result = vet_search_results.get(incident_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Search results are unavailable. The incident may be unknown or the backend restarted."
        )

    return {
        "incident_id": incident_id,
        "vet_search_status": result["status"],
        "live_vets_scraped": result["results"],
        "error": result["error"]
    }