import io
import os
import threading
from PIL import Image
import torch
import open_clip
from transformers import AutoProcessor
from config import settings

os.environ.setdefault("HF_HUB_OFFLINE", "1")

_model = None
_processor = None
_load_lock = threading.Lock()


def _load() -> None:
    global _model, _processor
    if _model is not None:
        return
    with _load_lock:
        if _model is not None:  # double-checked locking
            return
        # open_clip handles marqo-fashionSigLIP weights correctly; AutoModel.from_pretrained
        # fails with torch 2.x due to meta-tensor incompatibility in the custom __init__.
        _model, _, _ = open_clip.create_model_and_transforms(
            f"hf-hub:{settings.CLIP_MODEL_NAME}"
        )
        # AutoProcessor provides the correct T5-based tokenizer and SigLIP image processor
        _processor = AutoProcessor.from_pretrained(
            settings.CLIP_MODEL_NAME,
            trust_remote_code=True,
            local_files_only=True,
        )
        _model.eval()


def get_image_embedding(image_bytes: bytes) -> list[float]:
    _load()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    inputs = _processor(images=image, return_tensors="pt")
    with torch.no_grad():
        # normalize=True is required for correct cosine similarity scores with marqo-fashionSigLIP
        image_embeds = _model.encode_image(inputs["pixel_values"], normalize=True)
    return image_embeds.reshape(-1).tolist()


def get_text_embedding(text: str) -> list[float]:
    _load()
    inputs = _processor(text=[text], return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        # normalize=True is required for correct cosine similarity scores with marqo-fashionSigLIP
        text_embeds = _model.encode_text(inputs["input_ids"], normalize=True)
    return text_embeds.reshape(-1).tolist()
