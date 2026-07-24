class PromptBuilder:


    @staticmethod
    def build(

        question: str,

        contexts: list[str],

        history=None

    ):


        context_text = PromptBuilder._format_context(
            contexts
        )


        history_text = (
            PromptBuilder._format_history(history)
        )


        prompt = f"""
You are an AI assistant specialized in answering questions from provided documents.

Follow these rules strictly:

1. Answer only using the provided context.
2. Do not use external knowledge.
3. If the answer is not available in the context, respond exactly:
"I don't have enough information from the provided documents."
Do not add additional explanation.
4. Do not create or assume facts.
5. Keep the answer clear and concise.

Conversation History:
--------------------
{history_text}
--------------------

Retrieved Context:
--------------------
{context_text}
--------------------

User Question:
--------------------
{question}
--------------------

Answer:
"""


        return prompt



    @staticmethod
    def _format_context(
        contexts: list[str]
    ) -> str:


        formatted = []


        for index, context in enumerate(contexts):

            formatted.append(
                f"""
SOURCE {index + 1}
--------------------
{context}
"""
            )


        return "\n".join(formatted)



    @staticmethod
    def _format_history(
        history
    ) -> str:


        if not history:
            return "No previous conversation."


        return "\n".join(

            [
                f"{msg.role}: {msg.content}"
                for msg in history
            ]

        )