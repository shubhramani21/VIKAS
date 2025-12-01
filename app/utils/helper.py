import os
import sys



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
    """Returns True if lat lon value is valid, False otherwise"""
    try:
        return float(lat), float(lon) 
    except:
        raise ValueError("Invalid latitude or longitude")
    
def coordinates_match(c, lat, lon):
    return abs(c[0] - lat) < 0.0001 and abs(c[1] - lon) < 0.0001

