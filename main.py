from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uuid
import os
from core_engine import process_video_task

app = FastAPI()

# Folder Output
OUTPUT_DIR = "static/results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Database Job Sementara
jobs = {}

class RenderRequest(BaseModel):
    url: str
    start: str
    end: str

# API untuk memulai render
@app.post("/api/render")
async def api_render(req: RenderRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = "queued"
    
    # Fungsi background worker
    def worker(jid, u, s, e):
        # Update status di dalam fungsi core_engine atau manual disini
        # Agar simpel, kita update manual di wrapper ini
        #jobs[jid] = "processing"
        
        # Panggil Core Engine
        success = process_video_task(jid, u, s, e, OUTPUT_DIR, jobs) 
        
        if success:
            jobs[jid] = "completed"
        else:
            # PERBAIKAN: Jangan timpa status error yang sudah diset core_engine
            # Cek apakah statusnya sudah berisi pesan error?
            current_status = jobs.get(jid, "")
            if not current_status.startswith("error"):
                jobs[jid] = "failed_general"

    background_tasks.add_task(worker, job_id, req.url, req.start, req.end)
    return {"job_id": job_id}

# API Cek Status
@app.get("/api/status/{job_id}")
async def api_status(job_id: str):
    status = jobs.get(job_id, "not_found")
    file_url = f"/results/{job_id}.mp4" if status == "completed" else None
    return {"status": status, "file_url": file_url}

# Mount Folder Static
app.mount("/", StaticFiles(directory="static", html=True), name="static")
