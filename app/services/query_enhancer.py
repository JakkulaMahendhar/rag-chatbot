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
        question: str,
        history: list | None = None
    ) -> str:


        logger.info(
            "Enhancing query with conversation context"
        )


        conversation = self._format_history(
            history
        )


        prompt = f"""

You are a query rewriting engine for a RAG system.

Your task:
Rewrite the latest user question into a standalone search query.

Use previous conversation context if required.

Rules:
- Resolve pronouns like:
  it, this, that, they, its
- Add missing technical context.
- Preserve user intent.
- Do not answer the question.
- Return only the search query.


Conversation History:

{conversation}


Current Question:

{question}


Standalone Search Query:

"""


        enhanced_query = (
            self.llm.generate(
                prompt
            )
            .strip()
        )


        logger.info(
f"""
Conversation Aware Query Rewrite

Original:
{question}


Rewritten:
{enhanced_query}
"""
        )


        return enhanced_query



    def _format_history(
        self,
        history: list | None
    ) -> str:


        if not history:

            return "No previous conversation."


        conversation = ""


        for message in history:


            # Pydantic object
            if hasattr(message, "role"):


                conversation += f"""

{message.role}:

{message.content}

"""


            # Dictionary fallback
            elif isinstance(message, dict):


                conversation += f"""

{message.get('role')}

{message.get('content')}

"""


        return conversation