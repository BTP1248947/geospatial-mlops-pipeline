# app/main.py
from fastapi import FastAPI, UploadFile, File
import torch
from src.model import SiameseUNet
import io
from PIL import Image
import torchvision.transforms as T

app = FastAPI()

# Load Model (Global Variable)
model = SiameseUNet()
# Load weights - ensure 'model_final.pth' is inside the container
# model.load_state_dict(torch.load("model_final.pth", map_location=torch.device('cpu')))
model.eval()

transform = T.Compose([
    T.Resize((128, 128)),
    T.ToTensor()
])

@app.post("/predict")
async def predict(file_before: UploadFile = File(...), file_after: UploadFile = File(...)):
    # Read Images
    img1 = Image.open(io.BytesIO(await file_before.read())).convert("RGB")
    img2 = Image.open(io.BytesIO(await file_after.read())).convert("RGB")
    
    # Preprocess
    t1 = transform(img1).unsqueeze(0)
    t2 = transform(img2).unsqueeze(0)
    
    # Inference
    with torch.no_grad():
        prediction = model(t1, t2)
    
    # Postprocess (thresholding)
    mask = (prediction > 0.5).float().numpy()
    
    # Calculate anomaly percentage
    anomaly_score = mask.mean()
    
    return {
        "anomaly_score": float(anomaly_score), 
        "status": "Anomaly Detected" if anomaly_score > 0.1 else "Normal"
    }