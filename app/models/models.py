from pydantic import BaseModel, Field


class CandidateEvaluation(BaseModel):
    candidate_summary: str = Field(description="Summary of the candidate")
    skills_match: str = Field(description="Analysis of skills match")
    ats_score: int = Field(description="Estimated ATS Score (0-100)")
    technical_skills: list[str] = Field(description="Identified technical skills")
    soft_skills: list[str] = Field(description="Identified soft skills")
    education_analysis: str = Field(description="Analysis of education")
    experience_analysis: str = Field(description="Analysis of work experience")
    project_analysis: str = Field(description="Analysis of projects")
    strengths: list[str] = Field(description="Key strengths")
    weaknesses: list[str] = Field(description="Key weaknesses or areas of concern")
    missing_skills: list[str] = Field(description="Skills required by JD but missing in resume")
    relevant_certifications: list[str] = Field(description="Relevant certifications")
    risk_factors: list[str] = Field(description="Potential risk factors")
    match_percentage: int = Field(description="Overall match percentage (0-100)")
    recommendation: str = Field(description="Hiring recommendation (e.g., Selected, Rejected, Keep on file)")
    technical_interview_questions: list[str] = Field(description="Technical interview questions to ask")
    hr_interview_questions: list[str] = Field(description="HR interview questions to ask")
    final_decision: str = Field(description="Final decision summary")
    confidence_score: int = Field(description="Confidence in this evaluation (0-100)")
    analysis: str = Field(description="Detailed explanation of the evaluation")