# serve/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 1. Install system dependencies (required for Rasterio/GDAL)
RUN apt-get update && apt-get install -y \
    build-essential \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# 2. Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy Model Architecture (from train folder) and Inference Code (from serve folder)
# We structure it so Python can find 'train.model'
COPY train/ ./train/
COPY serve/app/ ./app/

# 4. Copy the Trained Weights
COPY runs/model_inference.pth .

# 5. Run the API
# Assuming your FastAPI code is in serve/app/main.py or serve/app/app.py
ENV PYTHONPATH=/app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]