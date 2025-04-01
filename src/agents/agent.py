from typing import Dict, List

from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph
from pydantic import BaseModel, Field

llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")


# Define schemas for structured output
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


# Define state structure
class AgentState(BaseModel):
    job_description: str
    resume: str
    company_context: CompanyContext = None
    requirements: List[Requirement] = []
    matches: List[MatchedSkill] = []
    gaps: List[Gap] = []
    prioritized_improvements: List[PrioritizedImprovement] = []
    tailoring_suggestions: List[TailoringSuggestion] = []
    verification_queue: List[Dict] = []
    human_feedback: Dict = {}
    tailored_resume: str = ""
    ats_score: float = 0.0
    final_notes: List[str] = []
    output: str = ""


def extract_requirements(state: AgentState) -> AgentState:
    """Extract key requirements and company context"""
    # Get job requirements
    requirements_llm = llm.with_structured_output(List[Requirement])

    requirements = requirements_llm.invoke(f"""
    Extract key requirements from this job description:
    {state["job_description"]}
    
    For each requirement, identify:
    1. The specific skill or qualification
    2. Its importance level (High, Medium, Low)
    3. The experience level required
    """)

    state["requirements"] = [req.model_dump() for req in requirements]

    # Get company context
    context_llm = llm.with_structured_output(CompanyContext)
    company_context = context_llm.invoke(f"""
    Analyze this job description and identify:
    1. Company culture and values
    2. Industry specifics
    3. Key terminology/buzzwords
    4. Level of formality expected
    
    Job description:
    {state["job_description"]}
    """)

    state["company_context"] = company_context.model_dump()
    return state


def analyze_resume(state: AgentState) -> AgentState:
    """Analyze resume for matches and gaps against requirements"""
    matches = []
    gaps = []

    # Create structured output LLMs
    match_llm = llm.with_structured_output(MatchedSkill)
    gap_llm = llm.with_structured_output(Gap)

    for req in state["requirements"]:
        # First check if this is a match
        prompt = f"""
        Does this resume demonstrate {req["skill"]} at {req["experience_level"]} level?
        
        Resume:
        {state["resume"]}
        
        If this skill IS demonstrated in the resume, respond with details about the match.
        If this skill is NOT demonstrated adequately, respond with "NO_MATCH".
        """

        try:
            response = match_llm.invoke(prompt)
            if response != "NO_MATCH":
                # We have a match
                matches.append(response.model_dump())
            else:
                # We have a gap
                gap_prompt = f"""
                The resume does not adequately demonstrate {req["skill"]} at {req["experience_level"]} level.
                
                Resume:
                {state["resume"]}
                
                Analyze what evidence (if any) exists in the resume related to this skill,
                and which section it appears in.
                """
                gap = gap_llm.invoke(gap_prompt)
                gaps.append(
                    {
                        **gap.model_dump(),
                        "skill": req["skill"],
                        "required_level": req["experience_level"],
                        "importance": req["importance"],
                    }
                )
        except Exception as e:
            print(f"Error analyzing requirement {req['skill']}: {e}")
            continue

    state["matches"] = matches
    state["gaps"] = gaps
    return state


def prioritize_improvements(state: AgentState) -> AgentState:
    """Prioritize which improvements will have the biggest impact"""
    # Sort gaps by importance and ability to address
    prioritize_llm = llm.with_structured_output(List[PrioritizedImprovement])

    prioritized = prioritize_llm.invoke(f"""
    Analyze these skill gaps and prioritize which ones should be addressed in the resume:
    
    Gaps: {state["gaps"]}
    Current resume: {state["resume"]}
    
    For each gap, determine:
    1. Impact (high/medium/low) - how important is this for the job?
    2. Addressability (high/medium/low) - can we reasonably tailor the resume to address this?
    3. Priority (1-10 scale) - overall priority to fix
    4. Approach - how should we address this gap?
    """)

    state["prioritized_improvements"] = [p.model_dump() for p in prioritized]
    return state


def generate_suggestions(state: AgentState) -> AgentState:
    """Generate specific tailoring suggestions for the resume"""
    suggestion_llm = llm.with_structured_output(List[TailoringSuggestion])

    suggestions = suggestion_llm.invoke(f"""
    Create specific suggestions to improve this resume based on the identified gaps:
    
    Resume:
    {state["resume"]}
    
    Gaps:
    {state["gaps"]}
    
    Job requirements:
    {state["requirements"]}
    
    For each suggestion, provide:
    1. The skill being addressed
    2. Exact section to modify
    3. Original text (if any)
    4. Suggested new text
    5. Explanation of why this change helps
    6. Confidence in suggestion (high/medium/low)
    """)

    state["tailoring_suggestions"] = [
        suggestion.model_dump() for suggestion in suggestions
    ]

    # Determine which need human verification
    verification_queue = []
    for i, suggestion in enumerate(state["tailoring_suggestions"]):
        if suggestion["confidence"] != "high":
            verification_queue.append(
                {
                    "question_id": i,
                    "skill": suggestion.get("skill", "Unknown"),
                    "suggestion_index": i,
                    "question": f"Should we make this change to the resume?\n\nOriginal: {suggestion['original_text']}\n\nSuggested: {suggestion['new_text']}\n\nRationale: {suggestion['explanation']}",
                    "options": ["Yes", "No", "Yes with modifications"],
                    "context": {
                        "section": suggestion["section"],
                        "confidence": suggestion["confidence"],
                    },
                }
            )

    state["verification_queue"] = verification_queue
    return state


def request_human_verification(state: AgentState) -> AgentState:
    """Prepare requests for human verification"""
    if not state["verification_queue"]:
        return state

    requests = []
    for item in state["verification_queue"]:
        requests.append(
            {
                "question": f"Should we make this change to the resume?\n\nOriginal: {item['suggestion']['original_text']}\n\nSuggested: {item['suggestion']['new_text']}\n\nRationale: {item['suggestion']['explanation']}",
                "options": ["Yes", "No", "Yes with modifications"],
                "context": {
                    "skill": item["skill"],
                    "section": item["suggestion"]["section"],
                    "confidence": item["suggestion"]["confidence"],
                },
            }
        )

    state["human_feedback"] = {"pending_requests": requests}
    return state


def process_human_feedback(state: AgentState) -> AgentState:
    """Integrate human verification responses"""
    if not state["human_feedback"].get("responses"):
        return state

    # Update suggestions based on feedback
    for i, response in enumerate(state["human_feedback"]["responses"]):
        if response["answer"] == "Yes":
            # Keep suggestion as is
            pass
        elif response["answer"] == "No":
            # Remove this suggestion
            state["tailoring_suggestions"][i]["approved"] = False
        elif response["answer"] == "Yes with modifications":
            # Update suggestion with human modifications
            state["tailoring_suggestions"][i]["new_text"] = response.get(
                "modified_text", state["tailoring_suggestions"][i]["new_text"]
            )
            state["tailoring_suggestions"][i]["approved"] = True

    return state


def implement_changes(state: AgentState) -> AgentState:
    """Implement approved changes to create tailored resume"""
    current_resume = state["resume"]

    # Group changes by section for more coherent implementation
    changes_by_section = {}
    for suggestion in state["tailoring_suggestions"]:
        if suggestion.get("approved", True):  # Default to True if not specified
            section = suggestion["section"]
            if section not in changes_by_section:
                changes_by_section[section] = []
            changes_by_section[section].append(suggestion)

    # Apply the changes
    updated_resume = llm.invoke(f"""
    Update this resume with the following changes:
    
    Current resume:
    {current_resume}
    
    Changes to make by section:
    {changes_by_section}
    
    Requirements from job:
    {state["requirements"]}
    
    Company context:
    {state["company_context"]}
    
    Return the complete updated resume in the same format as the original.
    """)

    state["tailored_resume"] = updated_resume
    return state


def ats_optimization(state: AgentState) -> AgentState:
    """Optimize resume for ATS systems"""
    ats_llm = llm.with_structured_output(ATSAnalysis)

    ats_analysis = ats_llm.invoke(f"""
    Analyze this resume for ATS optimization:
    {state["tailored_resume"]}
    
    Job description:
    {state["job_description"]}
    
    Check for:
    1. Keyword density compared to job description
    2. Use of industry-standard job titles
    3. Proper formatting that won't confuse ATS systems
    4. Appropriate use of bullet points and sections
    """)

    state["ats_score"] = ats_analysis.score

    # Apply ATS optimizations if score is low
    if ats_analysis.score < 80:
        optimized = llm.invoke(f"""
        Update this resume to improve ATS compatibility by addressing these issues:
        
        Current resume:
        {state["tailored_resume"]}
        
        Improvements needed:
        {ats_analysis.improvements}
        
        Return the complete updated resume with better ATS optimization.
        """)
        state["tailored_resume"] = optimized

    return state


def final_review(state: AgentState) -> AgentState:
    """Final review and polish of the resume"""
    review_llm = llm.with_structured_output(FinalReview)

    final_review = review_llm.invoke(f"""
    Perform a final review of this tailored resume:
    {state["tailored_resume"]}
    
    Job description:
    {state["job_description"]}
    
    Check for:
    1. Overall coherence and flow
    2. Appropriate highlighting of key qualifications
    3. Consistency in formatting and style
    4. Grammar and spelling
    5. Appropriate length and detail level
    """)

    # Make final adjustments if needed
    if final_review.adjustments:
        polished = llm.invoke(f"""
        Make these final adjustments to the resume:
        
        Current resume:
        {state["tailored_resume"]}
        
        Adjustments:
        {final_review.adjustments}
        
        Return the complete finalized resume.
        """)
        state["tailored_resume"] = polished

    state["final_notes"] = final_review.strengths
    return state


def generate_report(state: AgentState) -> AgentState:
    """Generate final tailored resume with summary"""
    summary = f"""
    # Resume Tailoring Summary
    
    ## Job Fit Analysis
    - Matched Skills: {len(state["matches"])}
    - Addressed Gaps: {len([g for g in state["gaps"] if g["skill"] in [s["skill"] for s in state["tailoring_suggestions"]]])}
    - ATS Compatibility Score: {state["ats_score"]}/100
    
    ## Key Improvements Made
    """

    for suggestion in state["tailoring_suggestions"]:
        if suggestion.get("approved", True):
            summary += f"- {suggestion['section']}: {suggestion['explanation']}\n"

    summary += "\n## Resume Strengths\n"
    for note in state["final_notes"]:
        summary += f"- {note}\n"

    summary += f"\n## Tailored Resume\n\n{state['tailored_resume']}"

    state["output"] = summary
    return state


def should_verify(state: AgentState) -> str:
    """Conditional edge to determine if human verification is needed"""
    if state["verification_queue"]:
        return "needs_verification"
    return "no_verification_needed"


# Build the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("extract_requirements", extract_requirements)
workflow.add_node("analyze_resume", analyze_resume)
workflow.add_node("prioritize_improvements", prioritize_improvements)
workflow.add_node("generate_suggestions", generate_suggestions)
workflow.add_node("request_verification", request_human_verification)
workflow.add_node("process_feedback", process_human_feedback)
workflow.add_node("implement_changes", implement_changes)
workflow.add_node("ats_optimization", ats_optimization)
workflow.add_node("final_review", final_review)
workflow.add_node("generate_report", generate_report)

# Add edges
workflow.add_edge("extract_requirements", "analyze_resume")
workflow.add_edge("analyze_resume", "prioritize_improvements")
workflow.add_edge("prioritize_improvements", "generate_suggestions")
workflow.add_edge("generate_suggestions", "request_verification")

# Add conditional edges
workflow.add_conditional_edges(
    "request_verification",
    should_verify,
    {
        "needs_verification": "process_feedback",
        "no_verification_needed": "implement_changes",
    },
)

workflow.add_edge("process_feedback", "implement_changes")
workflow.add_edge("implement_changes", "ats_optimization")
workflow.add_edge("ats_optimization", "final_review")
workflow.add_edge("final_review", "generate_report")

# Set entry point
workflow.set_entry_point("extract_requirements")

# Compile
app = workflow.compile()
