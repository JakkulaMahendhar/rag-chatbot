class PromptBuilder:


    @staticmethod
    def build(
        question: str,
        contexts: list[str]
    ) -> str:


        context_text = "\n\n".join(
            contexts
        )


        prompt = f"""
You are an AI assistant.

Answer the question using only the provided context.

If the answer is not available in the context,
say you don't know.

Context:
----------------
{context_text}
----------------

Question:
{question}

Answer:
"""


        return prompt