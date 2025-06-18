import pandas as pd
import numpy as np
import random
from PIL import Image

# ============================
# Get a Specific Accessory File
# ============================
def get_specific_file(accessory_type, filename, body_path="ToyPet/Data/"):
    """
    Returns the image and feature vector for a specific accessory.

    Parameters:
    - accessory_type (str): 'Torso', 'Head', or 'Face'
    - filename (str): image file name
    - body_path (str): base path to data directory

    Returns:
    - (PIL.Image, List[float]): the accessory image and its associated vector
    """
    df = pd.read_csv(f"{body_path}AccessoryDataset.csv")
    sub_df = df.loc[(df["Type"] == accessory_type) & (df["FileName"] == filename)]
    data = [list(row) for row in sub_df.itertuples(index=False)][0]

    file = data.pop(0)  # Remove filename from data vector
    image = Image.open(os.path.join(body_path, accessory_type, filename))
    return image, data

# ============================
# Generate Random User Dataset
# ============================
def get_some_data(n=50, styles=None):
    """
    Generates synthetic data representing attendee experiences.

    Parameters:
    - n (int): number of users to generate
    - styles (List[str]): list of genres/preferences

    Returns:
    - pd.DataFrame: dataset of user preference vectors
    """
    if styles is None:
        styles = ['Comedy','Art','Chill','Food','Social','Rock','Pop','Soul',
                  'Jazz','Electronic','Folk','Reggae','Hip-hop','Punk','Rap',
                  'Classical','Indie','Other']

    m = len(styles)
    styles.insert(0, "User_ID")  # Add User_ID as first column

    data = []
    for user_id in range(n):
        user_data = [user_id]
        user_data += random.sample(range(0, m**2 + 1), m)
        data.append(user_data)

    df = pd.DataFrame(data, columns=styles)
    df.index.name = 'User_ID'
    return df

# ====================
# Transform User Vector
# ====================
def data_transform(column_names, target_order, data):
    """
    Aligns input data with system genre order.

    Parameters:
    - column_names (List[str]): input column names
    - target_order (List[str]): desired column order
    - data (List[float/int]): user data

    Returns:
    - List[float]: transformed user vector
    """
    result = [0] * len(target_order)

    for i, name in enumerate(column_names):
        if name in target_order:
            result[target_order.index(name)] += data[i]
        elif "Other" in target_order:
            result[target_order.index("Other")] += data[i]

    return result

# ===================
# Validate the Dataset
# ===================
def check_dataset(filepath="ToyPet/Data/AccessoryDataset.csv"):
    """
    Validates that the dataset:
    - Can be read
    - Has consistent row lengths
    - Contains numeric feature vectors
    - References valid image files
    """
    try:
        df = pd.read_csv(filepath)
    except:
        print(f"Dataframe not found at: {filepath}")
        raise

    items = [list(row) for row in df.itertuples(index=False)]
    item_len = None

    for i, item in enumerate(items):
        if item_len is None:
            item_len = len(item)
        else:
            assert len(item) == item_len, f"Row {i} has inconsistent number of elements"

        # Ensure numeric values in vector
        numeric_count = len([n for n in item[2:] if isinstance(n, (int, float))])
        assert numeric_count == item_len - 2, f"Row {i} contains non-numeric vector values"

        # Verify image path can be opened
        try:
            get_specific_file(item[1], item[0], body_path="ToyPet/Data/")
        except:
            print(f"Row {i} references an image that cannot be opened")
            raise

    print("Dataset OK")

# =====================
# Script Entry Point
# =====================
if __name__ == "__main__":
    df = get_some_data()
    check_dataset()
    pass
