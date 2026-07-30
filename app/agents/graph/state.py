from typing import TypedDict


class AgentState(TypedDict):
    query: str

    resume_text: str

    intent: str

    next_node: str

    match_percentage: int

    recommendation: str

    analysis: str

    email: str

    policy: str

    final_answer: str

    execution_log: list[str]

    