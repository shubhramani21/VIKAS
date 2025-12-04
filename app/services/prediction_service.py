import io
import os
import time
import base64
import logging
from datetime import datetime

import cv2
import torch
import numpy as np
import pandas as pd
from PIL import Image
from torchvision import transforms

from app.services.satellite_img_service import get_image
from app.utils.helper import validate_latlon


def image_to_base64(image_np):
    """Converts image to base64 string"""
    pil_img = Image.fromarray(image_np.astype('uint8'))
    buffered = io.BytesIO()
    pil_img.save(buffered, format="JPEG")

    return base64.b64encode(buffered.getvalue()).decode('utf-8')


def fetch_satellite_image(lat, lon, cfg):
    """Fetch satellite image using app.utils.get_image. Returns ndarray or None."""

    image = get_image(lat, lon, cfg.zoom_level)
    
    if image is None or not isinstance(image, np.ndarray):
        return None
    
    return image

def run_prediction(model, lat, lon, cfg):
    """
    Fetch image → predict → save prediction → return data.
    Returns:
        image_base64, label, confidence
    """

    # 1. Fetch image
    image = fetch_satellite_image(lat, lon, cfg)

    if image is None:
        return None, None, None

    # 2. predict (model_service.predict_image should accept image and model)
    # predict_image(image, model) -> (label, confidence)
    label, confidence = predict_image(image, model)

    # 3. save prediction to CSV (append)
    try:
        save_prediction(lat, lon, label, confidence, cfg.predictions_file)
    except Exception as e:
        logging.error(f"Failed to save prediction CSV: {str(e)}")

    # 4. encode image for UI
    image_base64 = image_to_base64(image)


    return image_base64, label, confidence


def run_prediction_batch(model, coords, cfg, sleep_seconds):
    """
    Run predictions for list of coords -> returns dict with results.
    coords: list of [lat, lon]
    """

    results = []
    for c in coords:
        lat = c.get("lat")
        lon = c.get("lon")

        img_b64, label, confidence = run_prediction(model, lat, lon, cfg)

        if img_b64 is None:
            label = "N/A"
            confidence = 0.0
        
        results.append({
            "lat": lat,
            "lon": lon,
            "label": label,
            "confidence": confidence,
            "image_base64": img_b64
        })

        if sleep_seconds > 0:
            time.sleep(sleep_seconds)


    return {
        "predictions": results
    }

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
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406], 
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        img_tensor = transform(img_rgb).unsqueeze(0).to(model.cfg.device)
        
        with torch.no_grad():
            output = model(img_tensor)
            probs = torch.softmax(output, dim=1)
            confidence = probs[0, 1].item()
            label = "Solar Panel" if confidence > threshold else "Not a Solar Panel"
            
            
        return label, confidence
        
    except Exception as e:
        logging.error(f"Prediction error: {str(e)}", exc_info=True)
        return "Error", 0.0

def get_scan_coordinates(lat, lon):
    """Get coordinates for scan"""
    try:
        lat, lon = validate_latlon(lat, lon)
    except ValueError:
        raise ValueError("Invalid latitude or longitude values.")
    
    meters_per_degree_lat = 111000
    meters_per_degree_lon = 111000 * np.cos(np.radians(lat))

    tile_width_m = 333
    tile_height_m = 177

    tile_width_deg = tile_width_m / meters_per_degree_lon
    tile_height_deg = tile_height_m / meters_per_degree_lat

    total_width_deg = tile_width_deg * 5  
    total_height_deg = tile_height_deg * 5

    start_lat = lat - (total_height_deg / 2) + (tile_height_deg / 2)
    start_lon = lon - (total_width_deg / 2) + (tile_width_deg / 2)

    scan_coords = []
    for i in range(5):
        for j in range(5):
            tile_lat = start_lat + (i * tile_height_deg)
            tile_lon = start_lon + (j * tile_width_deg)
            scan_coords.append({"lat": round(tile_lat,6), "lon": round(tile_lon,6)})
    
    return scan_coords


def get_scan_stats(predictions):
    """Get scan statistics from predictions list"""
    solar_count = sum(1 for p in predictions if p.get("label") == "Solar Panel")
    total_count = len(predictions)

    percentage_solar = round(solar_count / total_count * 100, 2) if total_count > 0 else 0.0

    confidences = [p.get("confidence", 0.0) for p in predictions if p.get("label") == "Solar Panel"]
    average_confidence = np.mean(confidences) if confidences else 0.0

    confidence_range = f"{min(confidences):.4f} - {max(confidences):.4f}" if confidences else "N/A"

    summary_stats = {
        "solar_count": solar_count,
        "total_tiles": total_count,
        "percentage_solar": percentage_solar,
        "avg_confidence": average_confidence,
        "confidence_range": confidence_range
    }

    return summary_stats



def save_prediction(lat, lon, label, confidence, file_path):

    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
        

    data = {
        'Latitude': lat,
        'Longitude': lon,
        'Label': label,
        'Confidence': confidence,
        'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    df = pd.DataFrame([data])

    file_exists = os.path.exists(file_path)
    file_empty = file_exists and os.path.getsize(file_path) == 0

    if not file_exists:
        df.to_csv(file_path, mode='w', header=True, index=False)
        return
    
    if file_empty:
        df.to_csv(file_path, mode='w', header=True, index=False)
        return 
    
    df.to_csv(file_path, mode='a', header=False, index=False)
