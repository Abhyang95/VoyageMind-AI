from app.services.gemini_service import generate_itinerary


# ============================================================
# ITINERARY AGENT
# ============================================================

def run_itinerary_agent(
    trip: dict,
    destination: dict,
    weather: dict,
    places_data: dict,
    reflection_feedback=None,
    user_memories=None,
):

    print()
    print("🤖 Itinerary Agent started...")

    places = places_data.get(
        "places",
        []
    )

    places_success = places_data.get(
        "success",
        False
    )

    places_count = len(
        places
    )

    category_distribution = (
        places_data.get(
            "category_distribution",
            {}
        )
    )

    print(
        f"📍 Verified places available: "
        f"{places_count}"
    )

    if category_distribution:

        print()
        print(
            "📊 Place distribution by interest:"
        )

        for category, count in (
            category_distribution.items()
        ):

            print(
                f"   {category} → {count}"
            )

    # ========================================================
    # DAY 8 — USER MEMORY
    # ========================================================

    if user_memories:

        print()
        print(
            "🧠 User memory passed to "
            "Itinerary Agent."
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
            "🧠 No user memory passed "
            "to Itinerary Agent."
        )

    # ========================================================
    # REPLAN FEEDBACK
    # ========================================================

    if reflection_feedback:

        print()
        print(
            "🧠 Reflection feedback received."
        )

        correction_instructions = (

            reflection_feedback.get(
                "correction_instructions",
                []
            )

            if isinstance(
                reflection_feedback,
                dict
            )

            else []

        )

        if correction_instructions:

            for index, instruction in enumerate(
                correction_instructions,
                start=1,
            ):

                print(
                    f"   🔧 {index}. {instruction}"
                )

    # ========================================================
    # SAFETY CHECK
    # ========================================================

    if (
        not places_success
        or
        places_count == 0
    ):

        print(
            "⚠️ No verified places available."
        )

        return {

            "success": False,

            "error": (
                "Unable to generate a reliable "
                "itinerary because no verified "
                "places were found."
            ),

            "itinerary": None,

        }

    # ========================================================
    # GEMINI
    # ========================================================

    try:

        result = generate_itinerary(

            trip=trip,

            destination=destination,

            weather=weather,

            places=places,

            reflection_feedback=(
                reflection_feedback
            ),

            user_memories=(
                user_memories or []
            ),

        )

        if result.get("success"):

            print(
                "✅ Itinerary generated successfully."
            )

        else:

            print(
                "❌ Gemini itinerary generation failed."
            )

            print(
                f"Error: "
                f"{result.get('error')}"
            )

        return result

    except Exception as error:

        print(
            "❌ Unexpected Itinerary Agent error:"
        )

        print(
            str(error)
        )

        return {

            "success": False,

            "error": str(error),

            "itinerary": None,

        }

    finally:

        print(
            "🤖 Itinerary Agent completed."
        )