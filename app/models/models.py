from typing import Literal, List, Optional
from pydantic import BaseModel, Field


class CandidateEvaluation(BaseModel):
    match_percentage: int = Field(
        description="Overall match percentage between resume and role requirements (0-100)."
    )
    recommendation: Literal["Selected", "Rejected", "Hold"] = Field(
        description="Hiring decision. Must be exactly one of: Selected, Rejected, Hold."
    )
    analysis: str = Field(
        description=(
            "A SHORT 2-4 sentence executive summary of the candidate's suitability. "
            "Do NOT include interview questions, coaching advice, or candidate-facing commentary here. "
            "Focus only on key fit factors and major gaps."
        )
    )
    suggested_questions: Optional[List[str]] = Field(
        default=None,
        description=(
            "Up to 5 interview questions to ask this specific candidate. "
            "Only populate if the evaluation reveals specific angles worth probing. "
            "Never duplicate content from 'analysis'."
        )
    )
    final_answer: str = Field(
        description=(
            "A single short sentence (max 25 words) for display as the main chat response. "
            "Example: 'The candidate is a strong match for the React Developer role with 78% alignment.'"
        )
    )