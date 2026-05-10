from app.domain.entities import ImagePayload
from app.ports.image_processor import ImageProcessor


class FakeImageProcessor(ImageProcessor):
    def __init__(self, sharpness_value: float = 100.0):
        self._sharpness = sharpness_value

    def compress(self, payload: ImagePayload) -> ImagePayload:
        return payload

    def sharpness(self, payload: ImagePayload) -> float:
        return self._sharpness
