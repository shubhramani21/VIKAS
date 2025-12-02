import torch
import timm

class SolarModel(torch.nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.backbone = timm.create_model(
            cfg.model_name,
            pretrained=False,
            in_chans=cfg.in_channels,
            num_classes=cfg.num_classes
        )

    def forward(self, x):
        return self.backbone(x)
