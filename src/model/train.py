# src/model/train.py
import argparse
import os
import torch
from torch.utils.data import DataLoader
import torch.nn as nn
import torch.optim as optim
from tqdm import tqdm
import mlflow
import pandas as pd

# relative imports (package style). This file should be executed as:
# python -m src.model.train ...
from .model import build_unet_in6
from .dataset import LEVIRChangeDataset

def dice_loss(pred, target, eps=1e-6):
    prob = torch.sigmoid(pred)
    num = 2 * (prob * target).sum(dim=(1,2,3))
    den = prob.sum(dim=(1,2,3)) + target.sum(dim=(1,2,3))
    loss = 1 - (num + eps) / (den + eps)
    return loss.mean()

def train_one_epoch(model, loader, optimz, device, criterion):
    model.train()
    running_loss = 0.0
    for x,y in tqdm(loader, desc="train"):
        x = x.to(device); y = y.to(device)
        optimz.zero_grad()
        logits = model(x)
        loss = criterion(logits, y) + dice_loss(logits, y)
        loss.backward()
        optimz.step()
        running_loss += loss.item() * x.size(0)
    return running_loss / len(loader.dataset)

def validate(model, loader, device, criterion):
    model.eval()
    running_loss=0.0
    with torch.no_grad():
        for x,y in tqdm(loader, desc="val"):
            x = x.to(device); y=y.to(device)
            logits = model(x)
            loss = criterion(logits, y) + dice_loss(logits, y)
            running_loss += loss.item() * x.size(0)
    return running_loss / len(loader.dataset)

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--mapping", required=True)
    p.add_argument("--batch", type=int, default=4)
    p.add_argument("--epochs", type=int, default=10)
    p.add_argument("--encoder", default="resnet34")
    p.add_argument("--weights", default="imagenet")
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--out", default="trained.pth")
    return p.parse_args()

def main():
    args = parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("Device:", device)

    # read mapping and split
    df = pd.read_csv(args.mapping)
    if len(df) < 2:
        raise RuntimeError("Mapping CSV seems too small. Add rows or check path.")
    train_df = df.sample(frac=0.9, random_state=42)
    val_df = df.drop(train_df.index)
    train_csv = "train_tmp.csv"
    val_csv = "val_tmp.csv"
    train_df.to_csv(train_csv, index=False)
    val_df.to_csv(val_csv, index=False)

    train_ds = LEVIRChangeDataset(train_csv)
    val_ds   = LEVIRChangeDataset(val_csv)

    train_loader = DataLoader(train_ds, batch_size=args.batch, shuffle=True, num_workers=0, pin_memory=False)
    val_loader   = DataLoader(val_ds, batch_size=args.batch, shuffle=False, num_workers=0, pin_memory=False)

    model = build_unet_in6(encoder_name=args.encoder, encoder_weights=(args.weights if args.weights!="none" else None), classes=1, device=device)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)

    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("PlanetSentinel")

    best_val = float("inf")
    with mlflow.start_run():
        mlflow.log_params({"encoder":args.encoder, "batch":args.batch, "epochs":args.epochs, "lr":args.lr})
        for epoch in range(1, args.epochs+1):
            print(f"Epoch {epoch}/{args.epochs}")
            train_loss = train_one_epoch(model, train_loader, optimizer, device, criterion)
            val_loss = validate(model, val_loader, device, criterion)
            mlflow.log_metrics({"train_loss": train_loss, "val_loss": val_loss}, step=epoch)
            print(f"train_loss={train_loss:.4f} val_loss={val_loss:.4f}")
            # save checkpoint and best
            ckpt = f"checkpoint_epoch{epoch}.pth"
            torch.save(model.state_dict(), ckpt)
            if val_loss < best_val:
                best_val = val_loss
                torch.save(model.state_dict(), args.out)
                print("Saved best", args.out)

    # save inference artifact copy
    torch.save(model.state_dict(), "model_inference.pth")
    # cleanup temp csvs
    try:
        os.remove(train_csv)
        os.remove(val_csv)
    except Exception:
        pass
    print("Training complete. Artifacts: ", args.out, "model_inference.pth")

if __name__ == "__main__":
    import os
    main()
