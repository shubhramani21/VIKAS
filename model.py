import torch
import timm
import logging
from config import resource_path 

class SolarModel(torch.nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.backbone = timm.create_model(
            cfg.model_name,
            pretrained=False,
            in_chans=cfg.in_channels,
            num_classes=cfg.num_classes
        )

    def forward(self, x):
        logits = self.backbone(x)
        return logits

# Modify model loading to use resource_path
def load_model(cfg):
    try:
        # Use full resource path
        model_path = resource_path(cfg.model_path)
        model = SolarModel(cfg)
        model.load_state_dict(torch.load(model_path, map_location=cfg.device))
        model.to(cfg.device)
        model.eval()
        return model
    except Exception as e:
        logging.error(f"Model load error: {str(e)}")
        return None