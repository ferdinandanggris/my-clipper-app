# 🎬 AI Smart Clipper Pro

**AI Smart Clipper Pro** adalah aplikasi web modern berbasis Python yang mengubah video panjang (Podcast, Interview, Talkshow) dari YouTube menjadi video pendek vertikal (Shorts, Reels, TikTok) secara otomatis dengan kualitas tinggi.

Sistem ini memiliki dua mesin render canggih: **AI Face Tracking** (untuk video ngobrol) dan **Cinema Blur** (untuk gaya repost).

---

## ✨ Fitur Utama

### 1. Dual Engine Technology 🎥
Pilih gaya video output sesuai kebutuhan melalui Web UI:
- **📱 Vertical AI Crop:** Menggunakan **MediaPipe** untuk mendeteksi wajah pembicara, melakukan zoom otomatis, dan menjaga subjek tetap di tengah frame (Smart Tracking).
- **🌫️ Horizontal + Blur:** Menampilkan video asli secara utuh di tengah dengan latar belakang blur (*Cinematic Background*), cocok untuk video tutorial atau gaming.

### 2. High Quality Production 💎
- **4K/1080p Download:** Menggunakan algoritma *Android Client Spoofing* untuk mengunduh source video kualitas tertinggi dari YouTube tanpa error 403.
- **Visual Pop:** Otomatis menerapkan *Sharpening (Lanczos)* dan *Color Grading* agar video terlihat tajam dan cerah di layar HP.
- **Audio Bypass:** Menjamin sinkronisasi bibir (*Lip-sync*) 100% akurat dan kualitas audio asli (tanpa kompresi ulang yang merusak).

### 3. Otomatisasi Cerdas 🧠
- **Auto Subtitle:** Transkripsi otomatis menggunakan **OpenAI Whisper** dengan gaya subtitle "Karaoke/Neon" yang viral.
- **Auto Cleanup:** Sistem otomatis membersihkan file sampah (*raw/cache*) setelah proses selesai (sukses maupun gagal), menjaga penyimpanan server tetap aman.

---

## 🛠️ Persiapan Sistem (Prerequisites)

Sebelum menginstall, pastikan perangkat kamu memenuhi syarat berikut:

### 1. Python 3.10 (Wajib)
Library MediaPipe berjalan paling stabil di Python 3.10. Hindari Python 3.12 untuk saat ini karena isu kompatibilitas.
- Cek versi: `python --version`

### 2. FFmpeg (Wajib)
Aplikasi ini membutuhkan FFmpeg di level sistem untuk memproses video.

- **Windows:**
  1. Download build terbaru di [ffmpeg.org](https://ffmpeg.org/download.html).
  2. Extract, lalu masukkan path folder `/bin` ke dalam **Environment Variables (PATH)** Windows.
  3. Verifikasi di CMD: `ffmpeg -version`.
  
- **Mac (macOS):**
  ```bash
  brew install ffmpeg

```

* **Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install ffmpeg

```



---

## 🚀 Cara Install (Deploy)

### 1. Clone / Siapkan Folder

Buat folder baru (misal: `ai-clipper`) dan masukkan semua file project ke dalamnya.

### 2. Buat Virtual Environment (Venv)

Penting agar library tidak bentrok dengan sistem lain.

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate

```

**Mac / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate

```

### 3. Install Library

Jalankan perintah ini untuk menginstall semua dependensi:

```bash
pip install -r requirements.txt

```

*(Tunggu hingga selesai. Proses ini akan mendownload model Machine Learning Whisper & MediaPipe).*

---

## ▶️ Cara Menjalankan

1. Pastikan Virtual Environment sudah aktif.
2. Jalankan server backend:
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

```


3. Buka browser dan akses:
👉 **http://localhost:8000**

---

## 📁 Struktur Project

Pastikan susunan folder kamu terlihat seperti ini:

```text
/project-folder
│
├── main.py              # Backend Server (FastAPI)
├── core_engine.py       # Engine 1: Vertical AI (Face Tracking)
├── engine_blur.py       # Engine 2: Horizontal Blur Style
├── requirements.txt     # Daftar Library
├── README.md            # File Dokumen ini
│
└── static/
    ├── index.html       # Tampilan Web (Frontend)
    └── results/         # Folder Output Video (Otomatis dibuat)

```

---

## ⚠️ Troubleshooting (Masalah Umum)

**Q: Muncul error `HTTP Error 403: Forbidden` saat download?**
**A:** YouTube sering memblokir bot. Script ini sudah menggunakan *User Agent Android* untuk menembusnya. Jika masih error, coba update `yt-dlp`:

```bash
pip install -U yt-dlp

```

**Q: Error `UserWarning: SymbolDatabase.GetPrototype() is deprecated`?**
**A:** Ini peringatan wajar dari Google Protobuf. Hiraukan saja, aplikasi tetap berjalan normal. Kode sudah memiliki penanganan otomatis (`os.environ`).

**Q: Video hasilnya patah-patah atau tidak ada wajah?**
**A:** Pada mode *Vertical*, pastikan video sumber memiliki wajah manusia yang jelas. Jika tidak ada wajah, sistem akan default ke tengah.

**Q: Error `returned non-zero exit status 234` pada mode Blur?**
**A:** Pastikan kamu menggunakan file `engine_blur.py` versi terbaru yang sudah menggunakan filter `split=2` dan `scale=1080:-2` untuk mengatasi bug dimensi ganjil pada FFmpeg.

---

## 📜 Lisensi & Credits

Dibuat dengan ❤️ menggunakan Python, OpenCV, dan FFmpeg.
