# RE:LIVE CRUÏLLA - Codebase Overview

This repository contains all the necessary scripts to Train, Evaluate, and Test the three components 
of the Re:Live Cruïlla project: PET (level 1), AVATAR (level 2), and CAROUSEL (level 3). The project 
structure is organized into three main folders, each corresponding to one level of ambition in 
Re:Live Cruïlla.

## Project Structure
<pre>
Re-Live-Cruilla/  
│  
├── AVATAR/                    
│   ├── AvatarGen_Base.py       
│   ├── AvatarGen.py          
│   ├── FeatureExtractor.py     
│   ├── utils.py              
│   └── requirements.txt      
│  
├── CARROUSEL/                  
│   ├── Collage_segmentation.py  
│   ├── Dataset.py  
│   ├── Model.py  
│   ├── Train.py  
│   ├── Evaluate.py  
│   ├── Inference.py  
│   └── Utils.py  
│  
├── PET/                        
│   ├── Data/  
│   │   ├── Body/  
│   │   ├── Face/  
│   │   ├── Head/  
│   │   ├── Torso/  
│   │   └── AccessoryDataset.csv  
│   ├── 1_TopN.py            
│   ├── 1.5_Plot_Pet.py       
│   ├── data.py               
│   ├── main.py               
│   └── PetEval.py            
│  
└── README.txt  
</pre>

## PET: Scripts Explanation

### 1_TopN.py
---------
- Loads user and accessory vectors from CSV files.
- Computes cosine similarity between user profiles and accessory features.
- Selects Top-N matching accessories per category (Head, Torso, Face).
- Evaluates all combinations to assign the optimal set to each user.
- Outputs a new CSV file with full vectors for user + selected accessories.

### 1.5_Plot_Pet.py
---------------
- Loads the CSV generated in 1_TopN.py.
- For each user:
    - Creates a pet image by overlaying accessories onto a base body.
    - Plots a bar chart comparing user preferences with accessory vectors.
    - Optionally combines both into a single image output.

### data.py
-------
- `get_specific_file`: returns both the image and vector for a given accessory file.
- `get_some_data`: generates synthetic user data for testing (random genre scores).
- `data_transform`: aligns arbitrary genre columns to system's internal order.
- `check_dataset`: validates AccessoryDataset.csv and checks image paths.

### main.py
-------
- Initializes canvas and loads a base body image.
- Loads accessory metadata from CSV.
- Normalizes user vectors and uses a KNN-like strategy to select one accessory per type.
- Pastes accessories in visual layers (Torso → Face → Head) onto the base body.
- Can display and/or save the final image.

### PetEval.py
----------
- Lightweight standalone script for evaluating pets.
- Uses random KNN logic to assign accessories based on vector proximity.
- Designed for fast generation of sample outputs or debugging logic.

### Data folders
----------
.png image accesories for Torso, Head and Face and the base Pet. Also, the .csv with 
the vectors corresponding to each accesory.

## AVATAR: Scripts Explanation

### AvatarGen_Base.py
-----------------
- Loads the base Stable Diffusion XL (SDXL) pipeline.
- Takes a user image and a prompt generated from analysis data.
- Runs two passes: first with the base SDXL model, then with the refiner.
- Outputs a clean 1024x1024 avatar with background removed.

### AvatarGen.py
------------
- Similar to AvatarGen_Base but loads a custom fine-tuned LoRA checkpoint.
- Injects the new weights into the UNet of the base model.
- Allows more personalized avatars that better reflect the user's preferences.
- Runs the same two-stage generation: base + refinement.

### FeatureExtractor.py
-------------------
- Uses DeepFace to analyze the input image and detect:
    - Dominant gender
    - Dominant race
- Identifies the top 3 music genres from the user preference vector.
- Saves a JSON with demographic and preference metadata used in prompt generation.

### utils.py
--------
- `center_crop_to_square`: crops any image to a square before resizing to 1024x1024.
- `generate_weighted_prompt`: builds a detailed textual prompt using:
    - Genre-based clothing/accessory mappings
    - Detected race and gender
- `remove_background`: removes the background of an image using rembg.

## CAROUSEL: Script Explanation

The CAROUSEL level is the most ambitious part of the Re:Live Cruïlla pipeline. It focuses on extracting
a person (avatar) from a real-world scene, removing the background, and learning how to reconstruct
a realistic fusion of the avatar onto a clean background using neural networks.

The scripts follow a pipeline of 5 key steps:

### [STEP 1] Collage_segmentation.py
---------------------------------
This script creates the training dataset (the collage format) by:
- Unzipping .zip archives containing images.
- Segmenting people using Mask R-CNN (via Detectron2).
- Generating collages composed of:
    [ Ground Truth | Clean Background | Segmented Avatar | Binary Mask ]
- Saving the resulting collage images in a target directory.

### [STEP 2] Dataset.py
-------------------
Defines the `AvatarFusionDataset`, a custom PyTorch dataset that:
- Loads collage images from disk.
- Splits them into the 4 key components (GT, background, avatar, mask).
- Applies transformations and returns input tensors:
    - Input: [Background + Avatar] → 6 channels
    - Target: Ground Truth → 3 channels
    - Mask: Binary mask → 1 channel

### [STEP 3] Model.py
-----------------
Defines the model used to reconstruct the fused avatar image:
- Encoder: ResNet-50 modified to accept 6-channel input (background + avatar).
- Decoder: Transformer-based upsampling network with skip connections.
- Includes a simpler alternative model with a standard CNN decoder.

### [STEP 4] Train.py
-----------------
Handles the training loop:
- Loads the dataset and model.
- Defines a custom loss function that combines:
    - L1 loss (global pixel-wise)
    - Perceptual loss (using VGG features)
    - Masked L1 loss (focused on the avatar region only)
- Trains the model for multiple epochs.
- Saves checkpoints and visual output samples.

### [STEP 5] Evaluate.py
--------------------
Used to evaluate a trained model:
- Loads a saved model checkpoint.
- Computes quantitative metrics (PSNR, SSIM).
- Saves a sample of visual results for inspection.

### Utils.py
--------
A collection of helper functions used by Train and Evaluate scripts:
- `save_result`: saves visual comparisons of input/output/ground truth
- `compute_psnr_ssim`: computes evaluation metrics
- `PerceptualLoss`: VGG-based loss wrapper
- `denorm`: inverse normalization for image tensors


