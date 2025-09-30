from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os
from typing import List, Optional
from pydantic import BaseModel
from resume_parser import ResumeParser
from automation.job_automation import JobAutomation
from db.init_db import create_tables

app = FastAPI(title="Job Automation API", version="1.0.0")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.getenv("DB_PATH", "jobs.db")
resume_parser = ResumeParser()
job_automation = JobAutomation(db_path=DB_PATH)


@app.on_event("startup")
async def ensure_database():
    create_tables(DB_PATH)

# Pydantic models
class Job(BaseModel):
    id: int
    title: str
    location: str
    company: str
    url: str
    status: str
    date_posted: str
    last_checked: str

class JobFilter(BaseModel):
    company: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    skills: Optional[List[str]] = None
    limit: Optional[int] = 50

class Application(BaseModel):
    id: int
    job_id: int
    applied_date: str
    status: str
    notes: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "Job Automation API", "version": "1.0.0"}

@app.get("/jobs", response_model=List[Job])
async def get_jobs(filter: JobFilter = JobFilter()):
    """Get jobs with optional filtering"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []
    
    if filter.company:
        query += " AND company = ?"
        params.append(filter.company)
    
    if filter.location:
        query += " AND location LIKE ?"
        params.append(f"%{filter.location}%")
    
    if filter.status:
        query += " AND status = ?"
        params.append(filter.status)
    
    query += " ORDER BY date_posted DESC LIMIT ?"
    params.append(filter.limit)
    
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    
    return [Job(**dict(row)) for row in rows]

@app.get("/jobs/{job_id}", response_model=Job)
async def get_job(job_id: int):
    """Get a specific job by ID"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return Job(**dict(row))

@app.get("/companies")
async def get_companies():
    """Get list of companies with job counts"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT company, COUNT(*) as count FROM jobs GROUP BY company ORDER BY count DESC")
    rows = c.fetchall()
    conn.close()
    
    return [{"company": row[0], "count": row[1]} for row in rows]

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """Upload resume file for parsing"""
    filename = file.filename
    if not filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename")

    normalized_name = filename.lower()
    if not normalized_name.endswith((".pdf", ".doc", ".docx")):
        raise HTTPException(status_code=400, detail="Only PDF, DOC, and DOCX files are allowed")
    
    # Read file content
    file_content = await file.read()
    
    # Parse resume
    result = resume_parser.parse_resume(file_content, filename)
    
    if result['status'] == 'error':
        raise HTTPException(status_code=400, detail=result['error'])
    
    return {
        "message": "Resume parsed successfully",
        "filename": file.filename,
        "size": len(file_content),
        "parsed_data": result
    }

@app.post("/jobs/{job_id}/apply")
async def apply_to_job(job_id: int, notes: Optional[str] = None):
    """Mark a job as applied to"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if job exists
    c.execute("SELECT id FROM jobs WHERE id = ?", (job_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if already applied
    c.execute("SELECT id FROM applications WHERE job_id = ?", (job_id,))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Already applied to this job")
    
    # Create application record
    from datetime import datetime
    applied_date = datetime.now().strftime("%Y-%m-%d")
    c.execute("""
        INSERT INTO applications (job_id, applied_date, status, notes)
        VALUES (?, ?, 'applied', ?)
    """, (job_id, applied_date, notes))
    
    # Update job status
    c.execute("UPDATE jobs SET status = 'applied' WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()
    
    return {"message": f"Job {job_id} marked as applied"}

@app.get("/applications", response_model=List[Application])
async def get_applications():
    """Get all applications"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("""
        SELECT a.*, j.title, j.company 
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        ORDER BY a.applied_date DESC
    """)
    rows = c.fetchall()
    conn.close()
    
    return [Application(**dict(row)) for row in rows]

@app.post("/automation/run")
async def run_automation(max_applications: int = 3):
    """Run job application automation"""
    try:
        # Get pending applications
        pending_jobs = job_automation.get_pending_applications()
        
        if not pending_jobs:
            return {"message": "No pending applications found", "count": 0}
        
        # Run automation
        await job_automation.run_automation(max_applications)
        
        return {
            "message": f"Automation completed for up to {max_applications} applications",
            "pending_jobs": len(pending_jobs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Automation error: {str(e)}")

@app.get("/automation/status")
async def get_automation_status():
    """Get automation status and pending applications"""
    try:
        pending_jobs = job_automation.get_pending_applications()
        
        return {
            "pending_applications": len(pending_jobs),
            "jobs": [
                {
                    "id": job[0],
                    "title": job[1],
                    "company": job[3],
                    "url": job[2]
                }
                for job in pending_jobs
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
