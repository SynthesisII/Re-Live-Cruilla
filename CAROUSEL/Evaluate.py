import torch
from torch.utils.data import DataLoader
from torchvision import transforms

from Synthesis.ToyExCarrusel.Model_que_funciona import AvatarFusionModel
from Dataset import AvatarFusionDataset
from Utils import compute_psnr_ssim, save_result, denorm

# ---------- 
# Configuration 
# ----------
checkpoint_path = "checkpoints/best.pt"
data_path = "avatares"
batch_size = 4
save_imgs = True         # Whether to save visualization images
max_saved = 40           # Max number of images to save
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ---------- 
# Data Transform
# ----------
transform = transforms.Compose([
    transforms.Resize((1024, 1024)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5] * 3, std=[0.5] * 3)  # Normalize to [-1, 1]
])

# ---------- 
# Load dataset 
# ----------
dataset = AvatarFusionDataset(data_path, transform=transform, position=True)
dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

# ---------- 
# Load model 
# ----------
model = AvatarFusionModel().to(device)

# Load weights from checkpoint
checkpoint = torch.load(checkpoint_path)
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

print(f"✅ Model loaded from {checkpoint_path} (epoch {checkpoint['epoch']})")

# ---------- 
# Evaluation
# ----------
with torch.no_grad():
    psnr_total = 0.0
    ssim_total = 0.0
    count = 0

    for i, (inputs, targets, _) in enumerate(dataloader):  # `_` = mask, unused here
        inputs = inputs.to(device)
        targets = targets.to(device)

        # Forward pass
        outputs = model(inputs)

        # Denormalize outputs and targets for metric computation
        outputs_denorm = denorm(outputs)
        targets_denorm = denorm(targets)

        # Compute PSNR and SSIM
        psnr, ssim = compute_psnr_ssim(outputs_denorm, targets_denorm)
        psnr_total += psnr
        ssim_total += ssim
        count += 1

        # Optionally save sample visualizations
        if save_imgs and i < max_saved:
            save_result(inputs, outputs, targets, idx=0, save_path="eval_images", step=i)

# ---------- 
# Results 
# ----------
avg_psnr = psnr_total / count
avg_ssim = ssim_total / count

print("\n� Final Evaluation:")
print(f"Average PSNR: {avg_psnr:.2f}")
print(f"Average SSIM: {avg_ssim:.4f}")
