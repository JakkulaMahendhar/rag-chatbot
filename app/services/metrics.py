from app.models.rag_metrics import RAGMetrics
from app.core.logger import logger


class MetricsService:


    @staticmethod
    def record(
        metrics: RAGMetrics
    ):


        logger.info(
            f"""
========== RAG METRICS ==========

Conversation ID:
{metrics.conversation_id}

Question:
{metrics.question}


Retrieval:

Retrieved Chunks:
{metrics.retrieved_chunks}

Accepted Chunks:
{metrics.accepted_chunks}


Context:

Context Length:
{metrics.context_length} characters


Performance:

Embedding:
{metrics.embedding_time:.3f}s

Retrieval:
{metrics.retrieval_time:.3f}s

LLM:
{metrics.llm_time:.3f}s

Total:
{metrics.total_time:.3f}s


=================================
"""
        )