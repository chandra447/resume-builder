import uuid
from typing import Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from src.utils.job_scraper import scrape_job_details
from src.utils.logger_config import setup_logger
from src.utils.parse_pdf import parse_resume_pdf

from ..services.tailoring_service import TailoringService

logger = setup_logger(__name__)

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

        # Save the state and send WebSocket update
        await tailoring_service.save_session_state(session_id, result)

        return {
            "id": session_id,
            "status": "started",
            "initial_state": result.model_dump(),
            "websocket_url": f"ws://localhost:8000/ws/{session_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-resume-and-job/")
async def upload_resume_and_job(
    resume_file: UploadFile = File(...),
    job_url: Optional[str] = Form(None),
    job_description: Optional[str] = Form(None),
):
    logger.info("Starting upload and tailoring process", 5 * "*")
    try:
        # Parse the uploaded resume PDF
        logger.info("Parsing resume PDF")
        resume_text = await parse_resume_pdf(resume_file)

        # Get job description either from URL or direct input
        logger.info("Getting job description")
        job_desc_text = ""
        if job_url:
            job_desc_text = await scrape_job_details(job_url)
        elif job_description:
            job_desc_text = job_description
        else:
            raise HTTPException(
                status_code=400,
                detail="Either job_url or job_description must be provided",
            )

        # Generate a unique session ID
        session_id = str(uuid.uuid4())

        # Start the tailoring process
        logger.info("Starting tailoring process")
        result = await tailoring_service.start_tailoring(
            resume=resume_text, job_description=job_desc_text
        )

        # Save the state and send WebSocket update
        await tailoring_service.save_session_state(session_id, result)

        return {
            "id": session_id,
            "status": "started",
            "initial_state": result.model_dump(),
            "websocket_url": f"ws://localhost:8000/ws/{session_id}"
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

        # Save the updated state and send WebSocket update
        await tailoring_service.save_session_state(session_id, result)

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
