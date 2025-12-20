# 🎬 AI Smart Clipper (Pro Edition)

**AI Smart Clipper** adalah tool otomatis "All-in-One" untuk mengubah video panjang (Podcast/Interview) menjadi konten **Shorts/TikTok viral** secara instan.

Didukung oleh **Google Gemini 2.5** (Otak) dan **FFmpeg** (Otot), tool ini aman, cepat, dan sekarang dilengkapi fitur keamanan standar industri (Environment Variables).

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Gemini](https://img.shields.io/badge/AI-Gemini%202.5-orange)
![Security](https://img.shields.io/badge/Config-.env-red)

---

## 🔥 Fitur Utama

### 🧠 1. AI Auto-Pilot (Gemini 2.5)
* **Auto-Detect Viral Clip:** AI membaca transkrip 1 jam dan memilih 30-60 detik bagian paling "daging".
* **Smart Captioning:** Membuat Judul Clickbait & Deskripsi + 3-5 Hashtag Viral.
* **Multi-Language Support:**
    * 🇮🇩 **Indo Mode:** Bahasa gaul/santai.
    * 🇺🇸 **English Mode:** Slang & Global hook style.
* **Custom Niche:** Targetkan topik spesifik (Crypto, Horror, Motivation).

### 🎨 2. Visual & Editing Otomatis
* **9:16 Vertical Crop:** Video landscape jadi portrait otomatis.
* **Gold Subtitles:** Subtitle emas ala "Hormozi" (Word-level timestamps).
* **Anti-Copyright:** Speed up 1.05x dan color grading otomatis.

### 📱 3. Pro Web UI
* **Live Preview:** Mockup layar HP Real-time (memastikan subtitle tidak tertutup caption).
* **Split Layout:** Tampilan 2 kolom profesional.
* **Manual Tools:** Tombol Copy Judul, Caption, dan Ekstrak Transkrip Full.

---

## 🛠️ Persiapan (Wajib)

Sebelum install, pastikan Anda memiliki:

1.  **FFmpeg** (Wajib terinstall di sistem).
    * *Windows:* Download dari ffmpeg.org & masukkan ke PATH.
    * *Ubuntu:* `sudo apt install ffmpeg`
    * *Mac:* `brew install ffmpeg`
2.  **API Key Google Gemini** (Gratis via [Google AI Studio](https://aistudio.google.com/)).
3.  **File `cookies.txt`** (Untuk login YouTube).
    * Gunakan ekstensi Chrome "Get cookies.txt LOCALLY".
    * Login YouTube, download, simpan file sebagai `cookies.txt` di folder project.

---

## 🚀 Cara Install & Jalanin

### A. Cara Lokal (Windows/Mac/Linux)

1.  **Clone Project**
    ```bash
    git clone [https://github.com/username/ai-clipper.git](https://github.com/username/ai-clipper.git)
    cd ai-clipper
    ```

2.  **Setup Environment (PENTING!)**
    Buat file bernama `.env` di folder root, lalu isi dengan API Key Anda:
    ```env
    GOOGLE_API_KEY=AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    ```
    *(Jangan pakai tanda kutip, jangan ada spasi)*

3.  **Install Dependencies**
    ```bash
    python -m venv venv
    # Windows: venv\Scripts\activate
    # Mac/Linux: source venv/bin/activate
    
    pip install -r requirements.txt
    ```

4.  **Jalankan Server**
    ```bash
    python -m uvicorn main:app --reload
    ```
    Buka browser: `http://127.0.0.1:8000`

---

### B. Cara Server (Docker / Ubuntu VPS)

Gunakan metode ini agar aman saat deploy (Key diambil dari file .env).

1.  **Build Image**
    ```bash
    sudo docker build -t ai-clipper .
    ```

2.  **Run Container**
    Kita gunakan flag `--env-file .env` agar Docker membaca kunci rahasia Anda.
    
    ```bash
    # Buat folder output dulu
    mkdir -p static/results
    
    # Jalankan
    sudo docker run -d \
      --name clipper-container \
      --restart unless-stopped \
      --env-file .env \
      -p 8080:8080 \
      -v $(pwd)/static/results:/app/static/results \
      -v $(pwd)/cookies.txt:/app/cookies.txt \
      ai-clipper
    ```
    *(Note: Kita juga me-mount `cookies.txt` agar tidak perlu copy-paste ke dalam image)*.

3.  Akses via IP VPS: `http://IP_SERVER_ANDA:8080`

---

## 📂 Struktur Project Aman

Project ini sudah dikonfigurasi agar file rahasia **TIDAK** ter-upload ke GitHub.

* `.env` -> **RAHASIA** (API Key disimpan di sini).
* `cookies.txt` -> **RAHASIA** (Login YouTube disimpan di sini).
* `.gitignore` -> File yang memberitahu Git untuk mengabaikan 2 file di atas.
* `main.py` -> Server Pusat.
* `ai_brain.py` -> Otak AI (Sekarang membaca Key dari .env).
* `static/` -> UI Frontend.

---

## ❓ Troubleshooting

**Q: Error `ValueError: API Key tidak ditemukan`?**
A: Anda lupa membuat file `.env` atau namanya salah (harus `.env` saja, bukan `.env.txt`).

**Q: Error 403 Forbidden saat download?**
A: `cookies.txt` kadaluwarsa. Download ulang dari browser (fresh login).

**Q: Video tidak muncul di tombol download?**
A: Cek folder `static/results`. Pastikan FFmpeg terinstall dengan benar.

---

### Credits
Dibuat untuk otomatisasi konten viral. Gunakan dengan bijak! 🚀