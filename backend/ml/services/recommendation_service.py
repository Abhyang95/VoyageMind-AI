from pathlib import Path
import hashlib
import math

import joblib

from app.config import BASE_DIR
from ml.services.currency_service import convert_currency


# ============================================================
# MODEL CONFIGURATION
# ============================================================

MODEL_PATH = (
    Path(BASE_DIR)
    / "ml"
    / "models"
    / "travel_recommender.pkl"
)

MODEL = None

# ML model is trained using USD-based cost values.
ML_CURRENCY = "USD"


# ============================================================
# LOAD ML MODEL
# ============================================================

def get_model():
    """
    Load the trained recommendation model.

    Supports:
    1. Normal sklearn model
    2. Model stored inside a dictionary
    """

    global MODEL

    if MODEL is not None:
        return MODEL

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Travel recommendation model not found: {MODEL_PATH}"
        )

    loaded_model = joblib.load(MODEL_PATH)

    # --------------------------------------------------------
    # Case 1: Normal sklearn model
    # --------------------------------------------------------

    if hasattr(loaded_model, "predict"):
        MODEL = loaded_model
        return MODEL

    # --------------------------------------------------------
    # Case 2: Model stored inside dictionary
    # --------------------------------------------------------

    if isinstance(loaded_model, dict):

        possible_keys = [
            "model",
            "ml_model",
            "estimator",
            "classifier",
            "regressor",
            "pipeline",
            "best_model",
        ]

        # Try known keys first
        for key in possible_keys:

            candidate = loaded_model.get(key)

            if (
                candidate is not None
                and hasattr(candidate, "predict")
            ):
                MODEL = candidate
                return MODEL

        # ----------------------------------------------------
        # Search every dictionary value
        # ----------------------------------------------------

        for value in loaded_model.values():

            if hasattr(value, "predict"):
                MODEL = value
                return MODEL

    # --------------------------------------------------------
    # Unsupported format
    # --------------------------------------------------------

    raise TypeError(
        "travel_recommender.pkl does not contain a "
        "predictable ML model. "
        f"Loaded object type: {type(loaded_model).__name__}."
    )


# ============================================================
# DESTINATION DATASET
# ============================================================
#
# KEEP YOUR EXISTING DESTINATIONS LIST EXACTLY AS IT IS.
#
# Paste your complete DESTINATIONS = [...] list here.
#
# ============================================================

DESTINATIONS = [

    # ========================================================
    # EUROPE
    # ========================================================

    {
        "destination": "Paris",
        "country": "France",
        "region": "Europe",

        "architecture_score": 0.98,
        "history_score": 0.96,
        "food_score": 0.97,
        "nightlife_score": 0.88,
        "museums_score": 0.99,
        "nature_score": 0.65,
        "shopping_score": 0.94,
        "adventure_score": 0.45,

        "average_daily_cost": 180,
        "walkability_score": 0.95,
        "weather_score": 0.82,

        "hotel_price": 140,
        "restaurant_price": 65,
    },

    {
        "destination": "Rome",
        "country": "Italy",
        "region": "Europe",

        "architecture_score": 1.00,
        "history_score": 1.00,
        "food_score": 0.98,
        "nightlife_score": 0.82,
        "museums_score": 0.96,
        "nature_score": 0.58,
        "shopping_score": 0.88,
        "adventure_score": 0.42,

        "average_daily_cost": 145,
        "walkability_score": 0.91,
        "weather_score": 0.88,

        "hotel_price": 105,
        "restaurant_price": 48,
    },

    {
        "destination": "Barcelona",
        "country": "Spain",
        "region": "Europe",

        "architecture_score": 0.98,
        "history_score": 0.89,
        "food_score": 0.96,
        "nightlife_score": 0.98,
        "museums_score": 0.87,
        "nature_score": 0.78,
        "shopping_score": 0.90,
        "adventure_score": 0.68,

        "average_daily_cost": 150,
        "walkability_score": 0.94,
        "weather_score": 0.91,

        "hotel_price": 110,
        "restaurant_price": 50,
    },

    {
        "destination": "Amsterdam",
        "country": "Netherlands",
        "region": "Europe",

        "architecture_score": 0.94,
        "history_score": 0.88,
        "food_score": 0.82,
        "nightlife_score": 0.91,
        "museums_score": 0.94,
        "nature_score": 0.76,
        "shopping_score": 0.84,
        "adventure_score": 0.50,

        "average_daily_cost": 175,
        "walkability_score": 0.96,
        "weather_score": 0.72,

        "hotel_price": 130,
        "restaurant_price": 58,
    },

    {
        "destination": "London",
        "country": "United Kingdom",
        "region": "Europe",

        "architecture_score": 0.92,
        "history_score": 0.95,
        "food_score": 0.88,
        "nightlife_score": 0.95,
        "museums_score": 0.99,
        "nature_score": 0.65,
        "shopping_score": 0.96,
        "adventure_score": 0.45,

        "average_daily_cost": 220,
        "walkability_score": 0.91,
        "weather_score": 0.68,

        "hotel_price": 165,
        "restaurant_price": 70,
    },

    {
        "destination": "Prague",
        "country": "Czech Republic",
        "region": "Europe",

        "architecture_score": 0.97,
        "history_score": 0.95,
        "food_score": 0.78,
        "nightlife_score": 0.91,
        "museums_score": 0.83,
        "nature_score": 0.67,
        "shopping_score": 0.76,
        "adventure_score": 0.55,

        "average_daily_cost": 95,
        "walkability_score": 0.93,
        "weather_score": 0.78,

        "hotel_price": 65,
        "restaurant_price": 35,
    },

    {
        "destination": "Vienna",
        "country": "Austria",
        "region": "Europe",

        "architecture_score": 0.98,
        "history_score": 0.96,
        "food_score": 0.86,
        "nightlife_score": 0.75,
        "museums_score": 0.96,
        "nature_score": 0.68,
        "shopping_score": 0.82,
        "adventure_score": 0.40,

        "average_daily_cost": 165,
        "walkability_score": 0.92,
        "weather_score": 0.79,

        "hotel_price": 115,
        "restaurant_price": 55,
    },

    {
        "destination": "Athens",
        "country": "Greece",
        "region": "Europe",

        "architecture_score": 0.95,
        "history_score": 1.00,
        "food_score": 0.91,
        "nightlife_score": 0.88,
        "museums_score": 0.92,
        "nature_score": 0.73,
        "shopping_score": 0.75,
        "adventure_score": 0.62,

        "average_daily_cost": 110,
        "walkability_score": 0.86,
        "weather_score": 0.92,

        "hotel_price": 75,
        "restaurant_price": 38,
    },

    {
        "destination": "Lisbon",
        "country": "Portugal",
        "region": "Europe",

        "architecture_score": 0.91,
        "history_score": 0.90,
        "food_score": 0.94,
        "nightlife_score": 0.92,
        "museums_score": 0.79,
        "nature_score": 0.79,
        "shopping_score": 0.78,
        "adventure_score": 0.67,

        "average_daily_cost": 105,
        "walkability_score": 0.89,
        "weather_score": 0.94,

        "hotel_price": 72,
        "restaurant_price": 37,
    },

    {
        "destination": "Budapest",
        "country": "Hungary",
        "region": "Europe",

        "architecture_score": 0.93,
        "history_score": 0.91,
        "food_score": 0.84,
        "nightlife_score": 0.94,
        "museums_score": 0.80,
        "nature_score": 0.70,
        "shopping_score": 0.75,
        "adventure_score": 0.58,

        "average_daily_cost": 90,
        "walkability_score": 0.91,
        "weather_score": 0.80,

        "hotel_price": 62,
        "restaurant_price": 32,
    },

    {
        "destination": "Florence",
        "country": "Italy",
        "region": "Europe",

        "architecture_score": 1.00,
        "history_score": 0.99,
        "food_score": 0.96,
        "nightlife_score": 0.70,
        "museums_score": 1.00,
        "nature_score": 0.65,
        "shopping_score": 0.89,
        "adventure_score": 0.40,

        "average_daily_cost": 135,
        "walkability_score": 0.95,
        "weather_score": 0.89,

        "hotel_price": 95,
        "restaurant_price": 45,
    },

    {
        "destination": "Dublin",
        "country": "Ireland",
        "region": "Europe",

        "architecture_score": 0.82,
        "history_score": 0.90,
        "food_score": 0.80,
        "nightlife_score": 0.95,
        "museums_score": 0.79,
        "nature_score": 0.80,
        "shopping_score": 0.79,
        "adventure_score": 0.63,

        "average_daily_cost": 175,
        "walkability_score": 0.88,
        "weather_score": 0.66,

        "hotel_price": 125,
        "restaurant_price": 55,
    },

    # ========================================================
    # ASIA
    # ========================================================

    {
        "destination": "Tokyo",
        "country": "Japan",
        "region": "Asia",

        "architecture_score": 0.93,
        "history_score": 0.88,
        "food_score": 0.99,
        "nightlife_score": 0.96,
        "museums_score": 0.91,
        "nature_score": 0.77,
        "shopping_score": 1.00,
        "adventure_score": 0.66,

        "average_daily_cost": 155,
        "walkability_score": 0.93,
        "weather_score": 0.83,

        "hotel_price": 105,
        "restaurant_price": 50,
    },

    {
        "destination": "Kyoto",
        "country": "Japan",
        "region": "Asia",

        "architecture_score": 1.00,
        "history_score": 1.00,
        "food_score": 0.98,
        "nightlife_score": 0.60,
        "museums_score": 0.88,
        "nature_score": 0.91,
        "shopping_score": 0.78,
        "adventure_score": 0.65,

        "average_daily_cost": 145,
        "walkability_score": 0.90,
        "weather_score": 0.82,

        "hotel_price": 100,
        "restaurant_price": 45,
    },

    {
        "destination": "Seoul",
        "country": "South Korea",
        "region": "Asia",

        "architecture_score": 0.90,
        "history_score": 0.84,
        "food_score": 0.98,
        "nightlife_score": 0.97,
        "museums_score": 0.86,
        "nature_score": 0.78,
        "shopping_score": 0.98,
        "adventure_score": 0.67,

        "average_daily_cost": 125,
        "walkability_score": 0.91,
        "weather_score": 0.81,

        "hotel_price": 82,
        "restaurant_price": 42,
    },

    {
        "destination": "Bangkok",
        "country": "Thailand",
        "region": "Asia",

        "architecture_score": 0.82,
        "history_score": 0.80,
        "food_score": 1.00,
        "nightlife_score": 0.99,
        "museums_score": 0.72,
        "nature_score": 0.70,
        "shopping_score": 0.94,
        "adventure_score": 0.82,

        "average_daily_cost": 70,
        "walkability_score": 0.76,
        "weather_score": 0.91,

        "hotel_price": 45,
        "restaurant_price": 25,
    },

    {
        "destination": "Bali",
        "country": "Indonesia",
        "region": "Asia",

        "architecture_score": 0.72,
        "history_score": 0.70,
        "food_score": 0.91,
        "nightlife_score": 0.88,
        "museums_score": 0.55,
        "nature_score": 0.99,
        "shopping_score": 0.77,
        "adventure_score": 0.97,

        "average_daily_cost": 80,
        "walkability_score": 0.62,
        "weather_score": 0.94,

        "hotel_price": 48,
        "restaurant_price": 28,
    },

    {
        "destination": "Singapore",
        "country": "Singapore",
        "region": "Asia",

        "architecture_score": 0.88,
        "history_score": 0.70,
        "food_score": 0.97,
        "nightlife_score": 0.92,
        "museums_score": 0.76,
        "nature_score": 0.82,
        "shopping_score": 0.99,
        "adventure_score": 0.60,

        "average_daily_cost": 190,
        "walkability_score": 0.94,
        "weather_score": 0.93,

        "hotel_price": 135,
        "restaurant_price": 55,
    },

    {
        "destination": "Kuala Lumpur",
        "country": "Malaysia",
        "region": "Asia",

        "architecture_score": 0.83,
        "history_score": 0.76,
        "food_score": 0.96,
        "nightlife_score": 0.87,
        "museums_score": 0.67,
        "nature_score": 0.72,
        "shopping_score": 0.96,
        "adventure_score": 0.72,

        "average_daily_cost": 75,
        "walkability_score": 0.75,
        "weather_score": 0.92,

        "hotel_price": 48,
        "restaurant_price": 25,
    },

    {
        "destination": "Hanoi",
        "country": "Vietnam",
        "region": "Asia",

        "architecture_score": 0.83,
        "history_score": 0.90,
        "food_score": 0.98,
        "nightlife_score": 0.81,
        "museums_score": 0.75,
        "nature_score": 0.76,
        "shopping_score": 0.77,
        "adventure_score": 0.72,

        "average_daily_cost": 65,
        "walkability_score": 0.82,
        "weather_score": 0.87,

        "hotel_price": 40,
        "restaurant_price": 23,
    },

    {
        "destination": "Phuket",
        "country": "Thailand",
        "region": "Asia",

        "architecture_score": 0.62,
        "history_score": 0.60,
        "food_score": 0.90,
        "nightlife_score": 0.92,
        "museums_score": 0.48,
        "nature_score": 0.97,
        "shopping_score": 0.74,
        "adventure_score": 0.94,

        "average_daily_cost": 85,
        "walkability_score": 0.58,
        "weather_score": 0.95,

        "hotel_price": 50,
        "restaurant_price": 28,
    },

    # ========================================================
    # MIDDLE EAST
    # ========================================================

    {
        "destination": "Dubai",
        "country": "United Arab Emirates",
        "region": "Middle East",

        "architecture_score": 0.94,
        "history_score": 0.68,
        "food_score": 0.96,
        "nightlife_score": 0.96,
        "museums_score": 0.73,
        "nature_score": 0.68,
        "shopping_score": 1.00,
        "adventure_score": 0.91,

        "average_daily_cost": 220,
        "walkability_score": 0.62,
        "weather_score": 0.95,

        "hotel_price": 155,
        "restaurant_price": 65,
    },

    {
        "destination": "Abu Dhabi",
        "country": "United Arab Emirates",
        "region": "Middle East",

        "architecture_score": 0.96,
        "history_score": 0.71,
        "food_score": 0.91,
        "nightlife_score": 0.78,
        "museums_score": 0.86,
        "nature_score": 0.69,
        "shopping_score": 0.93,
        "adventure_score": 0.72,

        "average_daily_cost": 190,
        "walkability_score": 0.63,
        "weather_score": 0.96,

        "hotel_price": 135,
        "restaurant_price": 58,
    },

    {
        "destination": "Muscat",
        "country": "Oman",
        "region": "Middle East",

        "architecture_score": 0.86,
        "history_score": 0.84,
        "food_score": 0.83,
        "nightlife_score": 0.48,
        "museums_score": 0.64,
        "nature_score": 0.92,
        "shopping_score": 0.69,
        "adventure_score": 0.89,

        "average_daily_cost": 120,
        "walkability_score": 0.65,
        "weather_score": 0.94,

        "hotel_price": 78,
        "restaurant_price": 36,
    },

    # ========================================================
    # NORTH AMERICA
    # ========================================================

    {
        "destination": "New York",
        "country": "United States",
        "region": "North America",

        "architecture_score": 0.94,
        "history_score": 0.86,
        "food_score": 0.98,
        "nightlife_score": 1.00,
        "museums_score": 1.00,
        "nature_score": 0.60,
        "shopping_score": 0.99,
        "adventure_score": 0.54,

        "average_daily_cost": 260,
        "walkability_score": 0.93,
        "weather_score": 0.75,

        "hotel_price": 195,
        "restaurant_price": 78,
    },

    {
        "destination": "Vancouver",
        "country": "Canada",
        "region": "North America",

        "architecture_score": 0.78,
        "history_score": 0.70,
        "food_score": 0.90,
        "nightlife_score": 0.79,
        "museums_score": 0.77,
        "nature_score": 0.99,
        "shopping_score": 0.82,
        "adventure_score": 0.94,

        "average_daily_cost": 180,
        "walkability_score": 0.88,
        "weather_score": 0.78,

        "hotel_price": 125,
        "restaurant_price": 55,
    },

    {
        "destination": "Banff",
        "country": "Canada",
        "region": "North America",

        "architecture_score": 0.50,
        "history_score": 0.55,
        "food_score": 0.72,
        "nightlife_score": 0.40,
        "museums_score": 0.42,
        "nature_score": 1.00,
        "shopping_score": 0.50,
        "adventure_score": 1.00,

        "average_daily_cost": 190,
        "walkability_score": 0.73,
        "weather_score": 0.79,

        "hotel_price": 130,
        "restaurant_price": 55,
    },

    {
        "destination": "Mexico City",
        "country": "Mexico",
        "region": "North America",

        "architecture_score": 0.91,
        "history_score": 0.94,
        "food_score": 1.00,
        "nightlife_score": 0.95,
        "museums_score": 0.97,
        "nature_score": 0.67,
        "shopping_score": 0.86,
        "adventure_score": 0.70,

        "average_daily_cost": 85,
        "walkability_score": 0.82,
        "weather_score": 0.90,

        "hotel_price": 55,
        "restaurant_price": 30,
    },

    {
        "destination": "New Orleans",
        "country": "United States",
        "region": "North America",

        "architecture_score": 0.89,
        "history_score": 0.92,
        "food_score": 0.99,
        "nightlife_score": 0.98,
        "museums_score": 0.75,
        "nature_score": 0.60,
        "shopping_score": 0.67,
        "adventure_score": 0.58,

        "average_daily_cost": 125,
        "walkability_score": 0.86,
        "weather_score": 0.88,

        "hotel_price": 80,
        "restaurant_price": 42,
    },

    # ========================================================
    # SOUTH AMERICA
    # ========================================================

    {
        "destination": "Rio de Janeiro",
        "country": "Brazil",
        "region": "South America",

        "architecture_score": 0.75,
        "history_score": 0.72,
        "food_score": 0.91,
        "nightlife_score": 0.98,
        "museums_score": 0.65,
        "nature_score": 0.99,
        "shopping_score": 0.78,
        "adventure_score": 0.96,

        "average_daily_cost": 90,
        "walkability_score": 0.70,
        "weather_score": 0.95,

        "hotel_price": 55,
        "restaurant_price": 30,
    },

    {
        "destination": "Buenos Aires",
        "country": "Argentina",
        "region": "South America",

        "architecture_score": 0.91,
        "history_score": 0.86,
        "food_score": 0.97,
        "nightlife_score": 0.96,
        "museums_score": 0.84,
        "nature_score": 0.58,
        "shopping_score": 0.84,
        "adventure_score": 0.52,

        "average_daily_cost": 80,
        "walkability_score": 0.88,
        "weather_score": 0.88,

        "hotel_price": 52,
        "restaurant_price": 28,
    },

    # ========================================================
    # AFRICA
    # ========================================================

    {
        "destination": "Cape Town",
        "country": "South Africa",
        "region": "Africa",

        "architecture_score": 0.75,
        "history_score": 0.78,
        "food_score": 0.88,
        "nightlife_score": 0.83,
        "museums_score": 0.71,
        "nature_score": 1.00,
        "shopping_score": 0.76,
        "adventure_score": 1.00,

        "average_daily_cost": 95,
        "walkability_score": 0.72,
        "weather_score": 0.94,

        "hotel_price": 60,
        "restaurant_price": 32,
    },

    {
        "destination": "Marrakech",
        "country": "Morocco",
        "region": "Africa",

        "architecture_score": 0.94,
        "history_score": 0.94,
        "food_score": 0.93,
        "nightlife_score": 0.71,
        "museums_score": 0.69,
        "nature_score": 0.77,
        "shopping_score": 0.90,
        "adventure_score": 0.82,

        "average_daily_cost": 75,
        "walkability_score": 0.81,
        "weather_score": 0.92,

        "hotel_price": 45,
        "restaurant_price": 25,
    },

    {
        "destination": "Nairobi",
        "country": "Kenya",
        "region": "Africa",

        "architecture_score": 0.55,
        "history_score": 0.66,
        "food_score": 0.75,
        "nightlife_score": 0.74,
        "museums_score": 0.62,
        "nature_score": 0.97,
        "shopping_score": 0.68,
        "adventure_score": 0.98,

        "average_daily_cost": 80,
        "walkability_score": 0.56,
        "weather_score": 0.88,

        "hotel_price": 48,
        "restaurant_price": 27,
    },

    # ========================================================
    # OCEANIA
    # ========================================================

    {
        "destination": "Sydney",
        "country": "Australia",
        "region": "Oceania",

        "architecture_score": 0.87,
        "history_score": 0.70,
        "food_score": 0.94,
        "nightlife_score": 0.91,
        "museums_score": 0.82,
        "nature_score": 0.91,
        "shopping_score": 0.94,
        "adventure_score": 0.82,

        "average_daily_cost": 190,
        "walkability_score": 0.89,
        "weather_score": 0.92,

        "hotel_price": 135,
        "restaurant_price": 60,
    },

    {
        "destination": "Melbourne",
        "country": "Australia",
        "region": "Oceania",

        "architecture_score": 0.89,
        "history_score": 0.75,
        "food_score": 0.98,
        "nightlife_score": 0.92,
        "museums_score": 0.87,
        "nature_score": 0.84,
        "shopping_score": 0.93,
        "adventure_score": 0.75,

        "average_daily_cost": 180,
        "walkability_score": 0.91,
        "weather_score": 0.79,

        "hotel_price": 125,
        "restaurant_price": 58,
    },

    {
        "destination": "Queenstown",
        "country": "New Zealand",
        "region": "Oceania",

        "architecture_score": 0.55,
        "history_score": 0.52,
        "food_score": 0.77,
        "nightlife_score": 0.70,
        "museums_score": 0.45,
        "nature_score": 1.00,
        "shopping_score": 0.51,
        "adventure_score": 1.00,

        "average_daily_cost": 165,
        "walkability_score": 0.79,
        "weather_score": 0.82,

        "hotel_price": 110,
        "restaurant_price": 48,
    },

    {
        "destination": "Auckland",
        "country": "New Zealand",
        "region": "Oceania",

        "architecture_score": 0.70,
        "history_score": 0.64,
        "food_score": 0.88,
        "nightlife_score": 0.79,
        "museums_score": 0.72,
        "nature_score": 0.94,
        "shopping_score": 0.83,
        "adventure_score": 0.91,

        "average_daily_cost": 155,
        "walkability_score": 0.77,
        "weather_score": 0.84,

        "hotel_price": 105,
        "restaurant_price": 48,
    },

    # ========================================================
    # SWITZERLAND
    # ========================================================

    {
        "destination": "Interlaken",
        "country": "Switzerland",
        "region": "Europe",

        "architecture_score": 0.60,
        "history_score": 0.58,
        "food_score": 0.78,
        "nightlife_score": 0.48,
        "museums_score": 0.40,
        "nature_score": 1.00,
        "shopping_score": 0.55,
        "adventure_score": 1.00,

        "average_daily_cost": 230,
        "walkability_score": 0.84,
        "weather_score": 0.81,

        "hotel_price": 165,
        "restaurant_price": 65,
    },

    # ========================================================
    # TURKEY
    # ========================================================

    {
        "destination": "Istanbul",
        "country": "Turkey",
        "region": "Europe",

        "architecture_score": 0.93,
        "history_score": 0.96,
        "food_score": 0.94,
        "nightlife_score": 0.84,
        "museums_score": 0.88,
        "nature_score": 0.65,
        "shopping_score": 0.92,
        "adventure_score": 0.55,

        "average_daily_cost": 95,
        "walkability_score": 0.83,
        "weather_score": 0.87,

        "hotel_price": 62,
        "restaurant_price": 32,
    },
]


# ============================================================
# INTEREST MAPPING
# ============================================================

INTEREST_COLUMNS = {
    "architecture": "architecture_score",
    "history": "history_score",
    "food": "food_score",
    "nightlife": "nightlife_score",
    "museums": "museums_score",
    "nature": "nature_score",
    "shopping": "shopping_score",
    "adventure": "adventure_score",
}


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_interest(interest: str) -> str:
    return str(interest).strip().lower()


def normalize_interests(interests):
    if not interests:
        return []

    normalized = []

    for interest in interests:

        value = normalize_interest(interest)

        if (
            value in INTEREST_COLUMNS
            and value not in normalized
        ):
            normalized.append(value)

    return normalized


# ============================================================
# INTEREST SCORE
# ============================================================

def calculate_interest_preference_score(
    destination: dict,
    interests: list[str],
) -> float:

    if not interests:
        return 0.5

    scores = []

    for interest in interests:

        column = INTEREST_COLUMNS.get(
            normalize_interest(interest)
        )

        if column:
            scores.append(
                float(
                    destination.get(
                        column,
                        0.0,
                    )
                )
            )

    if not scores:
        return 0.5

    average_score = (
        sum(scores)
        / len(scores)
    )

    strongest_score = max(scores)

    # Strong emphasis on the user's interests.
    return (
        average_score * 0.60
        + strongest_score * 0.40
    )


# ============================================================
# BUDGET SCORE
# ============================================================

def calculate_budget_score(
    destination: dict,
    user_daily_budget: float,
) -> float:

    average_cost = float(
        destination.get(
            "average_daily_cost",
            destination.get(
                "average_daily_cost_usd",
                0,
            ),
        )
    )

    if (
        average_cost <= 0
        or user_daily_budget <= 0
    ):
        return 0.0

    ratio = (
        user_daily_budget
        / average_cost
    )

    if ratio >= 1.5:
        return 1.0

    if ratio >= 1.0:
        return (
            0.92
            + (
                (ratio - 1.0)
                / 0.5
            ) * 0.08
        )

    if ratio >= 0.75:
        return (
            0.70
            + (
                (ratio - 0.75)
                / 0.25
            ) * 0.22
        )

    if ratio >= 0.5:
        return (
            0.35
            + (
                (ratio - 0.5)
                / 0.25
            ) * 0.35
        )

    return max(
        0.05,
        ratio * 0.70,
    )


# ============================================================
# WALKING SCORE
# ============================================================

def calculate_walking_score(
    destination: dict,
    walking_preference: bool,
) -> float:

    walkability = float(
        destination.get(
            "walkability_score",
            0.5,
        )
    )

    if walking_preference:
        return walkability

    return (
        0.70
        + (
            (1.0 - walkability)
            * 0.15
        )
    )


# ============================================================
# NORMALIZE ML SCORES
# ============================================================

def normalize_ml_scores(scores):

    if not scores:
        return []

    minimum = min(scores)
    maximum = max(scores)

    if math.isclose(
        minimum,
        maximum,
    ):
        return [
            0.5
            for _ in scores
        ]

    return [
        (
            score - minimum
        )
        / (
            maximum - minimum
        )
        for score in scores
    ]


# ============================================================
# DIVERSITY PENALTY
# ============================================================

def calculate_diversity_penalty(
    destination: dict,
    selected: list[dict],
) -> float:

    if not selected:
        return 0.0

    penalty = 0.0

    current_region = destination.get(
        "region"
    )

    current_country = destination.get(
        "country"
    )

    for existing in selected:

        existing_region = existing.get(
            "region"
        )

        existing_country = existing.get(
            "country"
        )

        # Same country
        if (
            current_country
            and existing_country
            and current_country
            == existing_country
        ):
            penalty += 0.07

        # Same region
        elif (
            current_region
            and existing_region
            and current_region
            == existing_region
        ):
            penalty += 0.025

    return min(
        penalty,
        0.18,
    )


# ============================================================
# FEATURE ROW FOR ML MODEL
# ============================================================

def build_feature_row(
    destination,
    user_daily_budget,
    interests,
    walking_preference,
):

    return {
        "architecture_score":
            destination["architecture_score"],

        "history_score":
            destination["history_score"],

        "food_score":
            destination["food_score"],

        "nightlife_score":
            destination["nightlife_score"],

        "museums_score":
            destination["museums_score"],

        "nature_score":
            destination["nature_score"],

        "shopping_score":
            destination["shopping_score"],

        "adventure_score":
            destination["adventure_score"],

        "average_daily_cost":
            destination["average_daily_cost"],

        "walkability_score":
            destination["walkability_score"],

        "weather_score":
            destination["weather_score"],

        "hotel_price":
            destination["hotel_price"],

        "restaurant_price":
            destination["restaurant_price"],

        # IMPORTANT:
        # Model expects "budget".
        "budget":
            user_daily_budget,

        "walking_preference":
            int(walking_preference),
    }


# ============================================================
# QUERY-SPECIFIC DETERMINISTIC TIE BREAK
# ============================================================

def calculate_query_tiebreak(
    destination: dict,
    interests: list[str],
    budget: float,
    currency: str,
    days: int,
    walking_preference: bool,
) -> float:

    """
    Small deterministic variation based on the user's
    actual search.

    Same query:
        same ordering.

    Different query:
        close candidates can change ordering.

    This is NOT random.
    """

    query_string = "|".join(
        [
            ",".join(
                sorted(interests)
            ),

            str(
                round(
                    float(budget),
                    2,
                )
            ),

            str(currency).upper(),

            str(days),

            str(
                int(
                    walking_preference
                )
            ),

            destination.get(
                "destination",
                "",
            ),
        ]
    )

    digest = hashlib.sha256(
        query_string.encode(
            "utf-8"
        )
    ).hexdigest()

    number = int(
        digest[:8],
        16,
    )

    normalized = (
        number % 10000
    ) / 10000.0

    return normalized * 0.012


# ============================================================
# MATCH PERCENTAGE
# ============================================================

def calculate_match_percentage(
    final_score: float,
) -> float:

    """
    Converts the final normalized recommendation score
    into a user-friendly percentage.

    Example:
        0.85 -> 85%
        0.72 -> 72%
    """

    score = max(
        0.0,
        min(
            float(final_score),
            1.0,
        ),
    )

    return round(
        score * 100,
        1,
    )


# ============================================================
# RECOMMEND DESTINATIONS
# ============================================================

def recommend_destinations(
    interests: list[str],
    budget: float,
    currency: str = "INR",
    days: int = 1,
    walking_preference: bool = True,
    top_k: int = 5,
) -> list[dict]:

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if budget <= 0:
        raise ValueError(
            "Budget must be greater than zero."
        )

    if days <= 0:
        raise ValueError(
            "Days must be greater than zero."
        )

    currency = str(
        currency
    ).upper().strip()

    if len(currency) != 3:
        raise ValueError(
            "Currency must be a 3-letter currency code."
        )

    interests = normalize_interests(
        interests
    )

    top_k = max(
        1,
        min(
            int(top_k),
            10,
        ),
    )

    # --------------------------------------------------------
    # TOTAL BUDGET -> DAILY BUDGET
    # --------------------------------------------------------

    total_budget = float(
        budget
    )

    trip_days = max(
        int(days),
        1,
    )

    daily_budget_user_currency = (
        total_budget
        / trip_days
    )

    # --------------------------------------------------------
    # CONVERT TO USD
    # --------------------------------------------------------

    if currency == ML_CURRENCY:

        user_daily_budget = (
            daily_budget_user_currency
        )

    else:

        user_daily_budget = convert_currency(
            daily_budget_user_currency,
            currency,
            ML_CURRENCY,
        )

    user_daily_budget = float(
        user_daily_budget
    )

    # --------------------------------------------------------
    # LOAD MODEL
    # --------------------------------------------------------

    model = get_model()

    # --------------------------------------------------------
    # BUILD FEATURES
    # --------------------------------------------------------

    feature_rows = []

    for destination in DESTINATIONS:

        feature_rows.append(
            build_feature_row(
                destination=destination,
                user_daily_budget=user_daily_budget,
                interests=interests,
                walking_preference=walking_preference,
            )
        )

    # --------------------------------------------------------
    # ML PREDICTION
    # --------------------------------------------------------

    try:

        raw_predictions = model.predict(
            feature_rows
        )

    except Exception:

        import pandas as pd

        feature_df = pd.DataFrame(
            feature_rows
        )

        raw_predictions = model.predict(
            feature_df
        )

    raw_predictions = [
        float(score)
        for score in raw_predictions
    ]

    ml_scores = normalize_ml_scores(
        raw_predictions
    )

    # --------------------------------------------------------
    # CALCULATE CANDIDATE SCORES
    # --------------------------------------------------------

    candidates = []

    for index, destination in enumerate(
        DESTINATIONS
    ):

        # ----------------------------------------------------
        # Interest
        # ----------------------------------------------------

        interest_score = (
            calculate_interest_preference_score(
                destination,
                interests,
            )
        )

        # ----------------------------------------------------
        # Budget
        # ----------------------------------------------------

        budget_score = (
            calculate_budget_score(
                destination,
                user_daily_budget,
            )
        )

        # ----------------------------------------------------
        # Walking
        # ----------------------------------------------------

        walking_score = (
            calculate_walking_score(
                destination,
                walking_preference,
            )
        )

        # ----------------------------------------------------
        # Weather
        # ----------------------------------------------------

        weather_score = float(
            destination.get(
                "weather_score",
                0.5,
            )
        )

        # ----------------------------------------------------
        # ML
        # ----------------------------------------------------

        ml_score = float(
            ml_scores[index]
        )

        # ----------------------------------------------------
        # FINAL WEIGHTED SCORE
        # ----------------------------------------------------

        base_score = (
            interest_score * 0.58
            + ml_score * 0.17
            + budget_score * 0.13
            + walking_score * 0.07
            + weather_score * 0.05
        )

        # ----------------------------------------------------
        # QUERY TIEBREAK
        # ----------------------------------------------------

        tiebreak = (
            calculate_query_tiebreak(
                destination=destination,
                interests=interests,
                budget=total_budget,
                currency=currency,
                days=trip_days,
                walking_preference=walking_preference,
            )
        )

        final_score = (
            base_score
            + tiebreak
        )

        # ----------------------------------------------------
        # IMPORTANT:
        # Calculate match percentage HERE.
        # ----------------------------------------------------

        match_percentage = (
            calculate_match_percentage(
                final_score
            )
        )

        candidates.append(
    {
        "destination": destination["destination"],
        "country": destination["country"],
        "region": destination["region"],

        # Keep original destination values available
        # after scoring and diversity selection.
        "average_daily_cost": destination[
            "average_daily_cost"
        ],

        "hotel_price": destination[
            "hotel_price"
        ],

        "restaurant_price": destination[
            "restaurant_price"
        ],

        "walkability_score": destination[
            "walkability_score"
        ],

        "weather_score": weather_score,

        "base_score": base_score,

        "score": final_score,

        "match_percentage": calculate_match_percentage(
            final_score
        ),

        "interest_score": interest_score,

        "ml_score": ml_score,

        "budget_score": budget_score,

        "walking_score": walking_score,
    }
)
        

    # --------------------------------------------------------
    # SORT BY SCORE
    # --------------------------------------------------------

    candidates.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    # --------------------------------------------------------
    # DIVERSITY-AWARE SELECTION
    # --------------------------------------------------------

    selected = []

    remaining = candidates.copy()

    while (
        remaining
        and len(selected) < top_k
    ):

        best_candidate = None

        best_adjusted_score = (
            -float("inf")
        )

        for candidate in remaining:

            diversity_penalty = (
                calculate_diversity_penalty(
                    candidate,
                    selected,
                )
            )

            adjusted_score = (
                candidate["score"]
                - diversity_penalty
            )

            if (
                adjusted_score
                > best_adjusted_score
            ):

                best_adjusted_score = (
                    adjusted_score
                )

                best_candidate = (
                    candidate
                )

        if best_candidate is None:
            break

        selected.append(
            best_candidate
        )

        remaining.remove(
            best_candidate
        )
    # ============================================================
    # FINAL SORT + RANK
    # ============================================================

    selected = sorted(
        selected,
        key=lambda item: item["score"],
        reverse=True,
    )

    for index, item in enumerate(selected, start=1):
        item["rank"] = index
    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    recommendations = []

    for rank, item in enumerate(
        selected,
        start=1,
    ):

        recommendations.append(
            {
                "rank":
                    rank,

                "destination":
                    item["destination"],

                "country":
                    item["country"],

                "region":
                    item["region"],

                "score":
                    round(
                        item["score"],
                        4,
                    ),

                # FIX:
                # match_percentage now ALWAYS exists.
                "match_percentage":
                    item["match_percentage"],

                "interest_score":
                    round(
                        item["interest_score"],
                        4,
                    ),

                "ml_score":
                    round(
                        item["ml_score"],
                        4,
                    ),

                "budget_score":
                    round(
                        item["budget_score"],
                        4,
                    ),

                "walking_score":
                    round(
                        item["walking_score"],
                        4,
                    ),

                "weather_score":
                    round(
                        item["weather_score"],
                        4,
                    ),

                "average_daily_cost":
                    round(
                        item[
                            "average_daily_cost"
                        ],
                        2,
                    ),

                "hotel_price":
                    round(
                        item[
                            "hotel_price"
                        ],
                        2,
                    ),

                "restaurant_price":
                    round(
                        item[
                            "restaurant_price"
                        ],
                        2,
                    ),

                "walkability_score":
                    round(
                        item[
                            "walkability_score"
                        ],
                        4,
                    ),
            }
        )

    return recommendations


# ============================================================
# EXPLANATION FUNCTION
# ============================================================

def explain_recommendations(
    interests: list[str],
    budget: float,
    currency: str = "INR",
    days: int = 1,
    walking_preference: bool = True,
    top_k: int = 5,
) -> list[dict]:

    recommendations = (
        recommend_destinations(
            interests=interests,
            budget=budget,
            currency=currency,
            days=days,
            walking_preference=walking_preference,
            top_k=top_k,
        )
    )

    for recommendation in recommendations:

        reasons = []

        interest_score = (
            recommendation[
                "interest_score"
            ]
        )

        budget_score = (
            recommendation[
                "budget_score"
            ]
        )

        walking_score = (
            recommendation[
                "walking_score"
            ]
        )

        weather_score = (
            recommendation[
                "weather_score"
            ]
        )

        # ----------------------------------------------------
        # INTEREST REASON
        # ----------------------------------------------------

        if interest_score >= 0.90:

            reasons.append(
                "Excellent match for your interests."
            )

        elif interest_score >= 0.75:

            reasons.append(
                "Strong match for your interests."
            )

        elif interest_score >= 0.60:

            reasons.append(
                "Good match for your interests."
            )

        else:

            reasons.append(
                "Moderate match for your interests."
            )

        # ----------------------------------------------------
        # BUDGET REASON
        # ----------------------------------------------------

        if budget_score >= 0.90:

            reasons.append(
                "Fits comfortably within your budget."
            )

        elif budget_score >= 0.70:

            reasons.append(
                "Reasonably aligned with your budget."
            )

        elif budget_score >= 0.50:

            reasons.append(
                "May require some budget flexibility."
            )

        # ----------------------------------------------------
        # WALKING REASON
        # ----------------------------------------------------

        if walking_preference:

            if walking_score >= 0.85:

                reasons.append(
                    "Highly walkable destination."
                )

            elif walking_score >= 0.75:

                reasons.append(
                    "Good walking accessibility."
                )

        # ----------------------------------------------------
        # WEATHER REASON
        # ----------------------------------------------------

        if weather_score >= 0.90:

            reasons.append(
                "Very favorable weather profile."
            )

        elif weather_score >= 0.80:

            reasons.append(
                "Generally favorable weather profile."
            )

        # ----------------------------------------------------
        # ADD REASONS
        # ----------------------------------------------------

        recommendation[
            "reasons"
        ] = reasons

    return recommendations