
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

    # Find all 'before' images to identify AOIs
    before_images = glob.glob(os.path.join(args.visuals_dir, "*_before.png"))
    
    aois = []
    for before_path in before_images:
        # filename is like "india_wayanad_forest_before.png"
        filename = os.path.basename(before_path)
        aoi_name = filename.replace("_before.png", "")
        aois.append(aoi_name)
        
        # Copy files to UI format: before_{aoi}.png, after_{aoi}.png, mask_{aoi}.png
        # Source: {aoi}_before.png -> Dest: before_{aoi}.png
        
        # Before
        shutil.copy(before_path, os.path.join(args.ui_public_dir, f"before_{aoi_name}.png"))
        
        # After
        after_src = os.path.join(args.visuals_dir, f"{aoi_name}_after.png")
        if os.path.exists(after_src):
            shutil.copy(after_src, os.path.join(args.ui_public_dir, f"after_{aoi_name}.png"))
            
        # Mask
        mask_src = os.path.join(args.visuals_dir, f"{aoi_name}_mask.png")
        if os.path.exists(mask_src):
            shutil.copy(mask_src, os.path.join(args.ui_public_dir, f"mask_{aoi_name}.png"))
            
        print(f"[INFO] Copied assets for {aoi_name}")

    # Write index.json
    index_path = os.path.join(args.ui_public_dir, "index.json")
    with open(index_path, "w") as f:
        json.dump({"years": aois}, f, indent=2)
    
    print(f"[INFO] Updated {index_path} with {len(aois)} AOIs.")

if __name__ == "__main__":
    main()
