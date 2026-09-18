import os
import json
import time
import random
from typing import Any, Dict

from dotenv import load_dotenv
from google import genai
from google.genai import types


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is missing. "
        "Add it to your backend .env file."
    )


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ============================================================
# MODELS
# ============================================================

PRIMARY_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite",
)

FALLBACK_MODELS = [
    os.getenv(
        "GEMINI_FALLBACK_MODEL_1",
        "gemini-3.5-flash",
    )
]


MODELS = []

for model in [
    PRIMARY_MODEL,
    *FALLBACK_MODELS,
]:

    if model and model not in MODELS:
        MODELS.append(model)


# ============================================================
# RETRY CONFIGURATION
# ============================================================

MAX_RETRIES_PER_MODEL = 2

INITIAL_RETRY_DELAY = 0.7

MAX_RETRY_DELAY = 3


# ============================================================
# GEMINI OUTPUT CONFIGURATION
# ============================================================

MAX_OUTPUT_TOKENS = int(
    os.getenv(
        "GEMINI_MAX_OUTPUT_TOKENS",
        "5000",
    )
)


# ============================================================
# MEMORY OUTPUT CONFIGURATION
# ============================================================

MEMORY_MAX_OUTPUT_TOKENS = int(
    os.getenv(
        "GEMINI_MEMORY_MAX_OUTPUT_TOKENS",
        "1000",
    )
)


# ============================================================
# GEMINI PLACE CONTEXT
# ============================================================

MAX_PLACES_FOR_GEMINI = 18


# ============================================================
# CHECK RETRYABLE ERROR
# ============================================================

def is_retryable_error(
    error: Exception,
):

    error_text = str(error).lower()

    retry_keywords = [
        "503",
        "unavailable",
        "high demand",
        "500",
        "internal error",
        "timeout",
        "deadline exceeded",
        "temporarily unavailable",
        "429",
        "rate limit",
    ]

    return any(
        keyword in error_text
        for keyword in retry_keywords
    )


# ============================================================
# NORMALIZE INTEREST DISPLAY NAME
# ============================================================

def normalize_interest_name(
    interest,
):

    if not interest:
        return ""

    return (
        str(interest)
        .strip()
        .lower()
    )


# ============================================================
# GET PLACE INTEREST TAGS
# ============================================================

def get_place_interest_tags(
    place,
):

    tags = place.get(
        "interest_tags",
        [],
    )

    if not isinstance(tags, list):
        tags = []

    cleaned_tags = []

    for tag in tags:

        if not tag:
            continue

        clean_tag = str(
            tag
        ).strip()

        if (
            clean_tag
            and clean_tag not in cleaned_tags
        ):

            cleaned_tags.append(
                clean_tag
            )

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    if not cleaned_tags:

        fallback_interest = (
            place.get("interest")
            or place.get("interest_category")
        )

        if fallback_interest:

            cleaned_tags.append(
                str(
                    fallback_interest
                ).strip()
            )

    return cleaned_tags


# ============================================================
# CHECK WHETHER PLACE MATCHES INTEREST
# ============================================================

def place_matches_interest(
    place,
    interest,
):

    normalized_interest = (
        normalize_interest_name(
            interest
        )
    )

    tags = get_place_interest_tags(
        place
    )

    return any(
        normalize_interest_name(tag)
        == normalized_interest
        for tag in tags
    )


# ============================================================
# PREPARE VERIFIED PLACES
# ============================================================

def prepare_places_context(
    places: list,
    interests: list = None,
    limit: int = MAX_PLACES_FOR_GEMINI,
):

    # ========================================================
    # STEP 1 — CLEAN AND DEDUPLICATE
    # ========================================================

    unique_places = {}

    for place in places:

        if not isinstance(
            place,
            dict,
        ):
            continue

        name = place.get(
            "name"
        )

        if not name:
            continue

        clean_name = str(
            name
        ).strip()

        if not clean_name:
            continue

        normalized_name = (
            clean_name.lower()
        )

        # ----------------------------------------------------
        # FIRST OCCURRENCE
        # ----------------------------------------------------

        if normalized_name not in unique_places:

            interest_tags = (
                get_place_interest_tags(
                    place
                )
            )

            first_interest = (
                place.get("interest")
                or (
                    interest_tags[0]
                    if interest_tags
                    else "Other"
                )
            )

            unique_places[
                normalized_name
            ] = {

                "name":
                    clean_name,

                "category":
                    place.get(
                        "category",
                        "place",
                    ),

                "interest":
                    first_interest,

                "interest_tags":
                    interest_tags,

                "rating":
                    place.get(
                        "rating"
                    ),

                "review_count":
                    (
                        place.get(
                            "review_count"
                        )
                        or place.get(
                            "reviews"
                        )
                    ),

                "latitude":
                    place.get(
                        "latitude"
                    ),

                "longitude":
                    place.get(
                        "longitude"
                    ),

                "address":
                    place.get(
                        "address"
                    ),

                "opening_hours":
                    place.get(
                        "opening_hours"
                    ),

            }

        # ----------------------------------------------------
        # DUPLICATE OCCURRENCE
        # ----------------------------------------------------

        else:

            existing = unique_places[
                normalized_name
            ]

            existing_tags = existing.get(
                "interest_tags",
                [],
            )

            incoming_tags = (
                get_place_interest_tags(
                    place
                )
            )

            for tag in incoming_tags:

                if (
                    tag
                    and tag not in existing_tags
                ):

                    existing_tags.append(
                        tag
                    )

            existing[
                "interest_tags"
            ] = existing_tags

    # ========================================================
    # STEP 2 — BUILD REQUESTED INTEREST LIST
    # ========================================================

    requested_interests = []

    if isinstance(
        interests,
        list,
    ):

        for interest in interests:

            if not interest:
                continue

            clean_interest = str(
                interest
            ).strip()

            if (
                clean_interest
                and clean_interest
                not in requested_interests
            ):

                requested_interests.append(
                    clean_interest
                )

    # --------------------------------------------------------
    # DERIVE INTERESTS IF NONE PROVIDED
    # --------------------------------------------------------

    if not requested_interests:

        for place in unique_places.values():

            for tag in get_place_interest_tags(
                place
            ):

                if (
                    tag
                    and tag
                    not in requested_interests
                ):

                    requested_interests.append(
                        tag
                    )

    # ========================================================
    # STEP 3 — CREATE INTEREST BUCKETS
    # ========================================================

    buckets = {
        interest: []
        for interest in requested_interests
    }

    for place in unique_places.values():

        for interest in requested_interests:

            if place_matches_interest(
                place,
                interest,
            ):

                buckets[
                    interest
                ].append(
                    place
                )

    # ========================================================
    # STEP 4 — GUARANTEE INTEREST COVERAGE
    # ========================================================

    selected_places = []

    selected_names = set()

    covered_interests = set()

    # --------------------------------------------------------
    # Repeatedly choose the place that adds the most
    # currently uncovered interests.
    # --------------------------------------------------------

    while True:

        best_place = None

        best_new_interests = []

        for place in unique_places.values():

            normalized_name = (
                place["name"]
                .strip()
                .lower()
            )

            if normalized_name in selected_names:
                continue

            new_interests = []

            for interest in requested_interests:

                if (
                    interest
                    in covered_interests
                ):
                    continue

                if place_matches_interest(
                    place,
                    interest,
                ):

                    new_interests.append(
                        interest
                    )

            if (
                len(new_interests)
                > len(best_new_interests)
            ):

                best_place = place

                best_new_interests = (
                    new_interests
                )

        if not best_place:
            break

        if (
            len(selected_places)
            >= limit
        ):
            break

        selected_places.append(
            best_place
        )

        selected_names.add(
            best_place["name"]
            .strip()
            .lower()
        )

        for interest in best_new_interests:

            covered_interests.add(
                interest
            )

        # ----------------------------------------------------
        # All available interests covered
        # ----------------------------------------------------

        available_interests = {

            interest

            for interest in requested_interests

            if buckets.get(
                interest
            )
        }

        if available_interests.issubset(
            covered_interests
        ):

            break

    # ========================================================
    # STEP 5 — BALANCED ROUND-ROBIN FILL
    # ========================================================

    positions = {
        interest: 0
        for interest in requested_interests
    }

    while (
        len(selected_places)
        < limit
    ):

        added_this_round = False

        for interest in requested_interests:

            bucket = buckets.get(
                interest,
                [],
            )

            position = positions.get(
                interest,
                0,
            )

            while (
                position < len(bucket)
                and
                bucket[position][
                    "name"
                ]
                .strip()
                .lower()
                in selected_names
            ):

                position += 1

            positions[
                interest
            ] = position

            if position >= len(bucket):
                continue

            place = bucket[
                position
            ]

            positions[
                interest
            ] += 1

            normalized_name = (
                place["name"]
                .strip()
                .lower()
            )

            if (
                normalized_name
                in selected_names
            ):

                continue

            selected_names.add(
                normalized_name
            )

            selected_places.append(
                place
            )

            added_this_round = True

            if (
                len(selected_places)
                >= limit
            ):

                break

        if not added_this_round:
            break

    # ========================================================
    # STEP 6 — FILL ANY REMAINING CAPACITY
    # ========================================================

    if (
        len(selected_places)
        < limit
    ):

        for place in unique_places.values():

            if (
                len(selected_places)
                >= limit
            ):

                break

            normalized_name = (
                place["name"]
                .strip()
                .lower()
            )

            if (
                normalized_name
                in selected_names
            ):

                continue

            selected_names.add(
                normalized_name
            )

            selected_places.append(
                place
            )

    # ========================================================
    # DEBUG COVERAGE
    # ========================================================

    selected_interest_coverage = {
        interest: 0
        for interest in requested_interests
    }

    for place in selected_places:

        for interest in requested_interests:

            if place_matches_interest(
                place,
                interest,
            ):

                selected_interest_coverage[
                    interest
                ] += 1

    print()

    print(
        "📊 Final verified places selected for Gemini:"
    )

    print(
        f"   📍 Unique places → {len(selected_places)}"
    )

    print()

    print(
        "📊 Interest coverage within selected places:"
    )

    for (
        interest,
        count
    ) in selected_interest_coverage.items():

        print(
            f"   {interest} → {count} tagged places"
        )

    return selected_places


# ============================================================
# COMPACT JSON
# ============================================================

def compact_json(data):

    return json.dumps(
        data,
        ensure_ascii=False,
        separators=(",", ":"),
    )


# ============================================================
# ITINERARY JSON SCHEMA
# ============================================================

def build_itinerary_schema():

    return {

        "type": "object",

        "properties": {

            "trip_summary": {

                "type": "object",

                "properties": {

                    "destination": {
                        "type": "string"
                    },

                    "duration_days": {
                        "type": "integer"
                    },

                    "travel_style": {
                        "type": "string"
                    },

                    "weather_summary": {
                        "type": "string"
                    },

                },

                "required": [
                    "destination",
                    "duration_days",
                    "travel_style",
                    "weather_summary",
                ],

            },

            "budget_plan": {

                "type": "object",

                "properties": {

                    "total_budget": {
                        "type": "number"
                    },

                    "currency": {
                        "type": "string"
                    },

                    "estimated_daily_budget": {
                        "type": "number"
                    },

                    "notes": {
                        "type": "string"
                    },

                },

                "required": [
                    "total_budget",
                    "currency",
                    "estimated_daily_budget",
                    "notes",
                ],

            },

            "days": {

                "type": "array",

                "items": {

                    "type": "object",

                    "properties": {

                        "day": {
                            "type": "integer"
                        },

                        "theme": {
                            "type": "string"
                        },

                        "activities": {

                            "type": "array",

                            "items": {

                                "type": "object",

                                "properties": {

                                    "time": {
                                        "type": "string"
                                    },

                                    "place": {
                                        "type": "string"
                                    },

                                    "interest": {
                                        "type": "string"
                                    },

                                    "category": {
                                        "type": "string"
                                    },

                                    "reason": {
                                        "type": "string"
                                    },

                                    "estimated_cost": {
                                        "type": "string"
                                    },

                                    "notes": {
                                        "type": "string"
                                    },

                                },

                                "required": [
                                    "time",
                                    "place",
                                    "interest",
                                    "category",
                                    "reason",
                                    "estimated_cost",
                                    "notes",
                                ],

                            },

                        },

                        "daily_tip": {
                            "type": "string"
                        },

                    },

                    "required": [
                        "day",
                        "theme",
                        "activities",
                        "daily_tip",
                    ],

                },

            },

            "travel_tips": {

                "type": "array",

                "items": {
                    "type": "string"
                },

            },

            "warnings": {

                "type": "array",

                "items": {
                    "type": "string"
                },

            },

        },

        "required": [
            "trip_summary",
            "budget_plan",
            "days",
            "travel_tips",
            "warnings",
        ],

    }

# ============================================================
# CACHED ITINERARY SCHEMA
# ============================================================

ITINERARY_SCHEMA = build_itinerary_schema()
# ============================================================
# MEMORY EXTRACTION JSON SCHEMA
# ============================================================

def build_memory_extraction_schema():

    return {

        "type": "object",

        "properties": {

            "memories": {

                "type": "array",

                "items": {

                    "type": "object",

                    "properties": {

                        "memory": {
                            "type": "string"
                        },

                        "memory_type": {
                            "type": "string"
                        },

                    },

                    "required": [
                        "memory",
                        "memory_type",
                    ],

                },

            },

        },

        "required": [
            "memories",
        ],

    }


# ============================================================
# GENERATE WITH RETRY
# ============================================================

def generate_with_retry(
    model_name: str,
    prompt: str,
):

    last_error = None

    for attempt in range(
        1,
        MAX_RETRIES_PER_MODEL + 1,
    ):

        try:

            print()

            print(
                "=================================="
            )

            print(
                f"🤖 Calling Gemini model: "
                f"{model_name}"
            )

            print(
                f"🔁 Attempt "
                f"{attempt}/"
                f"{MAX_RETRIES_PER_MODEL}"
            )

            print(
                "=================================="
            )

            # ----------------------------------------------------
            # START GEMINI TIMER
            # ----------------------------------------------------

            gemini_start_time = time.perf_counter()

            response = client.models.generate_content(

                model=model_name,

                contents=prompt,

                config=types.GenerateContentConfig(

                    temperature=0.2,

                    response_mime_type="application/json",

                    response_schema=(
                        ITINERARY_SCHEMA
                    ),

                    automatic_function_calling=(
                        types.AutomaticFunctionCallingConfig(
                            disable=True
                        )
                    ),

                    max_output_tokens=(
                        MAX_OUTPUT_TOKENS
                    ),

                ),

            )

            # ----------------------------------------------------
            # END GEMINI TIMER
            # ----------------------------------------------------

            gemini_elapsed = (
                time.perf_counter()
                - gemini_start_time
            )

            print()

            print(
                "⏱️ Gemini generation time: "
                f"{gemini_elapsed:.2f}s"
            )

            # ----------------------------------------------------
            # GEMINI USAGE METADATA
            # ----------------------------------------------------

            usage = getattr(
                response,
                "usage_metadata",
                None,
            )

            if usage:

                prompt_tokens = getattr(
                    usage,
                    "prompt_token_count",
                    None,
                )

                output_tokens = getattr(
                    usage,
                    "candidates_token_count",
                    None,
                )

                thoughts_tokens = getattr(
                    usage,
                    "thoughts_token_count",
                    None,
                )

                total_tokens = getattr(
                    usage,
                    "total_token_count",
                    None,
                )

                print(
                    "📊 Gemini Usage:"
                )

                print(
                    f"   📥 Prompt tokens   → "
                    f"{prompt_tokens}"
                )

                print(
                    f"   📤 Output tokens   → "
                    f"{output_tokens}"
                )

                print(
                    f"   🧠 Thoughts tokens → "
                    f"{thoughts_tokens}"
                )

                print(
                    f"   🔢 Total tokens    → "
                    f"{total_tokens}"
                )

            else:

                print(
                    "📊 Gemini Usage Metadata "
                    "→ unavailable"
                )

            print()

            print(
                f"🤖 Model used → "
                f"{model_name}"
            )

            print(
                "✅ Gemini request successful"
            )

            return {

                "success": True,

                "response": response,

                "model": model_name,

                "attempt": attempt,

            }

        except Exception as error:

            # ----------------------------------------------------
            # MEASURE FAILED REQUEST TOO
            # ----------------------------------------------------

            gemini_elapsed = (
                time.perf_counter()
                - gemini_start_time
                if "gemini_start_time" in locals()
                else 0
            )

            last_error = error

            print()

            print(
                "❌ Gemini attempt failed."
            )

            print(
                f"⏱️ Gemini request time: "
                f"{gemini_elapsed:.2f}s"
            )

            print(
                f"Model: {model_name}"
            )

            print(
                f"Attempt: "
                f"{attempt}/"
                f"{MAX_RETRIES_PER_MODEL}"
            )

            print(
                f"Error type: "
                f"{type(error).__name__}"
            )

            print(
                f"Error message: "
                f"{str(error)}"
            )

            error_text = str(
                error
            ).lower()

            # ==================================================
            # QUOTA
            # ==================================================

            if (
                "quota exceeded"
                in error_text
                or
                "generate_content_free_tier_requests"
                in error_text
                or
                "resource_exhausted"
                in error_text
            ):

                print()

                print(
                    "⚠️ Model quota exhausted."
                )

                print(
                    "🔄 Moving directly to fallback model."
                )

                break

            # ==================================================
            # NON-RETRYABLE
            # ==================================================

            if not is_retryable_error(
                error
            ):

                print()

                print(
                    "⛔ Non-retryable error."
                )

                print(
                    "Skipping retries for this model."
                )

                break

            # ==================================================
            # MAX RETRIES
            # ==================================================

            if (
                attempt
                == MAX_RETRIES_PER_MODEL
            ):

                print()

                print(
                    "⚠️ Maximum retries reached."
                )

                break

            # ==================================================
            # FAST EXPONENTIAL BACKOFF
            # ==================================================

            delay = min(

                INITIAL_RETRY_DELAY
                *
                (
                    2
                    **
                    (
                        attempt - 1
                    )
                ),

                MAX_RETRY_DELAY,

            )

            delay += random.uniform(
                0.1,
                0.4,
            )

            print()

            print(
                f"⏳ Retrying in "
                f"{delay:.2f} seconds..."
            )

            time.sleep(
                delay
            )

    return {

        "success": False,

        "error": str(
            last_error
        ),

    }


# ============================================================
# GENERATE MEMORY EXTRACTION WITH RETRY
# ============================================================

def generate_memory_with_retry(
    model_name: str,
    prompt: str,
):

    last_error = None

    for attempt in range(
        1,
        MAX_RETRIES_PER_MODEL + 1,
    ):

        try:

            print()

            print(
                "=================================="
            )

            print(
                f"🧠 Calling Gemini memory model: "
                f"{model_name}"
            )

            print(
                f"🔁 Memory attempt "
                f"{attempt}/"
                f"{MAX_RETRIES_PER_MODEL}"
            )

            print(
                "=================================="
            )

            response = client.models.generate_content(

                model=model_name,

                contents=prompt,

                config=types.GenerateContentConfig(

                    temperature=0.1,

                    response_mime_type="application/json",

                    response_schema=(
                        build_memory_extraction_schema()
                    ),

                    automatic_function_calling=(
                        types.AutomaticFunctionCallingConfig(
                            disable=True
                        )
                    ),

                    max_output_tokens=(
                        MEMORY_MAX_OUTPUT_TOKENS
                    ),

                ),

            )

            print()

            print(
                f"✅ Gemini memory extraction "
                f"successful using {model_name}"
            )

            return {

                "success": True,

                "response": response,

                "model": model_name,

                "attempt": attempt,

            }

        except Exception as error:

            last_error = error

            print()

            print(
                "❌ Gemini memory extraction failed."
            )

            print(
                f"Model: {model_name}"
            )

            print(
                f"Attempt: "
                f"{attempt}/"
                f"{MAX_RETRIES_PER_MODEL}"
            )

            print(
                f"Error type: "
                f"{type(error).__name__}"
            )

            print(
                f"Error message: "
                f"{str(error)}"
            )

            error_text = str(
                error
            ).lower()

            # ==================================================
            # QUOTA
            # ==================================================

            if (
                "quota exceeded"
                in error_text
                or
                "generate_content_free_tier_requests"
                in error_text
                or
                "resource_exhausted"
                in error_text
            ):

                print()

                print(
                    "⚠️ Gemini memory extraction "
                    "quota exhausted."
                )

                break

            # ==================================================
            # NON-RETRYABLE
            # ==================================================

            if not is_retryable_error(
                error
            ):

                print()

                print(
                    "⛔ Non-retryable memory "
                    "extraction error."
                )

                break

            # ==================================================
            # MAX RETRIES
            # ==================================================

            if (
                attempt
                == MAX_RETRIES_PER_MODEL
            ):

                print()

                print(
                    "⚠️ Maximum memory extraction "
                    "retries reached."
                )

                break

            # ==================================================
            # BACKOFF
            # ==================================================

            delay = min(

                INITIAL_RETRY_DELAY
                *
                (
                    2
                    **
                    (
                        attempt - 1
                    )
                ),

                MAX_RETRY_DELAY,

            )

            delay += random.uniform(
                0.1,
                0.4,
            )

            print()

            print(
                f"⏳ Retrying memory extraction "
                f"in {delay:.2f} seconds..."
            )

            time.sleep(
                delay
            )

    return {

        "success": False,

        "error": str(
            last_error
        ),

    }


# ============================================================
# GENERATE MEMORY EXTRACTION
# ============================================================

def generate_memory_extraction(
    text: str,
) -> Dict[str, Any]:

    if not text or not text.strip():

        return {

            "success": False,

            "memories": [],

            "error": "Text cannot be empty.",

        }

    clean_text = text.strip()

    # ========================================================
    # MEMORY EXTRACTION PROMPT
    # ========================================================

    prompt = f"""
You are the long-term travel preference extraction
component of VoyageMind AI.

Your task is to identify ONLY useful long-term travel
preferences explicitly expressed by the user.

USER TEXT
============================================================

{clean_text}

============================================================
WHAT COUNTS AS A MEMORY
============================================================

A memory is information that can reasonably improve
future travel planning for this user.

Useful examples:

- I prefer walking instead of taxis.
- I prefer mid-range hotels.
- I prefer moderate restaurants.
- I enjoy museums.
- I enjoy historical architecture.
- I prefer quiet destinations.
- I dislike very expensive restaurants.
- I prefer nature-focused trips.
- I enjoy local food.
- I prefer slower-paced travel.

============================================================
DO NOT STORE THESE
============================================================

Do NOT extract temporary or trip-specific information such
as:

- Current destination
- Current trip dates
- Current trip duration
- Current trip budget
- Current weather
- Temporary hotel booking
- Temporary restaurant reservation
- Current itinerary
- Current flight information
- One-time scheduling information
- Temporary requests such as "plan Paris for 5 days"

============================================================
IMPORTANT RULES
============================================================

1. Only extract preferences explicitly supported by the
   user's text.

2. NEVER invent a preference.

3. Do not infer a preference from a single temporary
   logistical request.

4. Do not store personal information that is unrelated to
   travel planning.

5. Do not store sensitive personal information.

6. Keep every memory concise and reusable.

7. Prefer first-person preference statements such as:
   "I prefer walking instead of taxis."

8. Use memory_type values such as:
   "preference"
   "interest"
   "dislike"
   "travel_style"

9. If the user expresses no useful long-term preference,
   return an empty memories array.

10. Multiple useful preferences may be extracted from the
    same text.

11. Do not duplicate the same preference.

12. Return ONLY the requested JSON structure.

============================================================
OUTPUT FORMAT
============================================================

Return:

{{
    "memories": [
        {{
            "memory": "I prefer walking instead of taxis.",
            "memory_type": "preference"
        }}
    ]
}}

If there are no useful memories:

{{
    "memories": []
}}
"""

    try:

        print()

        print(
            "🧠 Gemini memory extraction started..."
        )

        generation_result = None

        model_errors = {}

        # ====================================================
        # TRY AVAILABLE GEMINI MODELS
        # ====================================================

        for model_name in MODELS:

            print()

            print(
                "=================================="
            )

            print(
                f"🚀 Trying memory model: "
                f"{model_name}"
            )

            print(
                "=================================="
            )

            result = generate_memory_with_retry(

                model_name=model_name,

                prompt=prompt,

            )

            if result.get(
                "success"
            ):

                generation_result = result

                break

            model_errors[
                model_name
            ] = result.get(
                "error"
            )

            print()

            print(
                f"⚠️ Memory model failed: "
                f"{model_name}"
            )

        # ====================================================
        # ALL MODELS FAILED
        # ====================================================

        if not generation_result:

            print()

            print(
                "❌ ALL GEMINI MEMORY MODELS FAILED"
            )

            return {

                "success": False,

                "memories": [],

                "error": (
                    "All Gemini models failed "
                    "during memory extraction."
                ),

                "model_errors":
                    model_errors,

            }

        # ====================================================
        # RESPONSE
        # ====================================================

        response = generation_result[
            "response"
        ]

        used_model = generation_result[
            "model"
        ]

        response_text = (
            response.text
            or ""
        ).strip()

        if not response_text:

            return {

                "success": False,

                "memories": [],

                "error":
                    "Gemini returned an empty "
                    "memory extraction response.",

            }

        print()

        print(
            "✅ Gemini memory response received."
        )

        print(
            f"🤖 Memory model used: "
            f"{used_model}"
        )

        # ====================================================
        # CLEAN POSSIBLE MARKDOWN
        # ====================================================

        if response_text.startswith(
            "```"
        ):

            response_text = (
                response_text
                .replace(
                    "```json",
                    "",
                )
                .replace(
                    "```",
                    "",
                )
                .strip()
            )

        # ====================================================
        # PARSE JSON
        # ====================================================

        try:

            data = json.loads(
                response_text
            )

        except json.JSONDecodeError as error:

            print()

            print(
                "❌ Invalid JSON returned "
                "during memory extraction."
            )

            return {

                "success": False,

                "memories": [],

                "error":
                    "Gemini returned invalid "
                    "memory extraction JSON.",

                "details":
                    str(error),

            }

        # ====================================================
        # VALIDATE RESPONSE STRUCTURE
        # ====================================================

        if not isinstance(
            data,
            dict,
        ):

            return {

                "success": False,

                "memories": [],

                "error":
                    "Memory extraction response "
                    "must be a JSON object.",

            }

        memories = data.get(
            "memories",
            []
        )

        if not isinstance(
            memories,
            list,
        ):

            memories = []

        cleaned_memories = []

        seen_memories = set()

        for memory_item in memories:

            if not isinstance(
                memory_item,
                dict,
            ):

                continue

            memory_text = str(
                memory_item.get(
                    "memory",
                    "",
                )
            ).strip()

            memory_type = str(
                memory_item.get(
                    "memory_type",
                    "preference",
                )
            ).strip()

            if not memory_text:
                continue

            if not memory_type:
                memory_type = "preference"

            normalized_memory = (
                memory_text.lower()
            )

            if (
                normalized_memory
                in seen_memories
            ):

                continue

            seen_memories.add(
                normalized_memory
            )

            cleaned_memories.append(
                {

                    "memory":
                        memory_text,

                    "memory_type":
                        memory_type,

                }
            )

        # ====================================================
        # FINAL RESULT
        # ====================================================

        print()

        if cleaned_memories:

            print(
                f"🧠 Extracted "
                f"{len(cleaned_memories)} "
                f"useful long-term memories."
            )

            for memory in cleaned_memories:

                print(
                    f"   • "
                    f"{memory['memory']}"
                )

        else:

            print(
                "ℹ️ No useful long-term "
                "memories detected."
            )

        return {

            "success": True,

            "memories":
                cleaned_memories,

            "model":
                used_model,

            "generation_attempt":
                generation_result.get(
                    "attempt"
                ),

        }

    except Exception as error:

        print()

        print(
            "❌ Memory extraction failed."
        )

        print(
            f"Error type: "
            f"{type(error).__name__}"
        )

        print(
            f"Error: "
            f"{str(error)}"
        )

        return {

            "success": False,

            "memories": [],

            "error":
                str(error),

        }


# ============================================================
# NORMALIZE REFLECTION FEEDBACK
# ============================================================

def prepare_reflection_feedback(
    reflection_feedback,
):

    if not reflection_feedback:
        return ""

    feedback_lines = []

    # --------------------------------------------------------
    # CASE 1 — Reflection Agent returns a dictionary
    # --------------------------------------------------------

    if isinstance(
        reflection_feedback,
        dict,
    ):

        correction_instructions = (
            reflection_feedback.get(
                "correction_instructions",
                [],
            )
        )

        # Support the feedback field used by the
        # Reflection Agent / LangGraph version.

        if not correction_instructions:

            correction_instructions = (
                reflection_feedback.get(
                    "feedback",
                    [],
                )
            )

        # A single string is also supported.

        if isinstance(
            correction_instructions,
            str,
        ):

            correction_instructions = [
                correction_instructions
            ]

        if isinstance(
            correction_instructions,
            list,
        ):

            for index, instruction in enumerate(
                correction_instructions,
                start=1,
            ):

                if instruction:

                    feedback_lines.append(
                        f"{index}. "
                        f"{str(instruction).strip()}"
                    )

    # --------------------------------------------------------
    # CASE 2 — Reflection Agent returns a string
    # --------------------------------------------------------

    elif isinstance(
        reflection_feedback,
        str,
    ):

        clean_feedback = (
            reflection_feedback.strip()
        )

        if clean_feedback:

            feedback_lines.append(
                clean_feedback
            )

    # --------------------------------------------------------
    # FINAL TEXT
    # --------------------------------------------------------

    if not feedback_lines:
        return ""

    return "\n".join(
        feedback_lines
    )


# ============================================================
# PREPARE USER MEMORY
# ============================================================

def prepare_user_memory(
    user_memories,
    max_memories: int = 5,
):
    """
    Convert ChromaDB memory search results into
    concise text for Gemini.

    Expected memory format:

    {
        "memory": "I prefer walking instead of taxis",
        "metadata": {...},
        "distance": 0.42
    }
    """

    if not user_memories:
        return ""

    memory_lines = []

    if not isinstance(
        user_memories,
        list,
    ):

        return ""

    for memory_item in user_memories:

        if len(memory_lines) >= max_memories:
            break

        # ----------------------------------------------------
        # ChromaDB search result
        # ----------------------------------------------------

        if isinstance(
            memory_item,
            dict,
        ):

            memory_text = memory_item.get(
                "memory",
                "",
            )

        # ----------------------------------------------------
        # Plain string memory
        # ----------------------------------------------------

        else:

            memory_text = str(
                memory_item
            )

        if not memory_text:
            continue

        memory_text = str(
            memory_text
        ).strip()

        if not memory_text:
            continue

        memory_lines.append(
            f"- {memory_text}"
        )

    if not memory_lines:
        return ""

    return "\n".join(
        memory_lines
    )


# ============================================================
# GENERATE ITINERARY
# ============================================================

def generate_itinerary(
    trip: dict,
    destination: dict,
    weather: dict,
    places: list,
    reflection_feedback=None,
    user_memories=None,
):

    try:

        print()
        print(
            "🤖 Gemini itinerary generation started..."
        )

        # ====================================================
        # REQUEST DETAILS
        # ====================================================

        requested_days = int(
            trip.get(
                "days",
                1,
            )
        )

        interests = trip.get(
            "interests",
            [],
        )

        if not isinstance(
            interests,
            list,
        ):

            interests = []

        # ====================================================
        # PREPARE VERIFIED PLACES
        # ====================================================

        places_context = prepare_places_context(

            places=places,

            interests=interests,

            limit=MAX_PLACES_FOR_GEMINI,

        )

        print()
        print(
            "📦 Places prepared for Gemini:"
        )

        print(
            f"Original count: "
            f"{len(places)}"
        )

        print(
            f"Sent to Gemini: "
            f"{len(places_context)} unique places"
        )

        # ====================================================
        # PRINT INTEREST DISTRIBUTION
        # ====================================================

        sent_distribution = {}

        for interest in interests:

            sent_distribution[
                interest
            ] = 0

        for place in places_context:

            tags = get_place_interest_tags(
                place
            )

            for tag in tags:

                normalized_tag = (
                    normalize_interest_name(
                        tag
                    )
                )

                for interest in interests:

                    if (
                        normalized_tag
                        ==
                        normalize_interest_name(
                            interest
                        )
                    ):

                        sent_distribution[
                            interest
                        ] += 1

        print()
        print(
            "📊 Balanced Gemini input:"
        )

        print(
            f"   📍 Unique places sent → "
            f"{len(places_context)}"
        )

        print()
        print(
            "📊 Interest coverage inside those places:"
        )

        for (
            interest,
            count
        ) in sent_distribution.items():

            print(
                f"   {interest} → "
                f"{count} tagged places"
            )

        # ====================================================
        # SAFETY CHECK
        # ====================================================

        if not places_context:

            return {

                "success": False,

                "error": (
                    "No verified places were "
                    "available for itinerary generation."
                ),

            }

        # ====================================================
        # COMPACT DATA
        # ====================================================

        interests_json = compact_json(
            interests
        )

        trip_json = compact_json(
            trip
        )

        destination_json = compact_json(
            destination
        )

        weather_json = compact_json(
            weather
        )

        places_json = compact_json(
            places_context
        )

        # ====================================================
        # REFLECTION / REPLAN FEEDBACK
        # ====================================================

        reflection_feedback_text = (
            prepare_reflection_feedback(
                reflection_feedback
            )
        )

        if reflection_feedback_text:

            print()
            print(
                "🔄 Reflection Agent feedback received."
            )

            print(
                "🧠 Applying Reflection Agent corrections "
                "to Gemini..."
            )

            print(
                reflection_feedback_text
            )

        # ====================================================
        # USER MEMORY / PERSONALIZATION
        # ====================================================

        user_memory_text = (
            prepare_user_memory(
                user_memories
            )
        )

        if user_memory_text:

            print()
            print(
                "🧠 User memory personalization "
                "enabled."
            )

            print(
                user_memory_text
            )

        else:

            print()
            print(
                "🧠 No user memory personalization "
                "available."
            )

        # ====================================================
        # AVAILABLE INTERESTS
        # ====================================================

        available_interest_lines = []

        for (
            interest,
            count
        ) in sent_distribution.items():

            if count > 0:

                available_interest_lines.append(
                    f"- {interest}: {count} verified record(s)"
                )

            else:

                available_interest_lines.append(
                    f"- {interest}: 0 verified places"
                )

        available_interests_text = "\n".join(
            available_interest_lines
        )

        # ====================================================
        # REFLECTION SECTION
        # ====================================================

        reflection_section = ""

        if reflection_feedback_text:

            reflection_section = f"""

============================================================
REFLECTION AGENT — REQUIRED CORRECTIONS
============================================================

The previous itinerary was checked by the Validation Agent.

The Reflection Agent identified these problems:

{reflection_feedback_text}

You MUST correct these problems in the NEW itinerary.

IMPORTANT:

- Do NOT repeat the identified problems.
- Keep all existing strict itinerary rules.
- Continue using ONLY the verified places supplied below.
- Do NOT invent replacement locations.
- Do NOT use places outside the verified place data.
- Do NOT remove valid user preferences.
- Do NOT reduce the requested number of days.
- Do NOT repeat physical places.
- Make the smallest practical corrections necessary.
- The new itinerary must be genuinely improved.

============================================================
END REFLECTION AGENT CORRECTIONS
============================================================
"""

        # ====================================================
        # OPTIMIZED PROMPT
        # ====================================================

        prompt = f"""
You are VoyageMind AI's itinerary planning engine.

Create a practical, personalized travel itinerary using ONLY
the verified place data supplied below.

============================================================
USER SELECTED INTERESTS
============================================================

{interests_json}

============================================================
VERIFIED INTEREST COVERAGE
============================================================

{available_interests_text}

============================================================
CRITICAL INTEREST COVERAGE RULE
============================================================

The user intentionally selected multiple interests.

You MUST include ALL selected interests that have at least
one verified place available.

Do NOT focus mainly on the first few interests.

Every available selected interest must appear in at least
ONE activity.

If one physical place satisfies multiple interests, that
place can count toward multiple interests.

NEVER repeat the same physical place merely to represent
another interest.

If an interest has ZERO verified places available, do NOT
invent a place. Mention that interest in the warnings array.

{reflection_section}

============================================================
STRICT RULES
============================================================

1. Use ONLY verified place names contained in VERIFIED PLACES DATA.

2. Every activity "place" MUST exactly match a verified place name.

3. NEVER invent a location.

4. NEVER create a location from general knowledge.

5. NEVER modify, translate, shorten or creatively rewrite a
   verified place name.

6. Generate EXACTLY {requested_days} day objects.

7. Each day MUST contain exactly 2 activities.

8. Do NOT repeat the same physical place.

9. Cover EVERY selected interest that has verified places.

10. Spread interests across the itinerary.

11. Do NOT prioritize Architecture, Food, Museums or Nature
    unless those are the available selected interests.

12. Use "interest_tags" from the verified place data.

13. The activity "interest" MUST contain one of the user's
    selected interests.

14. The activity "interest" should explain why that place
    satisfies the selected interest.

15. A place may satisfy multiple interests.

16. If a place satisfies multiple interests, select the most
    appropriate interest for the activity.

17. Consider weather conditions.

18. Consider opening hours when available.

19. Prefer geographically close places on the same day.

20. Do not claim exact ticket prices unless explicitly provided.

21. For unknown costs use exactly:

    "Not provided"

22. Keep descriptions concise.

23. Use clear natural English.

24. Do not include Markdown.

25. Do not include code fences.

26. Do not include explanations outside the JSON object.

27. Return ONLY the requested structured JSON.

============================================================
USER TRIP REQUEST
============================================================

{trip_json}

============================================================
DESTINATION
============================================================

{destination_json}

============================================================
CURRENT WEATHER
============================================================

{weather_json}

============================================================
USER MEMORY — PERSONALIZATION
============================================================

{user_memory_text}

============================================================
MEMORY RULES
============================================================

Use the user memories above to personalize the itinerary.

1. Treat memories as preferences, not hard constraints.

2. Preserve explicit preferences from the current trip request.

3. If a memory conflicts with the current trip request,
   follow the current trip request.

4. Do NOT invent user preferences.

5. Use memories only when relevant to travel planning.

6. Continue using ONLY verified places.

7. Do NOT mention internal memory retrieval in the final itinerary.

8. Do NOT expose memory metadata, similarity scores,
   database information, or internal system information.

9. Use memories naturally when selecting activities,
   travel style, restaurants, hotels, walking preferences,
   and other relevant planning decisions.

10. Current user instructions always have higher priority
    than stored memories.

============================================================
VERIFIED PLACES DATA
============================================================

{places_json}

============================================================
REPLAN RULE
============================================================

If Reflection Agent corrections are provided above, this is
a REPLANNING request.

You MUST correct every identified problem.

IMPORTANT:

1. Do NOT blindly reproduce the previous itinerary.

2. Fix every correction instruction.

3. Continue using ONLY verified places.

4. Do NOT invent new places.

5. Do NOT remove selected interests unless there are no
   verified places for that interest.

6. Preserve the user's budget and preferences.

7. Prefer geographically close activities when travel
   distance was identified as a problem.

8. If travel time was identified as a problem, replace or
   reorder activities to reduce unnecessary travel.

9. If an opening-hours problem was identified, reorganize
   using verified alternatives.

10. If a preference problem was identified, adjust the
    itinerary accordingly.

11. The corrected itinerary must still contain exactly
    {requested_days} day objects.

12. Each day MUST contain exactly 2 activities.

13. Do not repeat physical places.

14. Return ONLY the final structured JSON.

Create the itinerary now.
"""

        # ====================================================
        # TRY GEMINI MODELS
        # ====================================================

        generation_result = None

        model_errors = {}

        for model_name in MODELS:

            print()
            print(
                "=================================="
            )

            print(
                f"🚀 Trying model: "
                f"{model_name}"
            )

            print(
                "=================================="
            )

            result = generate_with_retry(

                model_name=model_name,

                prompt=prompt,

            )

            if result.get(
                "success"
            ):

                generation_result = result

                break

            model_errors[
                model_name
            ] = result.get(
                "error"
            )

            print()
            print(
                f"⚠️ Model failed: "
                f"{model_name}"
            )

        # ====================================================
        # ALL MODELS FAILED
        # ====================================================

        if not generation_result:

            print()
            print(
                "❌ ALL GEMINI MODELS FAILED"
            )

            print(
                json.dumps(
                    model_errors,
                    indent=2,
                )
            )

            return {

                "success": False,

                "error": (
                    "All Gemini models failed "
                    "after automatic retries."
                ),

                "model_errors":
                    model_errors,

            }

        # ====================================================
        # RESPONSE
        # ====================================================

        response = generation_result[
            "response"
        ]

        used_model = generation_result[
            "model"
        ]

        used_attempt = generation_result[
            "attempt"
        ]

        response_text = (
            response.text
            or ""
        ).strip()

        if not response_text:

            return {

                "success": False,

                "error":
                    "Gemini returned an empty response.",

            }

        print()
        print(
            "✅ Gemini response received."
        )

        print(
            f"🤖 Model used: "
            f"{used_model}"
        )

        # ====================================================
        # CLEAN POSSIBLE MARKDOWN
        # ====================================================

        if response_text.startswith(
            "```"
        ):

            response_text = (
                response_text
                .replace(
                    "```json",
                    "",
                )
                .replace(
                    "```",
                    "",
                )
                .strip()
            )

        # ====================================================
        # PARSE JSON WITH GENERATION RETRY
        # ====================================================

        itinerary = None

        json_error = None

        for json_attempt in range(
            1,
            3
        ):

            try:

                itinerary = json.loads(
                    response_text
                )

                break

            except json.JSONDecodeError as error:

                json_error = error

                print()
                print(
                    f"❌ Invalid JSON received "
                    f"(generation retry "
                    f"{json_attempt}/2)."
                )

                if json_attempt == 1:

                    repair_prompt = f"""
The previous itinerary response was incomplete or invalid JSON.

Generate the COMPLETE itinerary again.

CRITICAL REQUIREMENTS:

- Return ONLY valid JSON.
- Generate EXACTLY {requested_days} day objects.
- Each day MUST contain exactly 2 activities.
- Use ONLY verified place names contained in the verified
  places data below.
- Do NOT truncate the response.
- Complete every required field.
- Keep all text concise so the response fits within the
  output limit.
- Apply any Reflection Agent corrections.

VERIFIED PLACES DATA:

{places_json}

USER INTERESTS:

{interests_json}

USER MEMORY:

{user_memory_text}

TRIP:

{trip_json}

DESTINATION:

{destination_json}

WEATHER:

{weather_json}

REFLECTION CORRECTIONS:

{reflection_feedback_text}

Return ONLY the final structured JSON.
"""

                    retry_result = generate_with_retry(
                        model_name=used_model,
                        prompt=repair_prompt,
                    )

                    if retry_result.get(
                        "success"
                    ):

                        response = retry_result[
                            "response"
                        ]

                        used_attempt = (
                            retry_result.get(
                                "attempt",
                                used_attempt,
                            )
                        )

                        response_text = (
                            response.text
                            or ""
                        ).strip()

                        if response_text.startswith(
                            "```"
                        ):

                            response_text = (
                                response_text
                                .replace(
                                    "```json",
                                    "",
                                )
                                .replace(
                                    "```",
                                    "",
                                )
                                .strip()
                            )

                        continue

                print()
                print(
                    response_text
                )

        if itinerary is None:

            return {

                "success": False,

                "error":
                    "Gemini returned invalid JSON after automatic retries.",

                "json_error":
                    str(json_error),

            }

        # ====================================================
        # BASIC STRUCTURE VALIDATION
        # ====================================================

        if not isinstance(
            itinerary,
            dict,
        ):

            return {

                "success": False,

                "error": (
                    "Gemini returned an invalid "
                    "itinerary object."
                ),

            }

        generated_days = itinerary.get(
            "days",
            [],
        )

        if not isinstance(
            generated_days,
            list,
        ):

            return {

                "success": False,

                "error": (
                    "Gemini returned an invalid "
                    "days structure."
                ),

            }

        # ====================================================
        # VALIDATE NUMBER OF DAYS
        # ====================================================

        if (
            len(generated_days)
            != requested_days
        ):

            return {

                "success": False,

                "error": (
                    f"AI generated "
                    f"{len(generated_days)} days "
                    f"but "
                    f"{requested_days} days "
                    f"were requested."
                ),

            }

        # ====================================================
        # VERIFIED PLACE NAMES
        # ====================================================

        verified_place_names = {

            str(
                place.get(
                    "name"
                )
            ).strip().lower()

            for place
            in places_context

            if place.get(
                "name"
            )

        }

        # ====================================================
        # AVAILABLE INTERESTS
        # ====================================================

        available_interests = set()

        for interest in interests:

            for place in places_context:

                if place_matches_interest(
                    place,
                    interest,
                ):

                    available_interests.add(
                        normalize_interest_name(
                            interest
                        )
                    )

                    break

        # ====================================================
        # VALIDATE ACTIVITIES
        # ====================================================

        invalid_places = []

        used_places = set()

        generated_interest_coverage = set()

        for day in generated_days:

            activities = day.get(
                "activities",
                [],
            )

            if not isinstance(
                activities,
                list,
            ):

                continue

            for activity in activities:

                if not isinstance(
                    activity,
                    dict,
                ):

                    continue

                activity_place = str(
                    activity.get(
                        "place",
                        "",
                    )
                ).strip()

                normalized_place = (
                    activity_place.lower()
                )

                # --------------------------------------------
                # INVALID PLACE
                # --------------------------------------------

                if (
                    normalized_place
                    and
                    normalized_place
                    not in verified_place_names
                ):

                    invalid_places.append(
                        activity_place
                    )

                # --------------------------------------------
                # DUPLICATE PLACE
                # --------------------------------------------

                if normalized_place:

                    if (
                        normalized_place
                        in used_places
                    ):

                        print(
                            f"⚠️ Repeated place detected: "
                            f"{activity_place}"
                        )

                    used_places.add(
                        normalized_place
                    )

                # --------------------------------------------
                # INTEREST COVERAGE
                # --------------------------------------------

                activity_interest = (
                    activity.get(
                        "interest",
                        "",
                    )
                )

                normalized_activity_interest = (
                    normalize_interest_name(
                        activity_interest
                    )
                )

                if (
                    normalized_activity_interest
                    in available_interests
                ):

                    generated_interest_coverage.add(
                        normalized_activity_interest
                    )

                # --------------------------------------------
                # INFER INTEREST FROM VERIFIED PLACE
                # --------------------------------------------

                matching_place = next(

                    (
                        place
                        for place
                        in places_context

                        if (
                            str(
                                place.get(
                                    "name",
                                    ""
                                )
                            )
                            .strip()
                            .lower()
                            ==
                            normalized_place
                        )
                    ),

                    None,

                )

                if matching_place:

                    for interest in interests:

                        if place_matches_interest(
                            matching_place,
                            interest,
                        ):

                            if (
                                normalized_activity_interest
                                ==
                                normalize_interest_name(
                                    interest
                                )
                            ):

                                generated_interest_coverage.add(
                                    normalize_interest_name(
                                        interest
                                    )
                                )

        # ====================================================
        # STRICT PLACE VALIDATION
        # ====================================================

        if invalid_places:

            print()
            print(
                "❌ Gemini generated "
                "unverified places:"
            )

            print(
                invalid_places
            )

            return {

                "success": False,

                "error": (
                    "Gemini recommended places "
                    "that were not present in "
                    "the verified places database."
                ),

                "invalid_places":
                    invalid_places,

            }

        # ====================================================
        # INTEREST COVERAGE VALIDATION
        # ====================================================

        missing_interests = sorted(

            interest

            for interest
            in available_interests

            if interest
            not in generated_interest_coverage

        )

        if missing_interests:

            print()
            print(
                "⚠️ Gemini did not explicitly cover "
                "all available interests."
            )

            print(
                "Missing interests:"
            )

            print(
                missing_interests
            )

        # ====================================================
        # SUCCESS
        # ====================================================

        print()
        print(
            "🎉 Gemini itinerary generated successfully!"
        )

        print(
            f"📅 Days generated: "
            f"{len(generated_days)}"
        )

        print(
            f"📍 Verified places used: "
            f"{len(places_context)}"
        )

        print(
            "📊 Generated interest coverage:"
        )

        for interest in interests:

            normalized_interest = (
                normalize_interest_name(
                    interest
                )
            )

            if (
                normalized_interest
                in generated_interest_coverage
            ):

                print(
                    f"   ✅ {interest}"
                )

            elif (
                normalized_interest
                in available_interests
            ):

                print(
                    f"   ⚠️ {interest} → missing"
                )

            else:

                print(
                    f"   ℹ️ {interest} → "
                    f"no verified places"
                )

        # ====================================================
        # RETURN
        # ====================================================

        return {

            "success": True,

            "itinerary":
                itinerary,

            "metadata": {

                "model_used":
                    used_model,

                "generation_attempt":
                    used_attempt,

                "requested_days":
                    requested_days,

                "generated_days":
                    len(generated_days),

                "verified_places_sent":
                    len(places_context),

                "selected_interests":
                    interests,

                "gemini_interest_distribution":
                    sent_distribution,

                "available_interests":
                    list(
                        available_interests
                    ),

                "generated_interest_coverage":
                    list(
                        generated_interest_coverage
                    ),

                "missing_interests":
                    missing_interests,

                "invalid_places_detected":
                    [],

                "reflection_feedback_applied":
                    bool(
                        reflection_feedback_text
                    ),

                "user_memories_applied":
                    bool(
                        user_memory_text
                    ),

                "user_memory_count":
                    len(
                        user_memories
                        if isinstance(
                            user_memories,
                            list,
                        )
                        else []
                    ),

            },

        }

    except Exception as error:

        print()
        print(
            "❌ Gemini itinerary generation failed."
        )

        print(
            f"Error type: "
            f"{type(error).__name__}"
        )

        print(
            f"Error: "
            f"{str(error)}"
        )

        return {

            "success": False,

            "error":
                "Failed to generate AI itinerary.",

            "details":
                str(error),

        }