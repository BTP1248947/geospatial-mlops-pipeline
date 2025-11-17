# src/model.py
import torch
import torch.nn as nn
import torch.nn.functional as F

class DoubleConv(nn.Module):
    """(convolution => [BN] => ReLU) * 2"""
    def __init__(self, in_channels, out_channels, mid_channels=None):
        super().__init__()
        if not mid_channels:
            mid_channels = out_channels
        self.double_conv = nn.Sequential(
            nn.Conv2d(in_channels, mid_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(mid_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(mid_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        return self.double_conv(x)

class SiameseUNet(nn.Module):
    def __init__(self, in_channels=3, out_channels=1):
        super(SiameseUNet, self).__init__()
        
        # 1. The Shared Encoder (Contracting Path)
        self.inc = DoubleConv(in_channels, 64)
        self.down1 = nn.Sequential(nn.MaxPool2d(2), DoubleConv(64, 128))
        self.down2 = nn.Sequential(nn.MaxPool2d(2), DoubleConv(128, 256))
        self.down3 = nn.Sequential(nn.MaxPool2d(2), DoubleConv(256, 512))
        
        # 2. The Decoder (Expansive Path)
        
        # UP 1
        # Input: 1024 (512 from Image1 + 512 from Image2) -> Output: 512
        self.up1 = nn.ConvTranspose2d(1024, 512, kernel_size=2, stride=2)
        # FIX: Input is 512 (from up1), NOT 1024
        self.conv1 = DoubleConv(512, 512) 
        
        # UP 2
        # Input: 512 -> Output: 256
        self.up2 = nn.ConvTranspose2d(512, 256, kernel_size=2, stride=2)
        # FIX: Input is 256 (from up2), NOT 512
        self.conv2 = DoubleConv(256, 256)
        
        # UP 3
        # Input: 256 -> Output: 128
        self.up3 = nn.ConvTranspose2d(256, 128, kernel_size=2, stride=2)
        # FIX: Input is 128 (from up3), NOT 256
        self.conv3 = DoubleConv(128, 128)
        
        # Final output layer
        self.outc = nn.Conv2d(128, out_channels, kernel_size=1)

    def forward_once(self, x):
        """Passes one image through the encoder"""
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)
        x4 = self.down3(x3)
        return x4

    def forward(self, t1, t2):
        # Encode both images
        feat_t1 = self.forward_once(t1)
        feat_t2 = self.forward_once(t2)
        
        # Concatenate the deep features (512 + 512 = 1024 channels)
        x = torch.cat([feat_t1, feat_t2], dim=1)
        
        # Decode (Upscale)
        x = self.up1(x) # Becomes 512 channels
        x = self.conv1(x)
        
        x = self.up2(x) # Becomes 256 channels
        x = self.conv2(x)
        
        x = self.up3(x) # Becomes 128 channels
        x = self.conv3(x)
        
        logits = self.outc(x)
        return torch.sigmoid(logits)