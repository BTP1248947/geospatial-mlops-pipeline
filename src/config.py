# src/config.py
import os

# --------------------------
# GOOGLE CLOUD & EARTH ENGINE
# --------------------------
# Your GCP Project ID
# It tries to get it from the computer's environment variables first, 
# otherwise it uses the hardcoded string.
EE_PROJECT_ID = os.getenv("GCP_PROJECT", "your-gcp-project-id")

# The Bucket where you store images and the 'last_processed_date.txt'
BUCKET_NAME = os.getenv("GCP_BUCKET", "sentinel-anomaly-data-bucket")

# --------------------------
# GEOSPATIAL CONFIG
# --------------------------
# Area of Interest (AOI) - Coordinates for your region
AOI_COORDINATES = [
    [73.8, 18.5], 
    [73.9, 18.5], 
    [73.9, 18.6], 
    [73.8, 18.6], 
    [73.8, 18.5] # Closing the loop (first point = last point)
]

# Date ranges (Used for manual ingestion or testing)
START_DATE_PRE = '2024-01-01'
END_DATE_PRE = '2024-01-30'
START_DATE_POST = '2024-02-01'
END_DATE_POST = '2024-02-28'

# --------------------------
# MODEL HYPERPARAMETERS
# --------------------------
# Critical: The AI needs to know the image size
IMG_HEIGHT = 128
IMG_WIDTH = 128
CHANNELS = 3            # RGB

# Training Settings
BATCH_SIZE = 16
EPOCHS = 10
LEARNING_RATE = 1e-4

# --------------------------
# PATHS & THRESHOLDS
# --------------------------
# Where to save the trained model inside the container/folder
MODEL_SAVE_PATH = os.path.join("src", "model_final.pth")

# Confidence threshold: Above 0.5 = Change detected
THRESHOLD = 0.5