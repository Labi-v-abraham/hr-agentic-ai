from typing import Literal, List, Optional
from pydantic import BaseModel, Field


class ScorecardItem(BaseModel):
    criterion: str = Field(
        description=(
            "A specific evaluation category relevant to this role, "
            "e.g. 'Technical Skills', 'Experience Relevance', 'Communication'. "
            "Derive categories from the role's actual requirements, not a fixed generic list."
        )
    )
    score: int = Field(
        description="Score for this criterion, 0-100",
        ge=0,
        le=100
    )
    justification: str = Field(
        description="One sentence explaining this score, grounded in the resume and role requirements."
    )


class CandidateEvaluation(BaseModel):
    candidate_name: str = Field(
        default="Unknown Candidate",
        description=(
            "The candidate's full name as it appears in the resume text. "
            "Extract it from the resume header, contact section, or any clear name identifier. "
            "If no name can be found, use 'Unknown Candidate'."
        )
    )
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
    scorecard: List[ScorecardItem] = Field(
        default_factory=list,
        description=(
            "3-6 criteria breaking down the overall match_percentage. "
            "Criteria should be specific to this role's requirements, not generic."
        )
    )
    final_answer: str = Field(
        description=(
            "A single short sentence (max 25 words) for display as the main chat response. "
            "Example: 'The candidate is a strong match for the React Developer role with 78% alignment.'"
        )
    )