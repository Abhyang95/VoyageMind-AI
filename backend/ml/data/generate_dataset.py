import csv
import os
import random


random.seed(42)


DESTINATIONS = [
    {
        "destination": "Paris",
        "architecture_score": 0.98,
        "history_score": 0.95,
        "food_score": 0.97,
        "nightlife_score": 0.82,
        "museums_score": 0.99,
        "nature_score": 0.65,
        "shopping_score": 0.92,
        "adventure_score": 0.45,
        "average_daily_cost": 180,
        "walkability_score": 0.95,
        "weather_score": 0.82,
        "hotel_price": 160,
        "restaurant_price": 70,
    },
    {
        "destination": "Rome",
        "architecture_score": 0.97,
        "history_score": 0.99,
        "food_score": 0.96,
        "nightlife_score": 0.78,
        "museums_score": 0.91,
        "nature_score": 0.62,
        "shopping_score": 0.76,
        "adventure_score": 0.48,
        "average_daily_cost": 145,
        "walkability_score": 0.91,
        "weather_score": 0.90,
        "hotel_price": 125,
        "restaurant_price": 55,
    },
    {
        "destination": "Barcelona",
        "architecture_score": 0.96,
        "history_score": 0.84,
        "food_score": 0.94,
        "nightlife_score": 0.96,
        "museums_score": 0.82,
        "nature_score": 0.82,
        "shopping_score": 0.88,
        "adventure_score": 0.72,
        "average_daily_cost": 150,
        "walkability_score": 0.93,
        "weather_score": 0.94,
        "hotel_price": 130,
        "restaurant_price": 58,
    },
    {
        "destination": "Amsterdam",
        "architecture_score": 0.91,
        "history_score": 0.88,
        "food_score": 0.79,
        "nightlife_score": 0.92,
        "museums_score": 0.95,
        "nature_score": 0.78,
        "shopping_score": 0.86,
        "adventure_score": 0.65,
        "average_daily_cost": 175,
        "walkability_score": 0.96,
        "weather_score": 0.68,
        "hotel_price": 155,
        "restaurant_price": 65,
    },
    {
        "destination": "London",
        "architecture_score": 0.94,
        "history_score": 0.97,
        "food_score": 0.91,
        "nightlife_score": 0.95,
        "museums_score": 0.98,
        "nature_score": 0.76,
        "shopping_score": 0.98,
        "adventure_score": 0.55,
        "average_daily_cost": 210,
        "walkability_score": 0.89,
        "weather_score": 0.64,
        "hotel_price": 190,
        "restaurant_price": 75,
    },
    {
        "destination": "Tokyo",
        "architecture_score": 0.90,
        "history_score": 0.91,
        "food_score": 0.99,
        "nightlife_score": 0.96,
        "museums_score": 0.88,
        "nature_score": 0.74,
        "shopping_score": 0.99,
        "adventure_score": 0.71,
        "average_daily_cost": 165,
        "walkability_score": 0.91,
        "weather_score": 0.79,
        "hotel_price": 135,
        "restaurant_price": 60,
    },
    {
        "destination": "Dubai",
        "architecture_score": 0.96,
        "history_score": 0.63,
        "food_score": 0.91,
        "nightlife_score": 0.92,
        "museums_score": 0.72,
        "nature_score": 0.68,
        "shopping_score": 0.99,
        "adventure_score": 0.91,
        "average_daily_cost": 190,
        "walkability_score": 0.58,
        "weather_score": 0.96,
        "hotel_price": 175,
        "restaurant_price": 70,
    },
    {
        "destination": "Singapore",
        "architecture_score": 0.91,
        "history_score": 0.72,
        "food_score": 0.98,
        "nightlife_score": 0.85,
        "museums_score": 0.79,
        "nature_score": 0.94,
        "shopping_score": 0.97,
        "adventure_score": 0.79,
        "average_daily_cost": 155,
        "walkability_score": 0.90,
        "weather_score": 0.94,
        "hotel_price": 145,
        "restaurant_price": 50,
    },
    {
        "destination": "New York",
        "architecture_score": 0.94,
        "history_score": 0.82,
        "food_score": 0.96,
        "nightlife_score": 0.99,
        "museums_score": 0.97,
        "nature_score": 0.71,
        "shopping_score": 0.99,
        "adventure_score": 0.63,
        "average_daily_cost": 230,
        "walkability_score": 0.92,
        "weather_score": 0.76,
        "hotel_price": 210,
        "restaurant_price": 85,
    },
    {
        "destination": "Bali",
        "architecture_score": 0.73,
        "history_score": 0.76,
        "food_score": 0.91,
        "nightlife_score": 0.87,
        "museums_score": 0.51,
        "nature_score": 0.99,
        "shopping_score": 0.72,
        "adventure_score": 0.98,
        "average_daily_cost": 90,
        "walkability_score": 0.62,
        "weather_score": 0.95,
        "hotel_price": 70,
        "restaurant_price": 35,
    },
    {
        "destination": "Switzerland",
        "architecture_score": 0.79,
        "history_score": 0.78,
        "food_score": 0.82,
        "nightlife_score": 0.58,
        "museums_score": 0.75,
        "nature_score": 0.99,
        "shopping_score": 0.76,
        "adventure_score": 0.98,
        "average_daily_cost": 240,
        "walkability_score": 0.88,
        "weather_score": 0.78,
        "hotel_price": 220,
        "restaurant_price": 90,
    },
    {
        "destination": "Istanbul",
        "architecture_score": 0.94,
        "history_score": 0.98,
        "food_score": 0.94,
        "nightlife_score": 0.89,
        "museums_score": 0.84,
        "nature_score": 0.71,
        "shopping_score": 0.91,
        "adventure_score": 0.58,
        "average_daily_cost": 85,
        "walkability_score": 0.84,
        "weather_score": 0.88,
        "hotel_price": 65,
        "restaurant_price": 32,
    },
]


INTERESTS = [
    "architecture",
    "history",
    "food",
    "nightlife",
    "museums",
    "nature",
    "shopping",
    "adventure",
]


def generate_user_preferences():
    preferences = {}

    for interest in INTERESTS:
        preferences[f"{interest}_preference"] = round(
            random.uniform(0.0, 1.0),
            3,
        )

    preferences["budget"] = random.choice(
        [700, 900, 1100, 1300, 1500, 1800, 2200, 2600]
    )

    preferences["walking_preference"] = random.choice(
        [0, 1]
    )

    return preferences


def calculate_match_score(destination, user):
    interest_score = sum(
        destination[f"{interest}_score"]
        * user[f"{interest}_preference"]
        for interest in INTERESTS
    )

    total_preference = sum(
        user[f"{interest}_preference"]
        for interest in INTERESTS
    )

    if total_preference > 0:
        interest_score /= total_preference

    budget_ratio = (
        user["budget"]
        / destination["average_daily_cost"]
    )

    if budget_ratio >= 1:
        budget_score = 1.0
    else:
        budget_score = max(
            0.0,
            budget_ratio,
        )

    walking_score = destination["walkability_score"]

    if user["walking_preference"] == 1:
        walking_component = walking_score
    else:
        walking_component = 0.5

    final_score = (
        interest_score * 0.60
        + budget_score * 0.20
        + destination["weather_score"] * 0.10
        + walking_component * 0.10
    )

    noise = random.uniform(
        -0.025,
        0.025,
    )

    final_score += noise

    return round(
        max(0.0, min(1.0, final_score)),
        4,
    )


def main():
    current_dir = os.path.dirname(
        os.path.abspath(__file__)
    )

    output_file = os.path.join(
        current_dir,
        "travel_recommendation_dataset.csv",
    )

    rows = []

    for _ in range(1500):
        user = generate_user_preferences()

        for destination in random.sample(
            DESTINATIONS,
            random.randint(3, 7),
        ):
            score = calculate_match_score(
                destination,
                user,
            )

            row = {
                "destination": destination["destination"],
            }

            for interest in INTERESTS:
                row[
                    f"{interest}_preference"
                ] = user[
                    f"{interest}_preference"
                ]

                row[
                    f"{interest}_score"
                ] = destination[
                    f"{interest}_score"
                ]

            row["budget"] = user["budget"]

            row["walking_preference"] = user[
                "walking_preference"
            ]

            row["average_daily_cost"] = destination[
                "average_daily_cost"
            ]

            row["walkability_score"] = destination[
                "walkability_score"
            ]

            row["weather_score"] = destination[
                "weather_score"
            ]

            row["hotel_price"] = destination[
                "hotel_price"
            ]

            row["restaurant_price"] = destination[
                "restaurant_price"
            ]

            row["match_score"] = score

            rows.append(row)

    fieldnames = list(rows[0].keys())

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)

    print()
    print("========================================")
    print("VoyageMind AI ML Dataset Generator")
    print("========================================")
    print()
    print(f"Dataset created successfully.")
    print(f"Rows: {len(rows)}")
    print(f"Columns: {len(fieldnames)}")
    print()
    print(f"File:")
    print(output_file)


if __name__ == "__main__":
    main()