import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import yt_dlp
import whisper
import subprocess
import shutil
import glob # Import glob buat cari file

# --- HELPER ---
def parse_time(time_str):
    parts = list(map(int, time_str.split(':')))
    if len(parts) == 3: return parts[0] * 3600 + parts[1] * 60 + parts[2]
    elif len(parts) == 2: return parts[0] * 60 + parts[1]
    return parts[0]

def format_timestamp_ass(seconds):
    if seconds < 0: seconds = 0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centi = int((seconds - int(seconds)) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centi:02d}"

def process_blur_style(job_id, url, start, end, output_dir, jobs_dict, subtitle_pos=300):
    cwd = os.getcwd()
    cut_video = f"cut_{job_id}.mp4"
    audio_track = f"audio_{job_id}.m4a"
    stage_1_video = f"stage1_{job_id}.mp4"
    ass_file = f"style_{job_id}.ass"
    final_video = os.path.join(os.path.abspath(output_dir), f"{job_id}.mp4")
    
    detected_raw = None

    try:
        jobs_dict[job_id]["status"] = "processing_download"
        
        # Pre-clean
        if os.path.exists(output_dir): os.makedirs(output_dir, exist_ok=True)
        for f in [cut_video, audio_track, stage_1_video, ass_file, final_video]:
            if os.path.exists(f): os.remove(f)
        for f in glob.glob(f"raw_{job_id}.*"): os.remove(f)

        start_sec = parse_time(str(start))
        end_sec = parse_time(str(end))

        # 1. DOWNLOAD (ANDROID CLIENT)
        print(f"📥 [BLUR ENGINE] Downloading...")
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best', 
            'outtmpl': f"raw_{job_id}.%(ext)s",
            'merge_output_format': 'mp4',
            'quiet': True, 
            'nocheckcertificate': True,
            'extractor_args': {'youtube': {'player_client': ['android']}},
            'user_agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([url])

        raw_candidates = glob.glob(f"raw_{job_id}.*")
        if raw_candidates: detected_raw = raw_candidates[0]
        else: raise Exception("Download gagal.")

        # 2. TRIM
        print(f"🔪 [BLUR ENGINE] Trimming...")
        subprocess.run([
            "ffmpeg", "-ss", str(start), "-to", str(end), 
            "-i", detected_raw, 
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "16", 
            "-c:a", "copy", "-y", cut_video
        ], check=True, stderr=subprocess.DEVNULL)

        subprocess.run([
            "ffmpeg", "-i", cut_video, "-vn", "-acodec", "copy", "-y", audio_track
        ], check=True, stderr=subprocess.DEVNULL)

        # 3. RENDER BLUR (SPLIT STREAM)
        print(f"🎨 [BLUR ENGINE] Compositing...")
        jobs_dict[job_id]["status"] = "processing_render"
        
        filter_complex = (
            "[0:v]split=2[v1][v2];" 
            "[v1]scale=1080:1920,setsar=1,boxblur=40:5[bg];" 
            "[v2]scale=1080:-2,setsar=1[fg];"                
            "[bg][fg]overlay=(W-w)/2:(H-h)/2"        
        )

        subprocess.run([
            "ffmpeg", "-i", cut_video, 
            "-vf", filter_complex,
            "-c:v", "libx264", 
            "-preset", "slow", "-crf", "18", 
            "-an", "-y", stage_1_video       
        ], check=True, stderr=subprocess.DEVNULL)

        # 4. MUX
        subprocess.run([
            "ffmpeg", "-i", stage_1_video, "-i", audio_track,
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-map", "0:v:0", "-map", "1:a:0", "-shortest", "-y", f"mux_{stage_1_video}"
        ], check=True, stderr=subprocess.DEVNULL)
        os.replace(f"mux_{stage_1_video}", stage_1_video)

        # 5. TRANSCRIBE
        print("🎤 [BLUR ENGINE] Transcribing...")
        jobs_dict[job_id]["status"] = "transcribing_ai"
        model = whisper.load_model("small") 
        result = model.transcribe(os.path.abspath(audio_track), fp16=False, word_timestamps=True)
        all_words = []
        for segment in result["segments"]: all_words.extend(segment.get("words", []))
            
        # 6. SUBTITLE
        print("📝 [BLUR ENGINE] Generating Subtitles...")
        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: NeonStyle,Arial,60,&H0000D7FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,0,2,10,10,{subtitle_pos},1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        with open(ass_file, "w", encoding="utf-8") as f:
            f.write(header)
            for i in range(0, len(all_words), 3): 
                chunk = all_words[i : i + 3]
                if not chunk: continue
                s_str = format_timestamp_ass(chunk[0]["start"])
                e_str = format_timestamp_ass(chunk[-1]["end"])
                text = "".join([w["word"] for w in chunk]).strip().upper()
                f.write(f"Dialogue: 0,{s_str},{e_str},NeonStyle,,0,0,0,,{{\\blur15\\bord3\\shad1}} {text}\n")

        # 7. FINAL BURN
        print("🔥 [BLUR ENGINE] Finalizing...")
        jobs_dict[job_id]["status"] = "rendering_final"
        subprocess.run([
            "ffmpeg", "-i", stage_1_video, "-vf", f"ass={os.path.basename(ass_file)}", 
            "-c:v", "libx264", "-preset", "slow", "-b:v", "8000k", 
            "-c:a", "copy", "-y", final_video
        ], stderr=subprocess.DEVNULL)

        return True

    except Exception as e:
        print(f"❌ Blur Engine Error: {e}")
        jobs_dict[job_id]["status"] = f"error: {str(e)}"
        return False

    finally:
        # --- CLEANUP WAJIB ---
        print("🧹 Cleaning up temporary files...")
        
        # 1. Hapus Raw Video (Apapun ekstensinya)
        for f in glob.glob(f"raw_{job_id}.*"):
            try: os.remove(f)
            except: pass

        # 2. Hapus File Intermediate
        for f in [cut_video, audio_track, stage_1_video, ass_file]:
            try:
                if os.path.exists(f): os.remove(f)
            except: pass
        
        print("✨ Workspace Cleaned.")