import torch
from app.utils.helper import resource_path

class Config:
    def __init__(self):
        # Use resource_path for all file paths
        self.model_path = resource_path("models/model_final.pth")  # absolute path
        self.predictions_file = resource_path("app/data/predictions.csv")  # absolute path

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