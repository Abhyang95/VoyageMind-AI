import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Trip, User


router = APIRouter(prefix="/trips", tags=["Trips"])


# ============================================================
# REQUEST SCHEMA
# ============================================================

class SaveTripRequest(BaseModel):
    destination: str
    departure_date: str | None = None
    return_date: str | None = None

    days: int
    budget: float
    currency: str = "INR"

    interests: list[str] = []

    # IMPORTANT:
    # This now contains the COMPLETE generated journey snapshot.
    itinerary: str | None = None


# ============================================================
# HELPERS
# ============================================================

def normalize_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip().lower()


def parse_interests(value: Any) -> list[str]:
    if not value:
        return []

    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    try:
        parsed = json.loads(value)

        if isinstance(parsed, list):
            return [
                str(item).strip()
                for item in parsed
                if str(item).strip()
            ]
    except Exception:
        pass

    return [
        item.strip()
        for item in str(value).split(",")
        if item.strip()
    ]


def parse_snapshot(value: Any):
    if not value:
        return None

    if isinstance(value, dict):
        parsed = value
    else:
        try:
            parsed = json.loads(value)
        except Exception:
            return None

    if (
        isinstance(parsed, dict)
        and parsed.get("__voyagemind_snapshot") is True
        and parsed.get("generated_trip")
    ):
        return parsed

    return None


def trip_fingerprint(
    destination,
    departure_date,
    return_date,
    days,
    budget,
    currency,
    interests,
):
    """
    Creates a stable identity for the SAME generated journey.

    This means:

    Chicago + 4 days + ₹100000 + same interests
    = same saved journey

    But:

    Chicago + 5 days
    or Chicago + different budget
    or Chicago + different dates
    = different journey.
    """

    normalized_interests = sorted(
        normalize_text(item)
        for item in (interests or [])
        if normalize_text(item)
    )

    data = {
        "destination": normalize_text(destination),
        "departure_date": normalize_text(departure_date),
        "return_date": normalize_text(return_date),
        "days": int(days or 1),
        "budget": float(budget or 0),
        "currency": normalize_text(currency or "INR"),
        "interests": normalized_interests,
    }

    return json.dumps(data, sort_keys=True)


def trip_to_dict(trip: Trip):
    return {
        "id": trip.id,
        "destination": trip.destination,
        "departure_date": trip.departure_date,
        "return_date": trip.return_date,
        "days": trip.days,
        "budget": trip.budget,
        "currency": trip.currency,
        "interests": parse_interests(trip.interests),
        "itinerary": trip.itinerary,
        "created_at": trip.created_at,
    }


def dedupe_user_trips(
    db: Session,
    user_id: int,
):
    """
    Removes duplicate saved journeys for the current user.

    Existing Chicago duplicates will be cleaned automatically
    the next time /trips/ or /trips/save is called.
    """

    trips = (
        db.query(Trip)
        .filter(Trip.user_id == user_id)
        .order_by(Trip.created_at.desc())
        .all()
    )

    seen = {}
    duplicates = []

    for trip in trips:
        fingerprint = trip_fingerprint(
            trip.destination,
            trip.departure_date,
            trip.return_date,
            trip.days,
            trip.budget,
            trip.currency,
            parse_interests(trip.interests),
        )

        if fingerprint in seen:
            duplicates.append(trip)
        else:
            seen[fingerprint] = trip

    for duplicate in duplicates:
        db.delete(duplicate)

    if duplicates:
        db.commit()

    return list(seen.values())


# ============================================================
# SAVE JOURNEY
# ============================================================

@router.post("/save")
def save_trip(
    request: SaveTripRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Idempotent save.

    Repeated clicks for the same generated journey UPDATE the
    existing row instead of creating another row.
    """

    # Remove old duplicate rows first.
    dedupe_user_trips(
        db,
        current_user.id,
    )

    requested_interests = request.interests or []

    requested_fingerprint = trip_fingerprint(
        request.destination,
        request.departure_date,
        request.return_date,
        request.days,
        request.budget,
        request.currency,
        requested_interests,
    )

    trips = (
        db.query(Trip)
        .filter(Trip.user_id == current_user.id)
        .order_by(Trip.created_at.desc())
        .all()
    )

    existing_trip = None

    for trip in trips:
        existing_fingerprint = trip_fingerprint(
            trip.destination,
            trip.departure_date,
            trip.return_date,
            trip.days,
            trip.budget,
            trip.currency,
            parse_interests(trip.interests),
        )

        if existing_fingerprint == requested_fingerprint:
            existing_trip = trip
            break

    # --------------------------------------------------------
    # UPDATE EXISTING JOURNEY
    # --------------------------------------------------------

    if existing_trip:
        existing_trip.destination = request.destination
        existing_trip.departure_date = request.departure_date
        existing_trip.return_date = request.return_date
        existing_trip.days = request.days
        existing_trip.budget = request.budget
        existing_trip.currency = request.currency

        # Store JSON instead of comma-separated text.
        existing_trip.interests = json.dumps(
            requested_interests
        )

        existing_trip.itinerary = request.itinerary

        db.commit()
        db.refresh(existing_trip)

        return {
            "success": True,
            "message": "Journey already existed. Saved journey updated.",
            "created": False,
            "trip": trip_to_dict(existing_trip),
        }

    # --------------------------------------------------------
    # CREATE NEW JOURNEY
    # --------------------------------------------------------

    trip = Trip(
        user_id=current_user.id,
        destination=request.destination,
        departure_date=request.departure_date,
        return_date=request.return_date,
        days=request.days,
        budget=request.budget,
        currency=request.currency,
        interests=json.dumps(requested_interests),
        itinerary=request.itinerary,
    )

    db.add(trip)
    db.commit()
    db.refresh(trip)

    return {
        "success": True,
        "message": "Journey saved successfully.",
        "created": True,
        "trip": trip_to_dict(trip),
    }


# ============================================================
# GET ALL SAVED JOURNEYS
# ============================================================

@router.get("/")
def get_saved_trips(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trips = dedupe_user_trips(
        db,
        current_user.id,
    )

    # Newest first
    trips.sort(
        key=lambda trip: trip.created_at,
        reverse=True,
    )

    return {
        "success": True,
        "count": len(trips),
        "trips": [
            trip_to_dict(trip)
            for trip in trips
        ],
    }


# ============================================================
# GET ONE SAVED JOURNEY
# ============================================================

@router.get("/{trip_id}")
def get_saved_trip(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trip = (
        db.query(Trip)
        .filter(
            Trip.id == trip_id,
            Trip.user_id == current_user.id,
        )
        .first()
    )

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved journey not found.",
        )

    return {
        "success": True,
        "trip": trip_to_dict(trip),
    }


# ============================================================
# DELETE SAVED JOURNEY
# ============================================================

@router.delete("/{trip_id}")
def delete_saved_trip(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trip = (
        db.query(Trip)
        .filter(
            Trip.id == trip_id,
            Trip.user_id == current_user.id,
        )
        .first()
    )

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved journey not found.",
        )

    db.delete(trip)
    db.commit()

    return {
        "success": True,
        "message": "Journey deleted successfully.",
    }