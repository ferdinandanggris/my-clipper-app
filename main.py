from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uuid
import os
import re

# IMPORT KEDUA ENGINE
from core_engine import process_video_task      # Vertical Crop (AI)
from engine_blur import process_blur_style      # Horizontal Blur

from ai_brain import (
    get_transcript_using_ytdlp, 
    ask_gemini_auto_clip, 
    ask_gemini_metadata_only
)

app = FastAPI()
OUTPUT_DIR = "static/results"
os.makedirs(OUTPUT_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

jobs = {}

def extract_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None

class RenderRequest(BaseModel):
    url: str
    start: str = ""
    end: str = ""
    subtitle_pos: int = 300
    use_ai: bool = False
    niche: str = "General"
    lang: str = "id"
    style: str = "vertical"  # <--- FIELD BARU (vertical / blur)

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.post("/api/render")
async def api_render(req: RenderRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = { "status": "queued", "metadata": {}, "file_url": "", "transcript_text": "" }
    
    def worker(jid, u, s, e, sub_pos, use_ai, niche, lang, video_style):
        try:
            print(f"🚀 Job {jid} Start. Style:{video_style}, AI:{use_ai}")
            
            video_id = extract_video_id(u)
            if not video_id: raise Exception("URL YouTube tidak valid")

            final_start = s
            final_end = e
            
            # 1. AMBIL TRANSKRIP
            transcript_text = get_transcript_using_ytdlp(u)
            if transcript_text:
                jobs[jid]["transcript_text"] = transcript_text
            
            # 2. LOGIKA AI (Untuk Start/End dan Metadata)
            if use_ai:
                if not transcript_text:
                    raise Exception("Gagal mengambil transkrip (Cek Cookies/Video/Bahasa).")
                
                jobs[jid]["status"] = "analyzing_ai_gemini"
                ai_result = ask_gemini_auto_clip(transcript_text, niche, lang)
                
                if ai_result:
                    final_start = ai_result.get('start')
                    final_end = ai_result.get('end')
                    jobs[jid]["metadata"] = {
                        "title": ai_result.get("title", "AI Auto Clip"),
                        "description": ai_result.get("description", "")
                    }
                else:
                    raise Exception("AI gagal menemukan clip.")

            elif not use_ai and s and e:
                jobs[jid]["status"] = "generating_metadata"
                context_prompt = f"Video clip about {niche}, from {s} to {e}."
                if transcript_text:
                    context_prompt += f" Based on content: {transcript_text[:2000]}..."
                
                meta_result = ask_gemini_metadata_only(context_prompt, niche, lang)
                if meta_result:
                    jobs[jid]["metadata"] = {
                        "title": meta_result.get("title", "Manual Clip"),
                        "description": meta_result.get("description", "")
                    }

            if not final_start or not final_end:
                raise Exception("Waktu Start/End kosong.")

            # 3. PROSES VIDEO BERDASARKAN STYLE
            if video_style == "blur":
                # Panggil Engine Blur
                success = process_blur_style(jid, u, final_start, final_end, OUTPUT_DIR, jobs, sub_pos)
            else:
                # Panggil Engine Vertical (Core Engine)
                success = process_video_task(jid, u, final_start, final_end, OUTPUT_DIR, jobs, sub_pos)
            
            if success:
                jobs[jid]["status"] = "completed"
                jobs[jid]["file_url"] = f"/static/results/{jid}.mp4"
            else:
                if not str(jobs[jid]["status"]).startswith("error"):
                    jobs[jid]["status"] = "failed_processing"

        except Exception as e:
            print(f"❌ Worker Error: {e}")
            jobs[jid]["status"] = f"error: {str(e)}"

    background_tasks.add_task(worker, job_id, req.url, req.start, req.end, req.subtitle_pos, req.use_ai, req.niche, req.lang, req.style)
    return {"job_id": job_id}

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    job = jobs.get(job_id)
    if not job: return {"status": "not_found"}
    return job

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)