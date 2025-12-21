FROM python:3.10-slim

# 1. Install alat sistem (Hanya jalan sekali, selamanya di-cache)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. COPY requirements DULU
# Ini kunci rahasianya. Selama isi file ini tidak berubah, 
# Docker TIDAK AKAN download ulang library meskipun kodemu berubah.
COPY requirements.txt .

# 3. Jalankan pip install
RUN pip install --no-cache-dir -r requirements.txt

# 4. Baru COPY seluruh kode
# Kode ditaruh paling bawah karena paling sering diubah.
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]