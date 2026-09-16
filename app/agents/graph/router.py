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
    except Exception as e:
        print(f"[Router] LLM intent classification failed: {e}. Falling back to keyword matching.")

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
    onboarding_start_phrases = ["start onboarding", "onboarding status", "onboarding checklist"]
    onboarding_complete_verbs = ["mark", "approve", "complete", "finish", "check off"]
    onboarding_complete_states = ["done", "complete", "completed", "finished"]
    onboarding_task_hints = ["equipment setup", "hr paperwork", "welcome meeting", "role-specific training", "team introduction", "it equipment"]

    cond1 = any(phrase in query_lower for phrase in onboarding_start_phrases)
    cond2 = any(verb in query_lower for verb in onboarding_complete_verbs) and \
            (any(state in query_lower for state in onboarding_complete_states) or "onboarding" in query_lower)
    cond3 = any(verb in query_lower for verb in onboarding_complete_verbs) and \
            any(hint in query_lower for hint in onboarding_task_hints)

    if cond1 or cond2 or cond3:
        return "onboarding"

    return "general"