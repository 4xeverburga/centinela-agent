from app.domain.entities import Cluster, EmbeddingVector, SharpnessResult
from app.ports.clustering_engine import ClusteringEngine


class GreedyClusteringEngine(ClusteringEngine):
    def cluster(
        self,
        embeddings: list[EmbeddingVector],
        sharpness_results: list[SharpnessResult],
        similarity_threshold: float,
    ) -> list[Cluster]:
        if not embeddings:
            return []

        from app.ports.image_embedder import ImageEmbedder

        sharpness_map = {s.file_id: s.score for s in sharpness_results}
        assigned: set[str] = set()
        clusters: list[Cluster] = []
        cluster_idx = 0

        for emb in embeddings:
            if emb.file_id in assigned:
                continue

            members = [emb.file_id]
            assigned.add(emb.file_id)

            for other in embeddings:
                if other.file_id in assigned:
                    continue
                dist = sum(abs(a - b) for a, b in zip(emb.vector, other.vector))
                if dist <= similarity_threshold:
                    members.append(other.file_id)
                    assigned.add(other.file_id)

            best_file = max(members, key=lambda fid: sharpness_map.get(fid, 0.0))
            clusters.append(
                Cluster(
                    cluster_id=f"cluster-{cluster_idx}",
                    representative_file_id=best_file,
                    representative_sharpness=sharpness_map.get(best_file, 0.0),
                    member_file_ids=members,
                )
            )
            cluster_idx += 1

        return clusters
