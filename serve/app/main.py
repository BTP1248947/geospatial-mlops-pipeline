#!/usr/bin/env python3
"""
Simple FastAPI server that accepts two uploaded GeoTIFFs (before/after) and returns a prediction mask (.npy)
This is a minimal working server to verify end-to-end functionality.
"""
from fastapi import FastAPI, File, UploadFile, HTTPException
import uvicorn, tempfile, os, numpy as np, rasterio, torch
from train.model.siamese_unet import SiameseUNet

app = FastAPI(title="Geospatial Change Detection API")

MODEL_PATH = os.environ.get("MODEL_PATH", "runs/model_inference.pth")
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = SiameseUNet(in_ch=6).to(DEVICE)
if os.path.exists(MODEL_PATH):
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
model.eval()

@app.get("/health")
async def health():
    return {"status":"ok", "model_loaded": os.path.exists(MODEL_PATH)}

def read_tiff_bytes(data: bytes):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".tif")
    tmp.write(data)
    tmp.close()
    return tmp.name

def predict_sliding(model, b_path, a_path, chip_size=256, stride=256):
    """
    Runs inference on large images by chopping them into chips.
    """
    with rasterio.open(b_path) as src_b, rasterio.open(a_path) as src_a:
        h, w = src_b.height, src_b.width
        profile = src_b.profile
        
        # Read entire images into RAM (assuming they fit in RAM, just not GPU RAM)
        # For truly massive images, we would read window-by-window from disk too.
        img_b = src_b.read().astype('float32') / 10000.0
        img_a = src_a.read().astype('float32') / 10000.0
        
    # Output mask
    prob_map = np.zeros((h, w), dtype=np.float32)
    counts = np.zeros((h, w), dtype=np.float32)
    
    # Sliding window loop
    for y in range(0, h, stride):
        for x in range(0, w, stride):
            y_end = min(h, y + chip_size)
            x_end = min(w, x + chip_size)
            
            # Extract chip (pad if needed)
            b_chip = img_b[:, y:y_end, x:x_end]
            a_chip = img_a[:, y:y_end, x:x_end]
            
            # Pad if smaller than chip_size
            cy, cx = b_chip.shape[1], b_chip.shape[2]
            if cy < chip_size or cx < chip_size:
                pad_y = chip_size - cy
                pad_x = chip_size - cx
                b_chip = np.pad(b_chip, ((0,0), (0,pad_y), (0,pad_x)))
                a_chip = np.pad(a_chip, ((0,0), (0,pad_y), (0,pad_x)))
            
            # To Tensor
            tb = torch.from_numpy(b_chip).unsqueeze(0).to(DEVICE)
            ta = torch.from_numpy(a_chip).unsqueeze(0).to(DEVICE)
            
            # Inference
            with torch.no_grad():
                out = model(tb, ta)
                prob = out.sigmoid().squeeze(0).squeeze(0).cpu().numpy()
            
            # Crop back if padded
            valid_prob = prob[:cy, :cx]
            
            # Accumulate
            prob_map[y:y_end, x:x_end] = valid_prob
            counts[y:y_end, x:x_end] = 1 # Simple stitching (no overlap averaging for speed)

    return prob_map

@app.post("/predict")
async def predict(before: UploadFile = File(...), after: UploadFile = File(...)):
    before_bytes = await before.read()
    after_bytes = await after.read()
    bpath = read_tiff_bytes(before_bytes)
    apath = read_tiff_bytes(after_bytes)
    try:
        # Use sliding window inference
        prob_map = predict_sliding(model, bpath, apath)
        
        # return a small npy as proof-of-concept (client can save & view)
        outfile = tempfile.NamedTemporaryFile(delete=False, suffix=".npy")
        np.save(outfile, prob_map)
        return {"result_npy": outfile.name, "shape": prob_map.shape}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(bpath): os.unlink(bpath)
        if os.path.exists(apath): os.unlink(apath)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
