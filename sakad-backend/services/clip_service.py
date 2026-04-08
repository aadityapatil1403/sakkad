import io
import os
from PIL import Image
import torch
from transformers import AutoProcessor, AutoModel
from config import settings

os.environ.setdefault("HF_HUB_OFFLINE", "1")

_model = None
_processor = None


def _load():
    global _model, _processor
    if _model is None:
        _model = AutoModel.from_pretrained(settings.CLIP_MODEL_NAME, local_files_only=True)
        _processor = AutoProcessor.from_pretrained(settings.CLIP_MODEL_NAME, local_files_only=True)
        _model.eval()


def get_image_embedding(image_bytes: bytes) -> list[float]:
    _load()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    inputs = _processor(images=image, return_tensors="pt")
    with torch.no_grad():
        image_features = _model.get_image_features(**inputs)
    if hasattr(image_features, "pooler_output"):
        image_features = image_features.pooler_output
    elif isinstance(image_features, tuple):
        image_features = image_features[0]
    embedding = image_features.reshape(-1).tolist()
    return embedding
