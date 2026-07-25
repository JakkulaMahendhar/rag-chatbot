from app.models.search_evaluation import SearchEvaluation
from app.core.logger import logger


class SearchEvaluator:


    @staticmethod
    def evaluate(
        question:str,
        results:dict
    ):


        scores = results["distances"][0]


        if not scores:

            return SearchEvaluation(

                question=question,

                vector_results=0,

                bm25_results=0,

                hybrid_results=0,

                best_score=0,

                average_score=0,

                quality="No Results"

            )


        best_score=max(scores)

        average_score=sum(scores)/len(scores)



        if best_score >= 0.8:

            quality="Excellent"


        elif best_score >=0.6:

            quality="Good"


        elif best_score >=0.4:

            quality="Average"


        else:

            quality="Weak"



        evaluation = SearchEvaluation(

            question=question,

            vector_results=len(scores),

            bm25_results=len(scores),

            hybrid_results=len(scores),

            best_score=best_score,

            average_score=average_score,

            quality=quality

        )


        logger.info(

f"""
========== SEARCH EVALUATION ==========

Question:
{question}

Retrieved:
{len(scores)}

Best Score:
{best_score}

Average Score:
{average_score}

Quality:
{quality}

=======================================
"""

        )


        return evaluation