
import asyncio
import json
import time

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from config import HOSPITAL_CACHE_MINUTES, PANIC_MAX_PER_WINDOW, PANIC_WINDOW_SECONDS
from database import SessionLocal, get_db
from models import IncidentModel
from schemas import PanicRequest
from services import hospital_search, notifier
from services.ratelimit import SlidingWindowLimiter, enforce

router = APIRouter(prefix="/api/panic", tags=["Panic Button"])

limiter = SlidingWindowLimiter(PANIC_MAX_PER_WINDOW, PANIC_WINDOW_SECONDS)

DEMO_NOTICE = (
    "Demo mode: the alert was sent to the PawRescue team only. "
    "No hospital or NGO was contacted."
)

# Progress of each panic run (in memory) and recently found hospitals per area.
panic_state = {}
hospital_cache = {}


def _cache_key(latitude, longitude):
    # ~1 km grid: hospitals don't move, so a recent search is still valid nearby.
    return (round(latitude, 2), round(longitude, 2))


def _cache_get(latitude, longitude):
    entry = hospital_cache.get(_cache_key(latitude, longitude))

    if entry and time.time() - entry["ts"] < HOSPITAL_CACHE_MINUTES * 60:
        return entry

    return None


def _cache_put(latitude, longitude, hospitals):
    hospital_cache[_cache_key(latitude, longitude)] = {
        "ts": time.time(),
        "hospitals": hospitals,
    }


def _new_state(incident_id, saved):
    return {
        "incident_id": incident_id,
        "saved_to_database": saved,
        "stage": "queued",
        # pending | running | done | failed | skipped | not_configured
        "steps": {
            "location": "done",
            "hospitals": "pending",
            "contacts": "pending",
            "alert": "pending",
        },
        "hospitals": [],
        "alerts": {},
        "cached": False,
        "cache_age_minutes": None,
        "error": None,
        "demo_notice": DEMO_NOTICE,
    }


def _persist(incident_id, state):
    if incident_id < 0:
        return

    db = SessionLocal()

    try:
        incident = db.query(IncidentModel).filter(IncidentModel.id == incident_id).first()

        if incident:
            incident.scraped_clinics = json.dumps(state, ensure_ascii=False, default=str)
            db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        print("PANIC PERSIST ERROR:", type(error).__name__)
    finally:
        db.close()


async def run_panic_pipeline(incident_id, latitude, longitude, animal_type, description):
    state = panic_state[incident_id]
    search_error = None

    try:
        # Instant alert first — runs while TinyFish is still searching.
        state["steps"]["alert"] = "running"
        instant_task = asyncio.create_task(
            notifier.send_alert(
                subject=f"🚨 PawRescue panic alert (DEMO) #{incident_id}",
                text=notifier.build_instant_message(
                    incident_id, latitude, longitude, animal_type, description
                ),
                latitude=latitude,
                longitude=longitude,
            )
        )

        # ---- Step 1: nearest 5 emergency animal hospitals -----------------
        state["stage"] = "searching_hospitals"
        state["steps"]["hospitals"] = "running"
        hospitals = []
        cached = _cache_get(latitude, longitude)

        if cached:
            hospitals = cached["hospitals"]
            state["hospitals"] = hospitals
            state["cached"] = True
            state["cache_age_minutes"] = int((time.time() - cached["ts"]) / 60)
            state["steps"]["hospitals"] = "done"
            state["steps"]["contacts"] = "done"
        else:
            try:
                hospitals = await hospital_search.find_nearest_hospitals(latitude, longitude)
                state["hospitals"] = hospitals
                state["steps"]["hospitals"] = "done"
            except Exception as error:
                print("PANIC HOSPITAL SEARCH ERROR:", repr(error))
                search_error = "Hospital search failed."
                state["steps"]["hospitals"] = "failed"
                state["steps"]["contacts"] = "skipped"

            # ---- Step 2: contact details for those hospitals --------------
            if hospitals:
                state["stage"] = "fetching_contacts"
                state["steps"]["contacts"] = "running"

                try:
                    hospitals = await hospital_search.get_contact_details(hospitals)
                    state["hospitals"] = hospitals
                    state["steps"]["contacts"] = "done"
                    _cache_put(latitude, longitude, hospitals)
                except Exception as error:
                    print("PANIC CONTACT ERROR:", repr(error))
                    state["steps"]["contacts"] = "failed"

        # ---- Step 3: alert the team (demo) -------------------------------
        state["stage"] = "sending_alert"

        try:
            state["alerts"]["instant"] = await instant_task
        except Exception as error:
            print("PANIC INSTANT ALERT ERROR:", repr(error))
            state["alerts"]["instant"] = {"any_sent": False}

        followup = await notifier.send_alert(
            subject=f"🏥 PawRescue: nearest emergency hospitals (DEMO) #{incident_id}",
            text=notifier.build_hospitals_message(
                incident_id, latitude, longitude, hospitals, search_error
            ),
        )
        state["alerts"]["followup"] = followup

        statuses = [
            channel["status"]
            for report in state["alerts"].values()
            for key, channel in report.items()
            if key != "any_sent"
        ]

        if any(s in ("sent", "partial") for s in statuses):
            state["steps"]["alert"] = "done"
        elif statuses and all(s == "not_configured" for s in statuses):
            state["steps"]["alert"] = "not_configured"
        else:
            state["steps"]["alert"] = "failed"

        state["error"] = search_error
        state["stage"] = "completed"

    except Exception as error:
        print("PANIC PIPELINE ERROR:", repr(error))
        state["stage"] = "failed"
        state["error"] = "Something went wrong while processing the panic alert."
    finally:
        await asyncio.to_thread(_persist, incident_id, state)


@router.post("/trigger")
async def trigger_panic(
    data: PanicRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    enforce(
        request,
        limiter,
        "Too many panic alerts from this device. Please wait a few minutes. "
        "If this is a real emergency, call a local vet or animal rescue directly.",
    )

    animal_type = (data.animal_type or "").strip() or "Unknown"
    description = (data.description or "").strip() or "Panic button pressed. No details provided."

    saved = True

    try:
        incident = IncidentModel(
            latitude=data.latitude,
            longitude=data.longitude,
            animal_type=animal_type,
            injury_description=description,
            source="panic",
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)
        incident_id = incident.id
    except SQLAlchemyError as error:
        # A panic alert must still go out even if the database is down.
        db.rollback()
        print("PANIC DATABASE ERROR:", type(error).__name__)
        saved = False
        incident_id = -int(time.time())

    panic_state[incident_id] = _new_state(incident_id, saved)

    background_tasks.add_task(
        run_panic_pipeline,
        incident_id,
        data.latitude,
        data.longitude,
        animal_type,
        description,
    )

    return {
        "success": True,
        "incident_id": incident_id,
        "saved_to_database": saved,
        "message": "Panic alert started.",
    }


@router.get("/{incident_id}")
async def get_panic_status(incident_id: int, db: Session = Depends(get_db)):
    state = panic_state.get(incident_id)

    if state:
        return state

    # Fall back to the saved copy (e.g. after a server restart).
    incident = (
        db.query(IncidentModel)
        .filter(IncidentModel.id == incident_id, IncidentModel.source == "panic")
        .first()
    )

    if incident and incident.scraped_clinics:
        try:
            return json.loads(incident.scraped_clinics)
        except json.JSONDecodeError:
            pass

    raise HTTPException(status_code=404, detail="Panic report not found.")