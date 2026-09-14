import re
from datetime import datetime


# ============================================================
# VALIDATION CONFIGURATION
# ============================================================

MAX_TRAVEL_TIME_MINUTES = 90
MAX_REASONABLE_DAILY_TRAVEL_MINUTES = 180

SEVERE_WEATHER_KEYWORDS = {
    "storm",
    "thunderstorm",
    "heavy rain",
    "snow",
    "blizzard",
    "hurricane",
    "extreme",
}


# ============================================================
# GENERAL HELPERS
# ============================================================

def _normalize_text(value):
    if value is None:
        return ""

    return str(value).strip().casefold()


def _safe_number(value):
    """
    Convert common numeric values into float.

    Examples:
        1500
        "1500"
        "₹1,500"
        "INR 1500"

    Returns None when a reliable numeric value cannot be extracted.
    """
    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()

    if not text:
        return None

    # Remove commas and currency symbols/text.
    cleaned = text.replace(",", "")

    match = re.search(
        r"\d+(?:\.\d+)?",
        cleaned,
    )

    if not match:
        return None

    try:
        return float(match.group())
    except (ValueError, TypeError):
        return None


def _time_to_minutes(value):
    """
    Convert HH:MM into minutes from midnight.
    """
    if not value:
        return None

    text = str(value).strip()

    match = re.match(
        r"^(\d{1,2}):(\d{2})$",
        text,
    )

    if not match:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2))

    if hour == 24 and minute == 0:
        return 1440

    if hour > 23 or minute > 59:
        return None

    return hour * 60 + minute


def _activity_time_to_minutes(value):
    """
    Extract the time from an itinerary activity.

    Example:
        "09:30" -> 570
    """
    if not value:
        return None

    text = str(value).strip()

    match = re.search(
        r"(\d{1,2}):(\d{2})",
        text,
    )

    if not match:
        return None

    return _time_to_minutes(
        f"{match.group(1)}:{match.group(2)}"
    )


# ============================================================
# OPENING HOURS
# ============================================================

DAY_NAMES = {
    "mo": 0,
    "monday": 0,
    "tu": 1,
    "tue": 1,
    "tuesday": 1,
    "we": 2,
    "wed": 2,
    "wednesday": 2,
    "th": 3,
    "thu": 3,
    "thursday": 3,
    "fr": 4,
    "fri": 4,
    "friday": 4,
    "sa": 5,
    "sat": 5,
    "saturday": 5,
    "su": 6,
    "sun": 6,
    "sunday": 6,
}


def _expand_day_range(day_range):
    """
    Convert:
        Mo-Fr -> [0,1,2,3,4]
        Tu-Su -> [1,2,3,4,5,6]
        Mo -> [0]
    """
    if not day_range:
        return None

    normalized = (
        day_range
        .strip()
        .lower()
        .replace(".", "")
    )

    if "-" in normalized:
        start, end = normalized.split("-", 1)

        start_day = DAY_NAMES.get(start.strip())
        end_day = DAY_NAMES.get(end.strip())

        if start_day is None or end_day is None:
            return None

        if start_day <= end_day:
            return list(
                range(start_day, end_day + 1)
            )

        return list(
            range(start_day, 7)
        ) + list(
            range(0, end_day + 1)
        )

    single_day = DAY_NAMES.get(normalized)

    if single_day is None:
        return None

    return [single_day]


def _parse_opening_hours(opening_hours):
    """
    Parse common OSM-style opening hour strings.

    Examples:

        Mo-Su 09:00-18:00

        Mo-Fr 12:00-14:00,19:30-21:30

        Tu off

    Returns a list of rules.
    """

    if not opening_hours:
        return []

    text = str(opening_hours).strip()

    if not text:
        return []

    rules = []

    # OSM commonly separates rules with semicolons.
    segments = [
        segment.strip()
        for segment in text.split(";")
        if segment.strip()
    ]

    for segment in segments:
        if segment.lower() == "24/7":
            rules.append(
                {
                    "days": list(range(7)),
                    "closed": False,
                    "intervals": [(0, 1440)],
                }
            )
            continue

        # Example:
        # Mo-Fr 12:00-14:00,19:30-21:30
        match = re.match(
            r"^([A-Za-z]{2,9}(?:-[A-Za-z]{2,9})?)\s+(.*)$",
            segment,
        )

        if not match:
            continue

        day_expression = match.group(1)
        hours_expression = match.group(2).strip()

        days = _expand_day_range(
            day_expression
        )

        if days is None:
            continue

        if hours_expression.lower() == "off":
            rules.append(
                {
                    "days": days,
                    "closed": True,
                    "intervals": [],
                }
            )
            continue

        intervals = []

        for interval in hours_expression.split(","):
            interval = interval.strip()

            time_match = re.match(
                r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})",
                interval,
            )

            if not time_match:
                continue

            start = _time_to_minutes(
                time_match.group(1)
            )

            end = _time_to_minutes(
                time_match.group(2)
            )

            if start is None or end is None:
                continue

            intervals.append(
                (start, end)
            )

        if intervals:
            rules.append(
                {
                    "days": days,
                    "closed": False,
                    "intervals": intervals,
                }
            )

    return rules


def _get_start_date(trip):
    """
    Optional support for future start_date.

    Current TripRequest does not require start_date,
    so validation continues to work without it.
    """

    start_date = trip.get("start_date")

    if not start_date:
        return None

    try:
        return datetime.fromisoformat(
            str(start_date)
        ).date()
    except (ValueError, TypeError):
        return None


def _get_activity_weekday(
    trip,
    day_number,
):
    """
    If start_date exists, calculate the real weekday
    for an itinerary day.

    Without start_date, returns None.
    """

    start_date = _get_start_date(trip)

    if start_date is None:
        return None

    try:
        offset = int(day_number) - 1

        return (
            start_date
            .toordinal()
            + offset
        ) % 7
    except (ValueError, TypeError):
        return None


def validate_opening_hours(
    trip,
    itinerary,
    places_index,
):
    """
    Validate activity times against known opening hours.

    Important:
    If no start_date exists, we can only validate
    hours when the opening rule applies to all days.

    We never guess the weekday.
    """

    issues = []
    checked = 0
    skipped = 0

    days = itinerary.get("days", [])

    for day in days:
        day_number = day.get("day")

        activities = day.get(
            "activities",
            [],
        )

        if not isinstance(
            activities,
            list,
        ):
            continue

        weekday = _get_activity_weekday(
            trip,
            day_number,
        )

        for activity in activities:
            place_name = activity.get(
                "place"
            )

            if not place_name:
                continue

            place = places_index.get(
                _normalize_text(place_name)
            )

            if not place:
                continue

            opening_hours = place.get(
                "opening_hours"
            )

            if not opening_hours:
                skipped += 1
                continue

            rules = _parse_opening_hours(
                opening_hours
            )

            if not rules:
                skipped += 1
                continue

            activity_minutes = (
                _activity_time_to_minutes(
                    activity.get("time")
                )
            )

            if activity_minutes is None:
                skipped += 1
                continue

            applicable_rules = rules

            if weekday is not None:
                applicable_rules = [
                    rule
                    for rule in rules
                    if weekday in rule["days"]
                ]
            else:
                # Without start_date, only use
                # rules that explicitly apply to
                # all seven days.
                applicable_rules = [
                    rule
                    for rule in rules
                    if set(rule["days"])
                    == set(range(7))
                ]

            if not applicable_rules:
                skipped += 1
                continue

            checked += 1

            is_closed = any(
                rule["closed"]
                for rule in applicable_rules
            )

            if is_closed:
                issues.append(
                    {
                        "type": "opening_hours",
                        "severity": "error",
                        "day": day_number,
                        "place": place_name,
                        "message": (
                            f"{place_name} is closed "
                            f"when the activity is scheduled."
                        ),
                    }
                )

                continue

            is_open = False

            for rule in applicable_rules:
                for start, end in rule["intervals"]:
                    if start <= activity_minutes <= end:
                        is_open = True
                        break

                if is_open:
                    break

            if not is_open:
                issues.append(
                    {
                        "type": "opening_hours",
                        "severity": "error",
                        "day": day_number,
                        "place": place_name,
                        "message": (
                            f"{place_name} may be closed "
                            f"at the scheduled time "
                            f"{activity.get('time')}."
                        ),
                    }
                )

    return {
        "status": (
            "passed"
            if not issues
            else "failed"
        ),
        "checked": checked,
        "skipped": skipped,
        "issues": issues,
    }


# ============================================================
# VERIFIED PLACE VALIDATION
# ============================================================

def validate_verified_places(
    itinerary,
    places_index,
):
    issues = []
    checked = 0

    for day in itinerary.get(
        "days",
        [],
    ):
        for activity in day.get(
            "activities",
            [],
        ):
            place_name = activity.get(
                "place"
            )

            if not place_name:
                continue

            checked += 1

            if (
                _normalize_text(place_name)
                not in places_index
            ):
                issues.append(
                    {
                        "type": "verified_place",
                        "severity": "error",
                        "day": day.get("day"),
                        "place": place_name,
                        "message": (
                            f"{place_name} was not found "
                            "in the verified places returned "
                            "by the Places Agent."
                        ),
                    }
                )

    return {
        "status": (
            "passed"
            if not issues
            else "failed"
        ),
        "checked": checked,
        "issues": issues,
    }


# ============================================================
# DUPLICATE VALIDATION
# ============================================================

def validate_duplicates(itinerary):
    issues = []

    global_places = {}

    for day in itinerary.get(
        "days",
        [],
    ):
        day_number = day.get("day")
        day_places = set()

        for activity in day.get(
            "activities",
            [],
        ):
            place_name = activity.get(
                "place"
            )

            if not place_name:
                continue

            normalized = _normalize_text(
                place_name
            )

            # Same place repeated in one day.
            if normalized in day_places:
                issues.append(
                    {
                        "type": "duplicate",
                        "severity": "error",
                        "day": day_number,
                        "place": place_name,
                        "message": (
                            f"{place_name} appears more than "
                            f"once on Day {day_number}."
                        ),
                    }
                )

            day_places.add(normalized)

            # Same place across multiple days.
            if normalized in global_places:
                previous_day = global_places[
                    normalized
                ]

                if previous_day != day_number:
                    issues.append(
                        {
                            "type": "duplicate",
                            "severity": "warning",
                            "day": day_number,
                            "place": place_name,
                            "message": (
                                f"{place_name} is repeated "
                                f"from Day {previous_day}."
                            ),
                        }
                    )
            else:
                global_places[
                    normalized
                ] = day_number

    return {
        "status": (
            "passed"
            if not issues
            else "failed"
        ),
        "issues": issues,
    }


# ============================================================
# DISTANCE VALIDATION
# ============================================================

def validate_distance(
    distance_data,
):
    issues = []

    if not distance_data:
        return {
            "status": "skipped",
            "issues": [
                {
                    "type": "distance",
                    "severity": "warning",
                    "message": (
                        "Distance data was not available "
                        "for validation."
                    ),
                }
            ],
        }

    if not distance_data.get(
        "success",
        False,
    ):
        return {
            "status": "failed",
            "issues": [
                {
                    "type": "distance",
                    "severity": "error",
                    "message": (
                        "Distance calculation failed, "
                        "so route validation could not "
                        "be completed."
                    ),
                }
            ],
        }

    routes = distance_data.get(
        "routes",
        [],
    )

    for route in routes:
        if not route.get(
            "success",
            False,
        ):
            issues.append(
                {
                    "type": "distance",
                    "severity": "error",
                    "day": route.get("day"),
                    "message": (
                        f"Unable to calculate the route "
                        f"from {route.get('from_place')} "
                        f"to {route.get('to_place')}."
                    ),
                }
            )

    return {
        "status": (
            "passed"
            if not issues
            else "failed"
        ),
        "route_count": distance_data.get(
            "route_count",
            len(routes),
        ),
        "total_distance": distance_data.get(
            "total_distance"
        ),
        "total_travel_time": distance_data.get(
            "total_travel_time"
        ),
        "issues": issues,
    }


# ============================================================
# TRAVEL TIME VALIDATION
# ============================================================

def validate_travel_time(
    distance_data,
):
    issues = []

    if not distance_data:
        return {
            "status": "skipped",
            "issues": [],
        }

    routes = distance_data.get(
        "routes",
        [],
    )

    total_minutes = 0

    for route in routes:
        if not route.get(
            "success",
            False,
        ):
            continue

        seconds = _safe_number(
            route.get(
                "travel_time_seconds"
            )
        )

        if seconds is not None:
            minutes = seconds / 60
            total_minutes += minutes

            if (
                minutes
                > MAX_TRAVEL_TIME_MINUTES
            ):
                issues.append(
                    {
                        "type": "travel_time",
                        "severity": "error",
                        "day": route.get("day"),
                        "from_place": route.get(
                            "from_place"
                        ),
                        "to_place": route.get(
                            "to_place"
                        ),
                        "message": (
                            f"{route.get('from_place')} → "
                            f"{route.get('to_place')} requires "
                            f"approximately {round(minutes)} "
                            f"minutes of travel."
                        ),
                    }
                )

    if (
        total_minutes
        > MAX_REASONABLE_DAILY_TRAVEL_MINUTES
    ):
        issues.append(
            {
                "type": "travel_time",
                "severity": "warning",
                "message": (
                    "The itinerary contains a high amount "
                    "of total travel time. Consider grouping "
                    "nearby activities together."
                ),
            }
        )

    return {
        "status": (
            "passed"
            if not issues
            else "failed"
        ),
        "total_travel_minutes": round(
            total_minutes
        ),
        "issues": issues,
    }


# ============================================================
# BUDGET VALIDATION
# ============================================================

def validate_budget(
    trip,
    itinerary,
):
    issues = []

    trip_budget = _safe_number(
        trip.get("budget")
    )

    if trip_budget is None:
        return {
            "status": "skipped",
            "issues": [
                {
                    "type": "budget",
                    "severity": "warning",
                    "message": (
                        "Trip budget could not be "
                        "validated."
                    ),
                }
            ],
        }

    numeric_activity_cost = 0
    activities_with_cost = 0
    activities_without_cost = 0

    for day in itinerary.get(
        "days",
        [],
    ):
        for activity in day.get(
            "activities",
            [],
        ):
            raw_cost = activity.get(
                "estimated_cost"
            )

            cost = _safe_number(
                raw_cost
            )

            if cost is None:
                activities_without_cost += 1
                continue

            numeric_activity_cost += cost
            activities_with_cost += 1

    # We deliberately do NOT treat "Not provided"
    # as zero.
    if activities_with_cost == 0:
        return {
            "status": "skipped",
            "budget": trip_budget,
            "numeric_activity_cost": 0,
            "activities_with_cost": 0,
            "activities_without_cost": activities_without_cost,
            "issues": [
                {
                    "type": "budget",
                    "severity": "warning",
                    "message": (
                        "Activity costs were not provided "
                        "in the itinerary, so a complete "
                        "budget validation could not be performed."
                    ),
                }
            ],
        }

    if numeric_activity_cost > trip_budget:
        issues.append(
            {
                "type": "budget",
                "severity": "error",
                "message": (
                    f"Known activity costs "
                    f"({numeric_activity_cost:.2f}) "
                    f"already exceed the trip budget "
                    f"({trip_budget:.2f})."
                ),
            }
        )

    if activities_without_cost > 0:
        issues.append(
            {
                "type": "budget",
                "severity": "warning",
                "message": (
                    f"{activities_without_cost} activities "
                    "do not have a numeric estimated cost, "
                    "so the budget check is incomplete."
                ),
            }
        )

    return {
        "status": (
            "passed"
            if not any(
                issue["severity"] == "error"
                for issue in issues
            )
            else "failed"
        ),
        "budget": trip_budget,
        "numeric_activity_cost": round(
            numeric_activity_cost,
            2,
        ),
        "activities_with_cost": activities_with_cost,
        "activities_without_cost": activities_without_cost,
        "issues": issues,
    }


# ============================================================
# WEATHER VALIDATION
# ============================================================

def validate_weather(
    weather,
    itinerary,
):
    issues = []

    if not weather:
        return {
            "status": "skipped",
            "issues": [],
        }

    current = weather.get(
        "current",
        weather,
    )

    condition = str(
        current.get(
            "condition",
            ""
        )
    ).lower()

    for keyword in SEVERE_WEATHER_KEYWORDS:
        if keyword in condition:
            issues.append(
                {
                    "type": "weather",
                    "severity": "warning",
                    "message": (
                        f"Current weather indicates "
                        f"'{current.get('condition')}'. "
                        "Outdoor activities should be reviewed."
                    ),
                }
            )
            break

    # We currently have current-weather data rather
    # than a day-by-day forecast, so do not pretend
    # to validate future days.
    if len(
        itinerary.get("days", [])
    ) > 1:
        weather_scope_note = (
            "Weather validation is based on the "
            "available current conditions; future "
            "day-specific weather is not assumed."
        )
    else:
        weather_scope_note = (
            "Weather validation uses the available "
            "current conditions."
        )

    return {
        "status": (
            "passed"
            if not issues
            else "warning"
        ),
        "condition": current.get(
            "condition"
        ),
        "temperature": current.get(
            "temperature"
        ),
        "precipitation": current.get(
            "precipitation"
        ),
        "scope": weather_scope_note,
        "issues": issues,
    }


# ============================================================
# PREFERENCE VALIDATION
# ============================================================

def validate_preferences(
    trip,
    distance_data,
    itinerary,
):
    issues = []

    preferences = trip.get(
        "preferences",
        {},
    )

    walking_preference = preferences.get(
        "walking_preference"
    )

    restaurant_budget = preferences.get(
        "restaurant_budget"
    )

    # --------------------------------------------------------
    # Walking preference
    # --------------------------------------------------------

    if (
        walking_preference is True
        and distance_data
        and distance_data.get("success")
    ):
        mode = str(
            distance_data.get(
                "mode",
                ""
            )
        ).lower()

        if mode != "walk":
            issues.append(
                {
                    "type": "preference",
                    "severity": "warning",
                    "message": (
                        "The user prefers walking, "
                        "but the calculated route mode "
                        f"is '{mode}'."
                    ),
                }
            )

    # --------------------------------------------------------
    # Restaurant budget
    # --------------------------------------------------------

    if restaurant_budget:
        restaurant_budget_text = str(
            restaurant_budget
        ).lower()

        if restaurant_budget_text in {
            "budget",
            "low",
            "cheap",
        }:
            preference_description = (
                "budget-friendly"
            )
        elif restaurant_budget_text in {
            "moderate",
            "mid-range",
            "medium",
        }:
            preference_description = (
                "moderately priced"
            )
        elif restaurant_budget_text in {
            "luxury",
            "high",
            "expensive",
        }:
            preference_description = (
                "higher-end"
            )
        else:
            preference_description = (
                restaurant_budget_text
            )

        # Current itinerary data does not contain
        # reliable restaurant price metadata.
        issues.append(
            {
                "type": "preference",
                "severity": "info",
                "message": (
                    f"Restaurant preference is "
                    f"'{preference_description}'. "
                    "Restaurant price validation requires "
                    "numeric price data from the Places Agent."
                ),
            }
        )

    return {
        "status": (
            "passed"
            if not any(
                issue["severity"] == "warning"
                for issue in issues
            )
            else "warning"
        ),
        "issues": issues,
    }


# ============================================================
# VALIDATION AGENT
# ============================================================

def run_validation_agent(
    trip,
    destination,
    weather,
    places_data,
    itinerary,
    distance_data,
):
    print()
    print("🔍 Validation Agent started...")

    # --------------------------------------------------------
    # Normalize itinerary
    # --------------------------------------------------------

    if not isinstance(
        itinerary,
        dict,
    ):
        return {
            "success": False,
            "is_valid": False,
            "error": (
                "Invalid itinerary supplied "
                "to Validation Agent."
            ),
            "issues": [],
        }

    # --------------------------------------------------------
    # Build verified-place index
    # --------------------------------------------------------

    raw_places = []

    if isinstance(
        places_data,
        dict,
    ):
        raw_places = places_data.get(
            "places",
            [],
        )

    places_index = {}

    for place in raw_places:
        if not isinstance(
            place,
            dict,
        ):
            continue

        name = place.get("name")

        if not name:
            continue

        places_index[
            _normalize_text(name)
        ] = place

    # --------------------------------------------------------
    # Run validation checks
    # --------------------------------------------------------

    checks = {}

    checks["verified_places"] = (
        validate_verified_places(
            itinerary,
            places_index,
        )
    )

    checks["duplicates"] = (
        validate_duplicates(
            itinerary
        )
    )

    checks["opening_hours"] = (
        validate_opening_hours(
            trip,
            itinerary,
            places_index,
        )
    )

    checks["distance"] = (
        validate_distance(
            distance_data
        )
    )

    checks["travel_time"] = (
        validate_travel_time(
            distance_data
        )
    )

    checks["budget"] = (
        validate_budget(
            trip,
            itinerary,
        )
    )

    checks["weather"] = (
        validate_weather(
            weather,
            itinerary,
        )
    )

    checks["preferences"] = (
        validate_preferences(
            trip,
            distance_data,
            itinerary,
        )
    )

    # --------------------------------------------------------
    # Collect all issues
    # --------------------------------------------------------

    issues = []

    for check_name, check_result in checks.items():
        for issue in check_result.get(
            "issues",
            [],
        ):
            issue_copy = dict(issue)

            issue_copy[
                "check"
            ] = check_name

            issues.append(
                issue_copy
            )

    # --------------------------------------------------------
    # Calculate summary
    # --------------------------------------------------------

    errors = sum(
        1
        for issue in issues
        if issue.get("severity")
        == "error"
    )

    warnings = sum(
        1
        for issue in issues
        if issue.get("severity")
        == "warning"
    )

    infos = sum(
        1
        for issue in issues
        if issue.get("severity")
        == "info"
    )

    total_checks = len(checks)

    failed_checks = sum(
        1
        for check in checks.values()
        if check.get("status")
        == "failed"
    )

    is_valid = (
        errors == 0
        and failed_checks == 0
    )

    # --------------------------------------------------------
    # Logging
    # --------------------------------------------------------

    print()
    print("📋 Validation Results")

    for check_name, check_result in checks.items():
        status = check_result.get(
            "status",
            "unknown",
        )

        if status == "passed":
            icon = "✅"
        elif status == "warning":
            icon = "⚠️"
        elif status == "failed":
            icon = "❌"
        else:
            icon = "ℹ️"

        print(
            f"   {icon} {check_name}"
        )

    print()
    print(
        f"   Errors   → {errors}"
    )
    print(
        f"   Warnings → {warnings}"
    )
    print(
        f"   Info     → {infos}"
    )
    print(
        f"   Checks   → {total_checks}"
    )

    if is_valid:
        print()
        print(
            "✅ Validation Agent: itinerary passed validation."
        )
    else:
        print()
        print(
            "⚠️ Validation Agent: issues detected."
        )

    print("🔍 Validation Agent completed.")

    return {
        "success": True,
        "is_valid": is_valid,
        "summary": {
            "errors": errors,
            "warnings": warnings,
            "info": infos,
            "total_checks": total_checks,
            "failed_checks": failed_checks,
        },
        "checks": checks,
        "issues": issues,
    }