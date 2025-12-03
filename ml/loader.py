import torch
import logging
from .solar_model import SolarModel
import os

def load_model(cfg):
    try:
        if not os.path.exists(cfg.model_path):
            logging.error(f"Model file not found: {cfg.model_path}")
            return None
        
        model = SolarModel(cfg)

        state = torch.load(cfg.model_path, map_location=cfg.device)

        if isinstance(state, dict) and "model" in state:
            state = state['model']

        model.load_state_dict(state)

        model.to(cfg.device)    
        model.eval()
        
        return model
    except Exception as e:
        logging.error(f"Model load error: {str(e)}")
        return None
