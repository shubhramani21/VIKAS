import torch
import logging
from .solar_model import SolarModel

def load_model(cfg):
    try:
        model = SolarModel(cfg)
        model.load_state_dict(torch.load(cfg.model_path, map_location=cfg.device))
        model.to(cfg.device)
        model.eval()
        return model
    except Exception as e:
        logging.error(f"Model load error: {str(e)}")
        return None
