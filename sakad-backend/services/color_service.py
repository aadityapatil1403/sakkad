import io

import numpy as np
from PIL import Image


def _kmeans_numpy(pixels: np.ndarray, k: int = 5, max_iter: int = 20) -> np.ndarray:
    rng = np.random.default_rng(0)
    centroids = pixels[rng.choice(len(pixels), k, replace=False)]
    for _ in range(max_iter):
        dists = np.linalg.norm(pixels[:, None] - centroids[None], axis=2)
        labels = np.argmin(dists, axis=1)
        new_centroids = np.array([
            pixels[labels == i].mean(axis=0) if np.any(labels == i) else centroids[i]
            for i in range(k)
        ])
        if np.allclose(centroids, new_centroids, atol=1.0):
            break
        centroids = new_centroids
    return centroids


def extract_palette(image_bytes: bytes, k: int = 5) -> list[str]:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = image.resize((150, 150))
    pixels = np.array(image).reshape(-1, 3).astype(np.float32)
    centroids = _kmeans_numpy(pixels, k=k)
    return [f"#{int(round(r)):02x}{int(round(g)):02x}{int(round(b)):02x}" for r, g, b in centroids]
