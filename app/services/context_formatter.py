from app.models.source import SourceReference


class ContextFormatter:


    @staticmethod
    def format(
        sources: list[SourceReference]
    ) -> str:


        formatted = []


        for index, source in enumerate(sources):

            formatted.append(
                f"""
SOURCE {index + 1}
--------------------

Document:
{source.filename}

Chunk ID:
{source.chunk_id}

Similarity Score:
{source.score}

Content:
{source.content}

"""
            )


        return "\n\n".join(formatted)