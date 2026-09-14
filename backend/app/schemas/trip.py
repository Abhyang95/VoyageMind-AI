from typing import List, Optional

from pydantic import BaseModel, Field


# ==========================================
# USER TRAVEL PREFERENCES
# ==========================================

class Preferences(BaseModel):

    restaurant_budget: str = Field(
        default="moderate",
        description="Restaurant spending preference",
    )

    walking_preference: bool = Field(
        default=True,
        description="Whether the user prefers walking",
    )

    hotel_preference: Optional[str] = Field(
        default="mid-range",
        description="Preferred hotel category",
    )


# ==========================================
# TRIP REQUEST
# ==========================================

class TripRequest(BaseModel):

    destination: str = Field(
        min_length=2,
        description="Travel destination",
    )

    days: int = Field(
        ge=1,
        le=30,
        description="Number of travel days",
    )

    budget: float = Field(
        gt=0,
        description="Total trip budget",
    )

    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
        description="Trip budget currency",
    )

    interests: List[str] = Field(
        min_length=1,
        description="User travel interests",
    )

    preferences: Preferences = Field(
        default_factory=Preferences,
        description="Travel preferences",
    )