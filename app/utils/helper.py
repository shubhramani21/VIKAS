import os
import sys
from flask import jsonify


def _return_json(payload, status_code=200):
    return jsonify(payload), status_code

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def is_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def get_response(message, status, status_code, isAjax=False, extra = None):
    
    # AJAX request - return JSON response
    if isAjax:
        response = {
            "status": status, # success
            "message": message # Prediction completed
        }

        if extra is not None:
            response.update(extra)

        return {
            "type": "ajax",
            "status_code" : status_code, # 200
            "message": message,
            "response": response 
        }

    if extra is None:
        extra = {}
    
    return {
        "type" : status,
        "status_code" : status_code,
        "response" : extra,
        "message" : message
    }

def validate_latlon(lat, lon):
    try:
        lat = float(lat)
        lon = float(lon)
        return lat, lon
    except ValueError:
        raise ValueError("Invalid latitude or longitude")

    
def coordinates_match(c, lat, lon, tolerance=0.0001):
    """
    Compare coordinates with tolerance.
    Supports:
        - dict  -> {"lat": X, "lon": Y}
        - tuple -> (lat, lon)
        - list  -> [lat, lon]
    """

    if isinstance(c, dict):
        clat, clon = c["lat"], c["lon"]
    else:
        clat, clon = c[0], c[1]

    return abs(clat - lat) < tolerance and abs(clon - lon) < tolerance
