import requests


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


WEATHER_CODES = {
    0: "Clear Sky",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Heavy Drizzle",
    61: "Slight Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    71: "Light Snow",
    73: "Moderate Snow",
    75: "Heavy Snow",
    80: "Rain Showers",
    81: "Moderate Rain Showers",
    82: "Heavy Rain Showers",
    95: "Thunderstorm",
}


def get_weather(
    latitude: float,
    longitude: float,
):

    try:

        params = {
            "latitude": latitude,
            "longitude": longitude,

            "current": (
                "temperature_2m,"
                "apparent_temperature,"
                "precipitation,"
                "weather_code,"
                "wind_speed_10m"
            ),
        }

        response = requests.get(
            OPEN_METEO_URL,
            params=params,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        current = data.get(
            "current",
            {}
        )

        weather_code = current.get(
            "weather_code"
        )

        return {

            "success": True,

            "temperature":
                current.get(
                    "temperature_2m"
                ),

            "apparent_temperature":
                current.get(
                    "apparent_temperature"
                ),

            "precipitation":
                current.get(
                    "precipitation"
                ),

            "weather_code":
                weather_code,

            "condition":
                WEATHER_CODES.get(
                    weather_code,
                    "Unknown",
                ),

            "wind_speed":
                current.get(
                    "wind_speed_10m"
                ),

            "units": {
                "temperature": "°C",
                "wind_speed": "km/h",
                "precipitation": "mm",
            },
        }

    except requests.RequestException as error:

        return {

            "success": False,

            "error": str(error),

        }