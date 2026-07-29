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

Generate {number_of_queries} search queries.

Return ONLY a JSON array.

Example:

[
  "Android activity lifecycle",
  "Android Activity component",
  "Activity lifecycle callbacks"
]

Rules:
- Return valid JSON only
- No markdown
- No explanation
- No code block

Original Query:

{query}
"""

        response = self.llm.generate(prompt)

        queries = []

        try:
            cleaned = response.strip()

            # Remove markdown if model adds it
            if cleaned.startswith("```"):
                cleaned = cleaned.replace("```json", "")
                cleaned = cleaned.replace("```", "")
                cleaned = cleaned.strip()

            queries = json.loads(cleaned)

        except Exception as e:

            logger.warning(f"Query expansion JSON parsing failed: {e}")

            # Better fallback
            lines = response.splitlines()

            for line in lines:
                ine = line.strip()

                if not line:
                    continue

                if line in ["[", "]"]:
                    continue

                line = line.strip(",")
                line = line.strip('"')

                if line:
                    queries.append(line)

        # Safety

        if not queries:
            queries = [query]

        # Ensure strings only

        queries = [q for q in queries if isinstance(q, str)]

        logger.info(f"""
    Multi Query Expansion

Original:

{query}


Generated:

{queries}
""")

        return queries[:number_of_queries]
