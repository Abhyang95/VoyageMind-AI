import os
import hashlib
from typing import Any, Dict, List

import chromadb


# ============================================================
# CHROMA CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

CHROMA_PATH = os.path.join(
    BASE_DIR,
    "chroma_db"
)


# Persistent ChromaDB client
client = chromadb.PersistentClient(
    path=CHROMA_PATH
)


# Collection for VoyageMind user memories
memory_collection = client.get_or_create_collection(
    name="voyagemind_user_memory"
)


# ============================================================
# SAVE MEMORY
# ============================================================

def save_memory(
    user_id: str,
    memory: str,
    memory_type: str = "preference",
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:

    if not memory or not memory.strip():
        return {
            "success": False,
            "error": "Memory cannot be empty.",
        }

    memory = memory.strip()

    metadata = metadata or {}

    memory_metadata = {
        "user_id": str(user_id),
        "memory_type": memory_type,
        **metadata,
    }

    # --------------------------------------------------------
    # Stable memory ID
    #
    # SHA-256 is used instead of Python's hash()
    # so the same memory gets the same ID across
    # application restarts.
    # --------------------------------------------------------

    memory_hash = hashlib.sha256(
        memory.encode("utf-8")
    ).hexdigest()[:24]

    memory_id = (
        f"{user_id}_{memory_hash}"
    )

    try:

        memory_collection.upsert(
            ids=[memory_id],
            documents=[memory],
            metadatas=[memory_metadata],
        )

        return {
            "success": True,
            "memory_id": memory_id,
            "memory": memory,
        }

    except Exception as error:

        return {
            "success": False,
            "error": str(error),
        }


# ============================================================
# SAVE TRIP PREFERENCES
# ============================================================
#
# Converts the explicit preferences from TripRequest into
# reusable long-term memories.
#
# IMPORTANT:
# - Budget is NOT stored because it is trip-specific.
# - Destination is NOT stored because it is trip-specific.
# - Current trip instructions remain higher priority.
# ============================================================

def save_trip_preferences(
    user_id: str,
    trip: Dict[str, Any],
) -> Dict[str, Any]:

    if not trip:
        return {
            "success": False,
            "saved_memories": [],
            "count": 0,
            "error": "Trip data cannot be empty.",
        }

    saved_memories: List[Dict[str, Any]] = []

    try:

        preferences = trip.get(
            "preferences",
            {}
        )

        if not isinstance(
            preferences,
            dict
        ):
            preferences = {}

        # ====================================================
        # RESTAURANT PREFERENCE
        # ====================================================

        restaurant_budget = preferences.get(
            "restaurant_budget"
        )

        if restaurant_budget:

            restaurant_memory = (
                f"I prefer {restaurant_budget} restaurants"
            )

            result = save_memory(
                user_id=user_id,
                memory=restaurant_memory,
                memory_type="restaurant_preference",
                metadata={
                    "source": "trip_request",
                },
            )

            if result.get("success"):
                saved_memories.append(result)

        # ====================================================
        # HOTEL PREFERENCE
        # ====================================================

        hotel_preference = preferences.get(
            "hotel_preference"
        )

        if hotel_preference:

            hotel_memory = (
                f"I prefer {hotel_preference} hotels"
            )

            result = save_memory(
                user_id=user_id,
                memory=hotel_memory,
                memory_type="hotel_preference",
                metadata={
                    "source": "trip_request",
                },
            )

            if result.get("success"):
                saved_memories.append(result)

        # ====================================================
        # WALKING PREFERENCE
        # ====================================================

        walking_preference = preferences.get(
            "walking_preference"
        )

        if walking_preference is True:

            walking_memory = (
                "I prefer walking instead of taxis"
            )

            result = save_memory(
                user_id=user_id,
                memory=walking_memory,
                memory_type="transport_preference",
                metadata={
                    "source": "trip_request",
                },
            )

            if result.get("success"):
                saved_memories.append(result)

        elif walking_preference is False:

            transport_memory = (
                "I prefer taxis instead of walking"
            )

            result = save_memory(
                user_id=user_id,
                memory=transport_memory,
                memory_type="transport_preference",
                metadata={
                    "source": "trip_request",
                },
            )

            if result.get("success"):
                saved_memories.append(result)

        # ====================================================
        # INTERESTS
        # ====================================================

        interests = trip.get(
            "interests",
            []
        )

        if isinstance(
            interests,
            list
        ):

            for interest in interests:

                if not interest:
                    continue

                interest_text = (
                    str(interest)
                    .strip()
                    .lower()
                )

                if not interest_text:
                    continue

                interest_memory = (
                    f"I enjoy {interest_text}"
                )

                result = save_memory(
                    user_id=user_id,
                    memory=interest_memory,
                    memory_type="interest",
                    metadata={
                        "source": "trip_request",
                    },
                )

                if result.get("success"):
                    saved_memories.append(result)

        return {
            "success": True,
            "saved_memories": saved_memories,
            "count": len(saved_memories),
        }

    except Exception as error:

        return {
            "success": False,
            "saved_memories": saved_memories,
            "count": len(saved_memories),
            "error": str(error),
        }


# ============================================================
# SEARCH MEMORIES
# ============================================================

def search_memories(
    user_id: str,
    query: str,
    n_results: int = 5,
) -> Dict[str, Any]:

    if not query or not query.strip():

        return {
            "success": False,
            "memories": [],
            "count": 0,
            "error": "Search query cannot be empty.",
        }

    try:

        # --------------------------------------------------------
        # Retrieve more results than requested.
        #
        # This gives us enough candidates to remove duplicates
        # while still returning up to n_results unique memories.
        # --------------------------------------------------------

        search_limit = max(
            n_results * 2,
            n_results,
        )

        results = memory_collection.query(
            query_texts=[query],
            n_results=search_limit,
            where={
                "user_id": str(user_id)
            },
        )

        documents = (
            results.get(
                "documents",
                [[]]
            )[0]
        )

        metadatas = (
            results.get(
                "metadatas",
                [[]]
            )[0]
        )

        distances = (
            results.get(
                "distances",
                [[]]
            )[0]
        )

        memories = []

        # --------------------------------------------------------
        # DUPLICATE MEMORY TRACKING
        # --------------------------------------------------------

        seen_memories = set()

        # --------------------------------------------------------
        # BUILD UNIQUE MEMORY RESULTS
        # --------------------------------------------------------

        for index, document in enumerate(
            documents
        ):

            if not document:
                continue

            memory_text = str(
                document
            ).strip()

            if not memory_text:
                continue

            # Case-insensitive duplicate detection.
            #
            # Example:
            # "I prefer Moderate restaurants"
            # "i prefer moderate restaurants"
            #
            # These will be treated as the same memory.
            # ----------------------------------------------------

            memory_key = memory_text.lower()

            if memory_key in seen_memories:
                continue

            seen_memories.add(
                memory_key
            )

            memories.append(
                {
                    "memory": memory_text,

                    "metadata": (
                        metadatas[index]
                        if index < len(metadatas)
                        else {}
                    ),

                    "distance": (
                        distances[index]
                        if index < len(distances)
                        else None
                    ),
                }
            )

            # ----------------------------------------------------
            # Stop once we have enough UNIQUE memories.
            # ----------------------------------------------------

            if len(memories) >= n_results:
                break

        # --------------------------------------------------------
        # RETURN CLEAN RESULTS
        # --------------------------------------------------------

        return {
            "success": True,
            "memories": memories,
            "count": len(memories),
        }

    except Exception as error:

        return {
            "success": False,
            "memories": [],
            "count": 0,
            "error": str(error),
        }


# ============================================================
# GET USER MEMORIES
# ============================================================

def get_user_memories(
    user_id: str,
) -> Dict[str, Any]:

    try:

        results = memory_collection.get(
            where={
                "user_id": str(user_id)
            }
        )

        documents = (
            results.get(
                "documents",
                []
            )
        )

        metadatas = (
            results.get(
                "metadatas",
                []
            )
        )

        memories = []

        for index, document in enumerate(
            documents
        ):

            memories.append(
                {
                    "memory": document,

                    "metadata": (
                        metadatas[index]
                        if index < len(metadatas)
                        else {}
                    ),
                }
            )

        return {
            "success": True,
            "memories": memories,
            "count": len(memories),
        }

    except Exception as error:

        return {
            "success": False,
            "memories": [],
            "count": 0,
            "error": str(error),
        }


# ============================================================
# DELETE USER MEMORIES
# ============================================================

def delete_user_memories(
    user_id: str,
) -> Dict[str, Any]:

    try:

        existing = memory_collection.get(
            where={
                "user_id": str(user_id)
            }
        )

        ids = existing.get(
            "ids",
            []
        )

        if ids:

            memory_collection.delete(
                ids=ids
            )

        return {
            "success": True,
            "deleted": len(ids),
        }

    except Exception as error:

        return {
            "success": False,
            "deleted": 0,
            "error": str(error),
        }