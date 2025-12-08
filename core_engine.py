import yt_dlp
import whisper
import os
import subprocess
import datetime

def parse_time(time_str):
    parts = list(map(int, time_str.split(':')))
    if len(parts) == 3: return parts[0] * 3600 + parts[1] * 60 + parts[2]
    elif len(parts) == 2: return parts[0] * 60 + parts[1]
    return parts[0]

def format_timestamp_ass(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centi = int((seconds - int(seconds)) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centi:02d}"

# Tambahkan parameter 'jobs_dict' untuk update status real-time
def process_video_task(job_id, url, start, end, output_dir, jobs_dict):
    try:
        # 1. DOWNLOAD
        jobs_dict[job_id] = "processing" # Status: Processing
        
        temp_name = f"raw_{job_id}.mp4"
        if os.path.exists(temp_name): os.remove(temp_name)

        opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': temp_name,
            'download_ranges': yt_dlp.utils.download_range_func(None, [(parse_time(start), parse_time(end))]),
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
            'force_keyframes_at_cuts': False, 'quiet': True, 'nocheckcertificate': True
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl: ydl.download([url])

        if not os.path.exists(temp_name): raise Exception("Download gagal")

        # 2. TRANSCRIBE
        jobs_dict[job_id] = "transcribing" # Status: Transcribing
        
        # Gunakan 'small' atau 'base' + Prompt agar akurat
        model = whisper.load_model("small") 
        INITIAL_PROMPT = "Podcast bisnis, investasi, saham, crypto, Indonesia, Inggris."
        result = model.transcribe(temp_name, fp16=False, word_timestamps=True, initial_prompt=INITIAL_PROMPT)
        
        ass_path = f"style_{job_id}.ass"
        # Style Neon (MarginV=300 sudah diterapkan)
        header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: NeonStyle,Arial Black,80,&H00FFFFFF,&H000000FF,&H00000000,&H60FFFFFF,-1,0,0,0,100,100,0,0,1,3,0,2,10,10,300,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(header)
            for segment in result["segments"]:
                words = segment.get("words", [])
                for i in range(0, len(words), 3):
                    chunk = words[i : i + 3]
                    if not chunk: continue
                    s = format_timestamp_ass(chunk[0]["start"])
                    e = format_timestamp_ass(chunk[-1]["end"])
                    t = "".join([w["word"] for w in chunk]).strip().upper()
                    f.write(f"Dialogue: 0,{s},{e},NeonStyle,,0,0,0,,{{\\blur15\\bord3\\shad1}} {t}\n")

        # 3. RENDER FFMPEG
        jobs_dict[job_id] = "rendering" # Status: Rendering
        
        final_output = f"{output_dir}/{job_id}.mp4"
        abs_ass = os.path.abspath(ass_path).replace("\\", "/").replace(":", "\\:")
        
        filter_complex = (
            f"[0:v]split=2[a][b];" 
            f"[a]scale=-1:1920,crop=1080:1920,boxblur=20:10[bg];"
            f"[b]scale=1080:-1[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[merged];"
            f"[merged]ass='{abs_ass}'"
        )
        
        subprocess.run(["ffmpeg", "-i", temp_name, "-filter_complex", filter_complex, 
                        "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-c:a", "copy", "-y", final_output], check=True)

        # Cleanup
        if os.path.exists(temp_name): os.remove(temp_name)
        if os.path.exists(ass_path): os.remove(ass_path)
        
        return True

    except Exception as e:
        print(f"Error Job {job_id}: {e}")
        jobs_dict[job_id] = f"error: {str(e)}"
        return False