# --- WAJIB DI PALING ATAS ---
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import cv2
import mediapipe as mp
import sys

# GANTI INI DENGAN NAMA FILE VIDEO YANG HASILNYA JELEK TADI
VIDEO_PATH = "testing.mp4" 
OUTPUT_PATH = "debug_output.mp4"

def run_debug():
    print(f"🕵️‍♂️ Memulai Debugging pada: {VIDEO_PATH}")
    
    mp_face_detection = mp.solutions.face_detection
    
    # KITA COBA TURUNKAN CONFIDENCE JADI 0.2 (Sangat Sensitif)
    # DAN GANTI MODEL KE 0 (Jarak Dekat) kalau videonya close-up
    with mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.2) as face_detection:
        
        cap = cv2.VideoCapture(VIDEO_PATH)
        if not cap.isOpened():
            print("❌ Video tidak ditemukan!")
            return

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Setup Video Writer untuk simpan hasil debug
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(OUTPUT_PATH, fourcc, fps, (width, height))
        
        scale_factor = 1920 / height
        scaled_w = int(width * scale_factor)

        last_face_center = None

        print("🎬 Sedang merender video debug... (Tunggu sebentar)")
        
        frame_count = 0
        while cap.isOpened():
            success, image = cap.read()
            if not success: break
            
            frame_count += 1
            if frame_count % 30 == 0: print(f"Processing frame {frame_count}...")

            # Proses AI
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = face_detection.process(image_rgb)
            
            final_center = None
            is_face_found = False

            if results.detections:
                is_face_found = True
                faces_data = []
                
                for detection in results.detections:
                    bboxC = detection.location_data.relative_bounding_box
                    w = int(bboxC.width * width)
                    h = int(bboxC.height * height)
                    x = int(bboxC.xmin * width)
                    y = int(bboxC.ymin * height)
                    center_x = x + (w / 2)
                    
                    # GAMBAR KOTAK MERAH DI WAJAH
                    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    
                    faces_data.append({"center": center_x, "area": w*h})

                # LOGIC PILIH WAJAH (Sama seperti Core Engine)
                faces_data.sort(key=lambda x: x["area"], reverse=True)
                candidate = faces_data[0]
                final_center = candidate["center"]

                if last_face_center is not None:
                    dist = abs(candidate["center"] - last_face_center)
                    if dist > 150:
                        # Logic Smart Switch Visualized
                        old_face_found = None
                        for f in faces_data:
                            if abs(f["center"] - last_face_center) < 150:
                                old_face_found = f
                                break
                        
                        if old_face_found:
                            ratio = candidate["area"] / old_face_found["area"]
                            if ratio < 1.3:
                                final_center = old_face_found["center"]
                                cv2.putText(image, "HOLD POS", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,255), 2)
                            else:
                                cv2.putText(image, "SWITCH!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

                last_face_center = final_center

            else:
                # KALO GAK ADA WAJAH
                cv2.putText(image, "NO FACE DETECTED", (50, height//2), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2)
                if last_face_center:
                    final_center = last_face_center
                else:
                    final_center = width / 2 # Default Tengah

            # HITUNG POSISI CROP
            # Kita simulasi crop 9:16 di video landscape
            # Rumus crop width relatif terhadap layar asli:
            # CropW_Asli = (1080 / 1920) * height = 0.5625 * height
            crop_w_real = int(height * (9/16))
            
            # Hitung Top-Left X biar final_center ada di tengah crop
            crop_x = int(final_center - (crop_w_real / 2))
            
            # Clamp
            crop_x = max(0, crop_x)
            crop_x = min(width - crop_w_real, crop_x)

            # GAMBAR KOTAK HIJAU (AREA YANG AKAN DIAMBIL)
            cv2.rectangle(image, (crop_x, 0), (crop_x + crop_w_real, height), (0, 255, 0), 4)
            cv2.line(image, (int(final_center), 0), (int(final_center), height), (0, 255, 0), 1)

            out.write(image)

        cap.release()
        out.release()
        print(f"✅ Selesai! Cek file video: {OUTPUT_PATH}")

if __name__ == "__main__":
    run_debug()