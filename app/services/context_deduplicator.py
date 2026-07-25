from app.core.logger import logger
from app.models.source import SourceReference


class ContextDeduplicator:

    @staticmethod
    def remove_duplicates(
        sources: list[SourceReference]
    ) -> list[SourceReference]:

        logger.info(
            "Removing duplicate context chunks"
        )

        unique_sources = []

        seen_contents = set()

        for source in sources:

            content = source.content.strip()

            if content in seen_contents:

                logger.info(
                    f"Duplicate removed | Chunk: {source.chunk_id}"
                )

                continue

            seen_contents.add(content)

            unique_sources.append(source)

        logger.info(
            f"Context Deduplication | "
            f"Before={len(sources)} "
            f"After={len(unique_sources)}"
        )

        return unique_sources