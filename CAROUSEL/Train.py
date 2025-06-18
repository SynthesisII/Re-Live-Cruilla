import torch
from torch.utils.data import DataLoader
from torchvision import transforms
from Dataset import AvatarFusionDataset
from Utils import *
from Model import AvatarFusionModel
import torch.optim as optim

# ----------
# Configuration
# ----------
lr = 1e-4
batch_size = 5
num_epochs = 100
loss_general = 1
loss_perceptual = 0.5
loss_mask = 0.5
weights = (loss_general, loss_perceptual, loss_mask)
data_path = "/export/hhome/uabcru03/Carrousel/Dataset_collage/"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Usando dispositivo: {device}")

# ----------
# Transforms
# ----------
transform = transforms.Compose([
    transforms.Resize((1024, 1024)), 
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5]*3, std=[0.5]*3)
])

transform_avatar = transforms.Compose([
    transforms.Resize((1024, 1024)),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.05),
    transforms.RandomPerspective(distortion_scale=0.5, p=0.5),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5]*3, std=[0.5]*3)
])

# ----------
# Dataset & Dataloader
# ----------
dataset = AvatarFusionDataset(data_path, transform=transform, transform_avatar=transform_avatar, position=True)
dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=4, drop_last=True)
print("Dataloader creado")

# ----------
# Model, Loss & Optimizer
# ----------
model = AvatarFusionModel().to(device)
print("Modelo AvatarFusion creado")

perceptual_model = PerceptualLoss().to(device)
print("Modelo Perceptual Loss creado")

optimizer = optim.Adam(model.parameters(), lr=lr)
print("Optimazer creado")

# ----------
# Training Loop
# ----------
model.train()
best_loss = float('inf')
total_batches = len(dataloader)

for epoch in range(num_epochs):
    running_loss = 0.0

    for i, (inputs, targets, masks) in enumerate(dataloader):
        print(f"[Epoch {epoch+1} | Batch {i+1}/{total_batches}]")

        inputs = inputs.to(device)
        targets = targets.to(device)
        masks = masks.to(device)

        optimizer.zero_grad()
        outputs = model(inputs)

        loss = loss_fn(outputs, targets, inputs, masks, perceptual_model, weights)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()

        # Save a few sample outputs
        if i < 5:
            save_result(inputs, outputs, targets, idx=i, step=epoch)

    # ----------
    # End of Epoch Logging & Checkpoint
    # ----------
    avg_loss = running_loss / len(dataloader)
    outputs_denorm = denorm(outputs)
    targets_denorm = denorm(targets)

    print(f"Epoch {epoch+1}/{num_epochs} - Loss: {avg_loss:.4f}")

    if avg_loss < best_loss:
        best_loss = avg_loss
        save_checkpoint(model, optimizer, epoch, best_loss, name="train_1024_transforms.pt")
