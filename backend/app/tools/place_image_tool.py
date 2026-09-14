import time
import requests
from urllib.parse import quote


# ==========================================
# WIKIMEDIA COMMONS API
# ==========================================

WIKIMEDIA_API_URL = (
    "https://commons.wikimedia.org/w/api.php"
)


HEADERS = {
    "User-Agent":
        "VoyageMind-AI/1.0 Travel Intelligence Platform",
    "Accept":
        "application/json",
}


# ==========================================
# CACHE
# ==========================================

IMAGE_CACHE = {}

IMAGE_CACHE_DURATION = 86400  # 24 hours


# ==========================================
# CATEGORY FALLBACK IMAGES
# ==========================================

CATEGORY_FALLBACK_IMAGES = {

    "Architecture":
        "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=900&q=85",

    "History":
        "https://images.unsplash.com/photo-1503919005314-30d93d07d823?auto=format&fit=crop&w=900&q=85",

    "Food":
        "https://images.unsplash.com/photo-1515003197210-e0cd71810b5f?auto=format&fit=crop&w=900&q=85",

    "Nightlife":
        "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=900&q=85",

    "Museums":
        "https://images.unsplash.com/photo-1564399579883-451a5d44ec08?auto=format&fit=crop&w=900&q=85",

    "Nature":
        "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=900&q=85",

    "Shopping":
        "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=900&q=85",

    "Adventure":
        "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=900&q=85",

}


DEFAULT_FALLBACK_IMAGE = (
    "https://images.unsplash.com/"
    "photo-1488646953014-85cb44e25828"
    "?auto=format&fit=crop&w=900&q=85"
)


# ==========================================
# NORMALIZE
# ==========================================

def normalize_text(value):

    if not value:
        return ""

    return (
        str(value)
        .strip()
    )


# ==========================================
# IMAGE SEARCH
# ==========================================

def search_wikimedia_image(
    place_name,
    destination_name=None,
    category=None,
):

    place_name = normalize_text(place_name)
    destination_name = normalize_text(destination_name)

    if not place_name:
        return None


    # ======================================
    # CACHE KEY
    # ======================================

    cache_key = (
        place_name.lower(),
        destination_name.lower(),
        str(category or "").lower(),
    )


    now = time.time()


    cached = IMAGE_CACHE.get(cache_key)


    if cached:

        if (
            now - cached["timestamp"]
            < IMAGE_CACHE_DURATION
        ):

            return cached["image_url"]


    # ======================================
    # SEARCH QUERIES
    # ======================================

    queries = []


    # Exact place first.
    queries.append(
        f'"{place_name}"'
    )


    # Place + destination.
    if destination_name:

        queries.append(
            f'"{place_name}" "{destination_name}"'
        )


    # Place + category.
    if category:

        queries.append(
            f'"{place_name}" {category}'
        )


    # Place + destination + category.
    if destination_name and category:

        queries.append(
            f'"{place_name}" "{destination_name}" {category}'
        )


    # ======================================
    # TRY SEARCHES
    # ======================================

    for search_query in queries:

        try:

            params = {

                "action":
                    "query",

                "generator":
                    "search",

                "gsrsearch":
                    search_query,

                "gsrnamespace":
                    6,

                "gsrlimit":
                    5,

                "prop":
                    "imageinfo",

                "iiprop":
                    "url",

                "iiurlwidth":
                    1200,

                "format":
                    "json",

                "origin":
                    "*",

            }


            response = requests.get(

                WIKIMEDIA_API_URL,

                params=params,

                headers=HEADERS,

                timeout=8,

            )


            response.raise_for_status()


            data = response.json()


            pages = (

                data
                .get("query", {})
                .get("pages", {})
            )


            if not pages:

                continue


            # ==================================
            # FIND BEST IMAGE
            # ==================================

            best_image = None


            for page in pages.values():

                image_info = (
                    page
                    .get("imageinfo", [])
                )


                if not image_info:

                    continue


                image_data = image_info[0]


                image_url = (

                    image_data.get(
                        "thumburl"
                    )

                    or

                    image_data.get(
                        "url"
                    )

                )


                if not image_url:

                    continue


                title = (
                    page.get("title", "")
                    .lower()
                )


                place_words = [

                    word.lower()

                    for word
                    in place_name.split()

                    if len(word) > 2

                ]


                # ==================================
                # SIMPLE RELEVANCE CHECK
                # ==================================

                relevance_score = 0


                for word in place_words:

                    if word in title:

                        relevance_score += 1


                if (
                    place_name.lower()
                    in title
                ):

                    relevance_score += 10


                candidate = {

                    "url":
                        image_url,

                    "score":
                        relevance_score,

                }


                if (
                    best_image is None
                    or candidate["score"]
                    > best_image["score"]
                ):

                    best_image = candidate


            if best_image:

                image_url = best_image["url"]


                IMAGE_CACHE[
                    cache_key
                ] = {

                    "timestamp":
                        now,

                    "image_url":
                        image_url,

                }


                print(
                    f"🖼️ Image found for "
                    f"{place_name}"
                )


                return image_url


        except Exception as error:

            print(
                f"⚠️ Image search failed "
                f"for {place_name}: "
                f"{error}"
            )


    # ======================================
    # FALLBACK
    # ======================================

    fallback = (
        CATEGORY_FALLBACK_IMAGES.get(
            category,
            DEFAULT_FALLBACK_IMAGE,
        )
    )


    IMAGE_CACHE[
        cache_key
    ] = {

        "timestamp":
            now,

        "image_url":
            fallback,

    }


    print(
        f"🖼️ Using fallback image for "
        f"{place_name}"
    )


    return fallback


# ==========================================
# ENRICH ONE PLACE
# ==========================================

def enrich_place_image(
    place,
    destination_name=None,
):

    if not place:

        return place


    # Do not overwrite an existing
    # verified image.

    existing_image = (

        place.get("image_url")

        or place.get("image")

        or place.get("photo")

    )


    if existing_image:

        place["image_url"] = existing_image

        return place


    image_url = search_wikimedia_image(

        place_name=place.get(
            "name"
        ),

        destination_name=destination_name,

        category=place.get(
            "interest_category"
        ),

    )


    if image_url:

        place["image_url"] = image_url


    return place


# ==========================================
# ENRICH ALL PLACES
# ==========================================

def enrich_places_with_images(
    places,
    destination_name=None,
):

    if not places:

        return []


    enriched_places = []


    for index, place in enumerate(places):

        try:

            enriched = enrich_place_image(

                place=place,

                destination_name=
                    destination_name,

            )


            enriched_places.append(
                enriched
            )


        except Exception as error:

            print(
                f"⚠️ Could not enrich "
                f"place #{index + 1}: "
                f"{error}"
            )


            enriched_places.append(
                place
            )


    return enriched_places