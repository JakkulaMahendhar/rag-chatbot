from app.core.logger import logger


class ContextWindowManager:

    def __init__(
        self, max_context_tokens: int = 4000, reserved_response_tokens: int = 1000
    ):

        self.max_context_tokens = max_context_tokens
        self.reserved_response_tokens = reserved_response_tokens

    def estimate_tokens(self, text: str) -> int:
        """
        Simple token estimation.
        Later we can replace with tiktoken.
        """

        return len(text.split())

    def select_context(self, documents):

        logger.info(f"Context window selection started | Documents={len(documents)}")

        selected = []

        current_tokens = 0

        available_tokens = self.max_context_tokens - self.reserved_response_tokens

        for doc in documents:

            tokens = self.estimate_tokens(doc.content)

            if current_tokens + tokens > available_tokens:

                logger.info(f"""
Context limit reached

Current:
{current_tokens}

Next chunk:
{tokens}

Limit:
{available_tokens}
""")

                break

            selected.append(doc)

            current_tokens += tokens

        logger.info(f"""
Context window completed

Before:
{len(documents)}

After:
{len(selected)}

Tokens:
{current_tokens}
""")

        return selected
