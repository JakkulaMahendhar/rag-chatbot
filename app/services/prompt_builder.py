class PromptBuilder:


    @staticmethod
    def build(

        question: str,

        contexts: list[str],

        history=None

    ):


        context_text = "\n\n".join(
            contexts
        )


        history_text = ""


        if history:

            history_text = "\n".join(

                [
                    f"{msg.role}: {msg.content}"
                    for msg in history
                ]

            )


        prompt = f"""
You are an AI assistant.

Use the conversation history and provided context.

Conversation History:
--------------------
{history_text}
--------------------

Context:
--------------------
{context_text}
--------------------

Question:
{question}

Answer:
"""


        return prompt