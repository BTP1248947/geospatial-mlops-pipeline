#!/usr/bin/env python3
"""
run_timeline.py

Automates the download of Sentinel-2 data for a multi-year timeline (2021-2024).
It generates pairs of years (e.g., 2021 vs 2022, 2022 vs 2023) to create a robust training dataset.

Usage:
  python ingest/run_timeline.py --project your-gcp-project --aoi aoi/india_wayanad.geojson --drive-folder EO_Exports
"""

import argparse
import subprocess
import sys
import os

def run_ingest(project, aoi, year_before, year_after, name_prefix, drive_folder, cloud_pct, service_account=None, key_file=None):
    """
    Calls gee_ingest.py to download a pair of years.
    """
    
    # Define dates for the full year
    before_start = f"{year_before}-01-01"
    before_end   = f"{year_before}-12-31"
    after_start  = f"{year_after}-01-01"
    after_end    = f"{year_after}-12-31"
    
    name = f"{name_prefix}_{year_before}_{year_after}"
    
    print(f"[TIMELINE] Processing pair: {year_before} vs {year_after}...")
    
    cmd = [
        sys.executable, "ingest/gee_ingest.py",
        "--project", project,
        "--aoi", aoi,
        "--before", before_start, before_end,
        "--after", after_start, after_end,
        "--name", name,
        "--drive-folder", drive_folder,
        "--cloud-pct", str(cloud_pct),
        "--method", "latest"
    ]
    
    if service_account and key_file:
        cmd.extend(["--service-account", service_account, "--key-file", key_file])
    
    try:
        subprocess.check_call(cmd)
        print(f"[TIMELINE] Success: {year_before} vs {year_after}")
    except subprocess.CalledProcessError as e:
        print(f"[TIMELINE] Error processing {year_before} vs {year_after}")
        sys.exit(1)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project", required=True, help="GCP Project ID")
    p.add_argument("--aoi", required=True, help="Path to AOI GeoJSON")
    p.add_argument("--drive-folder", required=True, help="Google Drive folder to export to")
    p.add_argument("--start-year", type=int, default=2021, help="Start year of the timeline")
    p.add_argument("--end-year", type=int, default=2024, help="End year of the timeline")
    p.add_argument("--cloud-pct", type=int, default=30, help="Cloud percentage filter (stricter for timeline)")
    p.add_argument("--service-account", default=None, help="Service Account Email")
    p.add_argument("--key-file", default=None, help="Path to Service Account JSON key")
    
    args = p.parse_args()
    
    if not os.path.exists("ingest/gee_ingest.py"):
        print("[ERR] ingest/gee_ingest.py not found. Run this from the repo root.")
        sys.exit(1)

    # Loop through the years to create pairs
    # 2021 -> 2022
    # 2022 -> 2023
    # 2023 -> 2024
    
    current_year = args.start_year
    while current_year < args.end_year:
        next_year = current_year + 1
        run_ingest(
            project=args.project,
            aoi=args.aoi,
            year_before=current_year,
            year_after=next_year,
            name_prefix="timeline",
            drive_folder=args.drive_folder,
            cloud_pct=args.cloud_pct,
            service_account=args.service_account,
            key_file=args.key_file
        )
        current_year += 1
        
    print("\n[DONE] All timeline pairs submitted to Earth Engine.")
    print("Check your Google Drive folder:", args.drive_folder)

if __name__ == "__main__":
    main()
