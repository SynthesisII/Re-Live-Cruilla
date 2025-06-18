import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision.models import resnet50

# ----------------------------
# Simple Decoder for Baseline
# ----------------------------
class SimpleDecoder(nn.Module):
    def __init__(self, in_channels=2048):
        super().__init__()
        self.up1 = nn.ConvTranspose2d(in_channels, 512, kernel_size=2, stride=2)
        self.conv1 = nn.Sequential(nn.Conv2d(512, 256, kernel_size=3, padding=1), nn.ReLU())

        self.up2 = nn.ConvTranspose2d(256, 128, kernel_size=2, stride=2)
        self.conv2 = nn.Sequential(nn.Conv2d(128, 64, kernel_size=3, padding=1), nn.ReLU())

        self.up3 = nn.ConvTranspose2d(64, 32, kernel_size=2, stride=2)
        self.conv3 = nn.Sequential(nn.Conv2d(32, 16, kernel_size=3, padding=1), nn.ReLU())

        self.out_conv = nn.Conv2d(16, 3, kernel_size=1)  # RGB output

    def forward(self, x):
        x = self.up1(x); x = self.conv1(x)
        x = self.up2(x); x = self.conv2(x)
        x = self.up3(x); x = self.conv3(x)
        return self.out_conv(x)


# ----------------------------
# Simple ResNet50 + Decoder Model
# ----------------------------
class AvatarFusionModel_0(nn.Module):
    def __init__(self):
        super().__init__()
        resnet = resnet50(pretrained=True)

        # Modify first layer to accept 7 input channels
        resnet.conv1 = nn.Conv2d(7, 64, kernel_size=7, stride=2, padding=3, bias=False)

        self.encoder = nn.Sequential(*list(resnet.children())[:-2])  # up to conv5_x
        self.decoder = SimpleDecoder()

    def forward(self, x):
        feats = self.encoder(x)
        return self.decoder(feats)


# ----------------------------
# Encoder with Skip Connections
# ----------------------------
class AvatarFusionEncoder(nn.Module):
    def __init__(self, in_channels=6, freeze=False):
        super().__init__()
        resnet = resnet50(pretrained=True)
        resnet.conv1 = nn.Conv2d(in_channels, 64, kernel_size=7, stride=2, padding=3, bias=False)

        # Encoder stages
        self.initial = nn.Sequential(resnet.conv1, resnet.bn1, resnet.relu, resnet.maxpool)
        self.layer1 = resnet.layer1  # Output: [B, 256, 64, 64]
        self.layer2 = resnet.layer2  # Output: [B, 512, 32, 32]
        self.layer3 = resnet.layer3  # Output: [B, 1024, 16, 16]
        self.layer4 = resnet.layer4  # Output: [B, 2048, 8, 8]

        if freeze:
            for param in self.parameters():
                param.requires_grad = False

    def forward(self, x):
        skips = {}
        x = self.initial(x)
        skips['layer1'] = self.layer1(x)
        skips['layer2'] = self.layer2(skips['layer1'])
        skips['layer3'] = self.layer3(skips['layer2'])
        x = self.layer4(skips['layer3'])
        return x, skips


# ----------------------------
# Transformer Decoder with Skip Connections
# ----------------------------
class TransformerDecoder(nn.Module):
    def __init__(self, token_dim=2048, num_tokens=64):
        super().__init__()

        self.pos_embed = nn.Parameter(torch.randn(1, num_tokens, token_dim))
        self.transformer = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(d_model=token_dim, nhead=8, dim_feedforward=4096),
            num_layers=4
        )

        self.reproject = nn.Sequential(
            # 16x16
            nn.Conv2d(token_dim + 1024, 512, kernel_size=3, padding=1), nn.ReLU(),
            nn.Upsample(scale_factor=2),  # → 32x32

            nn.Conv2d(512 + 512, 256, kernel_size=3, padding=1), nn.ReLU(),
            nn.Upsample(scale_factor=2),  # → 64x64

            nn.Conv2d(256 + 256, 128, kernel_size=3, padding=1), nn.ReLU(),
            nn.Upsample(scale_factor=2),  # → 128x128

            nn.Conv2d(128, 64, kernel_size=3, padding=1), nn.ReLU(),
            nn.Upsample(scale_factor=2),  # → 256x256

            nn.Conv2d(64, 3, kernel_size=1)  # RGB output
        )

    def forward(self, x, skips):
        B, C, H, W = x.shape  # [B, 2048, 8, 8]
        x = x.flatten(2).permute(0, 2, 1)  # [B, 64, 2048]
        x = x + self.pos_embed
        x = self.transformer(x)
        x = x.permute(0, 2, 1).view(B, C, H, W)  # [B, 2048, 8, 8]

        # Step-by-step upsampling with skip connections
        x = F.interpolate(x, scale_factor=2, mode='bilinear', align_corners=False)  # 8→16
        x = torch.cat([x, skips['layer3']], dim=1)

        x = self.reproject[0](x); x = self.reproject[1](x); x = self.reproject[2](x)
        x = torch.cat([x, skips['layer2']], dim=1)

        x = self.reproject[3](x); x = self.reproject[4](x); x = self.reproject[5](x)
        x = torch.cat([x, skips['layer1']], dim=1)

        return self.reproject[6:](x)  # Remaining convs + upsampling


# ----------------------------
# Full Avatar Fusion Model
# ----------------------------
class AvatarFusionModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = AvatarFusionEncoder(in_channels=6, freeze=False)
        self.decoder = TransformerDecoder()

    def forward(self, x):
        feats, skips = self.encoder(x)
        return self.decoder(feats, skips)
