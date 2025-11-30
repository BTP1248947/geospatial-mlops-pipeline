#!/usr/bin/env python3
"""
tools/fetch_landsat.py

Fetches Landsat 9 composites for specified AOIs using getThumbURL (PNG download).
Based on user-provided snippet.
"""

import ee
import os
import requests
import argparse

# Initialize EE (Assumes already authenticated via 'earthengine authenticate' or key file)
try:
    ee.Initialize()
except Exception:
    # Fallback to project if needed, but usually environment is set
    try:
        ee.Initialize(project='radiant-works-474616-t3')
    except:
        print("Warning: EE initialization failed. Ensure you are authenticated.")

# Define base AOIs
BASE_AOIS = [
    {
        "name": "brazil_mato_grosso",
        "notes": "Agricultural frontier in the Brazilian Amazon.",
        "lat": -11.5, "lon": -54.8,
        "size_m": 40000
    },
    {
        "name": "brazil_novo_progresso",
        "notes": "Deforestation hotspot.",
        "lat": -7.1, "lon": -55.4,
        "size_m": 40000
    },
    {
        "name": "brazil_rondonia",
        "notes": "Fishbone deforestation patterns.",
        "lat": -10.8, "lon": -62.8,
        "size_m": 40000
    },
    # New coordinates for the same areas
    {
        "name": "brazil_mato_grosso_2",
        "notes": "Secondary location in Mato Grosso.",
        "lat": -11.6, "lon": -54.9,
        "size_m": 40000
    },
    {
        "name": "brazil_novo_progresso_2",
        "notes": "Secondary location in Novo Progresso.",
        "lat": -7.2, "lon": -55.5,
        "size_m": 40000
    },
    {
        "name": "brazil_rondonia_2",
        "notes": "Secondary location in Rondonia.",
        "lat": -10.9, "lon": -62.9,
        "size_m": 40000
    }
]

# Generate time series pairs
AOIS = []
years = range(2020, 2025) # 2020, 2021, 2022, 2023, 2024

for base in BASE_AOIS:
    for i in range(len(years) - 1):
        y1 = years[i]
        y2 = years[i+1]
        
        # Define dry season window (Aug-Sep usually good for Brazil Amazon)
        # Or use the user's previous dates (June-Sept)
        
        AOIS.append({
            "name": f"{base['name']}_{y1}_{y2}", # e.g. brazil_mato_grosso_2020_2021
            "lat": base['lat'],
            "lon": base['lon'],
            "size_m": base['size_m'],
            "before_dates": (f'{y1}-06-01', f'{y1}-09-30'),
            "after_dates": (f'{y2}-06-01', f'{y2}-09-30')
        })

VIS_PARAMS = {'bands': ['SR_B4', 'SR_B3', 'SR_B2'], 'min': 0.0, 'max': 0.3}

def apply_scale_factors(image):
    optical_bands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
    thermal_bands = image.select('ST_B.*').multiply(0.00341802).add(149.0)
    return image.addBands(optical_bands, None, True).addBands(thermal_bands, None, True)

def generate_and_download_composite(start_date, end_date, point, region, output_path):
    print(f"Generating composite for {os.path.basename(output_path)}...")
    try:
        # Select collection based on year
        year = int(start_date.split("-")[0])
        if year >= 2022:
            col_id = "LANDSAT/LC09/C02/T1_L2" # Landsat 9
        else:
            col_id = "LANDSAT/LC08/C02/T1_L2" # Landsat 8
            
        print(f"  Using collection: {col_id}")
        
        collection = ee.ImageCollection(col_id) \
            .filterBounds(point).filterDate(start_date, end_date) \
            .filter(ee.Filter.lt('CLOUD_COVER', 25)).map(apply_scale_factors)

        if collection.size().getInfo() == 0:
            print(f"CRITICAL WARNING: Found 0 images for period {start_date}-{end_date}. Cannot generate image.")
            return

        composite = collection.median()
        # format: 'png' is important for visual download
        url = composite.getThumbURL({'region': region, 'scale': 30, 'format': 'PNG', **VIS_PARAMS})

        print(f"Downloading image to {output_path}...")
        response = requests.get(url)
        response.raise_for_status()
        with open(output_path, 'wb') as f: f.write(response.content)
        print(f"✅ Success! Image saved.")
    except Exception as e:
        print(f"❌ ERROR: Could not download image. {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="data/raw_landsat")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    for aoi in AOIS:
        print(f"\n{'='*25} Processing AOI: {aoi['name']} {'='*25}")
        point = ee.Geometry.Point(aoi['lon'], aoi['lat'])
        # buffer returns a Geometry, bounds() returns Geometry, getInfo()['coordinates'] gets the list
        region = point.buffer(aoi['size_m'] / 2).bounds().getInfo()['coordinates']
        
        generate_and_download_composite(
            aoi['before_dates'][0], aoi['before_dates'][1], 
            point, region, 
            os.path.join(args.out_dir, f"{aoi['name']}_before.png")
        )
        generate_and_download_composite(
            aoi['after_dates'][0], aoi['after_dates'][1], 
            point, region, 
            os.path.join(args.out_dir, f"{aoi['name']}_after.png")
        )

if __name__ == "__main__":
    main()
