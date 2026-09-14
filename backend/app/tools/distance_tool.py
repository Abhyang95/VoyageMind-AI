import time
import requests

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)

from app.config import GEOAPIFY_API_KEY


# ============================================================
# GEOAPIFY ROUTING API
# ============================================================

GEOAPIFY_ROUTING_URL = (
    "https://api.geoapify.com/v1/routing"
)


# ============================================================
# PERFORMANCE
# ============================================================

ROUTING_TIMEOUT = 8

MAX_DISTANCE_REQUESTS = 20

MAX_WORKERS = 5


# ============================================================
# FORMAT HELPERS
# ============================================================

def format_distance(distance_meters):
    """
    Convert meters into a user-friendly distance.
    """

    try:
        distance_meters = float(
            distance_meters
        )
    except (
        TypeError,
        ValueError,
    ):
        return "Unknown"


    if distance_meters < 1000:

        return (
            f"{round(distance_meters)} m"
        )


    distance_km = (
        distance_meters / 1000
    )

    return (
        f"{distance_km:.1f} km"
    )


# ============================================================
# TIME FORMATTER
# ============================================================

def format_travel_time(seconds):
    """
    Convert seconds into a human-readable duration.
    """

    try:
        seconds = int(
            round(
                float(seconds)
            )
        )

    except (
        TypeError,
        ValueError,
    ):
        return "Unknown"


    if seconds < 60:

        return (
            f"{seconds} sec"
        )


    minutes = round(
        seconds / 60
    )


    if minutes < 60:

        return (
            f"{minutes} min"
        )


    hours = minutes // 60

    remaining_minutes = (
        minutes % 60
    )


    if remaining_minutes == 0:

        return (
            f"{hours} hr"
        )


    return (
        f"{hours} hr "
        f"{remaining_minutes} min"
    )


# ============================================================
# GET TRAVEL MODE
# ============================================================

def get_travel_mode(
    walking_preference=True,
):
    """
    Convert VoyageMind walking preference
    into a Geoapify routing mode.
    """

    if walking_preference:

        return "walk"

    return "drive"


# ============================================================
# CALCULATE ONE ROUTE
# ============================================================

def calculate_route(
    from_latitude,
    from_longitude,
    to_latitude,
    to_longitude,
    mode="walk",
):
    """
    Calculate route distance and travel time
    between two coordinates.
    """

    if not GEOAPIFY_API_KEY:

        return {
            "success": False,
            "error": (
                "GEOAPIFY_API_KEY is missing."
            ),
        }


    # --------------------------------------------------------
    # Validate coordinates
    # --------------------------------------------------------

    try:

        from_latitude = float(
            from_latitude
        )

        from_longitude = float(
            from_longitude
        )

        to_latitude = float(
            to_latitude
        )

        to_longitude = float(
            to_longitude
        )

    except (
        TypeError,
        ValueError,
    ):

        return {
            "success": False,
            "error": (
                "Invalid route coordinates."
            ),
        }


    # --------------------------------------------------------
    # Same location
    # --------------------------------------------------------

    if (
        abs(
            from_latitude
            - to_latitude
        ) < 0.000001
        and
        abs(
            from_longitude
            - to_longitude
        ) < 0.000001
    ):

        return {
            "success": True,
            "distance_meters": 0,
            "distance": "0 m",
            "travel_time_seconds": 0,
            "travel_time": "0 min",
            "mode": mode,
        }


    # --------------------------------------------------------
    # Geoapify request
    # --------------------------------------------------------

    waypoints = (
        f"{from_latitude},"
        f"{from_longitude}|"
        f"{to_latitude},"
        f"{to_longitude}"
    )


    params = {

        "waypoints":
            waypoints,

        "mode":
            mode,

        "type":
            "balanced",

        "units":
            "metric",

        "format":
            "json",

        "apiKey":
            GEOAPIFY_API_KEY,

    }


    try:

        response = requests.get(

            GEOAPIFY_ROUTING_URL,

            params=params,

            timeout=ROUTING_TIMEOUT,

        )

        response.raise_for_status()

        data = response.json()


    except requests.RequestException as error:

        return {

            "success": False,

            "error":
                str(error),

        }


    except ValueError:

        return {

            "success": False,

            "error":
                "Geoapify returned invalid JSON.",

        }


    # --------------------------------------------------------
    # Parse route
    # --------------------------------------------------------

    results = data.get(
        "results",
        [],
    )


    if not results:

        return {

            "success": False,

            "error":
                "No route was returned by Geoapify.",

        }


    route = results[0]


    distance_meters = route.get(
        "distance"
    )

    travel_time_seconds = route.get(
        "time"
    )


    if (
        distance_meters is None
        or
        travel_time_seconds is None
    ):

        return {

            "success": False,

            "error":
                "Route distance or travel time is missing.",

        }


    return {

        "success": True,

        "distance_meters":
            round(
                float(
                    distance_meters
                )
            ),

        "distance":
            format_distance(
                distance_meters
            ),

        "travel_time_seconds":
            round(
                float(
                    travel_time_seconds
                )
            ),

        "travel_time":
            format_travel_time(
                travel_time_seconds
            ),

        "mode":
            mode,

    }


# ============================================================
# EXTRACT ACTIVITY COORDINATES
# ============================================================

def build_place_coordinate_index(
    places,
):
    """
    Build a fast lookup table:

        normalized place name
        →
        latitude / longitude
    """

    index = {}


    for place in places:

        if not isinstance(
            place,
            dict,
        ):
            continue


        name = place.get(
            "name"
        )

        latitude = place.get(
            "latitude"
        )

        longitude = place.get(
            "longitude"
        )


        if (
            not name
            or latitude is None
            or longitude is None
        ):
            continue


        normalized_name = (
            str(name)
            .strip()
            .lower()
        )


        index[
            normalized_name
        ] = {

            "name":
                str(name).strip(),

            "latitude":
                latitude,

            "longitude":
                longitude,

        }


    return index


# ============================================================
# BUILD ITINERARY ROUTES
# ============================================================

def build_itinerary_route_requests(
    itinerary,
    places,
    walking_preference=True,
):
    """
    Extract consecutive activities from the
    generated itinerary.

    Example:

        Louvre
          ↓
        Eiffel Tower
          ↓
        Arc de Triomphe

    creates:

        Louvre → Eiffel Tower
        Eiffel Tower → Arc de Triomphe
    """

    if not isinstance(
        itinerary,
        dict,
    ):

        return []


    days = itinerary.get(
        "days",
        [],
    )


    if not isinstance(
        days,
        list,
    ):

        return []


    coordinate_index = (
        build_place_coordinate_index(
            places
        )
    )


    mode = get_travel_mode(
        walking_preference
    )


    route_requests = []


    for day in days:

        if not isinstance(
            day,
            dict,
        ):
            continue


        activities = day.get(
            "activities",
            [],
        )


        if not isinstance(
            activities,
            list,
        ):
            continue


        previous_activity = None


        for activity in activities:

            if not isinstance(
                activity,
                dict,
            ):
                continue


            place_name = str(
                activity.get(
                    "place",
                    "",
                )
            ).strip()


            if not place_name:

                continue


            normalized_name = (
                place_name.lower()
            )


            current_place = (
                coordinate_index.get(
                    normalized_name
                )
            )


            if not current_place:

                previous_activity = None

                continue


            # ------------------------------------------------
            # First activity of the day
            # ------------------------------------------------

            if previous_activity:

                route_requests.append({

                    "day":
                        day.get(
                            "day"
                        ),

                    "from_place":
                        previous_activity[
                            "name"
                        ],

                    "from_latitude":
                        previous_activity[
                            "latitude"
                        ],

                    "from_longitude":
                        previous_activity[
                            "longitude"
                        ],

                    "to_place":
                        current_place[
                            "name"
                        ],

                    "to_latitude":
                        current_place[
                            "latitude"
                        ],

                    "to_longitude":
                        current_place[
                            "longitude"
                        ],

                    "mode":
                        mode,

                })


            previous_activity = (
                current_place
            )


    return route_requests


# ============================================================
# CALCULATE ITINERARY DISTANCES
# ============================================================

def calculate_itinerary_distances(
    itinerary,
    places,
    walking_preference=True,
):
    """
    Calculate travel distance/time between
    consecutive itinerary activities.
    """

    start_time = (
        time.perf_counter()
    )


    if not GEOAPIFY_API_KEY:

        return {

            "success": False,

            "error":
                "GEOAPIFY_API_KEY is missing.",

            "routes": [],

            "total_distance_meters":
                0,

            "total_distance":
                "0 m",

            "total_travel_time_seconds":
                0,

            "total_travel_time":
                "0 min",

        }


    route_requests = (
        build_itinerary_route_requests(

            itinerary=itinerary,

            places=places,

            walking_preference=(
                walking_preference
            ),

        )
    )


    if not route_requests:

        return {

            "success": True,

            "routes": [],

            "route_count": 0,

            "total_distance_meters":
                0,

            "total_distance":
                "0 m",

            "total_travel_time_seconds":
                0,

            "total_travel_time":
                "0 min",

            "mode":
                get_travel_mode(
                    walking_preference
                ),

        }


    # --------------------------------------------------------
    # Limit API calls
    # --------------------------------------------------------

    route_requests = (
        route_requests[
            :MAX_DISTANCE_REQUESTS
        ]
    )


    print()
    print(
        "🗺️ Distance Agent started..."
    )

    print(
        f"   Route requests: "
        f"{len(route_requests)}"
    )


    results = []


    # --------------------------------------------------------
    # Calculate routes in parallel
    # --------------------------------------------------------

    workers = min(
        MAX_WORKERS,
        len(route_requests),
    )


    with ThreadPoolExecutor(
        max_workers=workers
    ) as executor:

        future_map = {}


        for route in route_requests:

            future = executor.submit(

                calculate_route,

                route[
                    "from_latitude"
                ],

                route[
                    "from_longitude"
                ],

                route[
                    "to_latitude"
                ],

                route[
                    "to_longitude"
                ],

                route[
                    "mode"
                ],

            )


            future_map[
                future
            ] = route


        for future in as_completed(
            future_map
        ):

            route_request = (
                future_map[
                    future
                ]
            )


            try:

                result = (
                    future.result()
                )

            except Exception as error:

                result = {

                    "success":
                        False,

                    "error":
                        str(error),

                }


            route_result = {

                "day":
                    route_request[
                        "day"
                    ],

                "from_place":
                    route_request[
                        "from_place"
                    ],

                "to_place":
                    route_request[
                        "to_place"
                    ],

                "mode":
                    route_request[
                        "mode"
                    ],

                "success":
                    result.get(
                        "success",
                        False,
                    ),

                "distance_meters":
                    result.get(
                        "distance_meters"
                    ),

                "distance":
                    result.get(
                        "distance",
                        "Unknown",
                    ),

                "travel_time_seconds":
                    result.get(
                        "travel_time_seconds"
                    ),

                "travel_time":
                    result.get(
                        "travel_time",
                        "Unknown",
                    ),

            }


            if not result.get(
                "success"
            ):

                route_result[
                    "error"
                ] = result.get(
                    "error",
                    "Route calculation failed.",
                )


            results.append(
                route_result
            )


    # --------------------------------------------------------
    # Restore itinerary order
    # --------------------------------------------------------

    def route_sort_key(route):

        day = route.get(
            "day"
        )

        try:
            day = int(day)
        except (
            TypeError,
            ValueError,
        ):
            day = 999


        return (
            day,
            route.get(
                "from_place",
                "",
            ),
        )


    # We preserve API result order by matching
    # the original route request order.

    ordered_results = []


    for request in route_requests:

        matching_route = next(

            (
                route
                for route in results

                if (
                    route.get(
                        "day"
                    )
                    ==
                    request.get(
                        "day"
                    )
                    and
                    route.get(
                        "from_place"
                    )
                    ==
                    request.get(
                        "from_place"
                    )
                    and
                    route.get(
                        "to_place"
                    )
                    ==
                    request.get(
                        "to_place"
                    )
                )
            ),

            None,

        )


        if matching_route:

            ordered_results.append(
                matching_route
            )


    # --------------------------------------------------------
    # Totals
    # --------------------------------------------------------

    total_distance = 0

    total_time = 0


    successful_routes = 0


    for route in ordered_results:

        if not route.get(
            "success"
        ):
            continue


        distance = route.get(
            "distance_meters"
        )


        travel_time = route.get(
            "travel_time_seconds"
        )


        if distance is not None:

            total_distance += float(
                distance
            )


        if travel_time is not None:

            total_time += float(
                travel_time
            )


        successful_routes += 1


    elapsed = (
        time.perf_counter()
        - start_time
    )


    print()
    print(
        "📊 Distance Agent result:"
    )

    print(
        f"   Routes calculated → "
        f"{successful_routes}/"
        f"{len(route_requests)}"
    )

    print(
        f"   Total travel distance → "
        f"{format_distance(total_distance)}"
    )

    print(
        f"   Total travel time → "
        f"{format_travel_time(total_time)}"
    )

    print(
        f"   Mode → "
        f"{get_travel_mode(walking_preference)}"
    )

    print(
        f"   ⚡ Distance Agent time → "
        f"{elapsed:.2f}s"
    )


    return {

        "success":
            True,

        "routes":
            ordered_results,

        "route_count":
            len(ordered_results),

        "successful_routes":
            successful_routes,

        "total_distance_meters":
            round(
                total_distance
            ),

        "total_distance":
            format_distance(
                total_distance
            ),

        "total_travel_time_seconds":
            round(
                total_time
            ),

        "total_travel_time":
            format_travel_time(
                total_time
            ),

        "mode":
            get_travel_mode(
                walking_preference
            ),

    }