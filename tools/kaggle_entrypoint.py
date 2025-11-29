
import os
import zipfile
import subprocess
import sys
import shutil

def run_command(cmd):
    print(f"[RUN] {cmd}")
    subprocess.check_call(cmd, shell=True)

def main():
    print("=== Kaggle Entrypoint Started ===")
    
    # 1. Setup paths
    # Kaggle input is read-only. We must work in /kaggle/working
    INPUT_DIR = "/kaggle/input/geospatial-pipeline-context"
    WORK_DIR = "/kaggle/working"
    
    print(f"Listing /kaggle/input: {os.listdir('/kaggle/input')}")
    
    # Try to find the correct input dir dynamically
    if not os.path.exists(INPUT_DIR):
        print(f"[WARN] {INPUT_DIR} not found. Searching...")
        for d in os.listdir("/kaggle/input"):
            potential_path = os.path.join("/kaggle/input", d)
            if os.path.isdir(potential_path):
                print(f"Checking {potential_path}: {os.listdir(potential_path)}")
                if "code.zip" in os.listdir(potential_path):
                    INPUT_DIR = potential_path
                    print(f"[INFO] Found dataset at: {INPUT_DIR}")
                    break
    
    os.chdir(WORK_DIR)
    
    # 2. Setup Code and Data
    print("Setting up code and data...")
    
    # Check for 'code' directory (auto-unzipped)
    code_dir = os.path.join(INPUT_DIR, "code")
    if os.path.exists(code_dir) and os.path.isdir(code_dir):
        print(f"Found code directory at {code_dir}. Copying...")
        # Copy contents of code_dir to WORK_DIR
        run_command(f"cp -r {code_dir}/* {WORK_DIR}/")
    elif os.path.exists(os.path.join(INPUT_DIR, "code.zip")):
        print("Found code.zip. Extracting...")
        with zipfile.ZipFile(os.path.join(INPUT_DIR, "code.zip"), 'r') as z:
            z.extractall(WORK_DIR)
    else:
        print("[ERR] Could not find code (zip or dir)!")
        print(f"Contents of {INPUT_DIR}: {os.listdir(INPUT_DIR)}")

    # Check for 'dataset' directory
    dataset_dir = os.path.join(INPUT_DIR, "dataset")
    if os.path.exists(dataset_dir) and os.path.isdir(dataset_dir):
        print(f"Found dataset directory at {dataset_dir}. Linking...")
        # We need data/chips
        os.makedirs("data", exist_ok=True)
        if os.path.exists(os.path.join(dataset_dir, "chips")):
             run_command(f"cp -r {dataset_dir}/chips data/chips")
    elif os.path.exists(os.path.join(INPUT_DIR, "dataset.zip")):
        print("Found dataset.zip. Extracting...")
        with zipfile.ZipFile(os.path.join(INPUT_DIR, "dataset.zip"), 'r') as z:
            z.extractall(WORK_DIR)
    else:
        print("[ERR] Could not find dataset (zip or dir)!")
        
    # 3. Install Dependencies
    print("Installing dependencies...")
    # We might need to upgrade pip first
    run_command("pip install --upgrade pip")
    if os.path.exists("requirements.txt"):
        run_command("pip install -r requirements.txt")
    
    # Install project package in editable mode if needed, or just set PYTHONPATH
    sys.path.append(WORK_DIR)
    
    # 4. Run Training
    print("Starting training...")
    # Disable MLflow server connection, let it log locally to ./mlruns
    os.environ["MLFLOW_TRACKING_URI"] = "sqlite:///mlflow.db"
    
    # Run training
    # Adjust parameters as needed for Kaggle GPU (e.g., larger batch size)
    run_command("python -m train.train --data-dir data/chips --epochs 20 --batch-size 32 --experiment kaggle_run")
    
    # 5. Package Outputs
    print("Packaging outputs...")
    output_zip = "kaggle_output.zip"
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as z:
        # Add runs folder (models)
        for root, dirs, files in os.walk("runs"):
            for file in files:
                z.write(os.path.join(root, file))
        # Add mlruns (metrics)
        for root, dirs, files in os.walk("mlruns"):
            for file in files:
                z.write(os.path.join(root, file))
        # Add mlflow.db
        if os.path.exists("mlflow.db"):
            z.write("mlflow.db")
            
    print(f"Created {output_zip}")
    print("=== Kaggle Entrypoint Finished ===")

if __name__ == "__main__":
    main()
