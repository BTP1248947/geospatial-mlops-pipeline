"""
demo_train.py - Quick demo training with synthetic data

This script generates fake satellite images and trains the model locally.
You can watch the loss decrease in real-time!
"""
import torch, torch.nn as nn, torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from train.model.siamese_unet import SiameseUNet

class FakeDataset(Dataset):
    """Generates random 'before' and 'after' images for demo purposes"""
    def __init__(self, num_samples=20):
        self.num_samples = num_samples
        
    def __len__(self): 
        return self.num_samples
    
    def __getitem__(self, idx):
        # Generate random satellite-like images (6 bands, 256x256)
        before = torch.randn(6, 256, 256) * 0.3 + 0.5  # Random "forest"
        after = before + torch.randn(6, 256, 256) * 0.1  # Slightly changed
        
        # Generate a random deforestation mask
        mask = (torch.randn(1, 256, 256) > 1.0).float()  # Random patches
        
        return before, after, mask

def train_demo(epochs=3):
    print("=" * 60)
    print("DEMO TRAINING - Geospatial Change Detection")
    print("=" * 60)
    
    # Create dataset
    ds = FakeDataset(num_samples=20)
    dl = DataLoader(ds, batch_size=4, shuffle=True)
    
    # Setup device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n✓ Using device: {device}")
    print(f"✓ Dataset size: {len(ds)} samples")
    print(f"✓ Batch size: 4")
    print(f"✓ Epochs: {epochs}\n")
    
    # Create model
    model = SiameseUNet(in_ch=6).to(device)
    opt = optim.Adam(model.parameters(), lr=3e-4)
    bce = nn.BCEWithLogitsLoss()
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    print(f"✓ Model has {total_params:,} parameters\n")
    
    print("Starting training...\n")
    
    for ep in range(epochs):
        model.train()
        epoch_loss = 0.0
        
        for i, (b, a, m) in enumerate(dl):
            b = b.to(device)
            a = a.to(device) 
            m = m.to(device)
            
            # Forward pass
            out = model(b, a)
            loss = bce(out, m)
            
            # Backward pass
            opt.zero_grad()
            loss.backward()
            opt.step()
            
            epoch_loss += loss.item()
            
            # Print progress
            if i % 2 == 0:
                print(f"  Epoch {ep+1}/{epochs} | Batch {i+1}/{len(dl)} | Loss: {loss.item():.4f}")
        
        avg_loss = epoch_loss / len(dl)
        print(f"\n→ Epoch {ep+1} Complete | Average Loss: {avg_loss:.4f}\n")
    
    # Save model
    print("=" * 60)
    print("✓ Training Complete!")
    print(f"✓ Model saved to: runs/model_inference.pth")
    print("=" * 60)
    
    torch.save(model.state_dict(), "runs/model_inference.pth")

if __name__ == "__main__":
    train_demo()
