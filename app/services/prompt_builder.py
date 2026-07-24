class PromptBuilder:


    @staticmethod
    def build(

        question: str,

        contexts: str,

        history=None

    ):


        context_text = contexts


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
    def _format_history(history) -> str:


        if not history:

            return "No previous conversation."


        formatted_history = []


        for msg in history:


            if isinstance(msg, str):

                formatted_history.append(msg)


            else:

                formatted_history.append(
                f"{msg.role}: {msg.content}"
                )


        return "\n".join(
            formatted_history
        )