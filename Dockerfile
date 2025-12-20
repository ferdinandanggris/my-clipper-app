# 1. Gunakan Base Image Python yang ringan (Linux Debian)
FROM python:3.10-slim

# 2. Install System Dependencies (Wajib ada FFmpeg & Git)
# Kita juga membersihkan cache apt agar image lebih kecil
RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 3. Set folder kerja di dalam container
WORKDIR /app

# 4. Copy file requirements dulu (agar caching layer docker efisien)
COPY requirements.txt .

# 5. Install Library Python
# --no-cache-dir agar tidak menyimpan file mentahan (hemat space)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. Copy seluruh kode project ke dalam container
COPY . .

# 7. (Opsional) Buat folder static/results jika belum ada
RUN mkdir -p static/results

# 8. Perintah untuk menjalankan aplikasi saat container start
# Host 0.0.0.0 WAJIB agar bisa diakses dari luar container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]