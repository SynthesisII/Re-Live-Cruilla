import pandas as pd
import numpy as np
import random
from PIL import Image

from data import *  # Assumes external functions like data_transform are defined in data.py

# ===========================
# Normalize Vector to [0, 1]
# ===========================
def normalize_list(listy):
    """
    Scales a list of values to the [0, 1] range based on the maximum value.
    """
    total = max(listy)
    return [element / total for element in listy]

# ================================
# Load Accessory Data from CSV
# ================================
def load_data_accessories(filepath="ToyPet/Data/AccessoryDataset.csv"):
    """
    Loads accessory metadata from CSV and returns a nested dictionary:
    {Type -> {FileName -> FeatureVector}}.
    """
    df = pd.read_csv(filepath)
    accessory_types = df.get("Type").unique()
    
    accessories_dict = {}
    for accessory_type in accessory_types:
        accessories_dict[accessory_type] = {}
        sub_df = df.loc[df["Type"] == accessory_type]
        accessory_items = [list(row) for row in sub_df.itertuples(index=False)]

        for accessory in accessory_items:
            accessories_dict[accessory_type][accessory[0]] = list(accessory[2:])  # skip FileName and Type

    return accessories_dict

# ====================
# Custom Cost Function
# ====================
def cost_f(vector1, vector2):
    """
    Calculates a distance score between two vectors (custom metric).
    """
    assert len(vector1) == len(vector2), "User data and accessory data are not the same size"
    total = sum([(vector1[i] + vector2[i]) ** 2 for i in range(len(vector1))])
    return total ** 0.5

# ====================
# KNN Accessory Picker
# ====================
def knn_accessories(user_data, accessories_data, n_choices=2):
    """
    For each accessory type, selects the best-matching item using KNN logic.
    Returns one random top match per type.
    """
    user_data = normalize_list(user_data)
    accessories = {}

    for accessory_type in accessories_data:
        choices = {}
        for accessory, data in accessories_data[accessory_type].items():
            cost = cost_f(user_data, data)
            choices[accessory] = cost

            if len(choices) > n_choices:
                worst = max(choices, key=choices.get)
                del choices[worst]

        selected = random.choice(list(choices.keys()))
        accessories[accessory_type] = selected

    return accessories

# ==================
# Pet Image Generator
# ==================
def generate_pet(center, background_img, acc_data, atendee_id, atendee_data, filepath, save=False, display=False):
    """
    Pastes accessories on top of a pet base image using the selected vectors.
    """
    atendee_data = normalize_list(atendee_data)
    accessories = knn_accessories(atendee_data, acc_data)
    accessory_priority = ["Torso", "Face", "Head"]

    for accessory_type in accessory_priority:
        if accessory_type in accessories:
            filename = accessories[accessory_type]
            acc_image = Image.open(f"ToyPet/Data/{accessory_type}/{filename}")
            background_img.paste(acc_image, (center[0], center[1]), acc_image)

    if save:
        background_img.save(f"{filepath}/{str(atendee_id)}.png")
    
    if display:
        background_img.show()

# ===========================
# Main Loop to Generate Pets
# ===========================
def main_pet(atendee_data, save=False, display=False):
    """
    Generates personalized pet avatars for a group of users.
    """
    final_w, final_h = 4000, 4000
    background_img = Image.new("RGBA", (final_w, final_h), (0, 0, 0, 0))

    # Load body base
    body_name = "RockyBoi.png"
    body_img = Image.open("ToyPet/Data/Body/" + body_name)
    body_w, body_h = body_img.size
    center_coord = [final_w // 2 - body_w // 2, final_h // 2 - body_h // 2]

    background_img.paste(body_img, tuple(center_coord), body_img)

    # Load accessories
    acc_data = load_data_accessories()

    # Columns and genre alignment
    column_names = list(atendee_data.columns)[1:]
    objective_columns = ['Comedy','Art','Chill','Food','Social','Rock','Pop','Soul',
                         'Jazz','Electronic','Folk','Reggae','Hip-hop','Punk','Rap',
                         'Classical','Indie','Other']

    # Generate pet for each user
    for i in range(atendee_data.shape[0]):
        user_data = atendee_data.loc[i, :].values.flatten().tolist()
        user_id = user_data.pop(0)

        user_data = data_transform(column_names, objective_columns, user_data)

        base = background_img.copy()
        generate_pet(center_coord, base, acc_data, user_id, user_data, "ToyPet/Exports", save, display)

if __name__ == "__main__":
    # Example input: Replace with get_some_data() or real user data as needed
    atendee_data = {"0": [0,0,60,0,180,0,0,0,180,0,0,0,0,0,150,0,180,0]}
    atendee_df = pd.DataFrame.from_dict(atendee_data, orient='index')
    atendee_df.reset_index(inplace=True)
    atendee_df.rename(columns={'index': 'id'}, inplace=True)

    main_pet(atendee_df, save=True, display=True)
