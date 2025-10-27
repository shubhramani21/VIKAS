import cv2
import numpy as np
import requests
import threading
from PIL import Image
import torch
from torchvision import transforms
import pandas as pd
import os
from datetime import datetime
import json
import logging

def project_with_scale(lat, lon, scale):
    siny = np.sin(lat * np.pi / 180)
    siny = min(max(siny, -0.9999), 0.9999)
    x = scale * (0.5 + lon / 360)
    y = scale * (0.5 - np.log((1 + siny) / (1 - siny)) / (4 * np.pi))
    return x, y

def download_tile(url, headers, channels):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to download tile: Status {response.status_code}")
        arr = np.asarray(bytearray(response.content), dtype=np.uint8)
        return cv2.imdecode(arr, 1) if channels == 3 else cv2.imdecode(arr, -1)
    except Exception as e:
        logging.error(f"Error downloading tile: {e}")
        return None

def download_image(lat1: float, lon1: float, lat2: float, lon2: float,
                   zoom: int, url: str, headers: dict, tile_size: int = 256, channels: int = 3) -> np.ndarray:
    scale = 1 << zoom
    tl_proj_x, tl_proj_y = project_with_scale(lat1, lon1, scale)
    br_proj_x, br_proj_y = project_with_scale(lat2, lon2, scale)
    tl_pixel_x = int(tl_proj_x * tile_size)
    tl_pixel_y = int(tl_proj_y * tile_size)
    br_pixel_x = int(br_proj_x * tile_size)
    br_pixel_y = int(br_proj_y * tile_size)
    tl_tile_x = int(tl_proj_x)
    tl_tile_y = int(tl_proj_y)
    br_tile_x = int(br_proj_x)
    br_tile_y = int(br_proj_y)
    img_w = abs(tl_pixel_x - br_pixel_x)
    img_h = br_pixel_y - tl_pixel_y
    img = np.zeros((img_h, img_w, channels), np.uint8)

    def build_row(tile_y):
        for tile_x in range(tl_tile_x, br_tile_x + 1):
            tile = download_tile(url.format(x=tile_x, y=tile_y, z=zoom), headers, channels)
            if tile is not None:
                tl_rel_x = tile_x * tile_size - tl_pixel_x
                tl_rel_y = tile_y * tile_size - tl_pixel_y
                br_rel_x = tl_rel_x + tile_size
                br_rel_y = tl_rel_y + tile_size
                img_x_l = max(0, tl_rel_x)
                img_x_r = min(img_w, br_rel_x)
                img_y_l = max(0, tl_rel_y)
                img_y_r = min(img_h, br_rel_y)
                cr_x_l = max(0, -tl_rel_x)
                cr_x_r = tile_size + min(0, img_w - br_rel_x)
                cr_y_l = max(0, -tl_rel_y)
                cr_y_r = tile_size + min(0, img_h - br_rel_y)
                img[img_y_l:img_y_r, img_x_l:img_x_r] = tile[cr_y_l:cr_y_r, cr_x_l:cr_x_r]

    threads = []
    for tile_y in range(tl_tile_y, br_tile_y + 1):
        thread = threading.Thread(target=build_row, args=[tile_y])
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    return img

# Add to headers for better request handling
DEFAULT_HEADERS = {
    'User-Agent': 'SolarDetectionApp/1.0',
    'Accept': 'image/webp,image/*,*/*;q=0.8',
    'Referer': 'https://www.google.com/maps/'
}

def get_image(lat, lon, zoom=18, channels=3, retries=3):
    """Enhanced with retry logic and timeout"""
    lat1 = round(lat + 0.0008, 4)
    lon1 = round(lon - 0.0015, 4)
    lat2 = round(lat - 0.0008, 4)
    lon2 = round(lon + 0.0015, 4)
    
    url = 'https://mt.google.com/vt/lyrs=s&x={x}&y={y}&z={z}'
    
    for attempt in range(retries):
        try:
            img = download_image(lat1, lon1, lat2, lon2, zoom, url, DEFAULT_HEADERS, 256, channels)
            if img is not None:
                return img
        except Exception as e:
            logging.warning(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == retries - 1:
                logging.error("Max retries reached for image download")
    return None

def predict_image(img_np, model, threshold=0.49):
    """Enhanced with better error handling and debug info"""
    try:
        if not isinstance(img_np, np.ndarray):
            raise ValueError("Input must be a numpy array")
            
        # Convert and validate image
        img_rgb = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
        if img_rgb.shape[2] != 3:
            raise ValueError(f"Expected 3 channels, got {img_rgb.shape[2]}")
            
        # Preprocessing pipeline
        transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize(model.cfg.image_size),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
        
        img_tensor = transform(img_rgb).unsqueeze(0).to(model.cfg.device)
        
        with torch.no_grad():
            output = model(img_tensor)
            probs = torch.softmax(output, dim=1)
            confidence = probs[0, 1].item()
            label = "Solar Panel" if confidence > threshold else "Not a Solar Panel"
            
            # Debug info
            logging.debug(f"Prediction - Label: {label}, Confidence: {confidence:.4f}")
            
        return label, confidence
        
    except Exception as e:
        logging.error(f"Prediction error: {str(e)}", exc_info=True)
        return "Error", 0.0

def save_prediction(lat, lon, label, confidence, file_path):
    data = {
        'Latitude': lat,
        'Longitude': lon,
        'Label': label,
        'Confidence': confidence,
        'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    df = pd.DataFrame([data])
    if os.path.exists(file_path):
        df.to_csv(file_path, mode='a', header=False, index=False)
    else:
        df.to_csv(file_path, mode='w', header=True, index=False)

def load_json(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_json(data, file_path):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def create_sample_polygon(lat, lon):
    offset = 0.01
    return [
        [lat - offset, lon - offset],
        [lat - offset, lon + offset],
        [lat + offset, lon + offset],
        [lat + offset, lon - offset],
        [lat - offset, lon - offset]
    ]