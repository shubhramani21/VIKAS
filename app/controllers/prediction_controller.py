import os
import pandas as pd
from flask import session
from app.utils.helper import get_response, validate_latlon
from app.services.prediction_service import run_prediction, run_prediction_batch, coordinates_match

class PredictionController:
    MAX_LIMIT = 30

    @staticmethod
    def predict_single(lat, lon, model, cfg):
        """Predict a single coordinate."""

        # Validate coordinate
        try:
            lat, lon = validate_latlon(lat, lon)
        except ValueError:
            return get_response("Invalid coordinates.", "error_coordinates", 400)
        
        # Update session map center
        session["map_center"] = {"lat": lat, "lon": lon}
        existing = session.get("coordinates", [])
        session["coordinates"] = [
            c for c in existing
            if not coordinates_match((c["lat"], c["lon"]), lat, lon)
        ]
        session.modified = True

        try:
            image_base64, label, confidence = run_prediction(model, lat, lon, cfg)
            if image_base64 is None:
                return get_response("Failed to fetch satellite image for the given coordinates.", "error_response", 500)
        except:
            return get_response("Failed to run prediction.", "error_response", 500)

        extras = {
            'lat': lat,
            'lon': lon,
            'label': label,
            'confidence': confidence,
            "image_base64": image_base64
        }
        return get_response(
            "Prediction completed",
            "success",
            200,
            False,
            extras
        )

    
    @staticmethod
    def predict_batch(model, coords, cfg):
        """Predict all coordinates stored in session"""
        
        if not coords:
            return get_response("No coordinates to predict.", "error", 400)

        if len(coords) > PredictionController.MAX_LIMIT:
            return get_response(f"Maximum {PredictionController.MAX_LIMIT} coordinates allowed.", "error", 400)
        
        try:
            batch = run_prediction_batch(model, coords, cfg, sleep_seconds=1)
        except:
            return get_response(f"Failed to run batch prediction. {str(e)}", "error", 500)

        session["coordinates"] = []
        session.modified = True

        # Normal page render
        return get_response(
            "Prediction completed",
            "success",
            200,
            False,
            { "predictions": batch["predictions"] }
        )
    
    @staticmethod
    def load_history(cfg):
        """Load predictions from file"""
        
        file_name = cfg.predictions_file

        if not os.path.exists(file_name):
            return get_response("No predictions file found.", "warning", 404)
        
        try:
            df = pd.read_csv(file_name)
            df.columns = df.columns.str.lower()

            required = ['latitude', 'longitude', 'label', 'confidence', 'timestamp']

            if not all(col in df.columns for col in required):
                return get_response("Predictions file is corrupted or has invalid format.", "error", 500)

            df = df.dropna(subset=required)
            predictions = df.to_dict("records")

            if not predictions:
                return get_response("No valid predictions found.", "warning", 404)
            
            return get_response("Predictions loaded.", "success", 200, False, {"predictions": predictions})
        
        except:
            return get_response(f"Failed to load predictions: {str(e)}", "error", 500)
        

    @staticmethod
    def clear_history(cfg):
        """Delete all predictions from file"""

        file_path = cfg.predictions_file

        try:
            if not os.path.exists(file_path):
                return get_response("No predictions found.", "error", 404)

            df = pd.read_csv(file_path)
            columns_names = df.columns.tolist()
            empty_df = pd.DataFrame(columns=columns_names)

            empty_df.to_csv(file_path, index=False)

            return get_response(
                "All predictions have been cleared!",
                "success",
                200
            )
            
            
        except Exception as e:
            return get_response(f"Error clearing predictions: {str(e)}", "error", 500)

    @staticmethod
    def download_history(file_path):
        """Download the predictions CSV file."""

        if not os.path.exists(file_path):
            return get_response("No predictions file found to download", "error", 404)
        
        data = {
            'file_path': file_path,
            'mime_type': 'text/csv',
            'download_name': 'predictions.csv',
            'as_attachment': True
        }

        return get_response("File ready for download", "success", 200, False, data)
        