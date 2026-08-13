import re


class QueryAccessService:

    def get_requested_user(
        self,
        query: str,
    ) -> str | None:

        query_lower = query.lower()

        # User 1, User 2, User 10
        match = re.search(
            r"\buser\s*(\d+)\b",
            query_lower,
        )

        if match:
            return match.group(1)

        # User one, User two, etc.
        word_numbers = {
            "one": "1",
            "two": "2",
            "three": "3",
            "four": "4",
            "five": "5",
        }

        match = re.search(
            r"\buser\s+(one|two|three|four|five)\b",
            query_lower,
        )

        if match:
            return word_numbers[match.group(1)]

        return None

    def is_cross_user_request(
        self,
        query: str,
        current_user_id: int,
    ) -> bool:

        requested_user = self.get_requested_user(query)

        if requested_user is None:
            return False

        return str(current_user_id) != requested_user
