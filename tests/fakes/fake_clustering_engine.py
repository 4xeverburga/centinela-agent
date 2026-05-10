from app.domain.entities import Cluster, EmbeddingVector, SharpnessResult
from app.ports.clustering_engine import ClusteringEngine


class FakeClusteringEngine(ClusteringEngine):
    def cluster(
        self,
        embeddings: list[EmbeddingVector],
        sharpness_results: list[SharpnessResult],
        similarity_threshold: float,
    ) -> list[Cluster]:
        if not embeddings:
            return []
        sharpness_map = {s.file_id: s for s in sharpness_results}
        best = max(sharpness_results, key=lambda s: s.score)
        return [
            Cluster(
                cluster_id="cluster-0",
                representative_file_id=best.file_id,
                representative_sharpness=best.score,
                member_file_ids=[e.file_id for e in embeddings],
            )
        ]
