from app.models.source import SourceReference


class SearchEvaluator:

    @staticmethod
    def evaluate(question: str, sources: list[SourceReference]):

        scores = [source.score for source in sources if source.score is not None]

        if not scores:

            return {
                "question": question,
                "retrieved": len(sources),
                "average_score": 0,
                "best_score": 0,
                "quality": "Weak",
            }

        average_score = sum(scores) / len(scores)

        best_score = max(scores)

        if best_score >= 0.7:
            quality = "Excellent"

        elif best_score >= 0.5:
            quality = "Good"

        else:
            quality = "Weak"

        return {
            "question": question,
            "retrieved": len(sources),
            "average_score": round(average_score, 4),
            "best_score": round(best_score, 4),
            "quality": quality,
        }
