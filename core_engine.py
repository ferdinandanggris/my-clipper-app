import yt_dlp
import whisper
import os
import subprocess
import uuid

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

def process_video_task(job_id, url, start, end, output_dir, jobs_dict, subtitle_pos=300):
    try:
        jobs_dict[job_id]["status"] = "processing_download"
        base_name = f"raw_{job_id}"
        
        # Cleanup
        for ext in [".mp4", ".webm", ".mkv"]:
            if os.path.exists(base_name + ext): os.remove(base_name + ext)

        start_sec = parse_time(str(start))
        end_sec = parse_time(str(end))

        # 1. DOWNLOAD (Buffer 2 detik)
        opts = {
            'format': 'bestvideo+bestaudio/best', 
            'merge_output_format': 'mp4',
            'outtmpl': base_name + '.%(ext)s',
            'download_ranges': yt_dlp.utils.download_range_func(None, [(start_sec, end_sec)]),
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
            'force_keyframes_at_cuts': False, 'quiet': True, 'nocheckcertificate': True,
            'cookiefile': 'cookies.txt' 
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl: ydl.download([url])

        temp_name = None
        for ext in [".mp4", ".webm", ".mkv"]:
            if os.path.exists(base_name + ext):
                temp_name = base_name + ext
                break
        
        if not temp_name: raise Exception("File video tidak ditemukan.")

        # 2. TRANSCRIBE (Smart Analysis)
        jobs_dict[job_id]["status"] = "transcribing_ai"
        model = whisper.load_model("small") 
        INITIAL_PROMPT = "Philosophy, Tech, Business, Future, AI, Smart, Indonesia."
        result = model.transcribe(temp_name, fp16=False, word_timestamps=True, initial_prompt=INITIAL_PROMPT)
        
        all_words = []
        for segment in result["segments"]:
            all_words.extend(segment.get("words", []))
            
        if not all_words: raise Exception("Tidak ada dialog terdeteksi.")

        # AI CUTTING LOGIC
        first_word_start = all_words[0]['start']
        last_word_end = all_words[-1]['end']
        trim_start = max(0, first_word_start - 0.1)
        trim_end = last_word_end + 0.1

        # 3. SUBTITLE (Emas & Elegan)
        ass_path = f"style_{job_id}.ass"
        
        # Style: Gold Color (&H0000D7FF), Font Besar (75), Outline Tebal (3)
        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: NeonStyle,Arial Black,75,&H0000D7FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,0,2,10,10,{subtitle_pos},1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(header)
            
            SPEED_FACTOR = 1.05 
            
            for i in range(0, len(all_words), 3): 
                chunk = all_words[i : i + 3]
                if not chunk: continue
                
                s_shifted = (chunk[0]["start"] - trim_start) / SPEED_FACTOR
                e_shifted = (chunk[-1]["end"] - trim_start) / SPEED_FACTOR
                
                s_str = format_timestamp_ass(s_shifted)
                e_str = format_timestamp_ass(e_shifted)
                text = "".join([w["word"] for w in chunk]).strip().upper()
                
                f.write(f"Dialogue: 0,{s_str},{e_str},NeonStyle,,0,0,0,,{{\\blur15\\bord3\\shad1}} {text}\n")

        # 4. RENDER (Anti-Copyright: Mirror + Speed 1.05x + Saturation)
        jobs_dict[job_id]["status"] = "rendering_final"
        final_output = f"{output_dir}/{job_id}.mp4"
        abs_ass = os.path.abspath(ass_path).replace("\\", "/").replace(":", "\\:")
        
        filter_complex = (
            f"[0:v]trim=start={trim_start}:end={trim_end},setpts=PTS-STARTPTS,"
            f"hflip,setpts=PTS/1.05,"
            f"eq=saturation=1.2:contrast=1.05[vproc];" 
            
            f"[0:a]atrim=start={trim_start}:end={trim_end},asetpts=PTS-STARTPTS,"
            f"atempo=1.05[aproc];"
            
            f"[vproc]split=2[a][b];" 
            f"[a]scale=-1:1920,crop=1080:1920,boxblur=20:10[bg];"
            f"[b]scale=1080:-1[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[merged];"
            f"[merged]ass='{abs_ass}'[outv]"
        )
        
        subprocess.run([
            "ffmpeg", "-i", temp_name, 
            "-filter_complex", filter_complex, 
            "-map", "[outv]", "-map", "[aproc]", 
            "-c:v", "libx264", "-preset", "fast", "-crf", "20", 
            "-c:a", "aac", "-b:a", "128k", 
            "-y", final_output
        ], check=True)

        if os.path.exists(temp_name): os.remove(temp_name)
        if os.path.exists(ass_path): os.remove(ass_path)
        return True

    except Exception as e:
        jobs_dict[job_id]["status"] = f"error: {str(e)}"
        return False