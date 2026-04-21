import io

from PIL import Image


def _make_solid_image_bytes(r: int, g: int, b: int) -> bytes:
    image = Image.new("RGB", (10, 10), color=(r, g, b))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


class TestExtractPalette:
    def test_returns_list_of_hex_strings(self) -> None:
        from services.color_service import extract_palette

        result = extract_palette(_make_solid_image_bytes(255, 0, 0))

        assert isinstance(result, list)
        assert len(result) == 5
        assert all(color.startswith("#") and len(color) == 7 for color in result)

    def test_solid_red_image_returns_red_dominant_color(self) -> None:
        from services.color_service import extract_palette

        result = extract_palette(_make_solid_image_bytes(255, 0, 0))

        assert "#fe0000" in result or "#ff0000" in result

    def test_returns_exactly_k_colors(self) -> None:
        from services.color_service import extract_palette

        result = extract_palette(_make_solid_image_bytes(100, 150, 200), k=3)

        assert len(result) == 3
