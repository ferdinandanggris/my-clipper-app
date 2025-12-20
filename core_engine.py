import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import yt_dlp
import whisper
import subprocess
import cv2
import sys
import shutil
import mediapipe as mp
import glob # Buat cari file raw dengan ekstensi apa aja

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

# --- 1. VISION AI (STICKY MODE - TOLERANCE 100px) ---
def analyze_face_track(video_path, duration):
    print(f"👀 AI Vision: Scanning '{video_path}'...")
    mp_face_detection = mp.solutions.face_detection
    try:
        with mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.2) as face_detection:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened(): return []
            raw_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            raw_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            if not fps or fps == 0: fps = 30
            target_crop_w = int((raw_h * 9) / 16)
            last_face_center = None 
            frame_data = [] 
            frame_idx = 0
            while cap.isOpened():
                success, image = cap.read()
                if not success: break
                if frame_idx % 60 == 0: print(f"   -> Scanning frame {frame_idx}...")
                image.flags.writeable = False
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                results = face_detection.process(image_rgb)
                final_center = None
                if results.detections:
                    faces_data = []
                    for detection in results.detections:
                        bboxC = detection.location_data.relative_bounding_box
                        w = int(bboxC.width * raw_w)
                        h = int(bboxC.height * raw_h)
                        x = int(bboxC.xmin * raw_w)
                        center_x = x + (w / 2)
                        area = w * h
                        faces_data.append({"center": center_x, "area": area})
                    faces_data.sort(key=lambda x: x["area"], reverse=True)
                    candidate_face = faces_data[0]
                    final_center = candidate_face["center"]
                    if last_face_center is not None:
                        dist_to_candidate = abs(candidate_face["center"] - last_face_center)
                        if dist_to_candidate > 200:
                            old_face_found = None
                            for f in faces_data:
                                if abs(f["center"] - last_face_center) < 200:
                                    old_face_found = f
                                    break
                            if old_face_found:
                                ratio = candidate_face["area"] / old_face_found["area"]
                                if ratio > 1.5: final_center = candidate_face["center"]
                                else: final_center = old_face_found["center"]
                            else: final_center = candidate_face["center"]
                    last_face_center = final_center
                else:
                    if last_face_center: final_center = last_face_center
                    else: final_center = raw_w / 2
                crop_x = int(final_center - (target_crop_w / 2))
                crop_x = max(0, min(raw_w - target_crop_w, crop_x))
                current_time = frame_idx / fps
                frame_data.append({"time": current_time, "x_pixel": crop_x})
                frame_idx += 1
            cap.release()
            if not frame_data: return []
            optimized_chunks = []
            interval_frames = int(fps * 0.5)
            for i in range(0, len(frame_data), interval_frames):
                optimized_chunks.append(frame_data[i])
            if frame_data[-1] != optimized_chunks[-1]:
                optimized_chunks.append(frame_data[-1])
            final_filtered = [optimized_chunks[0]]
            last_val = optimized_chunks[0]["x_pixel"]
            for pt in optimized_chunks[1:]:
                if abs(pt["x_pixel"] - last_val) > 100: 
                    final_filtered.append(pt)
                    last_val = pt["x_pixel"]
            return final_filtered
    except Exception as e:
        print(f"❌ Vision Error: {e}")
        return []

# --- 2. CORE ENGINE ---
def process_video_task(job_id, url, start, end, output_dir, jobs_dict, subtitle_pos=300):
    cwd = os.getcwd()
    # Definisi nama file
    cut_video = f"cut_{job_id}.mp4"
    audio_track = f"audio_{job_id}.m4a"
    visual_video = f"visual_{job_id}.mp4"
    stage_1_video = f"stage1_{job_id}.mp4"
    ass_file = f"style_{job_id}.ass"
    concat_list_file = f"concat_{job_id}.txt"
    chunks_dir = f"chunks_{job_id}"
    final_video = os.path.join(os.path.abspath(output_dir), f"{job_id}.mp4")

    # Variabel deteksi raw
    detected_raw = None

    try:
        jobs_dict[job_id]["status"] = "processing_download"
        
        # Bersih-bersih awal (Pre-clean)
        if os.path.exists(chunks_dir): shutil.rmtree(chunks_dir)
        for f in [cut_video, audio_track, visual_video, stage_1_video, ass_file, final_video, concat_list_file]:
            if os.path.exists(f): os.remove(f)
        # Hapus sisa raw lama
        for f in glob.glob(f"raw_{job_id}.*"): os.remove(f)

        start_sec = parse_time(str(start))
        end_sec = parse_time(str(end))
        duration = end_sec - start_sec

        # 1. DOWNLOAD (HIGHEST QUALITY - ANDROID CLIENT)
        print(f"📥 [STEP 1] Downloading Highest Quality...")
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best', 
            'merge_output_format': 'mp4',
            'outtmpl': f"raw_{job_id}.%(ext)s",
            'quiet': True, 
            'nocheckcertificate': True,
            'extractor_args': {'youtube': {'player_client': ['android']}}, 
            'user_agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([url])
            
        # Cari file raw yang barusan didownload
        raw_candidates = glob.glob(f"raw_{job_id}.*")
        if raw_candidates: detected_raw = raw_candidates[0]
        else: raise Exception("Download gagal, file raw tidak ditemukan.")
            
        print(f"✅ Downloaded: {detected_raw}")

        # 1.5 TRIMMING & AUDIO EXTRACT
        print(f"🔪 [STEP 1.5] Preparing Media...")
        cmd_trim = [
            "ffmpeg", "-ss", str(start), "-to", str(end), 
            "-i", detected_raw, 
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "16", 
            "-c:a", "copy", "-y", cut_video
        ]
        subprocess.run(cmd_trim, check=True, stderr=subprocess.DEVNULL)

        cmd_extract_audio = [
            "ffmpeg", "-i", cut_video, "-vn", "-acodec", "copy", "-y", audio_track
        ]
        subprocess.run(cmd_extract_audio, check=True, stderr=subprocess.DEVNULL)

        # 2. ANALYZE
        points = analyze_face_track(cut_video, duration) 
        if not points: points = [{"time": 0, "x_pixel": 0}] 

        # 3. RENDER VISUAL (AGGRESSIVE SHARPENING)
        print(f"✂️ [STEP 2] Rendering Visual Pop Segments...")
        os.makedirs(chunks_dir, exist_ok=True)
        chunk_files = []
        cap_temp = cv2.VideoCapture(cut_video)
        video_h = int(cap_temp.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap_temp.release()
        native_crop_w = int((video_h * 9) / 16)

        for i in range(len(points)):
            current_pt = points[i]
            chunk_start = current_pt["time"] 
            if i < len(points) - 1: chunk_duration = points[i+1]["time"] - chunk_start
            else: chunk_duration = duration - chunk_start
            if chunk_duration <= 0: continue

            crop_x = current_pt["x_pixel"]
            chunk_filename = os.path.join(chunks_dir, f"chunk_{i:03d}.mp4")
            
            filter_chunk = (
                f"crop={native_crop_w}:{video_h}:{crop_x}:0,"
                f"scale=1080:1920:flags=lanczos," 
                f"unsharp=7:7:1.5:7:7:0.0," 
                f"eq=saturation=1.2:contrast=1.1"
            )
            cmd_chunk = [
                "ffmpeg", "-ss", str(chunk_start), "-t", str(chunk_duration),
                "-i", cut_video, "-vf", filter_chunk,
                "-c:v", "libx264", "-preset", "slow", "-b:v", "8000k",
                "-pix_fmt", "yuv420p", "-an", "-y", chunk_filename
            ]
            res = subprocess.run(cmd_chunk, stderr=subprocess.DEVNULL)
            if res.returncode == 0:
                chunk_files.append(chunk_filename)
                print(f"   -> Chunk {i+1}: {chunk_duration}s (Visual Pop)")

        # 4. CONCAT
        print("🔗 [STEP 2.5] Merging...")
        with open(concat_list_file, "w") as f:
            for cf in chunk_files:
                clean_path = cf.replace("\\", "/")
                f.write(f"file '{clean_path}'\n")
        cmd_concat = [
            "ffmpeg", "-f", "concat", "-safe", "0", 
            "-i", concat_list_file, "-c", "copy", "-y", visual_video
        ]
        subprocess.run(cmd_concat, check=True, stderr=subprocess.DEVNULL)

        # 4.5 MERGE
        print("🔊 [STEP 2.8] Syncing Audio...")
        cmd_merge = [
            "ffmpeg", "-i", visual_video, "-i", audio_track,
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-map", "0:v:0", "-map", "1:a:0", "-shortest", "-y", stage_1_video
        ]
        subprocess.run(cmd_merge, check=True, stderr=subprocess.DEVNULL)

        # 5. TRANSCRIBE
        print("🎤 [STEP 3] Transcribing...")
        jobs_dict[job_id]["status"] = "transcribing_ai"
        model = whisper.load_model("small") 
        result = model.transcribe(os.path.abspath(audio_track), fp16=False, word_timestamps=True)
        all_words = []
        for segment in result["segments"]: all_words.extend(segment.get("words", []))
            
        if not all_words: 
            shutil.copy(stage_1_video, final_video)
            return True # Langsung ke finally

        # 6. SUBTITLE
        print("📝 [STEP 4] Subtitles...")
        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: NeonStyle,Arial,75,&H0000D7FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,0,2,10,10,{subtitle_pos},1
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

        # 7. FINAL RENDER
        print("🔥 [STEP 5] Burning...")
        jobs_dict[job_id]["status"] = "rendering_final"
        cmd_stage_2 = [
            "ffmpeg", "-i", stage_1_video, "-vf", f"ass={os.path.basename(ass_file)}", 
            "-c:v", "libx264", "-preset", "slow", "-b:v", "8000k",
            "-pix_fmt", "yuv420p", "-c:a", "copy", "-y", final_video
        ]
        res2 = subprocess.run(cmd_stage_2, stderr=subprocess.PIPE, text=True, cwd=cwd)
        if res2.returncode != 0:
            shutil.copy(stage_1_video, final_video) # Fallback

        print("✅ SUCCESS!")
        return True

    except Exception as e:
        jobs_dict[job_id]["status"] = f"error: {str(e)}"
        print(f"❌ Core Error: {e}")
        return False
    
    finally:
        # --- CLEANUP WAJIB (Jalan Baik Sukses maupun Gagal) ---
        print("🧹 Cleaning up temporary files...")
        
        # 1. Hapus Raw Video (Apapun ekstensinya)
        for f in glob.glob(f"raw_{job_id}.*"):
            try: os.remove(f)
            except: pass

        # 2. Hapus File Intermediate
        for f in [cut_video, audio_track, visual_video, stage_1_video, ass_file, concat_list_file]:
            try:
                if os.path.exists(f): os.remove(f)
            except: pass
        
        # 3. Hapus Folder Chunks
        try:
            if os.path.exists(chunks_dir): shutil.rmtree(chunks_dir)
        except: pass
        
        print("✨ Workspace Cleaned.")