from typing import Any, Dict
from uuid import uuid4

import uvicorn
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

from agents.agent import app as agent_workflow
from utils.job_scraper import scrape_job_details
from utils.parse_pdf import parse_resume_pdf

app = FastAPI(
    title="Resume Tailoring API",
    description="API for tailoring resumes to job descriptions using AI",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store job processing status and results
job_status = {}


class JobRequest(BaseModel):
    job_url: HttpUrl
    resume_id: str


class JobResponse(BaseModel):
    job_id: str
    status: str
    message: str


@app.post("/upload/resume", response_model=Dict[str, str])
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a resume PDF file and parse its contents.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    try:
        resume_id = str(uuid4())
        resume_text = await parse_resume_pdf(file)

        # Store the parsed resume text (you might want to use a proper database in production)
        job_status[resume_id] = {"resume_text": resume_text, "status": "parsed"}

        return {
            "resume_id": resume_id,
            "message": "Resume uploaded and parsed successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/job/details", response_model=JobResponse)
async def get_job_details(job_request: JobRequest, background_tasks: BackgroundTasks):
    """
    Get job details from URL and start the resume tailoring process.
    """
    if job_request.resume_id not in job_status:
        raise HTTPException(status_code=404, detail="Resume not found")

    try:
        job_id = str(uuid4())
        job_status[job_id] = {
            "status": "processing",
            "resume_id": job_request.resume_id,
            "job_url": str(job_request.job_url),
        }

        # Start job processing in background
        background_tasks.add_task(process_job, job_id, job_request)

        return JobResponse(
            job_id=job_id, status="processing", message="Job processing started"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/{job_id}", response_model=Dict[str, Any])
async def get_status(job_id: str):
    """
    Get the status of a job processing request.
    """
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")

    return job_status[job_id]


async def process_job(job_id: str, job_request: JobRequest):
    """
    Process the job in background.
    """
    try:
        # Get resume text
        resume_text = job_status[job_request.resume_id]["resume_text"]

        # Scrape job details
        job_description = await scrape_job_details(str(job_request.job_url))

        # Update status
        job_status[job_id].update(
            {"status": "analyzing", "job_description": job_description}
        )

        # Run agent workflow
        result = await agent_workflow.arun(
            {
                "job_description": job_description,
                "resume": resume_text,
                "company_context": {},
                "requirements": [],
                "matches": [],
                "gaps": [],
                "prioritized_improvements": [],
                "tailoring_suggestions": [],
                "verification_queue": [],
                "human_feedback": {},
                "tailored_resume": "",
                "ats_score": 0.0,
                "final_notes": [],
                "output": "",
            }
        )

        # Update status with results
        job_status[job_id].update({"status": "completed", "result": result})

    except Exception as e:
        job_status[job_id].update({"status": "failed", "error": str(e)})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
