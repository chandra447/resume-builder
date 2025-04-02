import uuid
from typing import Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.tailoring_service import TailoringService

router = APIRouter()
tailoring_service = TailoringService()


class TailoringRequest(BaseModel):
    resume: str
    job_description: str


class FeedbackRequest(BaseModel):
    feedback: Dict


@router.post("/tailoring-sessions/")
async def create_tailoring_session(request: TailoringRequest):
    try:
        # Generate a unique session ID
        session_id = str(uuid.uuid4())

        # Start the tailoring process
        result = await tailoring_service.start_tailoring(
            resume=request.resume, job_description=request.job_description
        )

        # Save the state
        tailoring_service.save_session_state(session_id, result)

        return {
            "id": session_id,
            "status": "started",
            "initial_state": result.model_dump(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tailoring-sessions/{session_id}/feedback")
async def provide_feedback(session_id: str, request: FeedbackRequest):
    try:
        # Process the feedback
        result = await tailoring_service.provide_feedback(
            session_id=session_id, feedback=request.feedback
        )

        # Save the updated state
        tailoring_service.save_session_state(session_id, result)

        return {"status": "success", "state": result.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tailoring-sessions/{session_id}")
async def get_session_state(session_id: str):
    try:
        state = tailoring_service.get_session_state(session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"id": session_id, "state": state.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
