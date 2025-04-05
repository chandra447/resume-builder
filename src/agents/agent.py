from typing import Dict, List, Optional

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from pydantic import BaseModel, Field

from src.agents.models.states import (
    ATSAnalysis,
    CompanyContext,
    FinalReview,
    Gap,
    MatchedSkill,
    PrioritizedImprovement,
    RequestType,
    Requirement,
    TailoringSuggestion,
)
from src.config.settings import settings
from src.utils.logger_config import setup_logger

logger = setup_logger(__name__)


class AgentState(BaseModel):
    job_description: str = ""
    resume: str
    request_type: RequestType = RequestType.TAILOR_RESUME
    user_edit_request: str = ""  # Store the specific edit request
    edit_section: str = ""  # Section to edit
    edit_content: str = ""  # Content to add/modify
    edit_completed: bool = False
    company_context: CompanyContext = None
    requirements: List[Requirement] = []
    matches: List[MatchedSkill] = []
    gaps: List[Gap] = []
    prioritized_improvements: List[PrioritizedImprovement] = []
    tailoring_suggestions: List[TailoringSuggestion] = []
    current_gap_index: int = 0  # Track which gap we're currently processing
    current_suggestion: Optional[Dict] = None  # Current suggestion being reviewed
    human_feedback: Dict = {}
    tailored_resume: str = ""
    ats_score: float = 0.0
    final_notes: List[str] = []
    output: str = ""
    # Human-in-the-loop fields
    waiting_for_human: bool = False  # Whether we're waiting for human input
    human_question: str = ""  # Question to ask the human
    step_name: str = ""  # Current step in the workflow


class ResumeTailoringAgent:
    def __init__(self):
        # Use environment variables for API key (no hardcoded keys)
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,  # Set temperature for deterministic outputs
            api_key=settings.openai_api_key,
        )
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build and return the workflow graph"""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("detect_intent", self.detect_intent)
        workflow.add_node("process_direct_edit", self.process_direct_edit)
        workflow.add_node("extract_requirements", self.extract_requirements)
        workflow.add_node("analyze_resume", self.analyze_resume)
        workflow.add_node("prioritize_improvements", self.prioritize_improvements)
        workflow.add_node("generate_suggestion", self.generate_suggestion_for_gap)
        workflow.add_node("request_verification", self.request_human_verification)
        workflow.add_node("process_feedback", self.process_human_feedback)
        workflow.add_node("implement_changes", self.implement_changes)
        workflow.add_node("ats_optimization", self.ats_optimization)
        workflow.add_node("final_review", self.final_review)
        workflow.add_node("generate_report", self.generate_report)

        # Add human-in-the-loop interrupt node
        workflow.add_node("human_input", lambda x: x)

        # Add branching from intent detection
        workflow.add_conditional_edges(
            "detect_intent",
            self.determine_next_step,
            {
                "direct_edit": "process_direct_edit",
                "tailor_resume": "extract_requirements",
            },
        )

        # Direct edit path is simple
        workflow.add_edge("process_direct_edit", "generate_report")

        # Tailoring path with human-in-the-loop
        workflow.add_edge("extract_requirements", "analyze_resume")
        workflow.add_edge("analyze_resume", "prioritize_improvements")
        workflow.add_edge("prioritize_improvements", "generate_suggestion")
        workflow.add_edge("generate_suggestion", "request_verification")

        # Add interrupt edge from request_verification to human_input
        workflow.add_edge("request_verification", "human_input", interrupt=True)

        # After human input is received, continue with process_feedback
        workflow.add_edge("human_input", "process_feedback")

        # Add conditional edges
        workflow.add_conditional_edges(
            "process_feedback",
            self.should_continue_processing,
            {"continue": "generate_suggestion", "complete": "implement_changes"},
        )

        workflow.add_edge("implement_changes", "ats_optimization")
        workflow.add_edge("ats_optimization", "final_review")
        workflow.add_edge("final_review", "generate_report")

        # Set entry point and compile
        workflow.set_entry_point("detect_intent")
        return workflow.compile()

    def detect_intent(self, state: AgentState) -> AgentState:
        """Determine if this is a tailoring request or a direct edit request"""

        # If job description is empty or user specifically asks for an edit
        # Define a proper pydantic model for structured output

        class EditDetails(BaseModel):
            section: str = Field(description="Section of the resume to edit")
            action: str = Field(description="Action to take: add, modify, or remove")
            content: str = Field(description="Content to add or modify")

        class RequestAnalysis(BaseModel):
            request_type: str = Field(
                description="Either 'tailor_resume' or 'direct_edit'"
            )
            edit_details: Optional[EditDetails] = Field(
                None, description="Details for direct edit request"
            )

        intent_llm = self.llm.with_structured_output(RequestAnalysis)

        request_analysis = intent_llm.invoke(f"""
        Determine what the user wants to do with their resume based on this input:
        
        User request: {state.user_edit_request or "No specific request provided"}
        Job description provided: {"Yes" if state.job_description else "No"}
        
        If the user is asking to make a specific edit to their resume (like adding a skill, 
        updating a job description, etc.), classify this as a "direct_edit" and extract the details.
        
        If the user wants their resume tailored to a job description, classify this as "tailor_resume".
        
        Example direct edit requests:
        - "Add Python to my skills section"
        - "Update my job title at Google to Senior Engineer"
        - "Remove my internship at Microsoft"
        """)

        # Access the Pydantic model using dot notation instead of dictionary access
        state.request_type = RequestType(request_analysis.request_type)

        if (
            state.request_type == RequestType.DIRECT_EDIT
            and request_analysis.edit_details
        ):
            state.edit_section = request_analysis.edit_details.section
            state.edit_content = request_analysis.edit_details.content

        return state

    def determine_next_step(self, state: AgentState) -> str:
        """Determine whether to follow the direct edit or tailoring path"""
        if state.request_type == RequestType.DIRECT_EDIT:
            return "direct_edit"
        return "tailor_resume"

    def process_direct_edit(self, state: AgentState) -> AgentState:
        """Make the requested edit directly to the resume"""

        edit_llm = self.llm.invoke(f"""
        Make the following edit to this resume:
        
        Resume:
        {state.resume}
        
        Edit request: {state.user_edit_request}
        Section to edit: {state.edit_section}
        Edit content: {state.edit_content}
        
        Return the complete updated resume with this specific edit applied.
        Make sure to maintain the same format and style as the original resume,
        just with this single change applied.
        """)

        state.tailored_resume = edit_llm
        state.edit_completed = True

        # Generate a simple report about what was changed
        state.output = f"""
        # Resume Edit Complete
        
        I've updated your resume by making the following change:
        
        **Section**: {state.edit_section}
        **Change**: {state.user_edit_request}
        
        ## Updated Resume
        
        {state.tailored_resume}
        """

        return state

    def extract_requirements(self, state: AgentState) -> AgentState:
        """Extract requirements from job description"""
        requirements_llm = self.llm.with_structured_output(List[Requirement])
        logger.info("Extracting requirements from job description")
        requirements = requirements_llm.invoke(f"""
        Extract key requirements from this job description:
        {state.job_description}
        
        For each requirement, specify:
        1. The skill or qualification
        2. Importance level (High/Medium/Low)
        3. Required experience level
        """)

        state.requirements = requirements

        # Get company context
        context_llm = self.llm.with_structured_output(CompanyContext)
        logger.info("Getting company context")
        company_context = context_llm.invoke(f"""
        Analyze this job description and identify:
        1. Company culture and values
        2. Industry specifics
        3. Key terminology/buzzwords
        4. Level of formality expected
        5. Company size (Small/Medium/Large)
        6. Technology stack mentioned
        
        Job description:
        {state.job_description}
        """)

        state.company_context = company_context
        return state

    def analyze_resume(self, state: AgentState) -> AgentState:
        """Analyze resume against job requirements"""
        matches = []
        gaps = []

        # Create structured output LLMs
        match_llm = self.llm.with_structured_output(MatchedSkill)
        gap_llm = self.llm.with_structured_output(Gap)

        for req in state.requirements:
            # First check if this is a match
            prompt = f"""
            Does this resume demonstrate {req.skill} at {req.experience_level} level?
            
            Resume:
            {state.resume}
            
            If this skill IS demonstrated in the resume, respond with details about the match.
            If this skill is NOT demonstrated adequately, respond with "NO_MATCH".
            """

            try:
                response = match_llm.invoke(prompt)
                if response != "NO_MATCH":
                    # We have a match
                    matches.append(response)
                else:
                    # We have a gap
                    gap_prompt = f"""
                    The resume does not adequately demonstrate {req.skill} at {req.experience_level} level.
                    
                    Resume:
                    {state.resume}
                    
                    Analyze what evidence (if any) exists in the resume related to this skill,
                    and which section it appears in.
                    """
                    gap = gap_llm.invoke(gap_prompt)
                    gaps.append(
                        Gap(
                            skill=req.skill,
                            required_level=req.experience_level,
                            importance=req.importance,
                            resume_evidence=gap.resume_evidence,
                            section=gap.section,
                            impact=f"Missing {req.skill} at {req.experience_level} level",
                        )
                    )
            except Exception as e:
                print(f"Error analyzing requirement {req.skill}: {e}")
                continue

        state.matches = matches
        state.gaps = gaps
        state.current_gap_index = 0  # Initialize the gap index
        return state

    def prioritize_improvements(self, state: AgentState) -> AgentState:
        """Prioritize which improvements will have the biggest impact"""
        # Sort gaps by importance and ability to address
        prioritize_llm = self.llm.with_structured_output(List[PrioritizedImprovement])

        prioritized = prioritize_llm.invoke(f"""
        Analyze these skill gaps and prioritize which ones should be addressed in the resume:
        
        Gaps: {state.gaps}
        Current resume: {state.resume}
        
        For each gap, determine:
        1. Impact (high/medium/low) - how important is this for the job?
        2. Addressability (high/medium/low) - can we reasonably tailor the resume to address this?
        3. Priority (1-10 scale) - overall priority to fix
        4. Approach - how should we address this gap?
        5. Rationale - why is this improvement important?
        """)

        state.prioritized_improvements = prioritized

        # Sort gaps by priority
        if state.prioritized_improvements:
            # Create a mapping of skill to priority
            priority_map = {p.skill: p.priority for p in state.prioritized_improvements}

            # Sort gaps by priority (highest first)
            state.gaps = sorted(
                state.gaps,
                key=lambda gap: priority_map.get(gap.skill, 0),
                reverse=True,
            )

        return state

    def generate_suggestion_for_gap(self, state: AgentState) -> AgentState:
        """Generate a suggestion for the current gap"""
        if state.current_gap_index >= len(state.gaps):
            return state

        current_gap = state.gaps[state.current_gap_index]
        suggestion_llm = self.llm.with_structured_output(TailoringSuggestion)

        suggestion = suggestion_llm.invoke(f"""
        Create a specific suggestion to improve this resume based on the identified gap:
        
        Resume:
        {state.resume}
        
        Gap:
        {current_gap}
        
        Job requirements:
        {state.requirements}
        
        Provide:
        1. The skill being addressed
        2. Exact section to modify
        3. Original text (if any)
        4. Suggested new text
        5. Explanation of why this change helps
        6. Confidence in suggestion (high/medium/low)
        """)

        if not state.tailoring_suggestions:
            state.tailoring_suggestions = []

        state.tailoring_suggestions.append(suggestion)
        state.current_suggestion = suggestion.model_dump()
        return state

    def request_human_verification(self, state: AgentState) -> AgentState:
        """Request human verification of the current suggestion"""
        if not state.current_suggestion:
            return state

        # Create a verification request for the current suggestion
        suggestion = state.current_suggestion

        # Determine if this needs human verification
        if suggestion["confidence"] == "high":
            # High confidence suggestions are automatically approved
            suggestion["approved"] = True
            state.human_feedback = {"current_response": {"answer": "Yes"}}
            # No need to interrupt for high confidence suggestions
            state.waiting_for_human = False
        else:
            # Set up state for human interruption
            state.waiting_for_human = True
            state.step_name = "request_verification"
            state.human_question = f"Should we make this change to the resume?\n\nOriginal: {suggestion['original_text']}\n\nSuggested: {suggestion['new_text']}\n\nRationale: {suggestion['explanation']}"

            # Create a verification request
            state.human_feedback = {
                "current_response": None,
                "pending_request": {
                    "question": state.human_question,
                    "options": ["Yes", "No", "Yes with modifications"],
                    "context": {
                        "skill": suggestion["skill"],
                        "section": suggestion["section"],
                        "confidence": suggestion["confidence"],
                    },
                },
            }

            # Set output message for the frontend
            state.output = f"Waiting for human verification on suggested change for {suggestion['skill']}"

        return state

    def process_human_feedback(self, state: AgentState) -> AgentState:
        """Process feedback from human verification"""
        if not state.human_feedback.get("current_response"):
            # No feedback yet, keep waiting
            return state

        # Get the current suggestion
        suggestion = state.current_suggestion

        # Process the feedback
        response = state.human_feedback["current_response"]

        if response["answer"] == "Yes":
            # Keep suggestion as is
            suggestion["approved"] = True
        elif response["answer"] == "No":
            # Remove this suggestion
            suggestion["approved"] = False
        elif response["answer"] == "Yes with modifications":
            # Update suggestion with human modifications
            suggestion["new_text"] = response.get(
                "modified_text", suggestion["new_text"]
            )
            suggestion["approved"] = True

        # Move to the next gap
        state.current_gap_index += 1
        return state

    def should_continue_processing(self, state: AgentState) -> str:
        """Determine if we should continue processing gaps"""
        if state.current_gap_index < len(state.gaps):
            return "continue"
        return "complete"

    def implement_changes(self, state: AgentState) -> AgentState:
        """Implement approved changes to create tailored resume"""
        changes_by_section = {}
        for suggestion in state.tailoring_suggestions:
            if suggestion.approved:
                section = suggestion.section
                if section not in changes_by_section:
                    changes_by_section[section] = []
                changes_by_section[section].append(suggestion.model_dump())

        updated_resume = self.llm.invoke(f"""
        Update this resume with the following changes to create a tailored version:
        
        Current resume:
        {state.resume}
        
        Changes to make by section:
        {changes_by_section}
        
        Requirements from job:
        {state.requirements}
        
        Company context:
        {state.company_context}
        
        FORMAT THE RESULT WITH THESE SECTIONS in this order:
        1. Full name at the top
        2. Current professional title
        3. Professional summary (concise paragraph highlighting key qualifications)
        4. Skills (comprehensive list of technical and soft skills relevant to the job)
        5. Work Experience (chronological, with company, title, dates, and key projects/accomplishments)
        6. Education (degrees, institutions, and dates)
        
        Make sure to integrate all the approved changes while maintaining this structure.
        """)

        state.tailored_resume = updated_resume
        return state

    def ats_optimization(self, state: AgentState) -> AgentState:
        """Optimize resume for ATS systems"""
        ats_llm = self.llm.with_structured_output(ATSAnalysis)

        ats_analysis = ats_llm.invoke(f"""
        Analyze this resume for ATS optimization:
        {state.tailored_resume}
        
        Job description:
        {state.job_description}
        
        Check for:
        1. Keyword density compared to job description
        2. Use of industry-standard job titles
        3. Proper formatting that won't confuse ATS systems
        4. Appropriate use of bullet points and sections
        """)

        state.ats_score = ats_analysis.score

        if ats_analysis.score < 80:
            optimized = self.llm.invoke(f"""
            Update this resume to improve ATS compatibility by addressing these issues:
            
            Current resume:
            {state.tailored_resume}
            
            Improvements needed:
            {ats_analysis.improvements}
            
            Return the complete updated resume with better ATS optimization.
            """)
            state.tailored_resume = optimized

        return state

    def final_review(self, state: AgentState) -> AgentState:
        """Final review and polish of the resume"""
        review_llm = self.llm.with_structured_output(FinalReview)

        final_review = review_llm.invoke(f"""
        Perform a final review of this tailored resume:
        {state.tailored_resume}
        
        Job description:
        {state.job_description}
        
        Check for:
        1. Overall coherence and flow
        2. Appropriate highlighting of key qualifications
        3. Consistency in formatting and style
        4. Grammar and spelling
        5. Appropriate length and detail level
        """)

        if final_review.adjustments:
            polished = self.llm.invoke(f"""
            Make these final adjustments to the resume:
            
            Current resume:
            {state.tailored_resume}
            
            Adjustments:
            {final_review.adjustments}
            
            Return the complete finalized resume.
            """)
            state.tailored_resume = polished

        state.final_notes = final_review.strengths
        return state

    def generate_report(self, state: AgentState) -> AgentState:
        """Generate final tailored resume with summary in markdown format"""
        # If this was a direct edit, we already have the output
        if state.edit_completed:
            return state

        summary = f"""
        # Resume Tailoring Summary
        
        ## Job Fit Analysis
        - Matched Skills: {len(state.matches)}
        - Addressed Gaps: {len([g for g in state.gaps if g.skill in [s.skill for s in state.tailoring_suggestions]])}
        - ATS Compatibility Score: {state.ats_score}/100
        
        ## Key Improvements Made
        """

        for suggestion in state.tailoring_suggestions:
            if suggestion.approved:
                summary += f"- {suggestion.section}: {suggestion.explanation}\n"

        summary += "\n## Resume Strengths\n"
        for note in state.final_notes:
            summary += f"- {note}\n"

        resume_structure_llm = self.llm.with_structured_output(dict)

        resume_components = resume_structure_llm.invoke(f"""
        Extract the following components from this resume:
        - name: The candidate's full name
        - current_title: Their current professional title
        - professional_summary: A paragraph summarizing their professional background
        - skills: A comprehensive list of all skills mentioned (technical and soft skills)
        - work_experience: List of all work experiences with company, title, dates, and key projects/accomplishments
        - education: List of educational background with degree, institution, and dates
        
        Resume:
        {state.tailored_resume}
        
        Return these components in a structured format.
        """)

        # Format the resume in markdown
        final_resume_markdown = f"# {resume_components['name']}\n\n"
        final_resume_markdown += f"## {resume_components['current_title']}\n\n"
        final_resume_markdown += f"{resume_components['professional_summary']}\n\n"

        final_resume_markdown += "## Skills\n\n"
        skills = resume_components["skills"]
        if isinstance(skills, list):
            for skill in skills:
                final_resume_markdown += f"- {skill}\n"
        else:
            final_resume_markdown += f"{skills}\n"

        final_resume_markdown += "\n## Work Experience\n\n"
        work_exp = resume_components["work_experience"]

        if isinstance(work_exp, list):
            for job in work_exp:
                final_resume_markdown += (
                    f"### {job.get('title')} | {job.get('company')}\n"
                )
                final_resume_markdown += f"*{job.get('dates')}*\n\n"

                if "projects" in job and isinstance(job["projects"], list):
                    final_resume_markdown += "**Key Projects:**\n\n"
                    for project in job["projects"]:
                        final_resume_markdown += f"- **{project.get('name', 'Project')}**: {project.get('description', '')}\n"

                if "accomplishments" in job and isinstance(
                    job["accomplishments"], list
                ):
                    final_resume_markdown += "\n**Accomplishments:**\n\n"
                    for accomplishment in job["accomplishments"]:
                        final_resume_markdown += f"- {accomplishment}\n"

                final_resume_markdown += "\n"
        else:
            final_resume_markdown += f"{work_exp}\n"

        final_resume_markdown += "\n## Education\n\n"
        education = resume_components["education"]
        if isinstance(education, list):
            for edu in education:
                final_resume_markdown += f"**{edu.get('degree')}** - {edu.get('institution')}, {edu.get('dates')}\n\n"
        else:
            final_resume_markdown += f"{education}\n"

        state.output = f"{summary}\n\n## Final Tailored Resume\n{final_resume_markdown}"
        return state

    async def run(self, initial_state: AgentState) -> AgentState:
        """Run the workflow with the given initial state"""
        # If we have human feedback, we're resuming from an interrupt
        if initial_state.human_feedback and initial_state.waiting_for_human:
            # Reset the waiting flag since we're continuing with human input
            initial_state.waiting_for_human = False

            # Try different async methods based on the LangGraph version
            try:
                # First try the newer method with the human_input node
                return await self.workflow.ainvoke(
                    initial_state, {"checkpoint": "human_input"}
                )
            except (AttributeError, ValueError):
                try:
                    # Then try the alternative method
                    return await self.workflow.invoke_async(
                        initial_state, {"checkpoint": "human_input"}
                    )
                except (AttributeError, ValueError):
                    # Fall back to compiled graph method
                    compiled = self.workflow.compile()
                    return await compiled.ainvoke(
                        initial_state, {"checkpoint": "human_input"}
                    )
        else:
            # Starting from the beginning
            try:
                # First try the newer method
                return await self.workflow.ainvoke(initial_state)
            except AttributeError:
                try:
                    # Then try the alternative method
                    return await self.workflow.invoke_async(initial_state)
                except AttributeError:
                    # Fall back to compiled graph method
                    compiled = self.workflow.compile()
                    return await compiled.ainvoke(initial_state)
