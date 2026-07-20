class PromptBuilder:


    @staticmethod
    def build(
        question: str,
        contexts: list[str]
    ):


        context_text = "\n\n".join(
            contexts
        )


        return f"""

You are an AI assistant.

Answer the question using only the provided context.

Context:

{context_text}


Question:

{question}


Answer:

"""