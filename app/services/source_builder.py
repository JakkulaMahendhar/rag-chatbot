from app.models.source import SourceReference
from app.core.logger import logger


class SourceBuilder:


    @staticmethod
    def build(results) -> list[SourceReference]:

        logger.info(
            "Building source references"
        )

        documents = results.get(
            "documents",
            [[]]
        )[0]

        metadatas = results.get(
            "metadatas",
            [[]]
        )[0]

        distances = results.get(
            "distances",
            [[]]
        )[0]

        sources = []

        for index, document in enumerate(documents):

            metadata = (
                metadatas[index]
                if index < len(metadatas)
                else {}
            )

            distance = (
                distances[index]
                if index < len(distances)
                else None
            )

            source = SourceReference(

                document_id=str(
                    metadata.get(
                        "document_id",
                        ""
                    )
                ),

                chunk_id=str(
                    metadata.get(
                        "chunk_id",
                        ""
                    )
                ),

                filename=str(
                    metadata.get(
                        "filename",
                        ""
                    )
                ),

                content=document,

                score=distance

            )

            sources.append(source)

        logger.info(
            f"Generated {len(sources)} source references"
        )

        return sources