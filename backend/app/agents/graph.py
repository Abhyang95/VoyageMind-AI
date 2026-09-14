# ============================================================
# VOYAGEMIND AI — LANGGRAPH ORCHESTRATION
# ============================================================

from typing import Any, Dict, TypedDict

from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from app.agents.itinerary_agent import (
    run_itinerary_agent,
)

from app.agents.validation_agent import (
    run_validation_agent,
)

from app.agents.reflection_agent import (
    run_reflection_agent,
)

from app.tools.distance_tool import (
    calculate_itinerary_distances,
)


# ============================================================
# GRAPH STATE
# ============================================================

class VoyageMindState(TypedDict, total=False):

    # Input
    trip: Dict[str, Any]
    destination: Dict[str, Any]
    weather: Dict[str, Any]
    places: Dict[str, Any]

    # ========================================================
    # DAY 8 — USER MEMORY
    # ========================================================

    user_memories: list

    # Agents
    itinerary_result: Dict[str, Any]
    distance_data: Dict[str, Any]
    validation_data: Dict[str, Any]
    reflection_data: Dict[str, Any]

    # ========================================================
    # DAY 7 — REFLECTION / REPLANNING
    # ========================================================

    reflection_feedback: str
    replan_attempt: int

    # Final
    success: bool
    error: str


# ============================================================
# NODE 1 — ITINERARY AGENT
# ============================================================

def itinerary_node(
    state: VoyageMindState,
):

    print()
    print("=" * 60)
    print("🧭 LANGGRAPH → ITINERARY NODE")
    print("=" * 60)

    trip = state["trip"]
    destination = state["destination"]
    weather = state["weather"]
    places = state["places"]

    # ========================================================
    # DAY 8 — USER MEMORIES
    # ========================================================

    user_memories = state.get(
        "user_memories",
        [],
    )

    if user_memories:

        print()
        print(
            f"🧠 User memories available → "
            f"{len(user_memories)}"
        )

        for memory_item in user_memories:

            if isinstance(
                memory_item,
                dict,
            ):

                memory_text = memory_item.get(
                    "memory",
                    "",
                )

            else:

                memory_text = str(
                    memory_item
                )

            if memory_text:

                print(
                    f"   • {memory_text}"
                )

    else:

        print()
        print(
            "🧠 No user memories available."
        )

    # ========================================================
    # REPLAN ATTEMPT
    # ========================================================

    attempt = state.get(
        "replan_attempt",
        0,
    )

    if attempt > 0:

        print()
        print(
            f"🔄 Replanning attempt #{attempt}"
        )

    # ========================================================
    # REFLECTION FEEDBACK
    # ========================================================

    reflection_feedback = state.get(
        "reflection_feedback",
        "",
    )

    if reflection_feedback:

        print()
        print(
            "🧠 Applying Reflection Agent "
            "feedback to itinerary generation..."
        )

    # ========================================================
    # RUN ITINERARY AGENT
    # ========================================================

    itinerary_result = run_itinerary_agent(

        trip=trip,

        destination=destination,

        weather=weather,

        places_data=places,

        reflection_feedback=(
            reflection_feedback
            or None
        ),

        user_memories=user_memories,

    )

    return {

        "itinerary_result":
            itinerary_result,

    }


# ============================================================
# NODE 2 — DISTANCE AGENT
# ============================================================

def distance_node(
    state: VoyageMindState,
):

    print()
    print("=" * 60)
    print("🗺️ LANGGRAPH → DISTANCE NODE")
    print("=" * 60)

    itinerary_result = state.get(
        "itinerary_result",
        {},
    )

    trip = state["trip"]

    places = state["places"]

    # ========================================================
    # DEFAULT DISTANCE
    # ========================================================

    distance_data = {

        "success": True,

        "routes": [],

        "route_count": 0,

        "total_distance_meters": 0,

        "total_distance": "0 m",

        "total_travel_time_seconds": 0,

        "total_travel_time": "0 min",

        "mode": (
            "walk"
            if trip.get(
                "preferences",
                {},
            ).get(
                "walking_preference",
                True,
            )
            else "drive"
        ),
    }

    # ========================================================
    # ONLY CALCULATE IF ITINERARY SUCCEEDED
    # ========================================================

    if (
        itinerary_result
        and itinerary_result.get(
            "success"
        )
    ):

        preferences = trip.get(
            "preferences",
            {},
        )

        walking_preference = preferences.get(
            "walking_preference",
            True,
        )

        print()
        print(
            "🗺️ Calculating itinerary distances..."
        )

        distance_data = (
            calculate_itinerary_distances(

                itinerary=(
                    itinerary_result.get(
                        "itinerary",
                        {},
                    )
                ),

                places=(
                    places.get(
                        "places",
                        [],
                    )
                ),

                walking_preference=(
                    walking_preference
                ),

            )
        )

    else:

        print()
        print(
            "⚠️ Skipping Distance Agent because "
            "itinerary generation failed."
        )

    return {

        "distance_data":
            distance_data,

    }


# ============================================================
# NODE 3 — VALIDATION AGENT
# ============================================================

def validation_node(
    state: VoyageMindState,
):

    print()
    print("=" * 60)
    print("🔍 LANGGRAPH → VALIDATION NODE")
    print("=" * 60)

    itinerary_result = state.get(
        "itinerary_result",
        {},
    )

    # ========================================================
    # DO NOT VALIDATE FAILED ITINERARY
    # ========================================================

    if not itinerary_result.get(
        "success",
        False,
    ):

        print()
        print(
            "⚠️ Validation skipped because "
            "itinerary generation failed."
        )

        validation_data = {

            "success": False,

            "is_valid": False,

            "error": (
                "Validation skipped because "
                "itinerary generation failed."
            ),

            "issues": [],

        }

        return {

            "validation_data":
                validation_data,

        }

    # ========================================================
    # NORMAL VALIDATION
    # ========================================================

    trip = state["trip"]

    destination = state["destination"]

    weather = state["weather"]

    places = state["places"]

    distance_data = state.get(
        "distance_data",
        {},
    )

    validation_data = (
        run_validation_agent(

            trip=trip,

            destination=destination,

            weather=weather,

            places_data=places,

            itinerary=(
                itinerary_result.get(
                    "itinerary",
                    {},
                )
            ),

            distance_data=distance_data,

        )
    )

    return {

        "validation_data":
            validation_data,

    }


# ============================================================
# NODE 4 — REFLECTION AGENT
# ============================================================

def reflection_node(
    state: VoyageMindState,
):

    print()
    print("=" * 60)
    print("🧠 LANGGRAPH → REFLECTION NODE")
    print("=" * 60)

    validation_data = state.get(
        "validation_data",
        {},
    )

    attempt = state.get(
        "replan_attempt",
        0,
    )

    itinerary_result = state.get(
        "itinerary_result",
        {},
    )

    reflection_data = (
        run_reflection_agent(

            validation_data=(
                validation_data
            ),

            itinerary=(
                itinerary_result.get(
                    "itinerary",
                    {},
                )
            ),

            attempt=attempt,

        )
    )

    # ========================================================
    # EXTRACT REFLECTION FEEDBACK
    # ========================================================

    reflection_feedback = ""

    if isinstance(
        reflection_data,
        dict,
    ):

        feedback = reflection_data.get(
            "feedback",
            "",
        )

        if isinstance(
            feedback,
            str,
        ):

            reflection_feedback = (
                feedback.strip()
            )

    return {

        "reflection_data":
            reflection_data,

        "reflection_feedback":
            reflection_feedback,

    }


# ============================================================
# ROUTING FUNCTION
# ============================================================

def reflection_router(
    state: VoyageMindState,
):

    reflection_data = state.get(
        "reflection_data",
        {},
    )

    itinerary_result = state.get(
        "itinerary_result",
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
        print(
            "❌ Graph routing → END"
        )

        return "end"

    # ========================================================
    # REPLAN
    # ========================================================

    if reflection_data.get(
        "needs_replanning",
        False,
    ):

        print()
        print(
            "🔄 Graph routing → REPLAN"
        )

        return "replan"

    # ========================================================
    # FINAL
    # ========================================================

    print()
    print(
        "✅ Graph routing → FINAL"
    )

    return "final"


# ============================================================
# REPLAN NODE
# ============================================================

def replan_node(
    state: VoyageMindState,
):

    attempt = state.get(
        "replan_attempt",
        0,
    )

    new_attempt = (
        attempt + 1
    )

    reflection_data = state.get(
        "reflection_data",
        {},
    )

    feedback = ""

    if isinstance(
        reflection_data,
        dict,
    ):

        feedback_value = (
            reflection_data.get(
                "feedback",
                "",
            )
        )

        if isinstance(
            feedback_value,
            str,
        ):

            feedback = (
                feedback_value.strip()
            )

    print()
    print("=" * 60)
    print(
        f"🔄 LANGGRAPH → REPLAN #{new_attempt}"
    )
    print("=" * 60)

    if feedback:

        print()
        print(
            "🧠 Reflection feedback carried "
            "into replan."
        )

    return {

        "replan_attempt":
            new_attempt,

        "reflection_feedback":
            feedback,

    }


# ============================================================
# BUILD GRAPH
# ============================================================

def build_voyagemind_graph():

    graph = StateGraph(
        VoyageMindState
    )

    # ========================================================
    # ADD NODES
    # ========================================================

    graph.add_node(
        "itinerary",
        itinerary_node,
    )

    graph.add_node(
        "distance",
        distance_node,
    )

    graph.add_node(
        "validation",
        validation_node,
    )

    graph.add_node(
        "reflection",
        reflection_node,
    )

    graph.add_node(
        "replan",
        replan_node,
    )

    # ========================================================
    # EDGES
    # ========================================================

    graph.add_edge(
        START,
        "itinerary",
    )

    graph.add_edge(
        "itinerary",
        "distance",
    )

    graph.add_edge(
        "distance",
        "validation",
    )

    graph.add_edge(
        "validation",
        "reflection",
    )

    # ========================================================
    # REFLECTION ROUTING
    # ========================================================

    graph.add_conditional_edges(

        "reflection",

        reflection_router,

        {

            "replan":
                "replan",

            "final":
                END,

            "end":
                END,

        },

    )

    # ========================================================
    # REPLAN → ITINERARY
    # ========================================================

    graph.add_edge(
        "replan",
        "itinerary",
    )

    # ========================================================
    # COMPILE
    # ========================================================

    return graph.compile()


# ============================================================
# COMPILED GRAPH
# ============================================================

voyagemind_graph = (
    build_voyagemind_graph()
)