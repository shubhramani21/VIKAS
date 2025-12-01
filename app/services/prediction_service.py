import io
import base64
import numpy as np
import time
from PIL import Image

from utils import get_image, predict_image, save_prediction

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