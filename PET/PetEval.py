import pandas as pd
from PIL import Image
import os
import matplotlib.pyplot as plt

csv_path = '1_DResultados2.csv'
df = pd.read_csv(csv_path)

# =====================================
# Load accessory image from its folder
# =====================================
def load_image_from_folder(accessory_name, folder_path):
    # Remove the prefix like "(Torso) ", "(Head) ", "(Face) " from the file name
    accessory_name = accessory_name.split(') ')[-1]
    image_path = os.path.join(folder_path, accessory_name)
    return Image.open(image_path)

# ================================================================
# Bar chart: user genres + individual accessories + average vector
# ================================================================
def plot_genres_5(user_genres, torso_genres, head_genres, face_genres, accessory_genres, user_id):
    user_genres = pd.DataFrame([user_genres])  # Make sure it's a DataFrame

    genres = user_genres.columns
    user_values = user_genres.values.flatten()
    torso_values = torso_genres.values.flatten()
    head_values = head_genres.values.flatten()
    face_values = face_genres.values.flatten()
    accessory_values = accessory_genres.values.flatten()

    fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    index = range(len(genres))
    bar_width = 0.15

    ax.bar(index, user_values, bar_width, label='User', color='b')
    ax.bar([i + bar_width for i in index], accessory_values, bar_width, label='Torso', color='r')
    ax.bar([i + 2 * bar_width for i in index], head_values, bar_width, label='Head', color='y')
    ax.bar([i + 3 * bar_width for i in index], face_values, bar_width, label='Face', color='purple')
    ax.bar([i + 4 * bar_width for i in index], accessory_values, bar_width, label='Accessories (Avg)', color='g')

    ax.set_xlabel('Genres')
    ax.set_ylabel('Values')
    ax.set_title('Comparison of User and Accessory Genres')
    ax.set_xticks([i + 2 * bar_width for i in index])
    ax.set_xticklabels(genres, rotation=90)
    ax.legend()

    plt.tight_layout()
    graph_path = f'genre_comparison_{user_id}.png'
    plt.savefig(graph_path)
    return graph_path

# ==================================================
# Bar chart: user genres vs. average accessory vector
# ==================================================
def plot_genres_2(user_genres, accessory_genres, user_id):
    user_genres = pd.DataFrame([user_genres])  # Make sure it's a DataFrame

    genres = user_genres.columns
    user_values = user_genres.values.flatten()
    accessory_values = accessory_genres.values.flatten()

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    index = range(len(genres))
    bar_width = 0.35

    ax.bar(index, user_values, bar_width, label='User', color='b')
    ax.bar([i + bar_width for i in index], accessory_values, bar_width, label='Accessories', color='r')

    ax.set_xlabel('Genres')
    ax.set_ylabel('Values')
    ax.set_title('Comparison of User and Accessory Genres')
    ax.set_xticks([i + 2 * bar_width for i in index])
    ax.set_xticklabels(genres, rotation=90)
    ax.legend()

    plt.tight_layout()
    graph_path = f'genre_comparison_{user_id}.png'
    plt.savefig(graph_path)
    return graph_path

# ================================
# UNCOMMENTED SECTIONS (IF NEEDED)
# ================================

"""
# Generate pet image with accessory overlays
def create_pet_image(user_id, torso_name, head_name, face_name):
    base_image_path = 'Synthesis/Synthesis/ToyPet/Data/Body/RockyBoi.png'
    base_image = Image.open(base_image_path)

    torso_image = load_image_from_folder(torso_name, 'Synthesis/Synthesis/ToyPet/Data/Torso')
    head_image = load_image_from_folder(head_name, 'Synthesis/Synthesis/ToyPet/Data/Head')
    face_image = load_image_from_folder(face_name, 'Synthesis/Synthesis/ToyPet/Data/Face')

    base_image.paste(torso_image, (0, 0), torso_image)
    base_image.paste(head_image, (0, 0), head_image)
    base_image.paste(face_image, (0, 0), face_image)

    pet_image_name = f'Pet_{user_id}.png'
    base_image.save(pet_image_name)
    return pet_image_name, base_image
"""

"""
# Combine pet image and genre plot into one
def combine_images(graph_path, pet_image, user_id):
    graph_image = Image.open(graph_path)
    graph_width = int(pet_image.width * 0.6)
    graph_height = int(graph_image.height * (graph_width / graph_image.width))
    graph_image = graph_image.resize((graph_width, graph_height))

    total_width = pet_image.width + graph_image.width
    total_height = max(pet_image.height, graph_image.height)

    combined_image = Image.new('RGB', (total_width, total_height))
    combined_image.paste(pet_image, (0, 0))
    combined_image.paste(graph_image, (pet_image.width, 0))

    combined_image_path = f'combined_image_{user_id}.png'
    combined_image.save(combined_image_path)
    return combined_image_path
"""

# ===============================
# Main loop to process all users
# ===============================
for i in range(0, len(df), 4):
    user_id = df.iloc[i, 0]
    user_genres = df.iloc[i, 1:]
    torso_name = df.iloc[i+1, 0]
    head_name = df.iloc[i+2, 0]
    face_name = df.iloc[i+3, 0]

    # Generate genre vectors
    torso_genres = df.iloc[i+1, 1:]
    head_genres = df.iloc[i+2, 1:]
    face_genres = df.iloc[i+3, 1:]
    accessory_genres = df.iloc[i+1:i+4, 1:].mean(axis=0)

    # Print genre values for debugging
    print(torso_genres)
    print(head_genres)
    print(face_genres)
    print("Accessory avg:", accessory_genres)
    print("User:", user_genres)

    # To activate image and graph generation, uncomment below:
    # pet_image_name, pet_image = create_pet_image(user_id, torso_name, head_name, face_name)
    # graph_path = plot_genres_5(user_genres, torso_genres, head_genres, face_genres, accessory_genres, user_id)
    # combined_image_path = combine_images(graph_path, pet_image, user_id)
    # print(f'Combined image for user {user_id} saved as {combined_image_path}')
