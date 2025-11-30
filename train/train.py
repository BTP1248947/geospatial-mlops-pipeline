import argparse, glob, os
import torch, torch.nn as nn, torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import rasterio
import numpy as np
import mlflow
from train.model.siamese_unet import SiameseUNet

class ChipDataset(Dataset):
    def __init__(self, folder):
        # Support both .tif and .png
        self.before = sorted(glob.glob(os.path.join(folder, "*_before.tif")) + glob.glob(os.path.join(folder, "*_before.png")))
    def __len__(self): return len(self.before)
    def __getitem__(self, idx):
        bfile = self.before[idx]
        ext = os.path.splitext(bfile)[1]
        afile = bfile.replace(f"_before{ext}", f"_after{ext}")
        mfile = bfile.replace(f"_before{ext}", f"_mask{ext}")
        
        with rasterio.open(bfile) as ds:
            b = ds.read().astype('float32')
            if ext == '.tif':
                b /= 10000.0
            elif ext == '.png':
                b /= 255.0
            
        with rasterio.open(afile) as ds:
            a = ds.read().astype('float32')
            if ext == '.tif':
                a /= 10000.0
            elif ext == '.png':
                a /= 255.0

        with rasterio.open(mfile) as ds:
            m = ds.read(1).astype('float32')
            # Mask is 0 or 255 for PNGs, 0 or 1 for TIFFs (already normalized)
            if ext == '.png' and m.max() > 1.0: # Assuming mask PNGs are 0 or 255
                m /= 255.0
            
        return torch.from_numpy(b), torch.from_numpy(a), torch.from_numpy(m).unsqueeze(0)

def calculate_metrics(pred, target, threshold=0.5):
    pred_bin = (torch.sigmoid(pred) > threshold).float()
    target = target.float()
    
    tp = (pred_bin * target).sum().item()
    fp = (pred_bin * (1 - target)).sum().item()
    fn = ((1 - pred_bin) * target).sum().item()
    tn = ((1 - pred_bin) * (1 - target)).sum().item()
    
    precision = tp / (tp + fp + 1e-8)
    recall = tp / (tp + fn + 1e-8)
    f1 = 2 * (precision * recall) / (precision + recall + 1e-8)
    accuracy = (tp + tn) / (tp + tn + fp + fn + 1e-8)
    
    return precision, recall, f1, accuracy

def train_loop(args):
    ds = ChipDataset(args.data_dir)
    print(f"DEBUG: dataset length = {len(ds)}")
    dl = DataLoader(ds, batch_size=args.batch_size, shuffle=True, num_workers=0)
    device = torch.device("cuda" if torch.cuda.is_available() else ("mps" if getattr(torch, "has_mps", False) and torch.has_mps else "cpu"))
    print("Using device:", device)
    model = SiameseUNet(in_ch=6).to(device)
    
    opt = optim.Adam(model.parameters(), lr=args.lr)
    bce = nn.BCEWithLogitsLoss()
    mlflow.set_experiment(args.experiment)
    with mlflow.start_run():
        mlflow.log_params({"epochs": args.epochs, "batch_size": args.batch_size, "lr": args.lr})
        for ep in range(args.epochs):
            model.train()
            epoch_loss = 0.0
            epoch_prec = 0.0
            epoch_rec = 0.0
            epoch_f1 = 0.0
            epoch_acc = 0.0
            
            for i, (b,a,m) in enumerate(dl):
                # Handle channel mismatch (3 vs 6)
                if b.shape[1] == 3:
                    # Pad with zeros to make it 6
                    # (B, 3, H, W) -> (B, 6, H, W)
                    b = torch.cat([b, b], dim=1) # simple duplication
                    a = torch.cat([a, a], dim=1)
                
                b = b.to(device); a = a.to(device); m = m.to(device)
                out = model(b, a)
                loss = bce(out, m)
                
                prec, rec, f1, acc = calculate_metrics(out, m)
                epoch_prec += prec
                epoch_rec += rec
                epoch_f1 += f1
                epoch_acc += acc
                
                opt.zero_grad(); loss.backward(); opt.step()
                epoch_loss += loss.item()
                if i % 10 == 0:
                    print(f"ep={ep} step={i} loss={loss.item():.4f}")
            
            avg_loss = epoch_loss / max(1, len(dl))
            avg_prec = epoch_prec / max(1, len(dl))
            avg_rec = epoch_rec / max(1, len(dl))
            avg_f1 = epoch_f1 / max(1, len(dl))
            avg_acc = epoch_acc / max(1, len(dl))
            
            print(f"Epoch {ep} loss {avg_loss:.4f} prec {avg_prec:.4f} rec {avg_rec:.4f} f1 {avg_f1:.4f} acc {avg_acc:.4f}")
            mlflow.log_metric("train_loss", avg_loss, step=ep)
            mlflow.log_metric("train_precision", avg_prec, step=ep)
            mlflow.log_metric("train_recall", avg_rec, step=ep)
            mlflow.log_metric("train_f1", avg_f1, step=ep)
            mlflow.log_metric("train_accuracy", avg_acc, step=ep)
        # save model
        os.makedirs("runs", exist_ok=True)
        model_path = "runs/model_inference.pth"
        torch.save(model.state_dict(), model_path)
        mlflow.log_artifact(model_path)
        print("[OK] model saved to", model_path)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", default="data/chips")
    p.add_argument("--epochs", type=int, default=2)
    p.add_argument("--batch-size", type=int, default=2)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--experiment", default="deforestation_demo")
    args = p.parse_args()
    train_loop(args)