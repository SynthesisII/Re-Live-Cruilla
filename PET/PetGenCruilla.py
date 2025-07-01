import os
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from scipy.stats import pearsonr
from sklearn.metrics.pairwise import cosine_similarity


class PetGenCruilla:

    def __init__(self):
        self._top_n = 10
        self._p_sim_global = 0.5
        self._p_w_error_score = 0.2
        self._p_min_sim = 0.15
        self._p_min_corr = 0.15

        self._genres = ['Comedy','Art','Chill','Food','Social','Rock','Pop','Soul',
                       'Jazz','Electronic','Folk','Reggae','Hip-hop','Punk','Rap',
                       'Classical','Indie','Other']
        
        root_path = Path(__file__).parent
        self._data_path = root_path / 'Data/'
        self._base_image = Image.open(root_path / 'Data/Body/RockyBoi.png')

        # Load accessory dataset
        dataset_path = root_path / 'Data/AccessoryDataset.csv'
        accessory_df = pd.read_csv(dataset_path)
        
        self.head_accessories = accessory_df[accessory_df['Type'] == 'Head'].iloc[:, 2:].values
        self.torso_accessories = accessory_df[accessory_df['Type'] == 'Torso'].iloc[:, 2:].values
        self.face_accessories = accessory_df[accessory_df['Type'] == 'Face'].iloc[:, 2:].values
        
        self.head_names = accessory_df[accessory_df['Type'] == 'Head']['FileName'].values
        self.torso_names = accessory_df[accessory_df['Type'] == 'Torso']['FileName'].values
        self.face_names = accessory_df[accessory_df['Type'] == 'Face']['FileName'].values

    # TODO: Can receive a constant vector (all values the same)?
    # (ConstantInputWarning: An input array is constant; the correlation coefficient is not defined.)
    def _evaluate(self, user_vector, head, torso, face, p1, p2, p3, p4):
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

    def _top_n_similar(self, user_vector, candidates, N=10):
        sims = [cosine_similarity([user_vector], [c])[0][0] for c in candidates]
        top_n = [candidates[i] for i in np.argsort(sims)[-N:][::-1]]
        return top_n

    def _find_accessory_name(self, accessory_array, accessory_vector, accessory_names):
        for i, vec in enumerate(accessory_array):
            if np.array_equal(vec, accessory_vector):
                return accessory_names[i]
        return None

    def _load_image_from_folder(self, accessory_name, folder_path):
        # Remove the prefix like '(Torso) ' from the name
        accessory_name = accessory_name.split(') ')[-1]
        image_path = os.path.join(folder_path, accessory_name)
        return Image.open(image_path)
    
    def _create_pet_image(self, torso_name, head_name, face_name):
        base_image = self._base_image.copy()

        # Load accessory images
        torso_image = self._load_image_from_folder(torso_name, self._data_path / 'Torso')
        head_image = self._load_image_from_folder(head_name, self._data_path / 'Head')
        face_image = self._load_image_from_folder(face_name, self._data_path / 'Face')

        # Paste accessories on top of base image (positions can be adjusted if needed)
        base_image.paste(torso_image, (0, 0), torso_image)
        base_image.paste(head_image, (0, 0), head_image)
        base_image.paste(face_image, (0, 0), face_image)

        return base_image

    def generate_pet_image(self, user_vector: np.ndarray) -> Image.Image:
        print(f"Working with user vector: {user_vector} {user_vector.shape} {user_vector.dtype}")

        top_heads = self._top_n_similar(user_vector, self.head_accessories, self._top_n)
        top_torsos = self._top_n_similar(user_vector, self.torso_accessories, self._top_n)
        top_faces = self._top_n_similar(user_vector, self.face_accessories, self._top_n)

        best_score = -float('inf')
        best_combo = None
        best_combo_names = None

        for head in top_heads:
            for torso in top_torsos:
                for face in top_faces:
                    score = self._evaluate(
                        user_vector,
                        head,
                        torso,
                        face,
                        self._p_sim_global,
                        self._p_w_error_score,
                        self._p_min_sim,
                        self._p_min_corr
                    )
                    if score > best_score:
                        best_score = score
                        best_combo = (head, torso, face)
                        best_combo_names = (
                            self._find_accessory_name(self.head_accessories, head, self.head_names),
                            self._find_accessory_name(self.torso_accessories, torso, self.torso_names),
                            self._find_accessory_name(self.face_accessories, face, self.face_names)
                        )
        
        print("🎯 Best Accessory Combo for the User")
        print("Torso:", best_combo_names[1])
        print("Head:", best_combo_names[0])
        print("Face:", best_combo_names[2])
        print("Score:", best_score)

        results_table = []

        results_table.append({
            "Genero": "User",
            **{genre: user_vector[self._genres.index(genre)] for genre in self._genres}
        })
        results_table.append({
            "Genero": "(Torso) " + best_combo_names[1],
            **{genre: best_combo[1][self._genres.index(genre)] for genre in self._genres}
        })
        results_table.append({
            "Genero": "(Head) " + best_combo_names[0],
            **{genre: best_combo[0][self._genres.index(genre)] for genre in self._genres}
        })
        results_table.append({
            "Genero": "(Face) " + best_combo_names[2],
            **{genre: best_combo[2][self._genres.index(genre)] for genre in self._genres}
        })

        df_results = pd.DataFrame(results_table)
        
        torso_name = df_results.iloc[1, 0]
        head_name = df_results.iloc[2, 0]
        face_name = df_results.iloc[3, 0]

        return self._create_pet_image(torso_name, head_name, face_name)


if __name__ == "__main__":
    pet_generator = PetGenCruilla()
    
    user_vector = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    image = pet_generator.generate_pet_image(user_vector)
    image.save("pet.png")
