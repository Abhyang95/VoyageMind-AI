import time
import requests

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)

from app.config import GEOAPIFY_API_KEY


# ============================================================
# GEOAPIFY API
# ============================================================

GEOAPIFY_PLACES_URL = (
    "https://api.geoapify.com/v2/places"
)


# ============================================================
# INTEREST → GEOAPIFY CATEGORIES
# ============================================================

GEOAPIFY_CATEGORIES = {

    "architecture": [
        "tourism.attraction",
        "entertainment.museum",
    ],

    "history": [
        "tourism.attraction",
        "entertainment.museum",
    ],

    "food": [
        "catering.restaurant",
        "catering.cafe",
    ],

    "nightlife": [
        "catering.bar",
        "catering.pub",
        "adult.nightclub",
    ],

    "museums": [
        "entertainment.museum",
    ],

    "nature": [
        "leisure.park",
        "natural",
    ],

    "shopping": [
        "commercial.shopping_mall",
        "commercial.marketplace",
    ],

    "adventure": [
        "tourism.attraction",
        "sport.sports_centre",
        "sport.stadium",
        "entertainment.water_park",
    ],
}


# ============================================================
# DISPLAY NAMES
# ============================================================

INTEREST_DISPLAY_NAMES = {

    "architecture": "Architecture",
    "history": "History",
    "food": "Food",
    "nightlife": "Nightlife",
    "museums": "Museums",
    "nature": "Nature",
    "shopping": "Shopping",
    "adventure": "Adventure",
}


# ============================================================
# PERFORMANCE SETTINGS
# ============================================================

PLACES_PER_INTEREST = 12

GEOAPIFY_TIMEOUT = 8


# ============================================================
# NORMALIZE INTERESTS
# ============================================================

def normalize_interests(interests):

    if not interests:
        return []

    normalized = []

    for interest in interests:

        if not interest:
            continue

        value = str(
            interest
        ).strip().lower()

        if value in GEOAPIFY_CATEGORIES:

            if value not in normalized:

                normalized.append(
                    value
                )

    return normalized


# ============================================================
# UNIQUE PLACE KEY
# ============================================================

def get_place_unique_key(place):

    name = str(
        place.get(
            "name",
            "",
        )
    ).strip().lower()

    try:

        latitude = round(
            float(
                place.get(
                    "latitude",
                    0,
                )
            ),
            5,
        )

    except (
        TypeError,
        ValueError,
    ):

        latitude = 0

    try:

        longitude = round(
            float(
                place.get(
                    "longitude",
                    0,
                )
            ),
            5,
        )

    except (
        TypeError,
        ValueError,
    ):

        longitude = 0

    return (
        f"{name}|"
        f"{latitude}|"
        f"{longitude}"
    )


# ============================================================
# PARSE GEOAPIFY PLACE
# ============================================================

def parse_geoapify_place(
    feature,
    interest_category=None,
):

    properties = feature.get(
        "properties",
        {},
    )

    name = (
        properties.get("name")
        or properties.get("address_line1")
    )

    if not name:
        return None

    name = str(
        name
    ).strip()

    if not name:
        return None

    geometry = feature.get(
        "geometry",
        {},
    )

    coordinates = geometry.get(
        "coordinates",
        [],
    )

    if len(coordinates) < 2:
        return None

    try:

        longitude = float(
            coordinates[0]
        )

        latitude = float(
            coordinates[1]
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    categories = properties.get(
        "categories",
        [],
    )

    category = "place"

    if categories:

        category = categories[0]

    address = (
        properties.get("formatted")
        or properties.get("address_line2")
        or ""
    )

    interest_name = (
        INTEREST_DISPLAY_NAMES.get(
            interest_category,
            "Place",
        )
    )

    opening_hours = (
        properties.get(
            "opening_hours"
        )
        or properties.get(
            "openingHours"
        )
        or properties.get(
            "opening_hours_text"
        )
    )

    rating = properties.get(
        "rating"
    )

    review_count = (
        properties.get(
            "review_count"
        )
        or properties.get(
            "reviews"
        )
    )

    return {

        "name": name,

        "category": category,

        "interest": interest_name,

        "interest_category": interest_name,

        "interest_tags": [
            interest_name
        ],

        "latitude": latitude,

        "longitude": longitude,

        "address": address,

        "opening_hours": opening_hours,

        "rating": rating,

        "review_count": review_count,

    }


# ============================================================
# FETCH ONE GEOAPIFY REQUEST
# ============================================================

def fetch_geoapify_interest(
    latitude,
    longitude,
    interest,
    radius,
    limit,
):

    categories = GEOAPIFY_CATEGORIES.get(
        interest,
        [],
    )

    if not categories:

        return {
            "success": False,
            "features": [],
        }

    params = {

        "categories":
            ",".join(categories),

        "filter":
            (
                f"circle:"
                f"{longitude},"
                f"{latitude},"
                f"{radius}"
            ),

        "bias":
            (
                f"proximity:"
                f"{longitude},"
                f"{latitude}"
            ),

        "limit":
            limit,

        "apiKey":
            GEOAPIFY_API_KEY,

    }

    try:

        response = requests.get(

            GEOAPIFY_PLACES_URL,

            params=params,

            timeout=GEOAPIFY_TIMEOUT,

        )

        response.raise_for_status()

        data = response.json()

        return {

            "success": True,

            "features":
                data.get(
                    "features",
                    [],
                ),

        }

    except requests.RequestException as error:

        print(
            f"   ❌ Geoapify {interest} failed: "
            f"{str(error)}"
        )

        return {

            "success": False,

            "error":
                str(error),

            "features": [],

        }


# ============================================================
# SEARCH ONE INTEREST
# ============================================================

def search_geoapify_interest(
    interest,
    latitude,
    longitude,
    radius,
    quota,
):

    start_time = time.perf_counter()

    display_name = (
        INTEREST_DISPLAY_NAMES.get(
            interest,
            interest.title(),
        )
    )

    print(
        f"   🌍 Geoapify → "
        f"{display_name}"
    )

    result = fetch_geoapify_interest(

        latitude=latitude,

        longitude=longitude,

        interest=interest,

        radius=radius,

        limit=quota,

    )

    if not result.get("success"):

        return []

    features = result.get(
        "features",
        [],
    )

    places = []

    seen = set()

    for feature in features:

        place = parse_geoapify_place(

            feature=feature,

            interest_category=interest,

        )

        if not place:
            continue

        unique_key = (
            get_place_unique_key(
                place
            )
        )

        if unique_key in seen:
            continue

        seen.add(
            unique_key
        )

        places.append(
            place
        )

        if len(places) >= quota:
            break

    elapsed = (
        time.perf_counter()
        - start_time
    )

    print(
        f"   ⚡ Geoapify → "
        f"{display_name}: "
        f"{len(places)} places "
        f"({elapsed:.2f}s)"
    )

    return places


# ============================================================
# GET GEOAPIFY PLACES
# ============================================================

def get_geoapify_places(
    latitude: float,
    longitude: float,
    interests: list,
    radius: int = 5000,
    limit: int = 60,
):

    start_time = time.perf_counter()

    print()
    print(
        "🟣 Geoapify Fallback Agent started..."
    )

    # ========================================================
    # API KEY
    # ========================================================

    if not GEOAPIFY_API_KEY:

        return {

            "success": False,

            "error":
                "GEOAPIFY_API_KEY is missing.",

            "count": 0,

            "places": [],

        }

    # ========================================================
    # NORMALIZE
    # ========================================================

    normalized_interests = (
        normalize_interests(
            interests
        )
    )

    if not normalized_interests:

        normalized_interests = [
            "architecture",
            "food",
            "museums",
        ]

    # ========================================================
    # IMPORTANT:
    #
    # Do NOT globally cap the selected interests at 60.
    #
    # Each selected interest gets its own quota.
    #
    # 7 interests × 12 places = up to 84 raw results.
    # ========================================================

    requested_per_interest = min(
        PLACES_PER_INTEREST,
        max(
            1,
            int(limit),
        ),
    )

    print(
        f"   Interests: "
        f"{normalized_interests}"
    )

    print(
        f"   Max per interest: "
        f"{requested_per_interest}"
    )

    # ========================================================
    # SEARCH ALL INTERESTS IN PARALLEL
    # ========================================================

    results_by_interest = {}

    max_workers = min(
        5,
        len(normalized_interests),
    )

    with ThreadPoolExecutor(
        max_workers=max_workers
    ) as executor:

        future_map = {}

        for interest in normalized_interests:

            future = executor.submit(

                search_geoapify_interest,

                interest,

                latitude,

                longitude,

                radius,

                requested_per_interest,

            )

            future_map[
                future
            ] = interest

        for future in as_completed(
            future_map
        ):

            interest = future_map[
                future
            ]

            display_name = (
                INTEREST_DISPLAY_NAMES.get(
                    interest,
                    interest.title(),
                )
            )

            try:

                places = future.result()

            except Exception as error:

                print(
                    f"   ❌ Geoapify "
                    f"{display_name} error: "
                    f"{str(error)}"
                )

                places = []

            results_by_interest[
                interest
            ] = places

    # ========================================================
    # MERGE
    # ========================================================

    all_places = []

    place_index = {}

    for interest in normalized_interests:

        places = results_by_interest.get(
            interest,
            [],
        )

        display_name = (
            INTEREST_DISPLAY_NAMES.get(
                interest,
                interest.title(),
            )
        )

        for place in places:

            unique_key = (
                get_place_unique_key(
                    place
                )
            )

            if unique_key in place_index:

                existing_place = (
                    all_places[
                        place_index[
                            unique_key
                        ]
                    ]
                )

                tags = existing_place.get(
                    "interest_tags",
                    [],
                )

                if display_name not in tags:

                    tags.append(
                        display_name
                    )

                existing_place[
                    "interest_tags"
                ] = tags

                continue

            clean_place = dict(
                place
            )

            clean_place[
                "interest_tags"
            ] = [
                display_name
            ]

            place_index[
                unique_key
            ] = len(
                all_places
            )

            all_places.append(
                clean_place
            )

    # ========================================================
    # DISTRIBUTION
    # ========================================================

    category_distribution = {}

    for interest in normalized_interests:

        display_name = (
            INTEREST_DISPLAY_NAMES.get(
                interest,
                interest.title(),
            )
        )

        category_distribution[
            display_name
        ] = 0

    for place in all_places:

        tags = place.get(
            "interest_tags",
            [],
        )

        if not isinstance(
            tags,
            list,
        ):
            tags = []

        for tag in tags:

            if tag in category_distribution:

                category_distribution[
                    tag
                ] += 1

    # ========================================================
    # TOTAL TIME
    # ========================================================

    elapsed = (
        time.perf_counter()
        - start_time
    )

    print()
    print(
        "📊 Geoapify distribution:"
    )

    for (
        category,
        count
    ) in category_distribution.items():

        print(
            f"   {category} → {count}"
        )

    print(
        f"🟣 Geoapify total: "
        f"{len(all_places)} unique places"
    )

    print(
        f"⚡ Geoapify time: "
        f"{elapsed:.2f}s"
    )

    # ========================================================
    # SUCCESS
    # ========================================================

    if all_places:

        return {

            "success": True,

            "count":
                len(all_places),

            "places":
                all_places,

            "source":
                "Geoapify",

            "fallback_used":
                True,

            "cached":
                False,

            "category_distribution":
                category_distribution,

        }

    # ========================================================
    # FAILURE
    # ========================================================

    return {

        "success": False,

        "error":
            (
                "Geoapify could not find "
                "places for the selected interests."
            ),

        "count": 0,

        "places": [],

        "fallback_used":
            True,

        "cached":
            False,

        "category_distribution":
            category_distribution,

    }