from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================
# USER TRAVEL PREFERENCES
# ============================================================

class Preferences(BaseModel):
    """
    User preferences used by the VoyageMind trip-planning graph.
    """

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


# ============================================================
# TRIP REQUEST
# ============================================================

class TripRequest(BaseModel):
    """
    Request payload received from the VoyageMind frontend.
    """

    destination: str = Field(
        min_length=2,
        description="Travel destination",
    )

    # --------------------------------------------------------
    # TRAVEL DATES
    # --------------------------------------------------------

    departure_date: Optional[str] = Field(
        default=None,
        description="Trip departure date in YYYY-MM-DD format",
    )

    return_date: Optional[str] = Field(
        default=None,
        description="Trip return date in YYYY-MM-DD format",
    )

    # --------------------------------------------------------
    # TRIP DETAILS
    # --------------------------------------------------------

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

    # ========================================================
    # VALIDATORS
    # ========================================================

    @field_validator("destination")
    @classmethod
    def validate_destination(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 2:
            raise ValueError(
                "Destination must contain at least 2 characters."
            )

        return value

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        value = value.strip().upper()

        if len(value) != 3:
            raise ValueError(
                "Currency must be a 3-letter currency code."
            )

        return value

    @field_validator("interests")
    @classmethod
    def validate_interests(
        cls,
        value: List[str],
    ) -> List[str]:
        cleaned_interests = [
            interest.strip()
            for interest in value
            if isinstance(interest, str)
            and interest.strip()
        ]

        if not cleaned_interests:
            raise ValueError(
                "At least one travel interest is required."
            )

        return cleaned_interests