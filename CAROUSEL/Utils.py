import matplotlib
matplotlib.use('Agg')  # Fuerza backend sin interfaz gráfica
import matplotlib.pyplot as plt
import torchvision.transforms.functional as TF
from torchvision.models import vgg16
from skimage.metrics import peak_signal_noise_ratio, structural_similarity
import numpy as np
import torch
import torch.nn.functional as F
import torch.nn as nn
import os

# ----------
# Image Visualization
# ----------
def show_images(inputs, targets, idx=0, save_path=None):
    """
    Visualiza fondo, avatar, máscara y ground truth de un sample del batch.
    """
    input_img = inputs[idx]
    target_img = targets[idx]

    fondo = input_img[0:3]
    avatar = input_img[3:6]
    mask = input_img[6]

    fondo_np = fondo.permute(1,2,0).cpu().numpy()
    avatar_np = avatar.permute(1,2,0).cpu().numpy()
    mask_np = mask.cpu().numpy()
    target_np = target_img.permute(1,2,0).cpu().numpy()

    def normalize_img(img):
        img = img - img.min()
        return img / img.max()

    fondo_np = normalize_img(fondo_np)
    avatar_np = normalize_img(avatar_np)
    target_np = normalize_img(target_np)

    fig, axs = plt.subplots(1,4, figsize=(15,5))
    axs[0].imshow(fondo_np); axs[0].set_title('Fondo limpio'); axs[0].axis('off')
    axs[1].imshow(avatar_np); axs[1].set_title('Avatar modificado'); axs[1].axis('off')
    axs[2].imshow(mask_np, cmap='gray'); axs[2].set_title('Máscara'); axs[2].axis('off')
    axs[3].imshow(target_np); axs[3].set_title('Ground truth'); axs[3].axis('off')

    if save_path:
        plt.savefig(save_path)
        print(f"Imagen guardada en {save_path}")
    else:
        plt.show()
    plt.close()

# ----------
# Basic Loss Function
# ----------
def loss_fn(output, target, mask=None):
    l1_total = F.l1_loss(output, target)
    if mask is not None:
        mask = mask.expand_as(output)
        l1_masked = torch.mean(mask * torch.abs(output - target))
        return l1_total + l1_masked
    else:
        return l1_total

# Denormalization
def denorm(tensor):
    return tensor * 0.5 + 0.5

# ----------
# Save Result Images
# ----------
def save_result(inputs, outputs, targets=None, idx=0, save_path="results/train_1024_transforms/", step=0):
    os.makedirs(save_path, exist_ok=True)
    input_img = inputs[idx].detach().cpu()
    output_img = outputs[idx].detach().cpu()
    target_img = targets[idx].detach().cpu()

    fondo = input_img[0:3]
    avatar = input_img[3:6]

    fondo = denorm(fondo).permute(1, 2, 0).numpy()
    avatar = denorm(avatar).permute(1, 2, 0).numpy()
    output = denorm(output_img).permute(1, 2, 0).numpy()
    target = denorm(target_img).permute(1, 2, 0).numpy()

    fig, axs = plt.subplots(1, 4, figsize=(20, 4))
    axs[0].imshow(fondo); axs[0].set_title("Fondo")
    axs[1].imshow(avatar); axs[1].set_title("Avatar")
    axs[2].imshow(output); axs[2].set_title("Output")
    axs[3].imshow(target); axs[3].set_title("Ground Truth")
    for ax in axs:
        ax.axis("off")

    plt.tight_layout()
    fname = os.path.join(save_path, f"idx_{idx:03d}_step_{step:04d}.png")
    plt.savefig(fname)
    plt.close()
    print(f"✅ Guardada imagen: {fname}")

# ----------
# Model Checkpointing
# ----------
def save_checkpoint(model, optimizer, epoch, loss, psnr=None, ssim=None, save_path="checkpoints", name="last.pt"):
    os.makedirs(save_path, exist_ok=True)
    path = os.path.join(save_path, name)
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'loss': loss,
    }
    if psnr is not None:
        checkpoint['psnr'] = psnr
    if ssim is not None:
        checkpoint['ssim'] = ssim
    torch.save(checkpoint, path)
    print(f"✅ Modelo guardado: {path}")

# ----------
# PSNR + SSIM Metrics
# ----------
def compute_psnr_ssim(output, target):
    psnr_total, ssim_total = 0.0, 0.0
    B = output.size(0)
    for i in range(B):
        out = output[i].detach().cpu().permute(1, 2, 0).numpy()
        tgt = target[i].detach().cpu().permute(1, 2, 0).numpy()
        out = np.clip(out, 0, 1)
        tgt = np.clip(tgt, 0, 1)
        psnr = peak_signal_noise_ratio(tgt, out, data_range=1.0)
        ssim = structural_similarity(tgt, out, multichannel=True, data_range=1.0)
        psnr_total += psnr
        ssim_total += ssim
    return psnr_total / B, ssim_total / B

# ----------
# Perceptual Loss Class
# ----------
class PerceptualLoss(nn.Module):
    def __init__(self, layer='relu2_2'):
        super().__init__()
        vgg = vgg16(pretrained=True).features[:9].eval()  # hasta relu2_2
        for param in vgg.parameters():
            param.requires_grad = False
        self.vgg = vgg

    def forward(self, x, y):
        return F.l1_loss(self.vgg(x), self.vgg(y))

# ----------
# Composite Loss Function
# ----------
def loss_fn(pred, gt, input_tensor, mask, perceptual_model, weights=(1.0, 0.5, 0.5)):
    """
    Combina:
    - L1 entre pred y ground truth
    - Perceptual loss entre pred y ground truth
    - L1 entre pred y avatar original en la región de la máscara
    """
    λ1, λ2, λ3 = weights
    loss_l1 = F.l1_loss(pred, gt)

    pred_vgg = denorm(pred).clamp(0, 1)
    gt_vgg = denorm(gt).clamp(0, 1)
    loss_perceptual = perceptual_model(pred_vgg, gt_vgg)

    input_avatar = input_tensor[:, 3:6, :, :]
    mask_expanded = mask.expand_as(pred)
    loss_mask = torch.mean(mask_expanded * torch.abs(pred - input_avatar))

    return λ1 * loss_l1 + λ2 * loss_perceptual + λ3 * loss_mask
