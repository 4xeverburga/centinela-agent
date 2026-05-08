from io import BytesIO

import imagehash
from PIL import Image

from app.domain.entities import EmbeddingVector, ImagePayload
from app.ports.image_embedder import ImageEmbedder


class PhashImageEmbedder(ImageEmbedder):
    def __init__(self, hash_size: int):
        self._hash_size = hash_size

    def embed(self, file_id: str, payload: ImagePayload) -> EmbeddingVector:
        img = Image.open(BytesIO(payload.data))
        h = imagehash.phash(img, hash_size=self._hash_size)
        vector = [float(b) for b in h.hash.flatten()]
        return EmbeddingVector(file_id=file_id, vector=vector)

    def distance(self, a: EmbeddingVector, b: EmbeddingVector) -> float:
        diff = sum(abs(x - y) for x, y in zip(a.vector, b.vector))
        return diff
