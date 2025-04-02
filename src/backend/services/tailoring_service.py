from typing import Dict, Optional

from src.agents.agent import AgentState, ResumeTailoringAgent


class TailoringService:
    def __init__(self):
        self.agent = ResumeTailoringAgent()

    async def start_tailoring(self, resume: str, job_description: str) -> Dict:
        """Start the tailoring process"""
        initial_state = AgentState(
            resume=resume,
            job_description=job_description,
        )

        # Run until human input is needed
        result = await self.agent.run(initial_state)
        return result

    async def provide_feedback(self, session_id: str, feedback: Dict) -> Dict:
        """Process human feedback and continue the workflow"""
        # Retrieve the current state for this session
        current_state = self.get_session_state(session_id)

        # Update state with feedback
        current_state.human_feedback = feedback

        # Continue the workflow
        result = await self.agent.run(current_state)
        return result

    def get_session_state(self, session_id: str) -> Optional[AgentState]:
        """Retrieve the current state for a session"""
        # TODO: Implement state persistence
        # This should retrieve the saved state from a database or cache
        pass

    def save_session_state(self, session_id: str, state: AgentState):
        """Save the current state for a session"""
        # TODO: Implement state persistence
        # This should save the state to a database or cache
        pass
