from abc import ABC, abstractmethod

from app.domain.entities import ImagePayload, SharpnessResult


class ImageProcessor(ABC):
    @abstractmethod
    def compress(self, payload: ImagePayload) -> ImagePayload: ...

    @abstractmethod
    def sharpness(self, payload: ImagePayload) -> float: ...
