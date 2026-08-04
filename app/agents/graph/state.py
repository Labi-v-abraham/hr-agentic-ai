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