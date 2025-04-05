from enum import Enum
from typing import Dict, List

from pydantic import BaseModel, Field


# Define the request types
class RequestType(str, Enum):
    TAILOR_RESUME = "tailor_resume"
    DIRECT_EDIT = "direct_edit"


class Requirement(BaseModel):
    skill: str
    importance: str = Field(description="High, Medium, or Low importance")
    experience_level: str = Field(description="Required experience level")


class MatchedSkill(BaseModel):
    skill: str
    evidence: str
    section: str
    confidence: str = Field(description="high, medium, or low")
    relevance: str = Field(
        description="How directly the evidence relates to the requirement"
    )


class Gap(BaseModel):
    skill: str
    required_level: str
    importance: str
    resume_evidence: str = Field(description="Evidence from resume or 'None found'")
    section: str = Field(
        description="Which section contains this evidence or 'Missing'"
    )
    impact: str = Field(description="How this gap affects job fit")


class PrioritizedImprovement(BaseModel):
    skill: str
    impact: str = Field(
        description="high/medium/low - how important is this for the job"
    )
    addressability: str = Field(
        description="high/medium/low - can we reasonably tailor the resume to address this"
    )
    priority: int = Field(description="1-10 scale - overall priority to fix")
    approach: str = Field(description="how should we address this gap")
    rationale: str = Field(description="Why this improvement is important")


class TailoringSuggestion(BaseModel):
    skill: str
    section: str = Field(description="Resume section to modify")
    original_text: str = Field(description="Original text from resume, if any")
    new_text: str = Field(description="Suggested new text")
    explanation: str = Field(description="Why this change helps")
    confidence: str = Field(description="high, medium, or low")
    approved: bool = True


class CompanyContext(BaseModel):
    culture: str = Field(description="Company culture and values")
    industry: str = Field(description="Industry specifics")
    terminology: List[str] = Field(description="Key terminology/buzzwords")
    formality: str = Field(description="Level of formality expected")
    company_size: str = Field(description="Small, Medium, or Large")
    tech_stack: List[str] = Field(description="List of technologies used")


class ATSAnalysis(BaseModel):
    score: float = Field(description="ATS compatibility score (0-100)")
    keyword_density: Dict[str, float] = Field(
        description="Keyword frequency compared to job description"
    )
    job_title_matches: List[str] = Field(
        description="Industry-standard job titles found"
    )
    format_issues: List[str] = Field(
        description="Formatting issues that might confuse ATS"
    )
    improvements: List[str] = Field(
        description="Specific improvements to increase ATS compatibility"
    )


class FinalReview(BaseModel):
    adjustments: List[str] = Field(description="Final adjustments to make")
    strengths: List[str] = Field(
        description="Notes on strengths of the tailored resume"
    )
    confidence: str = Field(description="Confidence level that resume is well-tailored")
