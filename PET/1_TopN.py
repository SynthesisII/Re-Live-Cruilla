import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from scipy.stats import pearsonr
import random

# ========================
# Evaluation & Similarity
# ========================

def evaluate(user_vector, head, torso, face, p1, p2, p3, p4):
    # Compute the average vector of the accessory combination
    combo_vector = (head + torso + face) / 3

    # Global similarity (cosine + Pearson)
    cos_global = cosine_similarity([user_vector], [combo_vector])[0][0]
    pearson_global = pearsonr(user_vector, combo_vector)[0]
    sim_global = (cos_global + pearson_global) / 2

    # Weighted error (gives more importance to genres the user likes)
    error = np.abs(user_vector - combo_vector)
    weighted_error = error * user_vector
    w_error_score = 1 - (weighted_error.sum() / user_vector.sum())

    # Minimum individual cosine similarity (ensures all accessories are at least decent)
    sim_head = cosine_similarity([user_vector], [head])[0][0]
    sim_torso = cosine_similarity([user_vector], [torso])[0][0]
    sim_face = cosine_similarity([user_vector], [face])[0][0]
    min_sim = min(sim_head, sim_torso, sim_face)

    # Minimum Pearson correlation between each accessory and the user
    corr_head = pearsonr(user_vector, head)[0]
    corr_torso = pearsonr(user_vector, torso)[0]
    corr_face = pearsonr(user_vector, face)[0]
    min_corr = min(corr_head, corr_torso, corr_face)

    # Final score combining all metrics
    score = p1 * sim_global + p2 * w_error_score + p3 * min_sim + p4 * min_corr
    return score

def top_n_similar(user_vector, candidates, N=10):
    # Compute cosine similarity between user and each candidate
    sims = [cosine_similarity([user_vector], [c])[0][0] for c in candidates]
    # Sort and return the top-N most similar vectors
    top_n = [candidates[i] for i in np.argsort(sims)[-N:][::-1]]
    return top_n

def find_accessory_name(accessory_array, accessory_vector, accessory_names):
    # Return the name of an accessory vector (exact match)
    for i, vec in enumerate(accessory_array):
        if np.array_equal(vec, accessory_vector):
            return accessory_names[i]
    return None

# ===================
# Load and Prepare Data
# ===================

# Load accessory and user data
accessory_df = pd.read_csv('1_AccessoryDataset.csv')
users_df = pd.read_csv('0_Diverse_users_100k.csv')

# Extract accessory vectors by type
head_accessories = accessory_df[accessory_df['Type'] == 'Head'].iloc[:, 2:].values
torso_accessories = accessory_df[accessory_df['Type'] == 'Torso'].iloc[:, 2:].values
face_accessories = accessory_df[accessory_df['Type'] == 'Face'].iloc[:, 2:].values

# Extract accessory filenames
head_names = accessory_df[accessory_df['Type'] == 'Head']['FileName'].values
torso_names = accessory_df[accessory_df['Type'] == 'Torso']['FileName'].values
face_names = accessory_df[accessory_df['Type'] == 'Face']['FileName'].values

# Extract user vectors and IDs
user_vectors = users_df.iloc[:, 1:].values
user_ids = users_df['UserID'].values

# =======================
# Sample a Subset of Users
# =======================

N_users = 10
random_users_indices = random.sample(range(len(user_vectors)), N_users)
random_user_vectors = user_vectors[random_users_indices]
random_user_ids = user_ids[random_users_indices]

# =============================
# Top-N Accessories for Each User
# =============================

N = 10
top_heads = [top_n_similar(user, head_accessories, N) for user in random_user_vectors]
top_torsos = [top_n_similar(user, torso_accessories, N) for user in random_user_vectors]
top_faces = [top_n_similar(user, face_accessories, N) for user in random_user_vectors]

# =====================
# Print Top-10 Accessory Names
# =====================

for i, user_vector in enumerate(random_user_vectors):
    print(f"\nUser {random_user_ids[i]}:")
    print(f"User vector: {user_vector}")

    print("\nTop 10 Head:")
    for name in head_names[np.argsort(cosine_similarity([user_vector], head_accessories))[::-1][:N]]:
        print(name)

    print("\nTop 10 Torso:")
    for name in torso_names[np.argsort(cosine_similarity([user_vector], torso_accessories))[::-1][:N]]:
        print(name)

    print("\nTop 10 Face:")
    for name in face_names[np.argsort(cosine_similarity([user_vector], face_accessories))[::-1][:N]]:
        print(name)

# ===============================
# Find Best Accessory Combination
# ===============================

best_combos = []
# Score weights
p_sim_global = 0.5
p_w_error_score = 0.2
p_min_sim = 0.15
p_min_corr = 0.15

# Evaluate all Top-N combinations for each user
for i, user_vector in enumerate(random_user_vectors):
    best_score = -float('inf')
    best_combo = None
    best_combo_names = None

    for head in top_heads[i]:
        for torso in top_torsos[i]:
            for face in top_faces[i]:
                score = evaluate(user_vector, head, torso, face, p_sim_global, p_w_error_score, p_min_sim, p_min_corr)
                if score > best_score:
                    best_score = score
                    best_combo = (head, torso, face)
                    best_combo_names = (
                        find_accessory_name(head_accessories, head, head_names),
                        find_accessory_name(torso_accessories, torso, torso_names),
                        find_accessory_name(face_accessories, face, face_names)
                    )
    best_combos.append((random_user_ids[i], best_combo, best_combo_names, best_score))

# ========================
# Format Resulting Table
# ========================

genres = users_df.columns[1:].values
results_table = []

for user_id, best_combo, best_combo_names, best_score in best_combos:
    user_vector = random_user_vectors[random_user_ids.tolist().index(user_id)]
    head_name, torso_name, face_name = best_combo_names
    head_vector, torso_vector, face_vector = best_combo

    results_table.append({
        "Genero": "User " + str(user_id),
        **{genre: user_vector[genres.tolist().index(genre)] for genre in genres}
    })

    results_table.append({
        "Genero": "(Torso) " + torso_name,
        **{genre: torso_vector[genres.tolist().index(genre)] for genre in genres}
    })

    results_table.append({
        "Genero": "(Head) " + head_name,
        **{genre: head_vector[genres.tolist().index(genre)] for genre in genres}
    })

    results_table.append({
        "Genero": "(Face) " + face_name,
        **{genre: face_vector[genres.tolist().index(genre)] for genre in genres}
    })

df_results = pd.DataFrame(results_table)
df_results.to_csv("1_DResultados2.csv", index=False)
print(df_results.to_string(index=False))
