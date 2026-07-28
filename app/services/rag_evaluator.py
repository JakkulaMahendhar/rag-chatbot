class RAGEvaluator:

    @staticmethod
    def evaluate(question, sources):

        scores = [source.score for source in sources if source.score is not None]

        if not scores:

            return {"average_score": 0, "best_score": 0, "quality": "Weak"}

        return {
            "average_score": sum(scores) / len(scores),
            "best_score": max(scores),
            "quality": "Good",
        }
