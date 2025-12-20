import subprocess
import os

def run_test(name, cmd):
    print(f"\n🧪 TEST {name} SEDANG DIJALANKAN...")
    try:
        # Jalankan FFmpeg dan tangkap outputnya
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ TEST {name}: BERHASIL!")
            return True
        else:
            print(f"❌ TEST {name}: GAGAL (Code {result.returncode})")
            # Tampilkan 10 baris terakhir error log
            error_log = result.stderr.split('\n')
            print("--- LOG ERROR (Lihat di bawah) ---")
            for line in error_log[-10:]:
                print(line)
            print("----------------------------------")
            return False
    except Exception as e:
        print(f"❌ TEST {name}: ERROR PYTHON -> {e}")
        return False

if __name__ == "__main__":
    print("=== MULAI DIAGNOSA FFMPEG ===")
    
    # Bersihkan file lama
    for f in ["test1.mp4", "test2.mp4", "test3.mp4", "dummy.ass"]:
        if os.path.exists(f): os.remove(f)

    # --- TES 1: GENERATE VIDEO (Cek Codec libx264) ---
    # Kita bikin video kotak hitam 5 detik
    cmd1 = [
        "ffmpeg", "-f", "lavfi", "-i", "testsrc=duration=5:size=1280x720:rate=30",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-y", "test1.mp4"
    ]
    if not run_test("1 (Generate Video)", cmd1):
        print("\n🛑 KESIMPULAN: FFmpeg Anda rusak parah. Tidak bisa bikin video MP4.")
        exit()

    # --- TES 2: CROP & SCALE (Cek Filter Video) ---
    cmd2 = [
        "ffmpeg", "-i", "test1.mp4",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-y", "test2.mp4"
    ]
    if not run_test("2 (Crop & Scale)", cmd2):
        print("\n🛑 KESIMPULAN: FFmpeg Anda tidak support filter scale/crop.")
        exit()

    # --- TES 3: SUBTITLE (Cek Library Font/Ass) ---
    # Bikin file subtitle dummy
    with open("dummy.ass", "w") as f:
        f.write("""[Script Info]
ScriptType: v4.00+
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,1,0,2,10,10,10,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,TESTING SUBTITLE
""")

    cmd3 = [
        "ffmpeg", "-i", "test2.mp4",
        "-vf", "ass=dummy.ass",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-y", "test3.mp4"
    ]
    if not run_test("3 (Burn Subtitle)", cmd3):
        print("\n🛑 KESIMPULAN: Masalahnya FIX di Library Subtitle/Font!")
        print("FFmpeg Mac Anda tidak support filter 'ass' atau tidak bisa baca Font.")
    else:
        print("\n🎉 SEMUA TES BERHASIL! Aneh, harusnya core_engine juga bisa.")

    print("\n=== DIAGNOSA SELESAI ===")