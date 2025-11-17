import torch
import argparse
from PIL import Image
import torchvision.transforms as T
import matplotlib.pyplot as plt
from model import SiameseUNet
import config
import os

def load_model(model_path):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = SiameseUNet().to(device)
    
    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path, map_location=device))
        print(f"Model loaded from {model_path}")
    else:
        print(f"Warning: No model found at {model_path}. Using random weights.")
    
    model.eval()
    return model, device

def preprocess_image(image_path):
    """Converts image path to tensor."""
    transform = T.Compose([
        T.Resize((config.IMG_HEIGHT, config.IMG_WIDTH)),
        T.ToTensor()
    ])
    img = Image.open(image_path).convert("RGB")
    return transform(img).unsqueeze(0) # Add batch dimension

def predict(before_path, after_path, output_path="result_mask.png"):
    model, device = load_model(config.MODEL_SAVE_PATH)
    
    t1 = preprocess_image(before_path).to(device)
    t2 = preprocess_image(after_path).to(device)
    
    with torch.no_grad():
        # Forward pass
        output = model(t1, t2)
        
        # Apply threshold to create binary mask (0 or 1)
        mask = (output > config.THRESHOLD).float().cpu().squeeze().numpy()
    
    # Save result
    plt.imsave(output_path, mask, cmap='gray')
    print(f"Prediction saved to {output_path}")
    
    # Simple anomaly score
    anomaly_score = mask.mean()
    print(f"Anomaly Score (Percentage of area changed): {anomaly_score * 100:.2f}%")

if __name__ == "__main__":
    # Example usage: python src/predict.py --before data/pre.jpg --after data/post.jpg
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", type=str, required=True, help="Path to pre-event image")
    parser.add_argument("--after", type=str, required=True, help="Path to post-event image")
    args = parser.parse_args()
    
    predict(args.before, args.after)