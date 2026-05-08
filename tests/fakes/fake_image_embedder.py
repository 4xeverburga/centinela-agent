from app.domain.entities import EmbeddingVector, ImagePayload
from app.ports.image_embedder import ImageEmbedder


class FakeImageEmbedder(ImageEmbedder):
    def embed(self, file_id: str, payload: ImagePayload) -> EmbeddingVector:
        h = hash(payload.data)
        return EmbeddingVector(file_id=file_id, vector=[float(h % 1000) / 1000.0])

    def distance(self, a: EmbeddingVector, b: EmbeddingVector) -> float:
        return abs(a.vector[0] - b.vector[0])
