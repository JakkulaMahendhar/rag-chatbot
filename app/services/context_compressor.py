from app.core.logger import logger
from app.models.source import SourceReference
import re

class ContextCompressor:

    @staticmethod
    def compress(
        question: str,
        sources: list[SourceReference]
    ) -> list[SourceReference]:

        logger.info(
            "Compressing retrieved context"
        )

        keywords = [
            word.lower()
            for word in re.findall(r"\w+", question)
            if len(word) > 2
        ]

        for source in sources:

            original_content = source.content
            original_length = len(original_content)

            paragraphs = original_content.split("\n")

            sentences = re.split(r'(?<=[.!?])\s+',source.content)

            relevant = []

            for sentence in sentences:

                text = sentence.lower()

                if any(
                    keyword in text
                    for keyword in keywords
                ):
                    relevant.append(sentence)

            if relevant:

                compressed_content = "\n".join(relevant)

                source.content = compressed_content
                
                logger.info(
                    f"""
Chunk: {source.chunk_id}

Original Length: {original_length}

Compressed Length: {len(compressed_content)}
"""
                )
            else:
                logger.debug(
                 f"No matching sentences found for {source.chunk_id}, using original chunk."
                )    



        logger.info(
            f"Compressed {len(sources)} retrieved chunks"
        )

        return sources