#!/usr/bin/env python3
"""
tools/fetch_from_gee.py

Automates the full cycle:
1. Submit GEE Export Task (via ingest/gee_ingest.py logic)
2. Poll Task Status until COMPLETED
3. Download resulting files from Drive (via tools/download_from_drive.py logic)

Usage:
  python tools/fetch_from_gee.py \
    --project my-project \
    --aoi aoi/my_area.geojson \
    --before 2020-01-01 2020-01-31 \
    --after 2021-01-01 2021-01-31 \
    --name my_area \
    --drive-folder EO_Exports \
    --out-dir data/raw
"""

import argparse
import time
import sys
import os
import ee
import fnmatch

# Add repo root to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingest.gee_ingest import init_ee, load_aoi, sentinel_composite, export_to_drive
from tools.download_from_drive import get_service_user, get_service_sa, find_folder, list_files, download

def poll_task(task_id, interval=30):
    print(f"[INFO] Polling task {task_id} every {interval}s...")
    while True:
        try:
            status = ee.data.getTaskStatus(task_id)[0]
        except Exception as e:
            print(f"[WARN] Failed to get task status: {e}")
            time.sleep(interval)
            continue
            
        state = status['state']
        print(f"   Status: {state}")
        if state == 'COMPLETED':
            print("[INFO] Task completed successfully.")
            return True
        elif state in ['FAILED', 'CANCELLED']:
            print(f"[ERR] Task failed: {status.get('error_message', 'Unknown error')}")
            return False
        time.sleep(interval)

def main():
    p = argparse.ArgumentParser()
    # GEE Args
    p.add_argument("--project", required=True, help="GCP Project ID for Earth Engine")
    p.add_argument("--service-account", default=None, help="Service account email (optional)")
    p.add_argument("--key-file", default=None, help="Path to service account key JSON (optional)")
    p.add_argument("--aoi", required=True, help="Path to AOI GeoJSON")
    p.add_argument("--before", nargs=2, required=True, help="Start End (YYYY-MM-DD)")
    p.add_argument("--after", nargs=2, required=True, help="Start End (YYYY-MM-DD)")
    p.add_argument("--name", required=True, help="Base name for output files")
    p.add_argument("--cloud-pct", type=int, default=60)
    p.add_argument("--scale", type=int, default=10)
    
    # Drive/Download Args
    p.add_argument("--drive-folder", default="EO_Exports", help="Google Drive folder to export to")
    p.add_argument("--out-dir", required=True, help="Local directory to download files to")
    p.add_argument("--client-secret", default=None, help="Path to client_secret.json for Drive OAuth (optional)")
    
    args = p.parse_args()

    # 1. Initialize & Submit
    init_ee(args.project, args.service_account, args.key_file)
    aoi_geom = load_aoi(args.aoi)
    
    # Submit Before
    print(f"[INFO] Preparing BEFORE image: {args.before}")
    before_img = sentinel_composite(aoi_geom, args.before[0], args.before[1], args.cloud_pct)
    fname_before = f"{args.name}_before_{args.before[0]}_{args.before[1]}"
    task_id_before = export_to_drive(before_img, aoi_geom, fname_before, args.drive_folder, args.scale, "EPSG:4326")
    
    # Submit After
    print(f"[INFO] Preparing AFTER image: {args.after}")
    after_img = sentinel_composite(aoi_geom, args.after[0], args.after[1], args.cloud_pct)
    fname_after = f"{args.name}_after_{args.after[0]}_{args.after[1]}"
    task_id_after = export_to_drive(after_img, aoi_geom, fname_after, args.drive_folder, args.scale, "EPSG:4326")

    # 2. Poll
    print("[INFO] Waiting for tasks to complete...")
    if not poll_task(task_id_before): sys.exit(1)
    if not poll_task(task_id_after): sys.exit(1)

    # 3. Download
    print("[INFO] Downloading files from Drive...")
    
    # Determine Drive credentials
    # If key-file is provided for GEE, try to use it for Drive SA if applicable, 
    # otherwise fall back to user auth.
    drive = None
    if args.key_file:
        try:
            drive = get_service_sa(args.key_file)
            print("[INFO] Authenticated Drive with Service Account.")
        except Exception:
            print("[INFO] Could not use key-file for Drive, falling back to User Auth.")
    
    if not drive:
        drive = get_service_user(args.client_secret)
        print("[INFO] Authenticated Drive with User OAuth.")

    folder_id = find_folder(drive, args.drive_folder)
    if not folder_id:
        print(f"[ERR] Drive folder '{args.drive_folder}' not found.")
        sys.exit(1)

    files = list_files(drive, folder_id)
    
    # Filter for our files
    # We search for files that start with our export names (handling potential tiling)
    targets = [fname_before, fname_after]
    downloaded_count = 0
    
    for t in targets:
        # Match any file starting with the name and ending in .tif
        matches = [f for f in files if f['name'].startswith(t) and f['name'].endswith('.tif')]
        if not matches:
            print(f"[WARN] No files found for {t} in Drive folder.")
            continue
            
        for m in matches:
            print(f"Downloading {m['name']}...")
            download(drive, m['id'], m['name'], args.out_dir)
            downloaded_count += 1

    print(f"[DONE] Downloaded {downloaded_count} files to {args.out_dir}")

if __name__ == "__main__":
    main()
