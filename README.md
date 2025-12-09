# 🎬 AI Video Clipper (Viral Shorts Generator)

Tools otomatis untuk mengubah video panjang (Podcast/Interview) menjadi video pendek vertikal (9:16) ala TikTok/Shorts dengan subtitle gaya **"Neon/Glow"** dan background blur.

**Fitur Utama:**
* ✅ **Anti-Blokir YouTube:** Menggunakan metode manual & cookies untuk menghindari error 429.
* ✅ **Tanpa API Key Berbayar:** Menggunakan workflow manual (Copy Transkrip -> ChatGPT) agar hemat biaya.
* ✅ **Neon Subtitles:** Auto-generate subtitle dengan efek glow, outline tebal, dan font rapi.
* ✅ **Blur Background:** Otomatis mengisi ruang kosong video vertikal dengan blur.
* ✅ **Docker Ready:** Siap deploy ke Railway/Render.

---

## 🛠️ Persiapan (Prerequisites)

Sebelum menjalankan, pastikan komputer Anda memiliki:
1.  **Python 3.9+**
2.  **FFmpeg** (Wajib terinstall dan masuk PATH).
    * *Mac:* `brew install ffmpeg`
    * *Windows:* [Download & Install FFmpeg](https://ffmpeg.org/download.html)
3.  **Google Chrome** (Untuk mengambil Cookies).

---

## 🚀 Instalasi Lokal

1.  **Clone Repository**
    ```bash
    git clone [https://github.com/username-anda/ai-clipper-web.git](https://github.com/username-anda/ai-clipper-web.git)
    cd ai-clipper-web
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **🔑 PENTING: Setup Cookies YouTube**
    Agar server tidak diblokir YouTube (Error: *Sign in to confirm you’re not a bot*), Anda wajib menyediakan file cookies.
    1.  Install ekstensi Chrome **"Get cookies.txt LOCALLY"**.
    2.  Buka [YouTube.com](https://www.youtube.com) dan pastikan sudah Login.
    3.  Klik ekstensi tersebut -> **Export**.
    4.  Rename file hasil download menjadi `cookies.txt`.
    5.  Pindahkan file `cookies.txt` ke dalam folder project ini (sejajar dengan `main.py`).

4.  **Jalankan Server**
    ```bash
    python -m uvicorn main:app --reload
    ```
    Akses web app di: `http://127.0.0.1:8000`

---

## 📖 Cara Penggunaan (Workflow)

Aplikasi ini menggunakan metode **"Curi Transkrip"** agar gratis dan akurat.

### Langkah 1: Pasang Tombol Curi Transkrip
Di halaman utama Web App (`http://127.0.0.1:8000`), ada tombol merah **"✂️ CURI TRANSKRIP"**.
* **Drag & Drop** tombol tersebut ke **Bookmarks Bar** browser Anda.

### Langkah 2: Cari Bahan
1.  Buka Video YouTube target.
2.  Buka Deskripsi -> Klik **Show Transcript**.
3.  Klik Bookmark **"Curi Transkrip"** yang tadi Anda pasang.
4.  Transkrip otomatis ter-copy!

### Langkah 3: Tanya AI (ChatGPT/Claude)
Paste transkrip tadi ke ChatGPT. Dia akan memberikan Timestamp viral.
> *Contoh Output AI: Start 00:14:20 - End 00:15:10*

### Langkah 4: Render Video
1.  Kembali ke Web App.
2.  Paste **Link YouTube**, **Start Time**, dan **End Time**.
3.  Klik **PROSES VIDEO**.
4.  Tunggu proses Download -> Transcribing -> Rendering.
5.  **Download** hasilnya!

---

## 🐳 Deployment (Docker)

Aplikasi ini siap deploy ke **Railway** atau **Render**.

### Struktur File Wajib:
Pastikan file ini ada sebelum push ke GitHub:
* `Dockerfile`
* `requirements.txt`
* `cookies.txt` (Jangan lupa `git add cookies.txt --force` jika pakai gitignore)

### Deploy ke Render.com (Gratis)
1.  Buat akun di [Render.com](https://render.com).
2.  New **Web Service** -> Connect GitHub Repo.
3.  Pilih **Runtime: Docker**.
4.  Pilih **Free Plan**.
5.  **Deploy**.

> **⚠️ Catatan untuk Server Gratis:**
> Server gratisan biasanya hanya punya RAM 512MB. Jika server crash/restart saat proses *Transcribing*, ubah model Whisper di `core_engine.py` menjadi **`tiny`**:
> `model = whisper.load_model("tiny")`

---

## 🔧 Troubleshooting

**Q: Error "Sign in to confirm you’re not a bot"?**
A: File `cookies.txt` Anda kadaluwarsa atau belum terupload. Ulangi langkah "Setup Cookies YouTube" di atas, lalu restart server/deploy ulang.

**Q: Error "FFmpeg not found"?**
A: Pastikan FFmpeg sudah terinstall di komputer Anda. Jika pakai Docker, pastikan `Dockerfile` Anda sudah berisi perintah install ffmpeg (`apt-get install -y ffmpeg`).

**Q: Transkrip AI salah/typo?**
A: Di `core_engine.py`, edit bagian `INITIAL_PROMPT`. Masukkan nama-nama tokoh atau istilah khusus di situ agar AI lebih paham konteks.

---

## 📝 License
Project ini dibuat untuk tujuan edukasi dan produktivitas pribadi.
