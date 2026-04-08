import io
from PIL import Image
from services.clip_service import get_image_embedding

def make_test_image() -> bytes:
    img = Image.new("RGB", (224, 224), color=(120, 80, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

if __name__ == "__main__":
    print("Creating test image...")
    image_bytes = make_test_image()

    print("Running CLIP embedding...")
    embedding = get_image_embedding(image_bytes)

    print(f"Embedding length: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
