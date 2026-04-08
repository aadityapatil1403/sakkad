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


def get_text_embedding(text: str) -> list[float]:
    _load()
    inputs = _processor(text=[text], return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        text_features = _model.get_text_features(**inputs)
    if hasattr(text_features, "pooler_output"):
        text_features = text_features.pooler_output
    elif isinstance(text_features, tuple):
        text_features = text_features[0]
    embedding = text_features.reshape(-1).tolist()
    return embedding
