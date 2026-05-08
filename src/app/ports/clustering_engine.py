from abc import ABC, abstractmethod

from app.domain.entities import Cluster, EmbeddingVector, SharpnessResult


class ClusteringEngine(ABC):
    @abstractmethod
    def cluster(
        self,
        embeddings: list[EmbeddingVector],
        sharpness_results: list[SharpnessResult],
        similarity_threshold: float,
    ) -> list[Cluster]: ...
