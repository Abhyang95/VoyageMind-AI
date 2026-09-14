# ============================================================
# VOYAGEMIND AI — REFLECTION AGENT
# ============================================================

"""
Reflection Agent

Purpose:
    Analyze the output of the Validation Agent and decide
    whether the itinerary should be accepted or regenerated.

Important:
    This agent does NOT perform validation itself.

    Validation Agent:
        Finds problems.

    Reflection Agent:
        Interprets those problems and creates correction
        instructions for the next itinerary generation.
"""


# ============================================================
# CONFIGURATION
# ============================================================

MAX_REPLAN_ATTEMPTS = 1


# ============================================================
# REFLECTION AGENT
# ============================================================

def run_reflection_agent(
    validation_data,
    itinerary=None,
    attempt=0,
):
    """
    Analyze validation results and decide whether the
    itinerary should be accepted or replanned.

    The Reflection Agent also creates explicit correction
    instructions that can be passed back to Gemini.
    """

    print()
    print("🧠 Reflection Agent started...")

    # --------------------------------------------------------
    # SAFETY
    # --------------------------------------------------------

    if not isinstance(validation_data, dict):

        print(
            "⚠️ Reflection Agent received invalid "
            "validation data."
        )

        return {
            "success": False,
            "decision": "accept",
            "needs_replanning": False,
            "reason": (
                "Validation data was unavailable, "
                "so no automatic replan was attempted."
            ),
            "issues": [],
            "critical_issues": [],
            "warning_issues": [],
            "info_issues": [],
            "correction_instructions": [],
            "attempt": attempt,
        }

    # --------------------------------------------------------
    # GET VALIDATION SUMMARY
    # --------------------------------------------------------

    summary = validation_data.get(
        "summary",
        {},
    )

    if not isinstance(summary, dict):
        summary = {}

    errors = summary.get(
        "errors",
        0,
    )

    warnings = summary.get(
        "warnings",
        0,
    )

    failed_checks = summary.get(
        "failed_checks",
        0,
    )

    issues = validation_data.get(
        "issues",
        [],
    )

    if not isinstance(issues, list):
        issues = []

    # --------------------------------------------------------
    # CLASSIFY ISSUES
    # --------------------------------------------------------

    critical_issues = []
    warning_issues = []
    info_issues = []

    for issue in issues:

        if not isinstance(issue, dict):
            continue

        severity = str(
            issue.get(
                "severity",
                "",
            )
        ).lower()

        if severity == "error":

            critical_issues.append(issue)

        elif severity == "warning":

            warning_issues.append(issue)

        elif severity == "info":

            info_issues.append(issue)

    # --------------------------------------------------------
    # LOGGING
    # --------------------------------------------------------

    print()
    print("📊 Reflection Input")

    print(
        f"   Errors         → {errors}"
    )

    print(
        f"   Warnings       → {warnings}"
    )

    print(
        f"   Failed checks  → {failed_checks}"
    )

    print(
        f"   Total issues   → {len(issues)}"
    )

    # --------------------------------------------------------
    # VALIDATION PASSED
    # --------------------------------------------------------

    if validation_data.get("is_valid"):

        print()
        print(
            "✅ Reflection Agent:"
            " itinerary is valid."
        )

        return {
            "success": True,
            "decision": "accept",
            "needs_replanning": False,
            "reason": (
                "The Validation Agent found no "
                "critical itinerary issues."
            ),
            "issues": issues,
            "critical_issues": [],
            "warning_issues": warning_issues,
            "info_issues": info_issues,
            "correction_instructions": [],
            "attempt": attempt,
        }

    # --------------------------------------------------------
    # VALIDATION FAILED
    # --------------------------------------------------------

    print()
    print(
        "⚠️ Reflection Agent detected "
        "validation problems."
    )

    # --------------------------------------------------------
    # REPLAN LIMIT
    # --------------------------------------------------------

    if attempt >= MAX_REPLAN_ATTEMPTS:

        print()
        print(
            "🛑 Maximum replan attempts reached."
        )

        return {
            "success": True,
            "decision": "accept_with_warnings",
            "needs_replanning": False,
            "reason": (
                "Validation issues remain after the "
                "maximum allowed replanning attempt."
            ),
            "issues": issues,
            "critical_issues": critical_issues,
            "warning_issues": warning_issues,
            "info_issues": info_issues,
            "correction_instructions": [],
            "attempt": attempt,
        }

    # ========================================================
    # BUILD CORRECTION INSTRUCTIONS
    # ========================================================

    correction_instructions = []

    # --------------------------------------------------------
    # CRITICAL ISSUES
    # --------------------------------------------------------

    for issue in critical_issues:

        message = issue.get(
            "message"
        )

        check_name = issue.get(
            "check"
            or issue.get(
                "name"
            )
        )

        if message:

            if check_name:

                instruction = (
                    f"Fix the {check_name} validation issue: "
                    f"{message}"
                )

            else:

                instruction = (
                    f"Fix this critical itinerary issue: "
                    f"{message}"
                )

            correction_instructions.append(
                instruction
            )

    # --------------------------------------------------------
    # WARNING ISSUES
    # --------------------------------------------------------

    for issue in warning_issues:

        message = issue.get(
            "message"
        )

        check_name = issue.get(
            "check"
            or issue.get(
                "name"
            )
        )

        if message:

            if check_name:

                instruction = (
                    f"Improve the {check_name} issue: "
                    f"{message}"
                )

            else:

                instruction = (
                    f"Improve this itinerary issue: "
                    f"{message}"
                )

            correction_instructions.append(
                instruction
            )

    # --------------------------------------------------------
    # LIMIT FEEDBACK
    # --------------------------------------------------------

    correction_instructions = (
        correction_instructions[:10]
    )

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    if not correction_instructions:

        correction_instructions = [
            (
                "Regenerate the itinerary while "
                "strictly following all validation rules."
            )
        ]

    # ========================================================
    # BUILD HUMAN-READABLE REASON
    # ========================================================

    reasons = []

    for instruction in correction_instructions:

        reasons.append(
            str(instruction)
        )

    reason = (
        "The itinerary should be replanned because: "
        + " | ".join(reasons)
    )

    # ========================================================
    # LOG FEEDBACK
    # ========================================================

    print()
    print(
        "🔄 Reflection Agent decision: REPLAN"
    )

    print()
    print(
        "🛠️ Correction instructions:"
    )

    for index, instruction in enumerate(
        correction_instructions,
        start=1,
    ):

        print(
            f"   {index}. {instruction}"
        )

    # ========================================================
    # RETURN
    # ========================================================

    return {
        "success": True,
        "decision": "replan",
        "needs_replanning": True,
        "reason": reason,
        "issues": issues,
        "critical_issues": critical_issues,
        "warning_issues": warning_issues,
        "info_issues": info_issues,
        "correction_instructions": correction_instructions,
        "attempt": attempt,
    }