from app.utils.config import get_llm
from pydantic import BaseModel, Field
from app.prompts.loader import render_prompt

class IntentClassification(BaseModel):
    intent: str = Field(description="The detected intent. One of: 'recruitment', 'resume', 'email', 'policy', 'general', 'onboarding', 'leave'")

def detect_intent(query: str) -> str:
    prompt = render_prompt("intent_classification.j2", query=query)

    try:
        structured_llm = get_llm().with_structured_output(IntentClassification)
        result = structured_llm.invoke(prompt)
        intent = result.intent.lower().strip()
        if intent in ["recruitment", "resume", "email", "policy", "general", "onboarding", "leave"]:
            return intent
    except Exception:
        pass

    # Fallback keyword logic
    query_lower = query.lower()

    if "resume" in query_lower and any(w in query_lower for w in ["interview", "email", "invite"]):
        return "recruitment"

    if "resume" in query_lower:
        return "resume"

    if any(w in query_lower for w in ["email", "offer", "welcome", "rejection"]):
        return "email"

    # Leave-specific fallback (checked before generic policy fallback)
    if any(phrase in query_lower for phrase in ["apply for leave", "request time off", "request leave", "leave status", "my leave", "pending leave", "approve leave", "reject leave"]):
        return "leave"

    if any(w in query_lower for w in ["leave", "policy", "benefits", "holiday", "hours", "timing", "probation", "dress", "late", "work from home", "attendance", "salary", "insurance", "medical", "notice", "schedule"]):
        return "policy"

    # Onboarding keyword fallback
    if any(phrase in query_lower for phrase in ["start onboarding", "onboarding status", "onboarding checklist"]) or \
       ("mark" in query_lower and any(w in query_lower for w in ["done", "complete"])):
        return "onboarding"

    return "general"