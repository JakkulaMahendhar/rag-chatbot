from app.models.rag_evaluation import RAGEvaluation
from app.core.logger import logger


class RAGEvaluator:


    @staticmethod
    def evaluate(
        question:str,
        sources:list
    ) -> RAGEvaluation:


        scores = [
            source.score
            for source in sources
        ]


        average_score = sum(scores) / len(scores)


        quality = (
            RAGEvaluator._calculate_quality(
                average_score
            )
        )


        evaluation = RAGEvaluation(

            question=question,

            retrieved_chunks=len(sources),

            average_score=round(
                average_score,
                4
            ),

            best_score=max(scores),

            worst_score=min(scores),

            quality=quality
        )


        logger.info(
            f"""
========== RAG EVALUATION ==========

Question:
{question}

Retrieved:
{evaluation.retrieved_chunks}

Average Score:
{evaluation.average_score}

Best Score:
{evaluation.best_score}

Worst Score:
{evaluation.worst_score}

Quality:
{evaluation.quality}

====================================
"""
        )


        return evaluation



    @staticmethod
    def _calculate_quality(
        score:float
    ):


        if score >= 0.90:
            return "Excellent"

        elif score >= 0.75:
            return "Good"

        elif score >= 0.50:
            return "Weak"

        return "Poor"