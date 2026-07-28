import time

from app.services.context_window_manager import ContextWindowManager
from app.services.embedding import EmbeddingService
from app.services.retrieval import RetrievalService
from app.services.prompt_builder import PromptBuilder
from app.services.conversation import ConversationService
from app.core.ai_registry import AIServiceRegistry
from app.core.logger import logger

from app.services.source_builder import SourceBuilder
from app.services.context_formatter import ContextFormatter

from app.models.rag_metrics import RAGMetrics
from app.services.metrics import MetricsService

from app.services.rag_evaluator import RAGEvaluator
from app.services.search_evaluator import SearchEvaluator

from app.services.context_ranker import ContextRanker
from app.services.context_deduplicator import ContextDeduplicator
from app.services.context_compressor import ContextCompressor

from app.services.query_enhancer import QueryEnhancer
from app.services.query_expander import QueryExpander

from app.services.reranker import Reranker


class RAGChatService:

    def __init__(self):

        logger.info("Initializing RAGChatService")

        self.embedding_service = EmbeddingService()

        self.retrieval_service = RetrievalService()

        self.llm = AIServiceRegistry.get_llm()

        self.conversation_service = ConversationService()

        # Query Optimization

        self.query_enhancer = QueryEnhancer()

        logger.info("QueryEnhancer initialized")

        self.query_expander = QueryExpander(self.llm)

        logger.info("QueryExpander initialized")

        # Cross Encoder

        self.reranker = Reranker()

        logger.info("Reranker initialized")

        self.context_manager = ContextWindowManager(
            max_context_tokens=4000, reserved_response_tokens=1000
        )

    def chat(self, question: str, conversation_id: str | None = None):

        start_time = time.perf_counter()

        logger.info("========== RAG CHAT STARTED ==========")

        logger.info(f"User question: {question}")

        # -------------------------------
        # Conversation
        # -------------------------------

        if not conversation_id or conversation_id == "string":

            conversation_id = self.conversation_service.create_conversation()

        self.conversation_service.add_user_message(conversation_id, question)

        # -------------------------------
        # Query Rewrite
        # -------------------------------

        history = self.conversation_service.get_history(conversation_id)

        enhanced_query = self.query_enhancer.enhance(question, history)

        # -------------------------------
        # Query Expansion
        # -------------------------------

        queries = self.query_expander.expand(enhanced_query)

        logger.info(f"""
Multi Query Expansion

Queries:

{queries}

""")

        # -------------------------------
        # Hybrid Retrieval
        # -------------------------------

        retrieval_start = time.perf_counter()

        documents = self.retrieval_service.multi_retrieve(
            queries=queries, embedding_service=self.embedding_service
        )

        retrieval_time = time.perf_counter() - retrieval_start

        logger.info(f"""
Retrieved Documents:

{len(documents)}

""")

        if not documents:

            return {
                "conversation_id": conversation_id,
                "answer": "I don't have enough information.",
            }

        # -------------------------------
        # Build Sources
        # -------------------------------

        sources = SourceBuilder.build(documents)

        logger.info(f"Source references created: {len(sources)}")

        # -------------------------------
        # Cross Encoder Reranking
        # -------------------------------

        sources = self.reranker.rerank(enhanced_query, sources)

        logger.info(f"""
After Cross Encoder:

{len(sources)}

""")

        # -------------------------------
        # Ranking
        # -------------------------------

        # sources = ContextRanker.rank(sources)

        sources = ContextDeduplicator.remove_duplicates(sources)

        logger.info(f"After deduplication: {len(sources)}")

        sources = ContextCompressor.compress(question, sources)

        logger.info(f"After compression: {len(sources)}")

        sources = self.context_manager.select_context(sources)

        logger.info(f"After context window selection: {len(sources)}")

        context = ContextFormatter.format(sources)

        # -------------------------------
        # Evaluation
        # -------------------------------

        search_evaluation = SearchEvaluator.evaluate(question, sources)

        evaluation = RAGEvaluator.evaluate(question, sources)

        # -------------------------------
        # Prompt
        # -------------------------------

        prompt = PromptBuilder.build(question, context, history)

        # -------------------------------
        # LLM
        # -------------------------------

        llm_start = time.perf_counter()

        answer = self.llm.generate(prompt)

        llm_time = time.perf_counter() - llm_start

        self.conversation_service.add_assistant_message(conversation_id, answer)

        total_time = time.perf_counter() - start_time

        metrics = RAGMetrics(
            conversation_id=conversation_id,
            question=question,
            retrieved_chunks=len(documents),
            accepted_chunks=len(sources),
            context_length=len(context),
            embedding_time=0,
            retrieval_time=retrieval_time,
            llm_time=llm_time,
            total_time=total_time,
        )

        MetricsService.record(metrics)

        logger.info(f"""
========== RAG CHAT COMPLETED ==========

Retrieval:
{retrieval_time:.3f}s

LLM:
{llm_time:.3f}s

Total:
{total_time:.3f}s

""")

        return {
            "conversation_id": conversation_id,
            "question": question,
            "answer": answer,
            "sources": sources,
            "search_evaluation": search_evaluation,
            "evaluation": evaluation,
        }
