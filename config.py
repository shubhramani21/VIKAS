import torch
import os
import sys

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class Config:
    def __init__(self):
        # Use resource_path for all file paths
        self.model_path = resource_path(os.path.join("models", "model_final.pth"))
        self.predictions_file = resource_path(os.path.join("data", "predictions.csv"))
        
        # Rest of your config remains the same
        self.image_size = (224, 224)
        self.in_channels = 3
        self.num_classes = 2
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_name = "resnet18"
        self.title = "Solar Panel Detection"
        self.map_default = {"lat": 34.137470, "lon": 77.571188, "zoom": 12.5}
        self.zoom_level = 18

    def to_dict(self):
        return {
            "map_default": self.map_default,
            "zoom_level": self.zoom_level
        }