import os
import json
import gc
from deepface import DeepFace
import numpy as np
import sys

# --- CONFIG ---

if len(sys.argv) < 2:
    raise ValueError("You must provide the path to the input image as the first argument.")

input_image_path = sys.argv[1]
print(f"Using input image: {input_image_path}")

output_json_path = "AVATAR/analysis_result.json"
user_vector = [0.5, 0.9, 0.11, 0.1, 0.3, 0.1, 0.1, 0.26, 0.23, 0.8, 0.7, 0.23, 0.21, 0.02, 0.23, 0.52, 0.34, 0.2]
genres = ['Comedy','Art','Chill','Food','Social','Rock','Pop','Soul','Jazz','Electronic','Folk','Reggae','Hip-hop','Punk','Rap','Classical','Indie','Other']

# --- DEEPFACE ANALYSIS (no torch yet!) ---
def analyze_image():
    result = {}
    try:
        demography = DeepFace.analyze(input_image_path, actions=['gender', 'race'], enforce_detection=False)
        features = {
            "race": demography[0]['dominant_race'] if demography else "unknown",
            "gender": demography[0]['dominant_gender'] if demography else "unknown"
        }
        top_indices = np.argsort(user_vector)[-3:][::-1]
        features["top_genres"] = [(genres[i], user_vector[i]) for i in top_indices]
        result[os.path.basename(input_image_path)] = features
    except Exception as e:
        print(f"Error analyzing image: {e}")
        result[os.path.basename(input_image_path)] = {"race": "error", "gender": "error", "error": str(e)}

    with open(output_json_path, 'w') as f:
        json.dump(result, f)

    print("Demographic analysis saved.")

# --- RUN ---
if __name__ == "__main__":
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Fuerza CPU para evitar conflicto con PyTorch
    analyze_image()
    gc.collect()

