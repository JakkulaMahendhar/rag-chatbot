from app.models.source import SourceReference
from app.core.logger import logger


class SourceBuilder:

    @staticmethod
    def build(results) -> list[SourceReference]:

        logger.info("Building source references")

        sources = []

        # -----------------------------------
        # New multi_retrieve format
        # -----------------------------------

        if isinstance(results, list):

            for document in results:

                metadata = document.get("metadata", {})

                source = SourceReference(
                    document_id=str(metadata.get("document_id", "")),
                    chunk_id=str(metadata.get("chunk_id", document.get("id", ""))),
                    filename=str(metadata.get("filename", "")),
                    content=document.get("content", ""),
                    score=document.get("score"),
                )

                sources.append(source)

        # -----------------------------------
        # Old Chroma format support
        # -----------------------------------

        else:

            documents = results.get("documents", [[]])[0]

            metadatas = results.get("metadatas", [[]])[0]

            distances = results.get("distances", [[]])[0]

            hybrid_scores = results.get("hybrid_scores", [[]])[0]

            for index, document in enumerate(documents):

                metadata = metadatas[index] if index < len(metadatas) else {}

                distance = distances[index] if index < len(distances) else None

                score = hybrid_scores[index] if index < len(hybrid_scores) else None

                source = SourceReference(
                    document_id=str(metadata.get("document_id", "")),
                    chunk_id=str(metadata.get("chunk_id", "")),
                    filename=str(metadata.get("filename", "")),
                    content=document,
                    score=score,
                )

                sources.append(source)

        logger.info(f"Generated {len(sources)} source references")

        return sources
