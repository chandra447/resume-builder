from typing import Dict, Optional

from src.agents.agent import AgentState, ResumeTailoringAgent
from src.backend.websockets.connection_manager import connection_manager
from src.utils.logger_config import setup_logger

logger = setup_logger(__name__)


class TailoringService:
    def __init__(self):
        self.agent = ResumeTailoringAgent()

    async def start_tailoring(self, resume: str, job_description: str) -> Dict:
        """Start the tailoring process"""
        initial_state = AgentState(
            resume=resume,
            job_description=job_description,
            step_name="start"
        )
        logger.info("Starting tailoring process")
        # Run until human input is needed
        result = await self.agent.run(initial_state)
        
        # Check if we need human input
        if result.waiting_for_human:
            logger.info(f"Waiting for human input: {result.human_question}")
        else:
            logger.info("Completed tailoring without human input")
            
        return result

    async def provide_feedback(self, session_id: str, feedback: Dict) -> Dict:
        """Process human feedback and continue the workflow"""
        logger.info("Processing human feedback")
        # Retrieve the current state for this session
        current_state = self.get_session_state(session_id)
        
        if not current_state:
            logger.error(f"No state found for session {session_id}")
            raise ValueError(f"Session {session_id} not found")

        # Update state with feedback
        current_state.human_feedback = feedback
        current_state.waiting_for_human = False  # Reset the waiting flag
        
        logger.info(f"Continuing workflow from step: {current_state.step_name}")

        # Continue the workflow
        result = await self.agent.run(current_state)
        
        # Check if we need more human input
        if result.waiting_for_human:
            logger.info(f"Waiting for more human input: {result.human_question}")
        else:
            logger.info("Completed tailoring process")
            
        return result

    # In-memory storage for session states (for development/testing)
    # In a production environment, this should be replaced with a database
    _session_states = {}

    def get_session_state(self, session_id: str) -> Optional[AgentState]:
        """Retrieve the current state for a session"""
        return self._session_states.get(session_id)

    async def save_session_state(self, session_id: str, state: AgentState):
        """Save the current state for a session and send update via WebSocket"""
        self._session_states[session_id] = state
        
        # Send update via WebSocket if there's an active connection
        try:
            # Prepare the update data
            update_data = {
                "type": "state_update",
                "state": state.model_dump(),
                "message": state.output if state.output else None,
                "waiting_for_human": state.waiting_for_human,
                "human_question": state.human_question if state.waiting_for_human else None,
                "step_name": state.step_name
            }
            
            # Send the update
            await connection_manager.send_update(session_id, update_data)
            logger.info(f"Sent state update for session {session_id}")
        except Exception as e:
            logger.error(f"Error sending WebSocket update: {str(e)}")
