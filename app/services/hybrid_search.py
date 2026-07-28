from app.services.vector_store import VectorStoreService
from app.services.bm25_search import BM25SearchService

from app.core.config import settings
from app.core.logger import logger


class HybridSearchService:

    def __init__(self):

        logger.info("Initializing Hybrid Retrieval Service")

        self.vector_store = VectorStoreService()

        self.bm25_service = BM25SearchService()

    def search(
        self,
        query_embedding: list[float],
        query: str,
        top_k: int = settings.hybrid_top_k,
    ):

        logger.info("Starting hybrid search")

        # ==================================================
        # Vector Search
        # ==================================================

        vector_results = self.vector_store.search(
            query_embedding=query_embedding, top_k=settings.top_k_vector
        )

        logger.info(f"Vector results: {len(vector_results)}")

        vector_documents = self._convert_vector_results(vector_results)

        # ==================================================
        # BM25 Search
        # ==================================================

        bm25_results = self.bm25_service.search(query=query, top_k=settings.top_k_BM25)

        self._normalize_bm25_scores(bm25_results)

        logger.info(f"BM25 results: {len(bm25_results)}")

        # ==================================================
        # Merge Vector + BM25
        # ==================================================

        merged = self._merge_results(vector_documents, bm25_results)

        ranked = sorted(
            [
                item
                for item in merged.values()
                if item["hybrid_score"] >= settings.hybrid_similarity_threshold
            ],
            key=lambda x: x["hybrid_score"],
            reverse=True,
        )

        logger.info(f"Hybrid ranking completed | Results={len(ranked)}")

        # ==================================================
        # Hybrid Ranking Logs
        # ==================================================

        logger.info("Hybrid ranking results")

        for item in ranked[:top_k]:

            logger.info(f"""
Chunk ID:
{item['chunk_id']}

Vector Score:
{item['vector_score']:.4f}

BM25 Score:
{item['bm25_score']:.4f}

Hybrid Score:
{item['hybrid_score']:.4f}

Filename:
{item['metadata'].get('filename','Unknown')}
""")

        # ==================================================
        # Hybrid Threshold Filtering
        # ==================================================

        filtered_results = [
            item
            for item in ranked
            if item["hybrid_score"] >= settings.hybrid_similarity_threshold
        ]

        logger.info(f"""
Hybrid filtering completed

Retrieved:
{len(ranked)}

Accepted:
{len(filtered_results)}

Rejected:
{len(ranked)-len(filtered_results)}

Threshold:
{settings.hybrid_similarity_threshold}
""")

        final_results = filtered_results[:top_k]

        # ==================================================
        # Return Same Structure Expected By RetrievalService
        # ==================================================

        return {
            "ids": [[item["chunk_id"] for item in final_results]],
            "documents": [[item["content"] for item in final_results]],
            "metadatas": [[item["metadata"] for item in final_results]],
            "distances": [[item["hybrid_score"] for item in final_results]],
            "hybrid_scores": [[item["hybrid_score"] for item in final_results]],
        }

    # ==================================================
    # Convert Vector Store Results
    # ==================================================

    def _convert_vector_results(self, results):

        documents = []

        for item in results:

            chunk_id = item["id"]

            distance = item["distance"]

            logger.info(f"""
Vector Raw Distance:

Chunk:
{chunk_id}

Distance:
{distance}
""")

            vector_score = self._normalize_distance(distance)

            logger.info(f"""
Vector Normalized Score:

Chunk:
{chunk_id}

Score:
{vector_score}
""")

            documents.append(
                {
                    "chunk_id": chunk_id,
                    "content": item["document"],
                    "metadata": item["metadata"],
                    "vector_score": vector_score,
                }
            )

        return documents

    # ==================================================
    # Merge Vector + BM25 Results
    # ==================================================

    def _merge_results(self, vector_results, bm25_results):

        merged = {}

        # ----------------------------
        # Vector Results
        # ----------------------------

        for item in vector_results:

            chunk_id = item["chunk_id"]

            merged[chunk_id] = {**item, "bm25_score": 0}

        # ----------------------------
        # BM25 Results
        # ----------------------------

        for item in bm25_results:

            chunk_id = item["chunk_id"]

            if chunk_id in merged:

                merged[chunk_id]["bm25_score"] = item["score"]

            else:

                merged[chunk_id] = {
                    "chunk_id": chunk_id,
                    "content": item["content"],
                    "metadata": item["metadata"],
                    "vector_score": 0,
                    "bm25_score": item["score"],
                }

        # ----------------------------
        # Hybrid Score Calculation
        # ----------------------------

        for item in merged.values():

            item["hybrid_score"] = (
                settings.vector_weight * item["vector_score"]
                + settings.bm25_weight * item["bm25_score"]
            )

        return merged

    # ==================================================
    # Chroma Distance Normalization
    # ==================================================

    def _normalize_distance(self, distance: float):

        # Lower distance = better similarity

        return max(0, 1 - distance)

    # ==================================================
    # BM25 Score Normalization
    # ==================================================

    def _normalize_bm25_scores(self, results: list[dict]):

        if not results:

            return

        max_score = max(result["score"] for result in results)

        if max_score == 0:

            return

        for result in results:

            result["score"] = result["score"] / max_score
