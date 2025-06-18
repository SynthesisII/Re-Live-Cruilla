===================================
RE:LIVE CRUÏLLA - Codebase Overview
===================================

This repository contains all the necessary scripts to Train, Evaluate, and Test the three components 
of the Re:Live Cruïlla project: PET (level 1), AVATAR (level 2), and CAROUSEL (level 3). The project 
structure is organized into three main folders, each corresponding to one level of ambition in Re:Live Cruïlla.

-----------------
Project Structure
-----------------

Re-Live-Cruilla/
│
├── AVATAR/                   # Folder for the AVATAR scripts
│
├── CARROUSEL/                # Folder for the CAROUSEL scripts
│   │
│   ├── Collage_segmentation.py   # [STEP 1] Generates dataset collages from ZIP images using Mask R-CNN
│   ├── Dataset.py                # [STEP 2] PyTorch Dataset class to load and preprocess collage images
│   ├── Model.py                  # [STEP 3] Defines the encoder-decoder model using ResNet + Transformer
│   ├── Train.py                  # [STEP 4] Training script using L1, perceptual, and masked losses
│   ├── Evaluate.py               # [STEP 5] Loads a trained model and evaluates PSNR/SSIM on validation data
│   └── Utils.py                  # Utility functions: saving images, metrics, perceptual loss, etc.
│
├── PET/                      # Folder for the PET scripts
│
└── README.txt               

-------------------------
PET: Scripts Explanation
-------------------------

-------------------------
AVATAR: Scripts Explanation
-------------------------

-------------------------
CAROUSEL: Script Explanation
-------------------------

The CAROUSEL level is the most ambitious part of the Re:Live Cruïlla pipeline. It focuses on extracting
a person (avatar) from a real-world scene, removing the background, and learning how to reconstruct
a realistic fusion of the avatar onto a clean background using neural networks.

The scripts follow a pipeline of 5 key steps:

[STEP 1] Collage_segmentation.py
---------------------------------
This script creates the training dataset (the collage format) by:
- Unzipping .zip archives containing images.
- Segmenting people using Mask R-CNN (via Detectron2).
- Generating collages composed of:
    [ Ground Truth | Clean Background | Segmented Avatar | Binary Mask ]
- Saving the resulting collage images in a target directory.

[STEP 2] Dataset.py
-------------------
Defines the `AvatarFusionDataset`, a custom PyTorch dataset that:
- Loads collage images from disk.
- Splits them into the 4 key components (GT, background, avatar, mask).
- Applies transformations and returns input tensors:
    - Input: [Background + Avatar] → 6 channels
    - Target: Ground Truth → 3 channels
    - Mask: Binary mask → 1 channel

[STEP 3] Model.py
-----------------
Defines the model used to reconstruct the fused avatar image:
- Encoder: ResNet-50 modified to accept 6-channel input (background + avatar).
- Decoder: Transformer-based upsampling network with skip connections.
- Includes a simpler alternative model with a standard CNN decoder.

[STEP 4] Train.py
-----------------
Handles the training loop:
- Loads the dataset and model.
- Defines a custom loss function that combines:
    - L1 loss (global pixel-wise)
    - Perceptual loss (using VGG features)
    - Masked L1 loss (focused on the avatar region only)
- Trains the model for multiple epochs.
- Saves checkpoints and visual output samples.

[STEP 5] Evaluate.py
--------------------
Used to evaluate a trained model:
- Loads a saved model checkpoint.
- Computes quantitative metrics (PSNR, SSIM).
- Saves a sample of visual results for inspection.

Utils.py
--------
A collection of helper functions used by Train and Evaluate scripts:
- `save_result`: saves visual comparisons of input/output/ground truth
- `compute_psnr_ssim`: computes evaluation metrics
- `PerceptualLoss`: VGG-based loss wrapper
- `denorm`: inverse normalization for image tensors


