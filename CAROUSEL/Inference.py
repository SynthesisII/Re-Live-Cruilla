import torch
from torchvision import transforms
from PIL import Image
from Utils import denorm
from Model import AvatarFusionModel
import os

# --------
# Config
# --------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Usando dispositivo: {device}")

# Paths
background_path = "/hhome/uabcru03/Carrousel+/Data/Backgrounds"
avatar_path = "/hhome/uabcru03/Carrousel+/Data/Avatars"
checkpoint_path = "/hhome/uabcru03/Carrousel+/checkpoints/train_1024_transforms.pt"
output_path = "/hhome/uabcru03/Carrousel+/Data/Results/1024_transforms"


# --------
# Transforms (same as training)
# --------
transform = transforms.Compose([
    transforms.Resize((1024, 1024)), 
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5]*3, std=[0.5]*3)
])


# --------
# Load model
# --------
model = AvatarFusionModel().to(device)
checkpoint = torch.load(checkpoint_path, map_location=device)
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()
print("Modelo cargado para inferencia.")


# --------
# Get image filenames
# --------

avatar_files = sorted([f for f in os.listdir(avatar_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
background_files = sorted([f for f in os.listdir(background_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])

# --------
# Inference loop
# --------

with torch.no_grad():
    for avatar_name in avatar_files:
        for background_name in background_files:
          # Load and process images
          background_img = Image.open(os.path.join(avatar_path, avatar_name)).convert("RGB")
          avatar_img = Image.open(os.path.join(background_path, background_name)).convert("RGB")
          
          bg_tensor = transform(background_img)
          avatar_tensor = transform(avatar_img)
          
          # Combine into 6 channel input
          input_tensor = torch.cat([bg_tensor, avatar_tensor], dim=0).unsqueeze(0).to(device)

          
          # Generate output
          output = model(input_tensor)  
          output_img = denorm(output.squeeze(0)).clamp(0, 1)
          output_img = transforms.ToPILImage()(output_img.cpu())
          
          # Save result with descriptive name
          save_name = f"{os.path.splitext(avatar_name)[0]}__{os.path.splitext(background_name)[0]}.png"
          output_img.save(os.path.join(output_path, save_name))
          print(f"[?] Guardado: {save_name}")
