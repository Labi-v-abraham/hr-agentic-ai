def detect_intent(query: str) -> str:

    query = query.lower()

    if (
        "resume" in query
        and (
            "interview" in query
            or "email" in query
            or "invite" in query
        )
    ):
        return "recruitment"

    if "resume" in query:
        return "resume"

    if any(
        word in query
        for word in [
            "email",
            "offer",
            "welcome",
            "rejection",
        ]
    ):
        return "email"

    if any(
        word in query
        for word in [
            "leave",
            "policy",
            "benefits",
            "holiday",
        ]
    ):
        return "policy"

    return "general"