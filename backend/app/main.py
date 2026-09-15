from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from app.routes.auth import router as auth_router
from pydantic import BaseModel, Field
from typing import List
from app.routes.users import router as users_router
from app.routes.trips import router as trips_router

from app.routes.favorites import router as favorites_router
from app.schemas.trip import TripRequest
from app.database import Base, engine

from ml.services.recommendation_service import (
    recommend_destinations,
)

from ml.services.currency_service import (
    get_currency_metadata,
)

from app.services.memory_service import (
    search_memories,
    save_trip_preferences,
)

from app.tools.geocoding_tool import (
    get_destination_coordinates,
)

from app.tools.weather_tool import (
    get_weather,
)

from app.tools.places_tool import (
    get_places,
)

from app.agents.graph import (
    voyagemind_graph,
)


# ============================================================
# ML RECOMMENDATION REQUEST
# ============================================================

class RecommendationRequest(BaseModel):

    interests: List[str] = Field(
        default_factory=list,
        description="User travel interests",
    )

    # --------------------------------------------------------
    # TOTAL TRIP BUDGET
    # --------------------------------------------------------

    budget: float = Field(
        gt=0,
        description="Total trip budget in selected currency",
    )

    # --------------------------------------------------------
    # USER SELECTED CURRENCY
    # --------------------------------------------------------

    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
        description="User selected ISO 4217 currency code",
    )

    # --------------------------------------------------------
    # TRIP DURATION
    # --------------------------------------------------------

    days: int = Field(
        gt=0,
        le=365,
        description="Trip duration in days",
    )

    # --------------------------------------------------------
    # WALKING PREFERENCE
    # --------------------------------------------------------

    walking_preference: bool = Field(
        default=True,
        description="Whether the user prefers walking",
    )

    # --------------------------------------------------------
    # NUMBER OF RECOMMENDATIONS
    # --------------------------------------------------------

    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Number of destinations to recommend",
    )


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="VoyageMind AI",
    description="Autonomous Multi-Agent Travel Intelligence Platform",
    version="1.0.0",
)
Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(trips_router)
app.include_router(favorites_router)
# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "message": "VoyageMind AI Backend Running 🚀"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# ============================================================
# PLAN TRIP
# ============================================================

@app.post("/plan-trip")
async def plan_trip(trip: TripRequest):

    # ========================================================
    # STEP 1 — DESTINATION AGENT
    # ========================================================

    print()
    print("=" * 70)
    print("📍 DESTINATION AGENT")
    print("=" * 70)

    location = get_destination_coordinates(
        trip.destination
    )

    if not location.get("success"):

        return {
            "success": False,
            "message": "Could not find destination.",
            "error": location.get("error"),
        }

    latitude = location["latitude"]
    longitude = location["longitude"]

    destination_data = {
        "name": location["name"],
        "latitude": latitude,
        "longitude": longitude,
    }

    print(
        f"✅ Destination found: "
        f"{location['name']}"
    )

    # ========================================================
    # STEP 2 + STEP 3
    # WEATHER + PLACES
    # RUN IN PARALLEL
    # ========================================================

    print()
    print("=" * 70)
    print("⚡ WEATHER + PLACES AGENTS")
    print("=" * 70)

    print(
        "⚡ Running Weather Agent + Places Agent in parallel..."
    )

    async def fetch_weather():

        print()
        print("🌤️ Weather Agent started...")

        result = await asyncio.to_thread(
            get_weather,
            latitude,
            longitude,
        )

        print(
            "✅ Weather Agent completed."
        )

        return result

    async def fetch_places():

        print()
        print("📌 Places Agent started...")

        print(
            f"🎯 Selected interests: "
            f"{trip.interests}"
        )

        # ====================================================
        # INTENTIONAL LOCATION COLLECTION
        # ====================================================

        result = await asyncio.to_thread(
            get_places,
            latitude=latitude,
            longitude=longitude,
            interests=trip.interests,
            radius=5000,
        )

        print(
            "✅ Places Agent completed."
        )

        return result

    # ========================================================
    # RUN WEATHER + PLACES SIMULTANEOUSLY
    # ========================================================

    weather, places = await asyncio.gather(
        fetch_weather(),
        fetch_places(),
    )

    # ========================================================
    # PLACES RESULT PROCESSING
    # ========================================================

    places["count"] = len(
        places.get("places", [])
    )

    places_count = places.get(
        "count",
        0,
    )

    category_distribution = places.get(
        "category_distribution",
        {},
    )

    print()
    print(
        f"📍 Places found: "
        f"{places_count}"
    )

    # ========================================================
    # DISPLAY CATEGORY DISTRIBUTION
    # ========================================================

    if category_distribution:

        print()
        print(
            "📊 Places by selected interest:"
        )

        for category, count in (
            category_distribution.items()
        ):

            print(
                f"   {category} → {count}"
            )

    # ========================================================
    # STOP IF NO VERIFIED PLACES
    # ========================================================

    if not places.get("success"):

        print()
        print(
            "❌ Places Agent could not find "
            "verified locations."
        )

        return {

            "success": False,

            "message":
                "Unable to find enough verified places "
                "for this destination.",

            "error":
                places.get("error"),

            "destination":
                destination_data,

            "weather":
                weather,

            "places":
                places,
        }

    # ========================================================
    # STEP 3.5 — USER MEMORY RETRIEVAL
    # ========================================================

    print()
    print("=" * 70)
    print("🧠 USER MEMORY RETRIEVAL")
    print("=" * 70)

    # --------------------------------------------------------
    # TEMPORARY USER ID
    # --------------------------------------------------------

    user_id = "user-1"

    # ========================================================
    # BUILD SEMANTIC MEMORY QUERY
    # ========================================================

    memory_query = (

        f"Travel preferences for planning a trip to "
        f"{trip.destination}. "

        f"Interests: "
        f"{', '.join(trip.interests)}. "

        f"Budget: "
        f"{trip.budget} {trip.currency}. "

        f"Preferences: "

        f"restaurant budget "
        f"{trip.preferences.restaurant_budget}, "

        f"walking preference "
        f"{trip.preferences.walking_preference}, "

        f"hotel preference "
        f"{trip.preferences.hotel_preference}."
    )

    # ========================================================
    # SEARCH CHROMADB
    # ========================================================

    memory_result = search_memories(

        user_id=user_id,

        query=memory_query,

        n_results=5,
    )

    user_memories = memory_result.get(
        "memories",
        [],
    )

    # ========================================================
    # DISPLAY RETRIEVED MEMORIES
    # ========================================================

    if user_memories:

        print(
            f"✅ Retrieved "
            f"{len(user_memories)} relevant memories:"
        )

        for item in user_memories:

            print(
                f"   • {item.get('memory')}"
            )

    else:

        print(
            "ℹ️ No relevant user memories found."
        )

    # ========================================================
    # STEP 4 — LANGGRAPH AUTONOMOUS TRAVEL WORKFLOW
    # ========================================================

    print()
    print("=" * 70)
    print("🚀 STARTING VOYAGEMIND LANGGRAPH WORKFLOW")
    print("=" * 70)

    print()
    print("🧠 Workflow:")

    print(
        "   Itinerary Agent"
        " → Distance Agent"
        " → Validation Agent"
        " → Reflection Agent"
    )

    print()
    print("🔄 Autonomous re-planning enabled.")

    # ========================================================
    # PREPARE INITIAL GRAPH STATE
    # ========================================================

    trip_data = trip.model_dump()

    initial_state = {

        "trip":
            trip_data,

        "destination":
            destination_data,

        "weather":
            weather,

        "places":
            places,

        "replan_attempt":
            0,

        "reflection_feedback":
            "",

        "user_memories":
            user_memories,
    }

    # ========================================================
    # RUN LANGGRAPH
    # ========================================================

    graph_result = await asyncio.to_thread(
        voyagemind_graph.invoke,
        initial_state,
    )

    # ========================================================
    # EXTRACT GRAPH RESULTS
    # ========================================================

    itinerary_result = graph_result.get(
        "itinerary_result",
        {},
    )

    distance_data = graph_result.get(
        "distance_data",
        {},
    )

    validation_data = graph_result.get(
        "validation_data",
        {},
    )

    reflection_data = graph_result.get(
        "reflection_data",
        {},
    )

    # ========================================================
    # ITINERARY FAILURE
    # ========================================================

    if not itinerary_result.get(
        "success",
        False,
    ):

        print()
        print("=" * 70)
        print("❌ AI ITINERARY GENERATION FAILED")
        print("=" * 70)

        return {

            "success": False,

            "message":
                "AI itinerary generation failed.",

            "error":
                itinerary_result.get(
                    "error"
                ),

            "details":
                itinerary_result.get(
                    "details"
                ),

            "destination":
                destination_data,

            "weather":
                weather,

            "places":
                places,

            "memory":
                user_memories,
        }

    # ========================================================
    # STEP 5 — AUTOMATIC USER MEMORY PERSISTENCE
    # ========================================================

    print()
    print("=" * 70)
    print("🧠 USER MEMORY PERSISTENCE")
    print("=" * 70)

    memory_save_result = save_trip_preferences(

        user_id=user_id,

        trip=trip_data,
    )

    saved_memories = memory_save_result.get(
        "saved_memories",
        [],
    )

    saved_memory_count = memory_save_result.get(
        "count",
        len(saved_memories),
    )

    if saved_memory_count > 0:

        print(
            f"✅ Saved {saved_memory_count} user memories."
        )

        for item in saved_memories:

            print(
                f"   💾 {item.get('memory')}"
            )

    else:

        if memory_save_result.get("success"):

            print(
                "ℹ️ No new user memories were added."
            )

        else:

            print(
                "⚠️ User memory persistence failed."
            )

            print(
                f"   Error: "
                f"{memory_save_result.get('error', 'Unknown error')}"
            )

    # ========================================================
    # LANGGRAPH WORKFLOW COMPLETED
    # ========================================================

    print()
    print("=" * 70)
    print("🎉 VOYAGEMIND LANGGRAPH WORKFLOW COMPLETED")
    print("=" * 70)

    # ========================================================
    # WORKFLOW SUMMARY
    # ========================================================

    print()

    print(
        f"🔄 Replan attempts: "
        f"{graph_result.get('replan_attempt', 0)}"
    )

    print(
        f"📏 Total distance: "
        f"{distance_data.get('total_distance', 'Unknown')}"
    )

    print(
        f"⏱️ Total travel time: "
        f"{distance_data.get('total_travel_time', 'Unknown')}"
    )

    print(
        f"🚶 Travel mode: "
        f"{distance_data.get('mode', 'Unknown')}"
    )

    # ========================================================
    # VALIDATION STATUS
    # ========================================================

    validation_status = validation_data.get(
        "is_valid",
        False,
    )

    print(
        f"🔍 Validation: "
        f"{'PASSED' if validation_status else 'ISSUES DETECTED'}"
    )

    # ========================================================
    # REFLECTION STATUS
    # ========================================================

    print(
        f"🧠 Reflection: "
        f"{reflection_data.get('decision', 'Unknown')}"
    )

    # ========================================================
    # VALIDATION SUMMARY
    # ========================================================

    validation_summary = validation_data.get(
        "summary",
        {},
    )

    if validation_summary:

        print()

        print(
            "📊 Validation Summary:"
        )

        print(
            f"   Errors: "
            f"{validation_summary.get('errors', 0)}"
        )

        print(
            f"   Warnings: "
            f"{validation_summary.get('warnings', 0)}"
        )

        print(
            f"   Info: "
            f"{validation_summary.get('info', 0)}"
        )

        print(
            f"   Failed checks: "
            f"{validation_summary.get('failed_checks', 0)}"
        )

    # ========================================================
    # FINAL PLAN TRIP RESPONSE
    # ========================================================

    return {

        "success":
            True,

        "message":
            "AI trip plan generated successfully.",

        "trip":
            trip_data,

        "destination":
            destination_data,

        "weather":
            weather,

        "places":
            places,

        # ====================================================
        # MEMORY DATA
        # ====================================================

        "memory":
            {
                "user_id":
                    user_id,

                "memories":
                    user_memories,

                "count":
                    len(user_memories),

                "saved":
                    saved_memories,

                "saved_count":
                    len(saved_memories),
            },

        "itinerary":
            itinerary_result,

        "distance":
            distance_data,

        "validation":
            validation_data,

        "reflection":
            reflection_data,

        "replan_attempts":
            graph_result.get(
                "replan_attempt",
                0,
            ),
    }


# ============================================================
# TEST MEMORY ENDPOINT
# ============================================================

@app.get("/test-memory/{user_id}")
async def test_memory(
    user_id: str,
    query: str,
):

    memory_result = search_memories(

        user_id=user_id,

        query=query,

        n_results=5,
    )

    return memory_result


# ============================================================
# AI DESTINATION RECOMMENDATIONS
# ============================================================

@app.post("/recommendations")
async def get_recommendations(
    request: RecommendationRequest,
):

    try:

        # ====================================================
        # NORMALIZE CURRENCY
        # ====================================================

        currency = (
            request.currency
            .strip()
            .upper()
        )

        # ====================================================
        # LOG REQUEST
        # ====================================================

        print()
        print("=" * 70)
        print(
            "🤖 VOYAGEMIND AI DESTINATION "
            "RECOMMENDATION ENGINE"
        )
        print("=" * 70)

        print()

        print(
            f"💰 Total Budget: "
            f"{request.budget:.2f} {currency}"
        )

        print(
            f"📅 Trip Duration: "
            f"{request.days} days"
        )

        daily_budget_user_currency = (
            float(request.budget)
            / int(request.days)
        )

        print(
            f"💰 Daily Budget: "
            f"{daily_budget_user_currency:.2f} "
            f"{currency}"
        )

        print(
            f"🎯 Interests: "
            f"{request.interests}"
        )

        print(
            f"🚶 Walking Preference: "
            f"{request.walking_preference}"
        )

        print(
            f"🏆 Requested Recommendations: "
            f"{request.top_k}"
        )

        # ====================================================
        # RUN ML RECOMMENDATION ENGINE
        # ====================================================
        #
        # TOTAL USER BUDGET
        #        ↓
        # divide by DAYS
        #        ↓
        # DAILY USER BUDGET
        #        ↓
        # convert to USD
        #        ↓
        # ML MODEL
        #
        # ====================================================

        recommendations = await asyncio.to_thread(

            recommend_destinations,

            interests=request.interests,

            budget=request.budget,

            currency=currency,

            days=request.days,

            walking_preference=(
                request.walking_preference
            ),

            top_k=request.top_k,
        )

        # ====================================================
        # CURRENCY METADATA
        # ====================================================

        currency_metadata = (
            get_currency_metadata(
                currency
            )
        )

        # ====================================================
        # SUCCESS LOG
        # ====================================================

        print()
        print(
            "✅ AI destination recommendations generated."
        )

        print(
            f"💱 Selected Currency: "
            f"{currency}"
        )

        print(
            f"💰 Total Budget: "
            f"{request.budget:.2f} "
            f"{currency}"
        )

        print(
            f"💰 Daily Budget: "
            f"{daily_budget_user_currency:.2f} "
            f"{currency}"
        )

        print(
            "🧠 ML Base Currency: USD"
        )

        print(
            f"💱 USD → {currency}: "
            f"{currency_metadata['usd_to_currency_rate']}"
        )

        print(
            f"📅 FX Rate Date: "
            f"{currency_metadata['rate_date']}"
        )

        print(
            f"🌐 FX Source: "
            f"{currency_metadata['rate_source']}"
        )

        print()

        # ====================================================
        # PRINT RECOMMENDATIONS
        # ====================================================

        for index, recommendation in enumerate(
            recommendations,
            start=1,
        ):

            # ------------------------------------------------
            # IMPORTANT FIX
            #
            # Some versions of recommendation_service.py
            # return:
            #
            # average_daily_cost
            #
            # while the current implementation may return:
            #
            # average_daily_cost_usd
            #
            # Support both without changing ML logic.
            # ------------------------------------------------

            average_daily_cost = recommendation.get(
                "average_daily_cost",
                recommendation.get(
                    "average_daily_cost_usd",
                    0,
                ),
            )

            print(
                f"   {index}. "
                f"{recommendation.get('destination', 'Unknown')} "
                f"→ "
                f"{recommendation.get('match_percentage', 0)}% "
                f"| "
                f"{average_daily_cost} "
                f"{currency}"
            )

        # ====================================================
        # FINAL RESPONSE
        # ====================================================

        return {

            "success":
                True,

            "recommendations":
                recommendations,

            "count":
                len(recommendations),

            # =================================================
            # BUDGET INFORMATION
            # =================================================

            "budget":
                {

                    "total":
                        float(request.budget),

                    "daily":
                        round(
                            daily_budget_user_currency,
                            2,
                        ),

                    "currency":
                        currency,

                    # ML model remains USD based.
                    "model_currency":
                        "USD",
                },

            # =================================================
            # CURRENCY INFORMATION
            # =================================================

            "currency":
                {

                    "selected":
                        currency,

                    "model":
                        "USD",

                    "usd_to_selected_rate":
                        currency_metadata[
                            "usd_to_currency_rate"
                        ],

                    "rate_date":
                        currency_metadata[
                            "rate_date"
                        ],

                    "rate_source":
                        currency_metadata[
                            "rate_source"
                        ],
                },
        }

    # ========================================================
    # VALIDATION ERROR
    # ========================================================

    except ValueError as error:

        print()
        print(
            "⚠️ Recommendation validation error:"
        )

        print(
            str(error)
        )

        return {

            "success":
                False,

            "recommendations":
                [],

            "count":
                0,

            "error":
                str(error),
        }

    # ========================================================
    # GENERAL ERROR
    # ========================================================

    except Exception as error:

        print()
        print(
            "❌ Recommendation engine error:"
        )

        print(
            str(error)
        )

        return {

            "success":
                False,

            "recommendations":
                [],

            "count":
                0,

            "error":
                "Unable to generate destination recommendations.",

            "details":
                str(error),
        }