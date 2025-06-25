import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from scipy.stats import pearsonr
from PIL import Image
import os
import matplotlib as plt

# ========================
# Evaluation & Similarity
# ========================

def evaluate(user_vector, head, torso, face, p1, p2, p3, p4):
    combo_vector = (head + torso + face) / 3

    cos_global = cosine_similarity([user_vector], [combo_vector])[0][0]
    pearson_global = pearsonr(user_vector, combo_vector)[0]
    sim_global = (cos_global + pearson_global) / 2

    error = np.abs(user_vector - combo_vector)
    weighted_error = error * user_vector
    w_error_score = 1 - (weighted_error.sum() / user_vector.sum())

    sim_head = cosine_similarity([user_vector], [head])[0][0]
    sim_torso = cosine_similarity([user_vector], [torso])[0][0]
    sim_face = cosine_similarity([user_vector], [face])[0][0]
    min_sim = min(sim_head, sim_torso, sim_face)

    corr_head = pearsonr(user_vector, head)[0]
    corr_torso = pearsonr(user_vector, torso)[0]
    corr_face = pearsonr(user_vector, face)[0]
    min_corr = min(corr_head, corr_torso, corr_face)

    score = p1 * sim_global + p2 * w_error_score + p3 * min_sim + p4 * min_corr
    return score

def top_n_similar(user_vector, candidates, N=10):
    sims = [cosine_similarity([user_vector], [c])[0][0] for c in candidates]
    top_n = [candidates[i] for i in np.argsort(sims)[-N:][::-1]]
    return top_n

def find_accessory_name(accessory_array, accessory_vector, accessory_names):
    for i, vec in enumerate(accessory_array):
        if np.array_equal(vec, accessory_vector):
            return accessory_names[i]
    return None

# =============================
# Load accessory image by name
# =============================
def load_image_from_folder(accessory_name, folder_path):
    # Remove the prefix like '(Torso) ' from the name
    accessory_name = accessory_name.split(') ')[-1]
    image_path = os.path.join(folder_path, accessory_name)
    return Image.open(image_path)

# ================================
# Generate pet image for a user
# ================================
def create_pet_image(user_id, torso_name, head_name, face_name):
    base_image_path = 'PET/Data/Body/RockyBoi.png'
    base_image = Image.open(base_image_path)

    # Load accessory images
    torso_image = load_image_from_folder(torso_name, 'PET/Data/Torso')
    head_image = load_image_from_folder(head_name, 'PET/Data/Head')
    face_image = load_image_from_folder(face_name, 'PET/Data/Face')

    # Paste accessories on top of base image (positions can be adjusted if needed)
    base_image.paste(torso_image, (0, 0), torso_image)
    base_image.paste(head_image, (0, 0), head_image)
    base_image.paste(face_image, (0, 0), face_image)

    # Save the resulting pet image
    pet_image_name = f'Pet_{user_id}.png'
    base_image.save(f"PET/{pet_image_name}") # REMOVE?
    return pet_image_name, base_image

# ===================
# Load Data
# ===================

accessory_df = pd.read_csv('PET/Data/AccessoryDataset.csv')

head_accessories = accessory_df[accessory_df['Type'] == 'Head'].iloc[:, 2:].values
torso_accessories = accessory_df[accessory_df['Type'] == 'Torso'].iloc[:, 2:].values
face_accessories = accessory_df[accessory_df['Type'] == 'Face'].iloc[:, 2:].values

head_names = accessory_df[accessory_df['Type'] == 'Head']['FileName'].values
torso_names = accessory_df[accessory_df['Type'] == 'Torso']['FileName'].values
face_names = accessory_df[accessory_df['Type'] == 'Face']['FileName'].values

genres = ['Comedy','Art','Chill','Food','Social','Rock','Pop','Soul',
          'Jazz','Electronic','Folk','Reggae','Hip-hop','Punk','Rap',
          'Classical','Indie','Other']

# ============================
# Define Single User Vector
# ============================

user_vector = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 0.0,
                        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]) # IDK how this will be loaded
print(f"Working with user vector: {user_vector}")

# ============================
# Top-N Accessories
# ============================

N = 10
top_heads = top_n_similar(user_vector, head_accessories, N)
top_torsos = top_n_similar(user_vector, torso_accessories, N)
top_faces = top_n_similar(user_vector, face_accessories, N)

# ============================
# Find Best Accessory Combo
# ============================

p_sim_global = 0.5
p_w_error_score = 0.2
p_min_sim = 0.15
p_min_corr = 0.15

best_score = -float('inf')
best_combo = None
best_combo_names = None

for head in top_heads:
    for torso in top_torsos:
        for face in top_faces:
            score = evaluate(user_vector, head, torso, face, p_sim_global, p_w_error_score, p_min_sim, p_min_corr)
            if score > best_score:
                best_score = score
                best_combo = (head, torso, face)
                best_combo_names = (
                    find_accessory_name(head_accessories, head, head_names),
                    find_accessory_name(torso_accessories, torso, torso_names),
                    find_accessory_name(face_accessories, face, face_names)
                )

# ============================
# Print and Save Result
# ============================

print("\n🎯 Best Accessory Combo for the User")
print("Torso:", best_combo_names[1])
print("Head:", best_combo_names[0])
print("Face:", best_combo_names[2])
print("Score:", best_score)

results_table = []

results_table.append({
    "Genero": "User",
    **{genre: user_vector[genres.index(genre)] for genre in genres}
})
results_table.append({
    "Genero": "(Torso) " + best_combo_names[1],
    **{genre: best_combo[1][genres.index(genre)] for genre in genres}
})
results_table.append({
    "Genero": "(Head) " + best_combo_names[0],
    **{genre: best_combo[0][genres.index(genre)] for genre in genres}
})
results_table.append({
    "Genero": "(Face) " + best_combo_names[2],
    **{genre: best_combo[2][genres.index(genre)] for genre in genres}
})

df_results = pd.DataFrame(results_table)

# ============================
# Build Pet
# ============================

user_id = "User"
user_genres = df_results.iloc[1]

torso_name = df_results.iloc[1, 0]
head_name = df_results.iloc[2, 0]
face_name = df_results.iloc[3, 0]

# Generate pet image
pet_image_name, pet_image = create_pet_image(user_id, torso_name, head_name, face_name)