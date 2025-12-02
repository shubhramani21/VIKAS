import io
import os
import time
import base64
import logging
from datetime import datetime

from PIL import Image
import cv2
import torch
from torchvision import transforms

from PIL import Image

import numpy as np
import pandas as pd


from app.services.satellite_img_service import get_image

# Perfect
def image_to_base64(image_np):
    """Converts image to base64 string"""
    pil_img = Image.fromarray(image_np.astype('uint8'))
    buffered = io.BytesIO()
    pil_img.save(buffered, format="JPEG")

    return base64.b64encode(buffered.getvalue()).decode('utf-8')


def fetch_satellite_image(lat, lon, cfg):
    """FFetch satellite image using app.utils.get_image. Returns ndarray or None."""

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
    except Exception:
        # don't fail the request just because CSV saving failed; still return prediction
        pass

    # 4. encode image for UI
    image_base64 = image_to_base64(image)


    return image_base64, label, confidence


def run_prediction_batch(model, coords, cfg, sleep_seconds):
    """
    Run predictions for list of coords -> returns dict with results.
    coords: list of [lat, lon]
    """

    results = []
    for lat, lon in coords:
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
