
import os
import glob
import json
import shutil
import argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--visuals-dir", default="outputs/site/visuals")
    p.add_argument("--raw-dir", default="data/raw")
    p.add_argument("--ui-public-dir", default="ui/public/visualization_results")
    args = p.parse_args()

    os.makedirs(args.ui_public_dir, exist_ok=True)

    # 1. Map AOI names to Years using data/raw files
    # Structure: { "aoi_name": { "before": year, "after": year } }
    aoi_years = {}
    raw_files = glob.glob(os.path.join(args.raw_dir, "*.tif"))
    for f in raw_files:
        # Expected: name_before_YYYY-MM-DD_...tif
        basename = os.path.basename(f)
        parts = basename.split("_")
        if "before" in parts:
            idx = parts.index("before")
            date_str = parts[idx+1] # YYYY-MM-DD
            year = int(date_str.split("-")[0])
            name = "_".join(parts[:idx])
            if name not in aoi_years: aoi_years[name] = {}
            aoi_years[name]["before"] = year
        elif "after" in parts:
            idx = parts.index("after")
            date_str = parts[idx+1]
            year = int(date_str.split("-")[0])
            name = "_".join(parts[:idx])
            if name not in aoi_years: aoi_years[name] = {}
            aoi_years[name]["after"] = year

    # 2. Copy visuals to ui/public/visualization_results/{aoi}/...
    # index.json: { "regions": [list], "years": { "region": [year_before, year_after] } }
    
    index_data = {"regions": [], "years": {}}
    
    visuals = glob.glob(os.path.join(args.visuals_dir, "*_before.png"))
    for vis_path in visuals:
        # vis_path: .../brazil_novo_progresso_before.png
        filename = os.path.basename(vis_path)
        aoi_name = filename.replace("_before.png", "")
        
        if aoi_name not in aoi_years:
            print(f"[WARN] Could not find raw data years for {aoi_name}, skipping.")
            continue
            
        years = aoi_years[aoi_name]
        before_year = years.get("before")
        after_year = years.get("after")
        
        if not before_year or not after_year:
            print(f"[WARN] Missing before/after year for {aoi_name}")
            continue

        # Create region folder
        region_dir = os.path.join(args.ui_public_dir, aoi_name)
        os.makedirs(region_dir, exist_ok=True)
        
        # Copy Before -> before_{year}.png
        shutil.copy(vis_path, os.path.join(region_dir, f"before_{before_year}.png"))
        
        # Copy After -> after_{year}.png
        after_src = os.path.join(args.visuals_dir, f"{aoi_name}_after.png")
        if os.path.exists(after_src):
            shutil.copy(after_src, os.path.join(region_dir, f"after_{after_year}.png"))
            
        # Copy Mask -> mask_{before_year}.png (associate mask with the 'before' timestamp for UI selection)
        mask_src = os.path.join(args.visuals_dir, f"{aoi_name}_mask.png")
        if os.path.exists(mask_src):
            shutil.copy(mask_src, os.path.join(region_dir, f"mask_{before_year}.png"))
            
        # Update Index
        index_data["regions"].append(aoi_name)
        # We want a list of available years for the selector. 
        # The selector usually picks one year. 
        # Let's provide both years so they appear in the dropdown.
        index_data["years"][aoi_name] = sorted(list(set([before_year, after_year])))
        
        print(f"[INFO] Processed {aoi_name}: {before_year} -> {after_year}")

    index_data["regions"].sort()
    
    with open(os.path.join(args.ui_public_dir, "index.json"), "w") as f:
        json.dump(index_data, f, indent=2)
    
    print(f"[INFO] Updated index.json with {len(index_data['regions'])} regions.")

if __name__ == "__main__":
    main()
