from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    query: str
    resume_text: str
    intent: str
    next_node: str
    current_role: Optional[str]
    active_kbs: list[str]
    evaluation_data: dict
    match_percentage: int
    recommendation: str
    analysis: str
    suggested_questions: List[str]
    email: str
    policy: str
    final_answer: str
    execution_log: list[str]
    # Onboarding Checklist Tracker fields (additive only)
    onboarding_result: Optional[str]
    candidate_id: Optional[str]
    # RAG citation / confidence fields (additive only)
    source_files: Optional[list]
    confidence_badge: Optional[str]
    knowledge_gap: Optional[bool]
    # Leave request fields (additive only)
    leave_result: Optional[str]
    request_analysis: Optional[dict]