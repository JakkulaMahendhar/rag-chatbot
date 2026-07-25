from app.core.logger import logger


class ContextRanker:


    @staticmethod
    def rank(
        sources: list
    ) -> list:


        logger.info(
            "Ranking sources based on relevance score"
        )


        logger.info(
            f"Sources received for ranking: {len(sources)}"
        )


        ranked_sources = sorted(

            sources,

            key=lambda source: source.score,

            reverse=True

        )


        logger.info(
            f"Sources after ranking: {len(ranked_sources)}"
        )


        for index, source in enumerate(ranked_sources):

            logger.info(
                f"""
================ RANK RESULT ================

Rank:
{index + 1}

Filename:
{source.filename}

Chunk ID:
{source.chunk_id}

Score:
{source.score}

==============================================
"""
            )


        return ranked_sources