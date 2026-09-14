from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Trip, User


router = APIRouter(
    prefix="/trips",
    tags=["Trips"],
)


# ---------------------------------------------------------
# REQUEST SCHEMA
# ---------------------------------------------------------

class SaveTripRequest(BaseModel):
    destination: str
    departure_date: str | None = None
    return_date: str | None = None
    days: int
    budget: float
    currency: str = "INR"
    interests: list[str] = []
    itinerary: str | None = None


# ---------------------------------------------------------
# SAVE TRIP
# ---------------------------------------------------------

@router.post("/save")
def save_trip(
    request: SaveTripRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trip = Trip(
        user_id=current_user.id,
        destination=request.destination,
        departure_date=request.departure_date,
        return_date=request.return_date,
        days=request.days,
        budget=request.budget,
        currency=request.currency,
        interests=",".join(request.interests),
        itinerary=request.itinerary,
    )

    db.add(trip)
    db.commit()
    db.refresh(trip)

    return {
        "success": True,
        "message": "Trip saved successfully.",
        "trip": {
            "id": trip.id,
            "destination": trip.destination,
            "departure_date": trip.departure_date,
            "return_date": trip.return_date,
            "days": trip.days,
            "budget": trip.budget,
            "currency": trip.currency,
            "interests": request.interests,
            "itinerary": trip.itinerary,
            "created_at": trip.created_at,
        },
    }


# ---------------------------------------------------------
# GET ALL SAVED TRIPS
# ---------------------------------------------------------

@router.get("/")
def get_saved_trips(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trips = (
        db.query(Trip)
        .filter(Trip.user_id == current_user.id)
        .order_by(Trip.created_at.desc())
        .all()
    )

    return {
        "success": True,
        "count": len(trips),
        "trips": [
            {
                "id": trip.id,
                "destination": trip.destination,
                "departure_date": trip.departure_date,
                "return_date": trip.return_date,
                "days": trip.days,
                "budget": trip.budget,
                "currency": trip.currency,
                "interests": (
                    trip.interests.split(",")
                    if trip.interests
                    else []
                ),
                "itinerary": trip.itinerary,
                "created_at": trip.created_at,
            }
            for trip in trips
        ],
    }


# ---------------------------------------------------------
# GET SINGLE SAVED TRIP
# ---------------------------------------------------------

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
            detail="Trip not found.",
        )

    return {
        "success": True,
        "trip": {
            "id": trip.id,
            "destination": trip.destination,
            "departure_date": trip.departure_date,
            "return_date": trip.return_date,
            "days": trip.days,
            "budget": trip.budget,
            "currency": trip.currency,
            "interests": (
                trip.interests.split(",")
                if trip.interests
                else []
            ),
            "itinerary": trip.itinerary,
            "created_at": trip.created_at,
        },
    }


# ---------------------------------------------------------
# DELETE SAVED TRIP
# ---------------------------------------------------------

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
            detail="Trip not found.",
        )

    db.delete(trip)
    db.commit()

    return {
        "success": True,
        "message": "Trip deleted successfully.",
    }