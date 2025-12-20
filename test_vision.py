import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import cv2
import mediapipe as mp
import sys

# --- CONFIG ---
# Ganti dengan nama file videomu yang ada 2 orangnya
VIDEO_PATH = "sample.mp4" 

# Inisialisasi MediaPipe Face Detection
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils

def run_vision_test():
    # Model selection 1 = Jarak jauh (Full body/Shot luas), 0 = Jarak dekat (Selfie/Webcam)
    # Untuk podcast/interview, biasanya model 1 lebih akurat.
    with mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.6) as face_detection:
        
        cap = cv2.VideoCapture(VIDEO_PATH)
        if not cap.isOpened():
            print(f"❌ Gagal membuka video: {VIDEO_PATH}")
            return

        # Ambil info video
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"ℹ️ Resolusi Video: {width}x{height}")

        while cap.isOpened():
            success, image = cap.read()
            if not success: break

            # 1. MediaPipe butuh gambar RGB, sedangkan OpenCV pakai BGR. Jadi harus dicorvert.
            image.flags.writeable = False
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # 2. INI PROSES DETEKSI AI-NYA
            results = face_detection.process(image_rgb)

            # Kembalikan ke BGR buat digambar
            image.flags.writeable = True
            image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

            if results.detections:
                # Kumpulkan semua wajah yang ketemu
                faces_data = []
                
                for detection in results.detections:
                    # MediaPipe kasih koordinat RELATIF (0.0 sampai 1.0)
                    # Kita harus kali dengan lebar/tinggi video biar jadi PIXEL.
                    bboxC = detection.location_data.relative_bounding_box
                    x = int(bboxC.xmin * width)
                    y = int(bboxC.ymin * height)
                    w = int(bboxC.width * width)
                    h = int(bboxC.height * height)
                    
                    # Hitung Skor Kepercayaan (Confidence)
                    score = detection.score[0]
                    
                    # Simpan data
                    faces_data.append({
                        "box": (x, y, w, h),
                        "center": x + (w/2),
                        "area": w * h,
                        "score": score
                    })

                    # GAMBAR KOTAK WAJAH (MERAH)
                    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    cv2.putText(image, f"{int(score*100)}%", (x, y - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                # --- LOGIKA CERDAS: PILIH SATU WAJAH ---
                # Urutkan berdasarkan Luas Area Terbesar (Yg paling dekat kamera / dominan)
                faces_data.sort(key=lambda x: x["area"], reverse=True)
                
                if faces_data:
                    main_face = faces_data[0]
                    cx = int(main_face["center"])
                    
                    # Simulasi Crop 9:16 (Vertikal)
                    # Lebar crop target (misal tinggi 1920, lebar 1080)
                    # Kita simulasi aspect ratio saja
                    crop_w = int(height * (9/16)) 
                    crop_x_start = int(cx - (crop_w / 2))
                    
                    # Gambar KOTAK CROP (HIJAU) - Ini yang akan jadi layar HP
                    cv2.rectangle(image, (crop_x_start, 0), (crop_x_start + crop_w, height), (0, 255, 0), 3)
                    cv2.putText(image, "KAMERA (CROP AREA)", (crop_x_start + 10, 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    # Tanda + di tengah wajah utama
                    cv2.drawMarker(image, (cx, int(main_face["box"][1] + main_face["box"][3]/2)), 
                                   (0, 255, 0), markerType=cv2.MARKER_CROSS, thickness=3)

            # Tampilkan Video di Layar (Tekan Q untuk keluar)
            # Resize dikit biar muat di layar laptop kalau videonya 4K
            display_h = 800
            scale = display_h / height
            display_w = int(width * scale)
            display_img = cv2.resize(image, (display_w, display_h))
            
            cv2.imshow('Belajar Vision AI - MediaPipe', display_img)
            if cv2.waitKey(5) & 0xFF == 27: # Tekan ESC buat stop
                break
        
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # Pastikan file video ada
    import os
    if not os.path.exists(VIDEO_PATH):
        print(f"⚠️ File '{VIDEO_PATH}' tidak ditemukan. Ganti variabel VIDEO_PATH di dalam script.")
    else:
        run_vision_test()