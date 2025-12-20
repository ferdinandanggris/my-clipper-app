import mediapipe
import os

print("\n=== LAPORAN DETEKTIF ===")
print(f"📂 Lokasi file mediapipe yang diload: {mediapipe.__file__}")
print(f"📂 Folder kerja saat ini: {os.getcwd()}")
print("========================\n")

try:
    print(f"Apakah punya 'solutions'? {mediapipe.solutions}")
except AttributeError:
    print("❌ TIDAK PUNYA 'solutions'. Ini file palsu/konflik!")