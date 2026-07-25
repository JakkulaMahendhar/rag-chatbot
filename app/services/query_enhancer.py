from app.core.logger import logger
from app.core.ai_registry import AIServiceRegistry


class QueryEnhancer:


    def __init__(self):

        self.llm = (
            AIServiceRegistry
            .get_llm()
        )


    def enhance(
        self,
        question: str
    ) -> str:


        logger.info(
            "Enhancing user query"
        )


        prompt = f"""

You are a search query optimizer for a RAG system.

Rewrite the user question into a more detailed
search query.

Rules:
- Keep the original intent.
- Add missing technical context.
- Do not answer the question.
- Return only the improved search query.

User Question:

{question}

Improved Search Query:

"""


        enhanced_query = (
            self.llm.generate(
                prompt
            )
        )


        enhanced_query = (
            enhanced_query
            .strip()
        )


        logger.info(
            f"""
Original Query:
{question}

Enhanced Query:
{enhanced_query}
"""
        )


        return enhanced_query