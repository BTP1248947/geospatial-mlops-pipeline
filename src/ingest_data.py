# src/ingest_data.py (Updated)
import ee
import config
import os
from google.cloud import storage

# Initialize GCS
storage_client = storage.Client()
bucket = storage_client.bucket("your-gcp-bucket-name")

def get_last_processed_date():
    blob = bucket.blob("state/last_processed_date.txt")
    if blob.exists():
        return blob.download_as_text().strip()
    return "2000-01-01" # Default for first run

def update_last_processed_date(date_str):
    blob = bucket.blob("state/last_processed_date.txt")
    blob.upload_from_string(date_str)

def check_and_download():
    ee.Initialize(project=config.EE_PROJECT_ID)
    aoi = ee.Geometry.Polygon(config.AOI_COORDINATES)

    # 1. Get the LATEST image from Earth Engine
    collection = ee.ImageCollection('COPERNICUS/S2_SR')\
        .filterBounds(aoi)\
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))\
        .sort('system:time_start', False) # Newest first
    
    latest_image = collection.first()
    latest_date = ee.Date(latest_image.get('system:time_start')).format('YYYY-MM-dd').getInfo()
    
    print(f"Latest Satellite Image Available: {latest_date}")
    
    # 2. Compare with what we have
    last_date = get_last_processed_date()
    print(f"Last Processed Date: {last_date}")

    if latest_date == last_date:
        print("No new data. Stopping.")
        # Write 'false' to GitHub Actions Output
        with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
            print(f"new_data=false", file=fh)
        return

    # 3. If New: Download and Process
    print("New data detected! Starting download...")
    # ... [Your existing download logic here] ...
    
    # 4. Update the state file in Cloud Storage
    update_last_processed_date(latest_date)
    
    # Write 'true' to GitHub Actions Output
    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        print(f"new_data=true", file=fh)

if __name__ == "__main__":
    check_and_download()