import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

def get_destination_coordinates(destination: str):
    try:
        params = {
            "q": destination,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
        }
        headers = {
            "User-Agent": "VoyageMind-AI/1.0",
            "Accept-Language": "en",
        }

        response = requests.get(
            NOMINATIM_URL,
            params=params,
            headers=headers,
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()

        if not data:
            return {
                "success": False,
                "error": f"Destination '{destination}' not found.",
            }

        location = data[0]
        address = location.get("address", {})

        clean_name = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("municipality")
            or address.get("state")
            or location.get("name")
            or destination
        )

        return {
            "success": True,
            "name": clean_name,
            "display_name": location.get("display_name"),
            "country": address.get("country"),
            "country_code": address.get("country_code"),
            "latitude": float(location["lat"]),
            "longitude": float(location["lon"]),
        }

    except requests.RequestException as error:
        return {
            "success": False,
            "error": str(error),
        }
