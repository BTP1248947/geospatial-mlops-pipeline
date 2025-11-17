# src/train.py
import torch
import mlflow
from model import SiameseUNet
import config
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from model import SiameseUNet

def train():
    # 1. Setup MLflow
    mlflow.set_experiment("Satellite_Anomaly_Detection")
    
    with mlflow.start_run():
        # Log params
        mlflow.log_param("epochs", config.EPOCHS)
        mlflow.log_param("batch_size", config.BATCH_SIZE)
        
        # 2. Initialize Model
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = SiameseUNet().to(device)
        optimizer = torch.optim.Adam(model.parameters(), lr=config.LEARNING_RATE)
        criterion = torch.nn.BCELoss()
        
        print(f"Training on {device}...")
        
        # 3. Mock Training Loop (Replace with real DataLoader loop)
        for epoch in range(config.EPOCHS):
            # Fake inputs for demonstration
            t1 = torch.randn(8, 3, 128, 128).to(device)
            t2 = torch.randn(8, 3, 128, 128).to(device)
            labels = torch.randint(0, 2, (8, 1, 64, 64)).float().to(device) # Output size depends on architecture
            
            optimizer.zero_grad()
            outputs = model(t1, t2)
            
            # Resize labels to match output if necessary
            labels_resized = torch.nn.functional.interpolate(labels, size=outputs.shape[2:])
            
            loss = criterion(outputs, labels_resized)
            loss.backward()
            optimizer.step()
            
            print(f"Epoch {epoch}, Loss: {loss.item()}")
            mlflow.log_metric("loss", loss.item(), step=epoch)
            
        # 4. Save Model
        torch.save(model.state_dict(), "model_final.pth")
        mlflow.log_artifact("model_final.pth")
        print("Training Complete. Model saved.")

if __name__ == "__main__":
    train()