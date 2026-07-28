from app.core.ai_registry import AIServiceRegistry
from app.core.logger import logger
import json


class QueryExpander:

    def __init__(self, llm):

        self.llm = llm

    def expand(self, query: str, number_of_queries: int = 3) -> list[str]:

        logger.info("Generating multiple search queries")

        prompt = f"""

You are a search query generator.

Generate {number_of_queries}
search queries.

Return ONLY a JSON array.

Example:

[
"Android activity lifecycle",
"Android Activity component",
"Activity vs Fragment"
]

Rules:

- No explanation
- No numbering
- No markdown
- No extra text

Original Query:

{query}

"""

        response = self.llm.generate(prompt)

        try:

            queries = json.loads(response)

        except Exception:
            queries = [q.strip("- ") for q in response.split("\n") if q.strip()]

        # Safety fallback

        if not queries:

            queries = [query]

        logger.info(f"""
Multi Query Expansion

Original:

{query}


Generated:

{queries}
""")

        return queries[:number_of_queries]
