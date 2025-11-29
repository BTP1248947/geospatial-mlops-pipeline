
import os
import json
import shutil
import subprocess
import time
import argparse
import zipfile
from pathlib import Path

def run_cmd(cmd, cwd=None):
    print(f"[CMD] {cmd}")
    subprocess.check_call(cmd, shell=True, cwd=cwd)

def get_kaggle_username():
    # Try to read from ~/.kaggle/kaggle.json
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    if kaggle_json.exists():
        with open(kaggle_json) as f:
            data = json.load(f)
            return data.get("username")
    # Fallback: try env var
    return os.environ.get("KAGGLE_USERNAME")

def zip_folder(folder_path, output_path):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, os.path.dirname(folder_path))
                z.write(abs_path, rel_path)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", help="Kaggle username")
    args = parser.parse_args()

    username = args.username or get_kaggle_username()
    if not username:
        print("[ERR] Could not find Kaggle username. Set KAGGLE_USERNAME or ~/.kaggle/kaggle.json")
        return

    print(f"[INFO] Using Kaggle user: {username}")
    
    # Paths
    ROOT = Path(".").resolve()
    BUILD_DIR = ROOT / "build_kaggle"
    KERNEL_DIR = ROOT / "build_kernel"
    
    if BUILD_DIR.exists(): shutil.rmtree(BUILD_DIR)
    if KERNEL_DIR.exists(): shutil.rmtree(KERNEL_DIR)
    
    BUILD_DIR.mkdir()
    KERNEL_DIR.mkdir()

    # 1. Package Data
    print("[1/5] Packaging Data...")
    zip_folder("data/chips", BUILD_DIR / "dataset.zip")
    
    # 2. Package Code
    print("[2/5] Packaging Code...")
    with zipfile.ZipFile(BUILD_DIR / "code.zip", 'w', zipfile.ZIP_DEFLATED) as z:
        # Add train folder
        for root, dirs, files in os.walk("train"):
            for file in files:
                z.write(os.path.join(root, file))
        # Add requirements.txt
        if os.path.exists("requirements.txt"):
            z.write("requirements.txt")
            
    # 3. Create/Update Dataset
    print("[3/5] Updating Dataset...")
    dataset_slug = "geospatial-pipeline-context"
    dataset_id = f"{username}/{dataset_slug}"
    
    # Create metadata
    meta = {
        "title": "Geospatial Pipeline Context",
        "id": dataset_id,
        "licenses": [{"name": "CC0-1.0"}]
    }
    with open(BUILD_DIR / "dataset-metadata.json", "w") as f:
        json.dump(meta, f, indent=2)
        
    # Check if dataset exists (simple check via list)
    # We'll just try 'version' first, if fails, 'create'
    try:
        run_cmd(f"kaggle datasets version -p {BUILD_DIR} -m 'Auto-update' --dir-mode zip")
    except subprocess.CalledProcessError:
        print("Dataset version failed, trying create...")
        run_cmd(f"kaggle datasets create -p {BUILD_DIR} --dir-mode zip")

    print("[INFO] Waiting 60s for dataset to propagate...")
    time.sleep(60)

    # 4. Push Kernel
    print("[4/5] Pushing Kernel...")
    shutil.copy("tools/kaggle_entrypoint.py", KERNEL_DIR / "main.py")
    
    kernel_slug = "geospatial-pipeline-runner"
    kernel_id = f"{username}/{kernel_slug}"
    
    kmeta = {
        "id": kernel_id,
        "title": "Geospatial Pipeline Runner",
        "code_file": "main.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": True,
        "enable_internet": True,
        "dataset_sources": [dataset_id],
        "competition_sources": [],
        "kernel_sources": []
    }
    with open(KERNEL_DIR / "kernel-metadata.json", "w") as f:
        json.dump(kmeta, f, indent=2)
        
    # Retry push if dataset is not ready
    max_retries = 3
    for i in range(max_retries):
        try:
            output = subprocess.check_output(f"kaggle kernels push -p {KERNEL_DIR}", shell=True, stderr=subprocess.STDOUT).decode()
            print(output)
            if "not valid dataset sources" in output:
                print(f"[WARN] Dataset not ready yet. Retrying in 30s... ({i+1}/{max_retries})")
                time.sleep(30)
                continue
            break
        except subprocess.CalledProcessError as e:
            print(f"[ERR] Push failed: {e.output.decode()}")
            if i < max_retries - 1:
                time.sleep(30)
            else:
                raise e
    
    # 5. Monitor
    print("[5/5] Monitoring Kernel (Polling)...")
    while True:
        try:
            status_out = subprocess.check_output(f"kaggle kernels status {kernel_id}", shell=True).decode().strip()
            # Output format: "username/slug has status \"complete\""
            print(f"Status: {status_out}")
            if '"complete"' in status_out:
                print("Kernel Finished!")
                break
            if '"error"' in status_out:
                print("Kernel Failed!")
                break
        except Exception as e:
            print(f"Polling error: {e}")
            
        time.sleep(30)
        
    # 6. Retrieve
    print("Retrieving results...")
    OUT_DIR = ROOT / "runs" / "kaggle_result"
    if OUT_DIR.exists(): shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)
    
    run_cmd(f"kaggle kernels output {kernel_id} -p {OUT_DIR}")
    print(f"Results downloaded to {OUT_DIR}")
    
    # Check for output zip
    out_zip = OUT_DIR / "kaggle_output.zip"
    if out_zip.exists():
        print("Unzipping results...")
        with zipfile.ZipFile(out_zip, 'r') as z:
            z.extractall(OUT_DIR)
        print("Done!")
    else:
        print("[WARN] kaggle_output.zip not found in results.")

if __name__ == "__main__":
    main()
