from app.services.vector_store import VectorStoreService
from app.services.bm25_search import BM25SearchService

from app.core.config import settings
from app.core.logger import logger



class HybridSearchService:


    def __init__(self):

        self.vector_store = VectorStoreService()

        self.bm25_service = BM25SearchService()



    def search(
        self,
        query_embedding: list[float],
        query: str,
        top_k: int = 3
    ):


        logger.info(
            "Starting hybrid search"
        )


        # --------------------------------
        # Vector Search
        # --------------------------------

        vector_results = (
            self.vector_store.search(

                query_embedding=query_embedding,

                top_k=top_k

            )
        )


        logger.info(
            f"Vector results: {len(vector_results['ids'][0])}"
        )



        vector_documents = self._convert_vector_results(
            vector_results
        )



        # --------------------------------
        # BM25 Search
        # --------------------------------

        bm25_results = (
            self.bm25_service.search(

                query=query,

                top_k=top_k

            )
        )

        self._normalize_bm25_scores(bm25_results)


        logger.info(
            f"BM25 results: {len(bm25_results)}"
        )



        # --------------------------------
        # Merge Results
        # --------------------------------

        merged = (
            self._merge_results(

                vector_documents,

                bm25_results

            )
        )


        ranked = sorted(

            merged.values(),

            key=lambda x:x["hybrid_score"],

            reverse=True

        )



        logger.info(
            f"Hybrid ranking completed | Results={len(ranked[:top_k])}"
        )

        logger.info(
            "Hybrid ranking results"
        )

        for item in ranked[:top_k]:

            logger.info(
                f"""
Chunk ID:
{item['chunk_id']}

Vector Score:
{item['vector_score']:.4f}

BM25 Score:
{item['bm25_score']:.4f}

Hybrid Score:
{item['hybrid_score']:.4f}

Filename:
{item['metadata'].get('filename', 'Unknown')}
"""
        )

        return {

            "ids":[
                [
                    item["chunk_id"]
                    for item in ranked[:top_k]
                ]
            ],

            "documents":[
                [
                    item["content"]
                    for item in ranked[:top_k]
                ]
            ],

            "metadatas":[
                [
                    item["metadata"]
                    for item in ranked[:top_k]
                ]
            ],

            "distances":[
                [
                    1 - item["hybrid_score"]
                    for item in ranked[:top_k]
                ]
            ]

        }



    def _convert_vector_results(
        self,
        results
    ):

        documents = []


        for index, chunk_id in enumerate(results["ids"][0]):


            distance = results["distances"][0][index]


            logger.info(
            f"""
            Vector Raw Distance:

            Chunk:
            {chunk_id}

            Distance:
            {distance}
            """
            )


            vector_score = self._normalize_distance(
                distance
            )


            logger.info(
            f"""
            Vector Normalized Score:

            Chunk:
            {chunk_id}

            Score:
            {vector_score}
            """
            )


            documents.append(

            {

                "chunk_id": chunk_id,

                "content":
                results["documents"][0][index],

                "metadata":
                results["metadatas"][0][index],

                "vector_score":
                vector_score

            }

        )


        return documents




    def _merge_results(
        self,
        vector_results,
        bm25_results
    ):


        merged={}


        # Vector results

        for item in vector_results:


            chunk_id=item["chunk_id"]


            merged[chunk_id]={

                **item,

                "bm25_score":0,

            }




        # BM25 results

        for item in bm25_results:


            chunk_id=item["chunk_id"]


            if chunk_id in merged:


                merged[chunk_id]["bm25_score"]=(
                    item["score"]
                )


            else:


                merged[chunk_id]={

                    "chunk_id":chunk_id,

                    "content":item["content"],

                    "metadata":item["metadata"],

                    "vector_score":0,

                    "bm25_score":item["score"]

                }



        # Calculate Hybrid Score

        for item in merged.values():


            item["hybrid_score"]=(

                settings.vector_weight
                *
                item["vector_score"]

                +

                settings.bm25_weight
                *
                item["bm25_score"]

            )


        return merged



    def _normalize_distance(
        self,
        distance:float
    ):


        # Chroma distance:
        # lower = better

        return max(
            0,
            1-distance
        )

    def _normalize_bm25_scores(
        self,
        results: list[dict]
    ):

        if not results:
            return

        max_score = max(
            result["score"]
            for result in results
        )

        if max_score == 0:
            return

        for result in results:

            result["score"] = (
            result["score"] / max_score
            )