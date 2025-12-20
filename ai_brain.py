import google.generativeai as genai
import subprocess
import os
import json
import re
from dotenv import load_dotenv 

# Load environment variables dari file .env
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("❌ API Key tidak ditemukan! Pastikan file .env sudah dibuat.")
# ======================

genai.configure(api_key=GOOGLE_API_KEY)

def get_transcript_using_ytdlp(url):
    """
    Mengambil transkrip menggunakan YT-DLP (Metode Paling Stabil)
    """
    try:
        print("🔍 Mengambil transkrip via YT-DLP...")
        
        temp_sub = "temp_transcript"
        
        # Bersihkan file lama
        for f in os.listdir():
            if f.startswith(temp_sub): os.remove(f)

        # Perintah YT-DLP
        cmd = [
            "yt-dlp",
            "--write-auto-sub",
            "--sub-lang", "en,id",
            "--skip-download",
            "--convert-subs", "srt", 
            "--output", temp_sub,
            "--cookies", "cookies.txt", 
            url
        ]
        
        # Jalankan diam-diam
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Cari file SRT hasil
        srt_file = None
        for f in os.listdir():
            if f.startswith(temp_sub) and f.endswith(".srt"):
                srt_file = f
                break
        
        if not srt_file:
            print("❌ YT-DLP tidak menemukan subtitle.")
            return None

        # Parsing SRT ke Text
        parsed_transcript = []
        with open(srt_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        current_time = 0
        for line in lines:
            line = line.strip()
            if "-->" in line:
                try:
                    start_str = line.split("-->")[0].strip().replace(",", ".")
                    h, m, s = start_str.split(":")
                    current_time = int(float(h)*3600 + float(m)*60 + float(s))
                except: pass
            elif line and not line.isdigit():
                clean_text = re.sub(r'<[^>]+>', '', line)
                if parsed_transcript and clean_text in parsed_transcript[-1]:
                    continue
                parsed_transcript.append(f"[{current_time}] {clean_text}")

        if os.path.exists(srt_file): os.remove(srt_file)
        return " ".join(parsed_transcript)

    except Exception as e:
        print(f"❌ Error YT-DLP Transcript: {e}")
        return None

# --- FUNGSI AI DENGAN FALLBACK ---

def generate_with_fallback(prompt):
    # Urutan model sesuai log akun Anda
    models_to_try = [
        'models/gemini-2.5-flash',
        'models/gemini-2.5-pro',
        'models/gemini-2.0-flash',
        'models/gemini-flash-latest',
        'gemini-pro'
    ]
    
    last_error = None
    
    for model_name in models_to_try:
        try:
            print(f"🤖 Mencoba Model: {model_name}...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response
        except Exception as e:
            print(f"⚠️ Gagal dengan {model_name}: {e}")
            last_error = e
            continue 
            
    print("❌ Semua model gagal.")
    raise last_error

def ask_gemini_auto_clip(transcript_text, niche="General", target_lang="id"):
    if not transcript_text: return None
    
    # Instruksi Bahasa
    lang_instruction = "BAHASA INDONESIA (Gunakan bahasa gaul/santai yang viral)"
    if target_lang == "en":
        lang_instruction = "ENGLISH (Use viral slang/hook style)"

    max_chars = 100000 
    
    prompt = f"""
    You are a viral video editor. Niche: {niche}.
    Task: Find ONE viral segment (30-60s) from transcript below.
    CRITICAL: The start/end time must be accurate based on [seconds] markers.
    
    INSTRUCTION: Create Title & Description strictly in {lang_instruction}.
    
    Transcript: 
    {transcript_text[:max_chars]}
    
    Output JSON (No Markdown):
    {{
        "start": "HH:MM:SS",
        "end": "HH:MM:SS",
        "title": "Clickbait Title (in {target_lang})",
        "description": "Caption with hashtags (in {target_lang})"
    }}
    """
    try:
        response = generate_with_fallback(prompt)
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"Gemini Fatal Error: {e}")
        return None

def ask_gemini_metadata_only(segment_text, niche="General", target_lang="id"):
    
    lang_instruction = "BAHASA INDONESIA"
    if target_lang == "en":
        lang_instruction = "ENGLISH"

    prompt = f"""
    Role: Copywriter. Niche: {niche}.
    Content: "{segment_text[:2000]}"
    Task: Viral Title & Description strictly in {lang_instruction}.
    Output JSON: {{ "title": "...", "description": "..." }}
    """
    try:
        response = generate_with_fallback(prompt)
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception as e:
        return {"title": "Error", "description": "Error"}