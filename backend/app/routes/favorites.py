from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Favorite, Trip, User


router = APIRouter(
    prefix="/favorites",
    tags=["Favorites"],
)


class FavoriteRequest(BaseModel):
    destination: str


def normalize_destination(value):
    return str(value or "").strip().lower()


def favorite_to_dict(favorite, trip=None):
    return {
        "id": favorite.id,
        "destination": favorite.destination,
        "created_at": favorite.created_at,

        # NEW:
        # Frontend can use this to open the actual saved journey.
        "trip_id": trip.id if trip else None,
        "trip": (
            {
                "id": trip.id,
                "destination": trip.destination,
                "departure_date": trip.departure_date,
                "return_date": trip.return_date,
                "days": trip.days,
                "budget": trip.budget,
                "currency": trip.currency,
                "interests": (
                    trip.interests
                    if isinstance(trip.interests, list)
                    else trip.interests
                ),
                "itinerary": trip.itinerary,
                "created_at": trip.created_at,
            }
            if trip
            else None
        ),
    }


def dedupe_favorites(
    db: Session,
    user_id: int,
):
    favorites = (
        db.query(Favorite)
        .filter(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc())
        .all()
    )

    seen = {}
    duplicates = []

    for favorite in favorites:
        key = normalize_destination(
            favorite.destination
        )

        if key in seen:
            duplicates.append(favorite)
        else:
            seen[key] = favorite

    for duplicate in duplicates:
        db.delete(duplicate)

    if duplicates:
        db.commit()

    return list(seen.values())


# ============================================================
# ADD FAVORITE
# ============================================================

@router.post("/")
def add_favorite(
    request: FavoriteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    favorites = dedupe_favorites(
        db,
        current_user.id,
    )

    destination_key = normalize_destination(
        request.destination
    )

    # Idempotent favorite.
    for favorite in favorites:
        if (
            normalize_destination(
                favorite.destination
            )
            == destination_key
        ):
            trip = (
                db.query(Trip)
                .filter(
                    Trip.user_id == current_user.id,
                    Trip.destination.ilike(
                        favorite.destination
                    ),
                )
                .order_by(Trip.created_at.desc())
                .first()
            )

            return {
                "success": True,
                "message": "Already favorited.",
                "created": False,
                "favorite": favorite_to_dict(
                    favorite,
                    trip,
                ),
            }

    favorite = Favorite(
        user_id=current_user.id,
        destination=request.destination,
    )

    db.add(favorite)
    db.commit()
    db.refresh(favorite)

    trip = (
        db.query(Trip)
        .filter(
            Trip.user_id == current_user.id,
            Trip.destination.ilike(
                request.destination
            ),
        )
        .order_by(Trip.created_at.desc())
        .first()
    )

    return {
        "success": True,
        "message": "Added to favorites.",
        "created": True,
        "favorite": favorite_to_dict(
            favorite,
            trip,
        ),
    }


# ============================================================
# GET FAVORITES
# ============================================================

@router.get("/")
def get_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    favorites = dedupe_favorites(
        db,
        current_user.id,
    )

    result = []

    for favorite in favorites:
        # Match favorite → newest saved journey.
        trip = (
            db.query(Trip)
            .filter(
                Trip.user_id == current_user.id,
                Trip.destination.ilike(
                    favorite.destination
                ),
            )
            .order_by(Trip.created_at.desc())
            .first()
        )

        result.append(
            favorite_to_dict(
                favorite,
                trip,
            )
        )

    return {
        "success": True,
        "count": len(result),
        "favorites": result,
    }


# ============================================================
# DELETE FAVORITE
# ============================================================

@router.delete("/{favorite_id}")
def delete_favorite(
    favorite_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    favorite = (
        db.query(Favorite)
        .filter(
            Favorite.id == favorite_id,
            Favorite.user_id == current_user.id,
        )
        .first()
    )

    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found.",
        )

    db.delete(favorite)
    db.commit()

    return {
        "success": True,
        "message": "Removed from favorites.",
    }