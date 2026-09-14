from typing import Any, Dict, List, Optional

from app.services.gemini_service import generate_memory_extraction
from app.services.memory_service import save_memory


# ============================================================
# MEMORY AGENT
# ============================================================

def run_memory_agent(
    user_id: str,
    text: str,
    source: str = "conversation",
) -> Dict[str, Any]:

    print()
    print("=" * 60)
    print("🧠 MEMORY AGENT")
    print("=" * 60)

    if not text or not text.strip():

        print("⚠️ No text provided for memory extraction.")

        return {
            "success": False,
            "saved": [],
            "count": 0,
            "error": "Text cannot be empty.",
        }

    try:

        # ====================================================
        # EXTRACT MEMORIES USING GEMINI
        # ====================================================

        extraction_result = generate_memory_extraction(
            text=text
        )

        if not extraction_result.get("success"):

            print("⚠️ Memory extraction failed.")

            return {
                "success": False,
                "saved": [],
                "count": 0,
                "error": extraction_result.get(
                    "error",
                    "Memory extraction failed.",
                ),
            }

        memories = extraction_result.get(
            "memories",
            []
        )

        if not isinstance(memories, list):

            memories = []

        if not memories:

            print("ℹ️ No useful long-term preferences detected.")

            return {
                "success": True,
                "saved": [],
                "count": 0,
            }

        print(
            f"🧠 Extracted {len(memories)} "
            f"potential memories."
        )

        # ====================================================
        # SAVE MEMORIES
        # ====================================================

        saved_memories: List[Dict[str, Any]] = []

        for memory_item in memories:

            if isinstance(memory_item, str):

                memory_text = memory_item
                memory_type = "preference"

            elif isinstance(memory_item, dict):

                memory_text = memory_item.get(
                    "memory",
                    ""
                )

                memory_type = memory_item.get(
                    "memory_type",
                    "preference"
                )

            else:

                continue

            if not memory_text:
                continue

            memory_text = memory_text.strip()

            if not memory_text:
                continue

            save_result = save_memory(
                user_id=user_id,
                memory=memory_text,
                memory_type=memory_type,
                metadata={
                    "source": source,
                },
            )

            if save_result.get("success"):

                saved_memories.append(
                    save_result
                )

                print(
                    f"   ✅ Saved: {memory_text}"
                )

            else:

                print(
                    f"   ❌ Failed: {memory_text}"
                )

        print()
        print(
            f"🧠 Memories saved → "
            f"{len(saved_memories)}"
        )

        return {
            "success": True,
            "saved": saved_memories,
            "count": len(saved_memories),
        }

    except Exception as error:

        print(
            "❌ Unexpected Memory Agent error:"
        )

        print(str(error))

        return {
            "success": False,
            "saved": [],
            "count": 0,
            "error": str(error),
        }