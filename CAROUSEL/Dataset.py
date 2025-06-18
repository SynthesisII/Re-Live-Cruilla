import torch
from torch.utils.data import Dataset
from torchvision import transforms
from PIL import Image
import cv2
import os

class AvatarFusionDataset(Dataset):
    def __init__(self, data_path, transform=None, transform_avatar=None, position=False, alone=False):
        """
        Custom dataset for avatar fusion from 4-part collage images.

        Args:
            data_path (str): Path to the folder containing collage images.
            transform (callable, optional): Transformations for general images (e.g., GT and background).
            transform_avatar (callable, optional): Transformations specifically for the avatar image.
            position (bool): If True, uses the 4-part collage format (GT, background, avatar, mask).
            alone (bool): Reserved for future use. If True, avatar is alone (not implemented).
        """
        self.data_path = data_path
        self.transform = transform
        self.transform_avatar = transform_avatar
        self.position = position
        self.alone = alone

        # ----------
        # Load Image Paths
        # ----------
        self.image_paths = sorted([
            os.path.join(data_path, f)
            for f in os.listdir(data_path)
            if f.lower().endswith(('.jpg', '.png', '.jpeg'))
        ])

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img_path = self.image_paths[idx]

        if not self.position:
            if self.alone:
                raise NotImplementedError("Mode 'alone' is not implemented.")
            else:
                raise ValueError("You must specify either position=True or alone=True")

        # ----------
        # Load and Split Collage into 4 Parts
        # ----------
        collage = cv2.imread(img_path)
        if collage is None:
            raise RuntimeError(f"Failed to load image: {img_path}")
        collage = cv2.cvtColor(collage, cv2.COLOR_BGR2RGB)

        h, w, _ = collage.shape
        part_width = w // 4

        gt     = Image.fromarray(collage[:, 0*part_width:1*part_width, :])
        fondo  = Image.fromarray(collage[:, 1*part_width:2*part_width, :])
        avatar = Image.fromarray(collage[:, 2*part_width:3*part_width, :])
        mask   = Image.fromarray(collage[:, 3*part_width:4*part_width, :]).convert("L")

        # ----------
        # Apply Transforms
        # ----------
        if self.transform:
            gt = self.transform(gt)
            fondo = self.transform(fondo)
        if self.transform_avatar:
            avatar = self.transform_avatar(avatar)

        mask = transforms.Compose([
            transforms.Resize((1024, 1024)),
            transforms.ToTensor()
        ])(mask)

        # ----------
        # Combine Inputs and Return
        # ----------
        input_tensor = torch.cat([fondo, avatar], dim=0)  # Shape: [6, H, W]
        return input_tensor, gt, mask

    def debug_shapes(self, idx):
        """
        Debugging method to print shapes of collage components for a given index.
        """
        img_path = self.image_paths[idx]
        collage = cv2.imread(img_path)
        if collage is None:
            print(f"Failed to load image: {img_path}")
            return

        collage = cv2.cvtColor(collage, cv2.COLOR_BGR2RGB)
        h, w, _ = collage.shape
        part_width = w // 4

        print("gt:", collage[:, 0*part_width:1*part_width, :].shape)
        print("fondo:", collage[:, 1*part_width:2*part_width, :].shape)
        print("avatar:", collage[:, 2*part_width:3*part_width, :].shape)
        print("mask:", collage[:, 3*part_width:4*part_width, :].shape)
