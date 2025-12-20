import google.generativeai as genai

# GANTI DENGAN API KEY ANDA
GOOGLE_API_KEY = "PASTE_API_KEY_DI_SINI"
genai.configure(api_key=GOOGLE_API_KEY)

print("🔍 Sedang mengecek daftar model yang tersedia...")

try:
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ Ditemukan: {m.name}")
            available_models.append(m.name)
            
    if not available_models:
        print("❌ Tidak ada model yang tersedia. Cek API Key atau Billing.")
    else:
        print(f"\n💡 Saran: Gunakan nama '{available_models[0]}' di script ai_brain.py")

except Exception as e:
    print(f"❌ Error Koneksi: {e}")