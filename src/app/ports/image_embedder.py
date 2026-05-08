from abc import ABC, abstractmethod

from app.domain.entities import EmbeddingVector, ImagePayload


class ImageEmbedder(ABC):
    @abstractmethod
    def embed(self, file_id: str, payload: ImagePayload) -> EmbeddingVector: ...

    @abstractmethod
    def distance(self, a: EmbeddingVector, b: EmbeddingVector) -> float: ...
