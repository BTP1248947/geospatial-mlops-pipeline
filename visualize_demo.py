"""
visualize_demo.py - Show predictions visually using matplotlib

This script:
1. Generates fake before/after satellite images
2. Runs the model to detect changes
3. Shows the results in a nice grid
"""
import torch
import numpy as np
import matplotlib.pyplot as plt
from train.model.siamese_unet import SiameseUNet

def generate_fake_images():
    """Generate realistic-looking satellite images with deforestation"""
    # Before: Dense forest (greenish)
    before = np.random.rand(6, 256, 256) * 0.3 + 0.4
    before[1] = np.random.rand(256, 256) * 0.3 + 0.5  # Green channel higher
    
    # After: Same image but with a deforested patch
    after = before.copy()
    # Create deforestation in center (brown/bare soil)
    y, x = np.ogrid[0:256, 0:256]
    mask = ((x - 128)**2 + (y - 128)**2) < 40**2  # Circle of deforestation
    after[0, mask] = 0.6  # Red (bare soil)
    after[1, mask] = 0.4  # Less green
    after[2, mask] = 0.3  # Less blue
    
    # Ground truth: where deforestation actually happened
    true_mask = mask.astype(float)
    
    return before, after, true_mask

def visualize_prediction():
    print("Loading model...")
    device = torch.device("cpu")
    model = SiameseUNet(in_ch=6).to(device)
    
    try:
        model.load_state_dict(torch.load("runs/model_inference.pth", map_location=device))
        print("✓ Loaded trained model")
    except:
        print("⚠️ No trained model found, using random weights (for demo only)")
    
    model.eval()
    
    print("Generating demo images...")
    before, after, true_mask = generate_fake_images()
    
    # Run prediction
    print("Running model inference...")
    with torch.no_grad():
        b_tensor = torch.from_numpy(before).unsqueeze(0).float()
        a_tensor = torch.from_numpy(after).unsqueeze(0).float()
        prediction = model(b_tensor, a_tensor)
        pred_mask = prediction.sigmoid().squeeze().cpu().numpy()
    
    # Create visualization
    print("Creating visualization...")
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('Geospatial Change Detection - Demo Results', fontsize=16, fontweight='bold')
    
    # Before image (RGB approximation)
    before_rgb = np.stack([before[3], before[2], before[1]], axis=-1)  # NIR, Red, Green
    before_rgb = np.clip(before_rgb * 2, 0, 1)  # Enhance for visualization
    axes[0, 0].imshow(before_rgb)
    axes[0, 0].set_title('Before (2021 Satellite Image)', fontsize=12)
    axes[0, 0].axis('off')
    
    # After image (RGB approximation)
    after_rgb = np.stack([after[3], after[2], after[1]], axis=-1)
    after_rgb = np.clip(after_rgb * 2, 0, 1)
    axes[0, 1].imshow(after_rgb)
    axes[0, 1].set_title('After (2022 Satellite Image)', fontsize=12)
    axes[0, 1].axis('off')
    
    # Ground truth (what we know is deforested)
    axes[0, 2].imshow(true_mask, cmap='Reds', vmin=0, vmax=1)
    axes[0, 2].set_title('Ground Truth (Actual Deforestation)', fontsize=12)
    axes[0, 2].axis('off')
    
    # Model prediction
    axes[1, 0].imshow(pred_mask, cmap='Reds', vmin=0, vmax=1)
    axes[1, 0].set_title('Model Prediction (Detected Change)', fontsize=12)
    axes[1, 0].axis('off')
    
    # Thresholded prediction (binary)
    pred_binary = (pred_mask > 0.5).astype(float)
    axes[1, 1].imshow(pred_binary, cmap='Reds', vmin=0, vmax=1)
    axes[1, 1].set_title('Binary Detection (Threshold = 0.5)', fontsize=12)
    axes[1, 1].axis('off')
    
    # Overlay on after image
    overlay = after_rgb.copy()
    overlay[pred_binary > 0.5] = [1, 0, 0]  # Red for detected deforestation
    axes[1, 2].imshow(overlay)
    axes[1, 2].set_title('Overlay (Red = Detected Deforestation)', fontsize=12)
    axes[1, 2].axis('off')
    
    plt.tight_layout()
    
    # Save the figure
    output_path = 'demo_results.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ Saved visualization to: {output_path}")
    
    # Show the plot
    print("✓ Displaying results...")
    plt.show()

if __name__ == "__main__":
    print("=" * 60)
    print("GEOSPATIAL CHANGE DETECTION - VISUALIZATION DEMO")
    print("=" * 60)
    visualize_prediction()
    print("\n✓ Demo complete!")
