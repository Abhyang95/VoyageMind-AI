from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Favorite, User


router = APIRouter(
    prefix="/favorites",
    tags=["Favorites"],
)


# ---------------------------------------------------------
# REQUEST SCHEMA
# ---------------------------------------------------------

class FavoriteRequest(BaseModel):
    destination: str


# ---------------------------------------------------------
# ADD FAVORITE
# ---------------------------------------------------------

@router.post("/")
def add_favorite(
    request: FavoriteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing_favorite = (
        db.query(Favorite)
        .filter(
            Favorite.user_id == current_user.id,
            Favorite.destination == request.destination,
        )
        .first()
    )

    if existing_favorite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Destination is already in favorites.",
        )

    favorite = Favorite(
        user_id=current_user.id,
        destination=request.destination,
    )

    db.add(favorite)
    db.commit()
    db.refresh(favorite)

    return {
        "success": True,
        "message": "Destination added to favorites.",
        "favorite": {
            "id": favorite.id,
            "destination": favorite.destination,
            "created_at": favorite.created_at,
        },
    }


# ---------------------------------------------------------
# GET ALL FAVORITES
# ---------------------------------------------------------

@router.get("/")
def get_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    favorites = (
        db.query(Favorite)
        .filter(Favorite.user_id == current_user.id)
        .order_by(Favorite.created_at.desc())
        .all()
    )

    return {
        "success": True,
        "count": len(favorites),
        "favorites": [
            {
                "id": favorite.id,
                "destination": favorite.destination,
                "created_at": favorite.created_at,
            }
            for favorite in favorites
        ],
    }


# ---------------------------------------------------------
# REMOVE FAVORITE
# ---------------------------------------------------------

@router.delete("/{favorite_id}")
def remove_favorite(
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
        "message": "Favorite removed successfully.",
    }