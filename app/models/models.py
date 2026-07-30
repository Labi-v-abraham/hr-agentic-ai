from pydantic import BaseModel, Field


class CandidateEvaluation(BaseModel):
    match_percentage: int = Field(
        description="Percentage match between the resume and the job description."
    )

    recommendation: str = Field(
        description="Selection decision. Example: Selected or Rejected."
    )

    analysis: str = Field(
        description="Detailed explanation of the evaluation."
    )