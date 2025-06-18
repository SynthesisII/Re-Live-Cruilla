import os
import cv2
import numpy as np
import zipfile
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2 import model_zoo

# ----------
# Create Collage Function
# ----------
def crear_collage(fondo_path, avatar_path, mask_path, real_path, save_path):
    fondo = cv2.imread(fondo_path)
    avatar = cv2.imread(avatar_path)
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    real = cv2.imread(real_path)

    mask_rgb = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

    # Ensure all images have the same height
    height = min(fondo.shape[0], avatar.shape[0], mask_rgb.shape[0], real.shape[0])
    fondo, avatar, mask_rgb, real = fondo[:height], avatar[:height], mask_rgb[:height], real[:height]

    # Concatenate images side by side
    collage = cv2.hconcat([real, fondo, avatar, mask_rgb])
    cv2.imwrite(save_path, collage)

# ----------
# Unzip ZIP Files
# ----------
def unzip_all_zips(base_dir, temp_dir):
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.lower().endswith(".zip"):
                zip_path = os.path.join(root, file)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    extract_path = os.path.join(temp_dir, os.path.splitext(file)[0])
                    os.makedirs(extract_path, exist_ok=True)
                    zip_ref.extractall(extract_path)

# ----------
# Main Dataset Creation
# ----------
def segmentar_y_crear_dataset(base_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    temp_unzip_dir = "/tmp/unzipped_cruilla"
    os.makedirs(temp_unzip_dir, exist_ok=True)

    unzip_all_zips(base_dir, temp_unzip_dir)

    # Load a pretrained Mask R-CNN model from Detectron2
    cfg = get_cfg()
    cfg.merge_from_file(model_zoo.get_config_file("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml"))
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5
    cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml")
    predictor = DefaultPredictor(cfg)

    collage_count = 0
    for root, _, files in os.walk(temp_unzip_dir):
        for file in files:
            if not file.lower().endswith(('.jpg', '.png')):
                continue

            image_path = os.path.join(root, file)
            image = cv2.imread(image_path)
            if image is None:
                continue

            outputs = predictor(image)
            instances = outputs["instances"]

            person_indices = instances.pred_classes == 0
            persons = instances[person_indices]
            masks = persons.pred_masks.cpu().numpy()

            for i, mask in enumerate(masks):
                mask_uint8 = (mask * 255).astype(np.uint8)

                # Create segmented avatar
                avatar = np.copy(image)
                avatar[mask == 0] = 0

                # Inpaint background
                fondo = cv2.inpaint(image, mask_uint8, 3, cv2.INPAINT_TELEA)

                # Save intermediate files for collage
                temp_mask_path = "/tmp/temp_mask.png"
                temp_avatar_path = "/tmp/temp_avatar.png"
                temp_fondo_path = "/tmp/temp_fondo.png"
                cv2.imwrite(temp_mask_path, mask_uint8)
                cv2.imwrite(temp_avatar_path, avatar)
                cv2.imwrite(temp_fondo_path, fondo)

                # Save final collage
                collage_path = os.path.join(output_dir, f"{collage_count:06d}.png")
                crear_collage(temp_fondo_path, temp_avatar_path, temp_mask_path, image_path, collage_path)

                collage_count += 1

# ----------
# Main Entry Point
# ----------
if __name__ == "__main__":
    base_folder = "/export/hhome/uabcru03/1.CRUILLA"
    output_folder = "/export/hhome/uabcru03/Carrousel/Dataset2"
    segmentar_y_crear_dataset(base_folder, output_folder)
