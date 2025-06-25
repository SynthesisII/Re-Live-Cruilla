import subprocess
import sys
import os

# --- COMPROBAR ARGUMENTO ---
if len(sys.argv) < 2:
    raise ValueError("You must provide the path to the input image as the first argument.")

image_path = sys.argv[1]

if not os.path.exists(image_path):
    raise FileNotFoundError(f"Image not found at path: {image_path}")

# --- DEFINIR RUTAS ---
feature_extractor_path = "AVATAR/FeatureExtractor.py"
avatar_gen_path = "AVATAR/AvatarGen.py"

# --- EJECUTAR FeatureExtractor.py ---
print("\n🚀 Running FeatureExtractor.py...")
subprocess.run(["python", feature_extractor_path, image_path], check=True)

# --- EJECUTAR AvatarGen.py ---
print("\n🎨 Running AvatarGen.py...")
subprocess.run(["python", avatar_gen_path, image_path], check=True)

print("\n✅ Avatar generation complete.")
