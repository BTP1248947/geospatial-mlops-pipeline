
import os
import glob
import json
import shutil
import argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--visuals-dir", default="outputs/site/visuals")
    p.add_argument("--ui-public-dir", default="ui/public/visualization_results")
    args = p.parse_args()

    os.makedirs(args.ui_public_dir, exist_ok=True)

    # Find all 'before' images to identify AOIs and Years
    # Expected format: {aoi}_before_{year}.png
    before_images = glob.glob(os.path.join(args.visuals_dir, "*_before_*.png"))
    
    regions = set()
    years_map = {} # {region: [year1, year2]}

    for before_path in before_images:
        filename = os.path.basename(before_path)
        # filename is like "india_wayanad_forest_before_2024.png"
        parts = filename.replace(".png", "").split("_before_")
        if len(parts) != 2:
            print(f"[WARN] Skipping malformed file: {filename}")
            continue
            
        aoi_name = parts[0]
        year = parts[1]
        
        regions.add(aoi_name)
        if aoi_name not in years_map:
            years_map[aoi_name] = []
        if year not in years_map[aoi_name]:
            years_map[aoi_name].append(year)
        
        # Copy files to UI format: {aoi}_before_{year}.png
        shutil.copy(before_path, os.path.join(args.ui_public_dir, filename))
        
        # After: {aoi}_after_{year}.png (assuming same year for simplicity or we need to find it)
        # Actually, generate_visuals saves as {aoi}_after_{year}.png
        # We need to find the matching after file for this AOI.
        # But wait, the UI needs to know which after year corresponds to which before year?
        # Or just list available years.
        # Let's copy all after files too.
    
    # Copy all after files and extract years
    after_images = glob.glob(os.path.join(args.visuals_dir, "*_after_*.png"))
    for after_path in after_images:
        filename = os.path.basename(after_path)
        shutil.copy(after_path, os.path.join(args.ui_public_dir, filename))
        
        # Extract year from after image: {aoi}_after_{year}.png
        parts = filename.replace(".png", "").split("_after_")
        if len(parts) == 2:
            aoi_name = parts[0]
            year = parts[1]
            
            regions.add(aoi_name)
            if aoi_name not in years_map:
                years_map[aoi_name] = []
            if year not in years_map[aoi_name]:
                years_map[aoi_name].append(year)

    # Copy all mask files
    mask_images = glob.glob(os.path.join(args.visuals_dir, "*_mask_*.png"))
    for mask_path in mask_images:
        shutil.copy(mask_path, os.path.join(args.ui_public_dir, os.path.basename(mask_path)))

    # Sort years
    for region in years_map:
        years_map[region].sort()

    # Write index.json
    index_path = os.path.join(args.ui_public_dir, "index.json")
    data = {
        "regions": sorted(list(regions)),
        "years": years_map
    }
    with open(index_path, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"[INFO] Updated {index_path} with {len(regions)} Regions.")

if __name__ == "__main__":
    main()
