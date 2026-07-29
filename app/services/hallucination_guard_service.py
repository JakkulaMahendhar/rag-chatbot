from app.core.logger import logger


class HallucinationGuardService:

    def __init__(self, llm_service):
        self.llm_service = llm_service

        logger.info("Hallucination Guard initialized")

    def validate(self, question: str, context: str, answer: str):

        prompt = f"""
You are a hallucination detection system.

Your task:
Check whether the answer is fully supported by the provided context.

Rules:
- Do not use external knowledge.
- Identify unsupported claims.
- Return only JSON.

Question:
{question}


Context:
{context}


Answer:
{answer}


Return:

{{
    "grounded": true/false,
    "confidence": 0-1,
    "unsupported_claims": []
}}

"""

        response = self.llm_service.generate(prompt)

        result = self._parse_response(response)

        logger.info(f"Hallucination result: {result}")

        return result

    def _parse_response(self, response: str):

        import json

        try:
            return json.loads(response)

        except Exception:

            return {
                "grounded": False,
                "confidence": 0,
                "unsupported_claims": ["Unable to validate response"],
            }
