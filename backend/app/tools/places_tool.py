import time
import requests

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)

from app.tools.geoapify_places_tool import (
    get_geoapify_places,
)


# ============================================================
# OVERPASS ENDPOINT
# ============================================================

OVERPASS_ENDPOINT = (
    "https://overpass-api.de/api/interpreter"
)


# ============================================================
# HTTP HEADERS
# ============================================================

HEADERS = {
    "User-Agent": "VoyageMind-AI/1.0",
    "Accept": "application/json",
}


# ============================================================
# PERFORMANCE
# ============================================================
#
# IMPORTANT:
#
# Overpass is used as the primary source.
# Geoapify is already a reliable fallback.
#
# Therefore we do NOT allow a slow Overpass request
# to hold the entire Places Agent for 5+ seconds.
#
# Previous:
#
# CONNECT = 2s
# READ    = 5s
# SERVER  = 5s
#
# New:
#
# CONNECT = 1s
# READ    = 2.5s
# SERVER  = 2.5s
#
# This gives Overpass enough time to respond when healthy,
# while allowing Geoapify fallback to start much earlier.
# ============================================================

OVERPASS_CONNECT_TIMEOUT = 1
OVERPASS_READ_TIMEOUT = 2.5
OVERPASS_SERVER_TIMEOUT = 2.5

OVERPASS_RESULT_LIMIT = 100


# ============================================================
# MAX PLACES PER INTEREST
# ============================================================

MAX_PLACES_PER_INTEREST = 12


# ============================================================
# MINIMUM REQUIRED FOR SUCCESS
# ============================================================

MINIMUM_TOTAL_PLACES = 5


# ============================================================
# CACHE
# ============================================================

PLACES_CACHE = {}

CACHE_DURATION = 300


# ============================================================
# INTEREST → OSM TAGS
# ============================================================

INTEREST_QUERIES = {

    "architecture": [
        ("tourism", "attraction"),
        ("historic", None),
        ("man_made", "tower"),
        ("amenity", "place_of_worship"),
    ],

    "history": [
        ("historic", None),
        ("tourism", "museum"),
        ("tourism", "attraction"),
        ("heritage", None),
    ],

    "food": [
        ("amenity", "restaurant"),
        ("amenity", "cafe"),
        ("amenity", "fast_food"),
        ("amenity", "food_court"),
    ],

    "nightlife": [
        ("amenity", "bar"),
        ("amenity", "pub"),
        ("amenity", "nightclub"),
        ("amenity", "biergarten"),
    ],

    "museums": [
        ("tourism", "museum"),
        ("tourism", "gallery"),
        ("tourism", "attraction"),
    ],

    "nature": [
        ("leisure", "park"),
        ("natural", "water"),
        ("natural", "wood"),
        ("leisure", "nature_reserve"),
    ],

    "shopping": [
        ("shop", "mall"),
        ("shop", "department_store"),
        ("shop", "clothes"),
        ("amenity", "marketplace"),
    ],

    "adventure": [
        ("tourism", "attraction"),
        ("leisure", "sports_centre"),
        ("leisure", "stadium"),
        ("leisure", "water_park"),
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
# NORMALIZE INTERESTS
# ============================================================

def normalize_interests(interests):

    if not interests:
        return []

    normalized = []

    for interest in interests:

        if not isinstance(
            interest,
            str,
        ):
            continue

        value = (
            interest
            .strip()
            .lower()
        )

        if value not in INTEREST_QUERIES:
            continue

        if value not in normalized:

            normalized.append(
                value
            )

    return normalized


# ============================================================
# BUILD ONE COMBINED OVERPASS QUERY
# ============================================================

def build_combined_overpass_query(
    latitude,
    longitude,
    interest,
    radius,
):

    filters = INTEREST_QUERIES.get(
        interest,
        [],
    )

    if not filters:
        return None

    query_parts = []

    for key, value in filters:

        if value is None:

            query_parts.append(
                f'nwr["{key}"]'
                f'(around:{radius},'
                f'{latitude},'
                f'{longitude});'
            )

        else:

            query_parts.append(
                f'nwr["{key}"="{value}"]'
                f'(around:{radius},'
                f'{latitude},'
                f'{longitude});'
            )

    query = f"""
[out:json][timeout:{OVERPASS_SERVER_TIMEOUT}];
(
    {' '.join(query_parts)}
);
out center {OVERPASS_RESULT_LIMIT};
"""

    return query.strip()


# ============================================================
# FETCH OVERPASS
# ============================================================

def fetch_overpass_query(query):

    start_time = time.perf_counter()

    try:

        response = requests.post(

            OVERPASS_ENDPOINT,

            data=query,

            headers=HEADERS,

            timeout=(
                OVERPASS_CONNECT_TIMEOUT,
                OVERPASS_READ_TIMEOUT,
            ),

        )

        response.raise_for_status()

        data = response.json()

        elapsed = (
            time.perf_counter()
            - start_time
        )

        print(
            f"      ⚡ Overpass success "
            f"({elapsed:.2f}s)"
        )

        return data

    except requests.exceptions.Timeout:

        elapsed = (
            time.perf_counter()
            - start_time
        )

        print(
            f"      ⏱️ Overpass fast timeout "
            f"({elapsed:.2f}s)"
        )

        return None

    except requests.exceptions.RequestException as error:

        elapsed = (
            time.perf_counter()
            - start_time
        )

        print(
            f"      ❌ Overpass request failed "
            f"({elapsed:.2f}s)"
        )

        print(
            f"         {str(error)}"
        )

        return None

    except ValueError:

        print(
            "      ❌ Overpass returned invalid JSON."
        )

        return None

    except Exception as error:

        print(
            f"      ❌ Overpass unexpected error: "
            f"{str(error)}"
        )

        return None


# ============================================================
# PARSE OSM PLACE
# ============================================================

def parse_place(
    element,
    interest,
):

    tags = element.get(
        "tags",
        {},
    )

    name = tags.get(
        "name"
    )

    if not name:
        return None

    name = str(
        name
    ).strip()

    if not name:
        return None


    # ========================================================
    # COORDINATES
    # ========================================================

    latitude = element.get(
        "lat"
    )

    longitude = element.get(
        "lon"
    )

    if (
        latitude is None
        or longitude is None
    ):

        center = element.get(
            "center",
            {},
        )

        latitude = center.get(
            "lat"
        )

        longitude = center.get(
            "lon"
        )

    if (
        latitude is None
        or longitude is None
    ):

        return None


    # ========================================================
    # CATEGORY
    # ========================================================

    category = (
        tags.get("tourism")
        or tags.get("amenity")
        or tags.get("historic")
        or tags.get("leisure")
        or tags.get("natural")
        or tags.get("shop")
        or tags.get("man_made")
        or "place"
    )


    # ========================================================
    # ADDRESS
    # ========================================================

    address_parts = []

    house_number = tags.get(
        "addr:housenumber"
    )

    street = tags.get(
        "addr:street"
    )

    city = tags.get(
        "addr:city"
    )

    postcode = tags.get(
        "addr:postcode"
    )

    if house_number:
        address_parts.append(
            str(house_number)
        )

    if street:
        address_parts.append(
            str(street)
        )

    if city:
        address_parts.append(
            str(city)
        )

    if postcode:
        address_parts.append(
            str(postcode)
        )

    address = ", ".join(
        address_parts
    )


    # ========================================================
    # INTEREST
    # ========================================================

    interest_name = (
        INTEREST_DISPLAY_NAMES.get(
            interest,
            interest.title(),
        )
    )


    # ========================================================
    # RETURN
    # ========================================================

    return {

        "name": name,

        "category": category,

        "interest": interest_name,

        "interest_category": interest_name,

        "interest_tags": [
            interest_name
        ],

        "latitude": float(latitude),

        "longitude": float(longitude),

        "address": address,

        "opening_hours": tags.get(
            "opening_hours"
        ),

        "rating": tags.get(
            "rating"
        ),

        "review_count": (
            tags.get("review_count")
            or tags.get("reviews")
        ),

    }


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
# SEARCH ONE INTEREST WITH OVERPASS
# ============================================================

def search_interest_places(
    latitude,
    longitude,
    interest,
    radius,
):

    display_name = (
        INTEREST_DISPLAY_NAMES.get(
            interest,
            interest.title(),
        )
    )

    start_time = time.perf_counter()

    print(
        f"   🔵 Overpass → "
        f"{display_name}"
    )

    query = build_combined_overpass_query(
        latitude=latitude,
        longitude=longitude,
        interest=interest,
        radius=radius,
    )

    if not query:
        return []

    data = fetch_overpass_query(
        query
    )

    if not data:
        return []

    elements = data.get(
        "elements",
        [],
    )

    places = []

    seen = set()

    for element in elements:

        place = parse_place(
            element,
            interest,
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

        if (
            len(places)
            >= MAX_PLACES_PER_INTEREST
        ):
            break

    elapsed = (
        time.perf_counter()
        - start_time
    )

    print(
        f"   ✅ {display_name}: "
        f"{len(places)} places "
        f"({elapsed:.2f}s)"
    )

    return places


# ============================================================
# SEARCH ONE INTEREST WITH FALLBACK
# ============================================================

def search_interest_with_fallback(
    latitude,
    longitude,
    interest,
    radius,
):

    display_name = (
        INTEREST_DISPLAY_NAMES.get(
            interest,
            interest.title(),
        )
    )

    # ========================================================
    # FIRST: OVERPASS
    # ========================================================

    places = search_interest_places(
        latitude=latitude,
        longitude=longitude,
        interest=interest,
        radius=radius,
    )

    if places:

        return {

            "interest": interest,

            "places": places,

            "source": "Overpass",

        }


    # ========================================================
    # FALLBACK
    # ========================================================

    print(
        f"   ⚡ {display_name}: "
        f"Overpass failed → "
        f"Geoapify fallback"
    )

    start_time = time.perf_counter()

    try:

        geoapify_result = (
            get_geoapify_places(

                latitude=latitude,

                longitude=longitude,

                interests=[
                    interest
                ],

                radius=radius,

                limit=MAX_PLACES_PER_INTEREST,

            )
        )

    except Exception as error:

        print(
            f"   ❌ Geoapify "
            f"{display_name} failed: "
            f"{str(error)}"
        )

        return {

            "interest": interest,

            "places": [],

            "source": "failed",

        }

    fallback_places = []

    if isinstance(
        geoapify_result,
        dict,
    ):

        fallback_places = (
            geoapify_result.get(
                "places",
                [],
            )
        )

    elapsed = (
        time.perf_counter()
        - start_time
    )

    print(
        f"   🟣 {display_name}: "
        f"{len(fallback_places)} "
        f"Geoapify places "
        f"({elapsed:.2f}s)"
    )

    return {

        "interest": interest,

        "places": fallback_places,

        "source": "Geoapify",

    }


# ============================================================
# ADD INTEREST TAG
# ============================================================

def add_interest_tag(
    place,
    interest_name,
):

    tags = place.get(
        "interest_tags",
        [],
    )

    if not isinstance(
        tags,
        list,
    ):
        tags = []

    normalized_tags = []

    for tag in tags:

        if not tag:
            continue

        clean_tag = str(
            tag
        ).strip()

        if (
            clean_tag
            and clean_tag not in normalized_tags
        ):
            normalized_tags.append(
                clean_tag
            )

    if (
        interest_name
        and interest_name not in normalized_tags
    ):

        normalized_tags.append(
            interest_name
        )

    place["interest_tags"] = (
        normalized_tags
    )

    if not place.get("interest"):

        place["interest"] = (
            interest_name
        )

    if not place.get(
        "interest_category"
    ):

        place["interest_category"] = (
            interest_name
        )

    return place


# ============================================================
# MAIN PLACES AGENT
# ============================================================

def get_places(
    latitude,
    longitude,
    interests=None,
    radius=5000,
):

    total_start_time = (
        time.perf_counter()
    )

    print()
    print("=" * 60)
    print(
        "🚀 VoyageMind Places Agent started"
    )
    print("=" * 60)

    print(
        f"📍 Coordinates: "
        f"{latitude}, {longitude}"
    )


    # ========================================================
    # NORMALIZE INTERESTS
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

    print(
        f"🎯 Interests: "
        f"{normalized_interests}"
    )

    print(
        "⚡ Searching interests in parallel..."
    )


    # ========================================================
    # CACHE
    # ========================================================

    cache_key = (

        round(
            float(latitude),
            3,
        ),

        round(
            float(longitude),
            3,
        ),

        tuple(
            sorted(
                normalized_interests
            )
        ),

        radius,

    )

    cached = (
        PLACES_CACHE.get(
            cache_key
        )
    )

    if cached:

        cache_age = (
            time.time()
            - cached["timestamp"]
        )

        if cache_age < CACHE_DURATION:

            print()
            print(
                f"⚡ CACHE HIT "
                f"({cache_age:.1f}s old)"
            )

            return cached[
                "data"
            ]

        del PLACES_CACHE[
            cache_key
        ]


    # ========================================================
    # PARALLEL SEARCH
    # ========================================================

    all_results = []

    max_workers = min(
        5,
        len(normalized_interests),
    )

    parallel_start = (
        time.perf_counter()
    )

    with ThreadPoolExecutor(
        max_workers=max_workers
    ) as executor:

        future_map = {}

        for interest in normalized_interests:

            future = executor.submit(

                search_interest_with_fallback,

                latitude,

                longitude,

                interest,

                radius,

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

            try:

                result = (
                    future.result()
                )

            except Exception as error:

                print(
                    f"   ❌ "
                    f"{interest}: "
                    f"{str(error)}"
                )

                result = {

                    "interest":
                        interest,

                    "places":
                        [],

                    "source":
                        "failed",

                }

            all_results.append(
                result
            )


    parallel_elapsed = (
        time.perf_counter()
        - parallel_start
    )

    print()
    print(
        f"⚡ Parallel search completed "
        f"in {parallel_elapsed:.2f}s"
    )


    # ========================================================
    # MERGE RESULTS
    # ========================================================

    all_places = []

    place_index = {}

    result_map = {

        result["interest"]:
            result

        for result in all_results

    }


    # ========================================================
    # RAW DISTRIBUTION
    # ========================================================

    raw_distribution = {}

    for interest in normalized_interests:

        result = result_map.get(
            interest
        )

        display_name = (
            INTEREST_DISPLAY_NAMES.get(
                interest,
                interest.title(),
            )
        )

        places = []

        if result:

            places = result.get(
                "places",
                [],
            )

        raw_distribution[
            display_name
        ] = len(places)


    # ========================================================
    # MERGE PHYSICAL PLACES
    # ========================================================

    for interest in normalized_interests:

        result = result_map.get(
            interest
        )

        if not result:
            continue

        places = result.get(
            "places",
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

            if not unique_key:
                continue


            # ------------------------------------------------
            # EXISTING PHYSICAL PLACE
            # ------------------------------------------------

            if unique_key in place_index:

                existing_index = (
                    place_index[
                        unique_key
                    ]
                )

                existing_place = (
                    all_places[
                        existing_index
                    ]
                )

                add_interest_tag(
                    existing_place,
                    display_name,
                )

                continue


            # ------------------------------------------------
            # NEW PHYSICAL PLACE
            # ------------------------------------------------

            clean_place = dict(
                place
            )

            add_interest_tag(
                clean_place,
                display_name,
            )

            place_index[
                unique_key
            ] = len(
                all_places
            )

            all_places.append(
                clean_place
            )


    # ========================================================
    # FINAL DISTRIBUTION
    # ========================================================

    final_distribution = {}

    for interest in normalized_interests:

        display_name = (
            INTEREST_DISPLAY_NAMES.get(
                interest,
                interest.title(),
            )
        )

        final_distribution[
            display_name
        ] = 0


    # ========================================================
    # COUNT INTEREST TAGS
    # ========================================================

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

            if tag in final_distribution:

                final_distribution[
                    tag
                ] += 1


    # ========================================================
    # TOTAL TIME
    # ========================================================

    total_elapsed = (
        time.perf_counter()
        - total_start_time
    )


    # ========================================================
    # LOG
    # ========================================================

    print()
    print("=" * 60)
    print(
        "📊 FINAL PLACES RESULT"
    )
    print("=" * 60)

    print()
    print(
        "📊 Raw search results:"
    )

    for (
        category,
        count
    ) in raw_distribution.items():

        print(
            f"   {category}: "
            f"{count}"
        )

    print()
    print(
        "📊 Interest coverage after merge:"
    )

    for (
        category,
        count
    ) in final_distribution.items():

        print(
            f"   {category}: "
            f"{count}"
        )

    print(
        f"📍 Unique physical places: "
        f"{len(all_places)}"
    )

    print(
        f"⚡ Total Places Agent time: "
        f"{total_elapsed:.2f}s"
    )


    # ========================================================
    # SUCCESS
    # ========================================================

    if (
        len(all_places)
        >= MINIMUM_TOTAL_PLACES
    ):

        result = {

            "success":
                True,

            "places":
                all_places,

            "count":
                len(all_places),

            "category_distribution":
                final_distribution,

            "raw_category_distribution":
                raw_distribution,

            "interests":
                normalized_interests,

            "source":
                "overpass+geoapify",

        }


        # ====================================================
        # CACHE
        # ====================================================

        PLACES_CACHE[
            cache_key
        ] = {

            "timestamp":
                time.time(),

            "data":
                result,

        }

        print()
        print(
            "✅ Places Agent completed."
        )

        return result


    # ========================================================
    # FAILURE
    # ========================================================

    print()
    print(
        "❌ Not enough verified places found."
    )

    return {

        "success":
            False,

        "places":
            all_places,

        "count":
            len(all_places),

        "category_distribution":
            final_distribution,

        "raw_category_distribution":
            raw_distribution,

        "interests":
            normalized_interests,

        "error":
            (
                "Unable to find enough "
                "verified places."
            ),

    }