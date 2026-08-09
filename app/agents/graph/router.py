from app.utils.config import get_llm
from pydantic import BaseModel, Field

class IntentClassification(BaseModel):
    intent: str = Field(description="The detected intent. One of: 'recruitment', 'resume', 'email', 'policy', 'general', 'onboarding'")

def detect_intent(query: str) -> str:
    prompt = f"""
Classify the user's HR query into exactly one of these intents:
- 'recruitment': User wants to evaluate a resume AND schedule an interview/send an email.
- 'resume': User wants to evaluate, screen, or analyze a resume.
- 'email': User wants to generate an HR email (e.g., offer, rejection, welcome).
- 'policy': User is asking ANY HR-related question (e.g., working hours, leave, dress code, probation, late coming, attendance, benefits, salary, work from home, office timings, etc.).
- 'onboarding': User wants to start onboarding for a candidate, mark an onboarding task as done or complete, or check onboarding status or checklist.
- 'general': Small talk, greetings, or queries completely unrelated to HR.

Query: "{query}"
"""
    try:
        structured_llm = get_llm().with_structured_output(IntentClassification)
        result = structured_llm.invoke(prompt)
        intent = result.intent.lower().strip()
        if intent in ["recruitment", "resume", "email", "policy", "general", "onboarding"]:
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

    if any(w in query_lower for w in ["leave", "policy", "benefits", "holiday", "hours", "timing", "probation", "dress", "late", "work from home", "attendance", "salary", "insurance", "medical", "notice", "schedule"]):
        return "policy"

    # Onboarding keyword fallback
    if any(phrase in query_lower for phrase in ["start onboarding", "onboarding status", "onboarding checklist"]) or \
       ("mark" in query_lower and any(w in query_lower for w in ["done", "complete"])):
        return "onboarding"

    return "general"