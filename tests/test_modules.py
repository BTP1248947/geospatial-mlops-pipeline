import torch
import pytest
import sys
import os

# Fix import path so we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from model import SiameseUNet
import config

def test_model_structure():
    """Checks if the model initializes without crashing."""
    model = SiameseUNet()
    assert model is not None
    print("Model initialization test passed.")

def test_forward_pass():
    """Checks if the model accepts input and returns the correct shape."""
    model = SiameseUNet()
    
    # Create dummy random tensors (Batch=1, Channels=3, Height=128, Width=128)
    dummy_input1 = torch.randn(1, 3, config.IMG_HEIGHT, config.IMG_WIDTH)
    dummy_input2 = torch.randn(1, 3, config.IMG_HEIGHT, config.IMG_WIDTH)
    
    output = model(dummy_input1, dummy_input2)
    
    # Expect output shape: (1, 1, 128, 128) -> Batch, MaskChannel, H, W
    assert output.shape == (1, 1, config.IMG_HEIGHT, config.IMG_WIDTH)
    
    # Output values should be between 0 and 1 (Sigmoid)
    assert output.min() >= 0
    assert output.max() <= 1
    print("Forward pass shape check passed.")

def test_overfit_small_batch():
    """Optional: Sanity check. Can the model learn a single example?"""
    model = SiameseUNet()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    criterion = torch.nn.BCELoss()
    
    t1 = torch.randn(1, 3, 64, 64)
    t2 = torch.randn(1, 3, 64, 64)
    target = torch.ones(1, 1, 64, 64) # All ones (dummy target)
    
    # Train for a few steps
    for _ in range(5):
        optimizer.zero_grad()
        output = model(t1, t2)
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()
    
    # Loss should decrease (very basic check)
    final_loss = criterion(model(t1, t2), target).item()
    assert final_loss < 1.0
    print("Overfit sanity check passed.")