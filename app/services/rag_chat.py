import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_registry import AIServiceRegistry
from app.core.config import settings
from app.core.logger import logger

from app.models.rag_metrics import RAGMetrics

from app.services.context_window_manager import ContextWindowManager
from app.services.embedding import EmbeddingService
from app.services.hallucination_guard_service import HallucinationGuardService
from app.services.retrieval import RetrievalService
from app.services.prompt_builder import PromptBuilder
from app.services.conversation import ConversationService

from app.services.source_builder import SourceBuilder
from app.services.context_formatter import ContextFormatter

from app.services.metrics import MetricsService

from app.services.rag_evaluator import RAGEvaluator
from app.services.search_evaluator import SearchEvaluator

from app.services.context_deduplicator import ContextDeduplicator
from app.services.context_compressor import ContextCompressor

from app.services.query_enhancer import QueryEnhancer
from app.services.query_expander import QueryExpander
from app.services.query_access import QueryAccessService


class RAGChatService:

    def __init__(self, session: AsyncSession, llm_provider: str | None = None):

        logger.info("Initializing RAGChatService")

        self.embedding_service = EmbeddingService()

        self.retrieval_service = RetrievalService(session=session)

        # llm_provider lets the frontend's Settings toggle pick Gemini
        # instead of the server's default (Ollama) on a per-request basis.
        self.llm = AIServiceRegistry.get_llm(llm_provider)

        self.conversation_service = ConversationService()

        # -----------------------------------
        # Query Optimization
        # -----------------------------------

        self.query_access_service = QueryAccessService()

        logger.info("QueryAccessService initialized")

        self.query_enhancer = QueryEnhancer(self.llm)

        logger.info("QueryEnhancer initialized")

        self.query_expander = QueryExpander(self.llm)

        logger.info("QueryExpander initialized")

        # -----------------------------------
        # Cross Encoder
        # -----------------------------------

        self.reranker = AIServiceRegistry.get_reranker()

        logger.info("Reranker initialized")

        # -----------------------------------
        # Context Management
        # -----------------------------------

        self.context_manager = ContextWindowManager(
            max_context_tokens=4000,
            reserved_response_tokens=1000,
        )

        # -----------------------------------
        # Hallucination Guard
        # -----------------------------------

        self.hallucination_guard = HallucinationGuardService(self.llm)

    async def chat(
        self,
        question: str,
        conversation_id: str | None = None,
        user_id: int | None = None,
    ):

        start_time = time.perf_counter()

        logger.info("========== RAG CHAT STARTED ==========")

        logger.info(f"User question: {question}")

        # -----------------------------------
        # Conversation
        # -----------------------------------

        if not conversation_id or conversation_id == "string":

            conversation_id = self.conversation_service.create_conversation()

        self.conversation_service.add_user_message(
            conversation_id,
            question,
        )

        # -----------------------------------
        # Cross-User Access Check
        # -----------------------------------
        #
        # IMPORTANT:
        #
        # This check happens BEFORE:
        #
        # Query Enhancement
        # Query Expansion
        # Vector Search
        # BM25 Search
        # Hybrid Retrieval
        #
        # Therefore a user cannot retrieve
        # another user's documents.
        # -----------------------------------

        if user_id is not None:

            cross_user_request = self.query_access_service.is_cross_user_request(
                query=question,
                current_user_id=user_id,
            )

            if cross_user_request:

                logger.warning(
                    f"Cross-user query blocked | "
                    f"user_id={user_id} | "
                    f"question={question}"
                )

                answer = "I don't have enough information to answer that."

                self.conversation_service.add_assistant_message(
                    conversation_id,
                    answer,
                )

                total_time = time.perf_counter() - start_time

                logger.info(f"""
========== RAG CHAT BLOCKED ==========

Reason:
Cross-user document access attempt

User:
{user_id}

Question:
{question}

Total:
{total_time:.3f}s

=======================================
""")

                return {
                    "conversation_id": conversation_id,
                    "question": question,
                    "answer": answer,
                    "sources": [],
                    "search_evaluation": {
                        "question": question,
                        "retrieved": 0,
                        "average_score": 0.0,
                        "best_score": 0.0,
                        "quality": "Not applicable",
                    },
                    "evaluation": {
                        "average_score": 0.0,
                        "best_score": 0.0,
                        "quality": "Not applicable",
                    },
                }

        # -----------------------------------
        # Query Rewrite
        # -----------------------------------

        history = self.conversation_service.get_history(conversation_id)

        enhanced_query = self.query_enhancer.enhance(
            question,
            history,
        )

        logger.info(f"""
Query Enhancement

Original:
{question}

Enhanced:
{enhanced_query}
""")

        # -----------------------------------
        # Query Expansion
        # -----------------------------------

        queries = self.query_expander.expand(enhanced_query)

        # Remove invalid queries

        queries = [
            q.strip() for q in queries if isinstance(q, str) and len(q.strip()) > 3
        ]

        # Remove duplicates

        queries = list(dict.fromkeys(queries))

        if not queries:

            queries = [enhanced_query]

        logger.info(f"""
Multi Query Expansion

Queries:

{queries}

""")

        # -----------------------------------
        # Hybrid Retrieval
        # -----------------------------------

        retrieval_start = time.perf_counter()

        documents = await self.retrieval_service.multi_retrieve(
            queries=queries,
            embedding_service=self.embedding_service,
            user_id=user_id,
        )

        retrieval_time = time.perf_counter() - retrieval_start

        logger.info(f"""
Retrieved Documents:

{len(documents)}

""")

        # -----------------------------------
        # No Documents
        # -----------------------------------

        if not documents:

            answer = "I don't have enough information."

            self.conversation_service.add_assistant_message(
                conversation_id,
                answer,
            )

            total_time = time.perf_counter() - start_time

            logger.info(f"""
========== RAG CHAT COMPLETED ==========

No relevant documents found.

Retrieval:
{retrieval_time:.3f}s

Total:
{total_time:.3f}s

""")

            return {
                "conversation_id": conversation_id,
                "question": question,
                "answer": answer,
                "sources": [],
                "search_evaluation": {
                    "question": question,
                    "retrieved": 0,
                    "average_score": 0.0,
                    "best_score": 0.0,
                    "quality": "Not applicable",
                },
                "evaluation": {
                    "average_score": 0.0,
                    "best_score": 0.0,
                    "quality": "Not applicable",
                },
            }

        # -----------------------------------
        # Build Sources
        # -----------------------------------

        sources = SourceBuilder.build(documents)

        logger.info(f"Source references created: {len(sources)}")

        # -----------------------------------
        # Cross Encoder Reranking
        # -----------------------------------

        sources = self.reranker.rerank(
            enhanced_query,
            sources,
        )

        logger.info(f"""
After Cross Encoder:

{len(sources)}

""")

        # -----------------------------------
        # Deduplication
        # -----------------------------------

        sources = ContextDeduplicator.remove_duplicates(sources)

        logger.info(f"After deduplication: {len(sources)}")

        # -----------------------------------
        # Context Compression
        # -----------------------------------

        sources = ContextCompressor.compress(
            question,
            sources,
        )

        logger.info(f"After compression: {len(sources)}")

        # -----------------------------------
        # Context Window
        # -----------------------------------

        sources = self.context_manager.select_context(sources)

        logger.info(f"After context window selection: " f"{len(sources)}")

        # -----------------------------------
        # Format Context
        # -----------------------------------

        context = ContextFormatter.format(sources)

        # -----------------------------------
        # Evaluation
        # -----------------------------------

        search_evaluation = SearchEvaluator.evaluate(
            question,
            sources,
        )

        evaluation = RAGEvaluator.evaluate(
            question,
            sources,
        )

        # -----------------------------------
        # Prompt
        # -----------------------------------

        prompt = PromptBuilder.build(
            question,
            context,
            history,
        )

        # -----------------------------------
        # LLM
        # -----------------------------------

        llm_start = time.perf_counter()

        hallucination_detected = False

        hallucination_check_time = 0.0

        answer = self.llm.generate(prompt)

        # -----------------------------------
        # Hallucination Guard
        # -----------------------------------

        if settings.enable_hallucination_guard:

            hallucination_start = time.perf_counter()

            validation = self.hallucination_guard.validate(
                question,
                context,
                answer,
            )

            hallucination_check_time = time.perf_counter() - hallucination_start

            if not validation["grounded"]:

                hallucination_detected = True

                logger.warning("Hallucination detected. " "Regenerating response")

                strict_prompt = self._build_strict_prompt(
                    question,
                    context,
                )

                answer = self.llm.generate(strict_prompt)

        llm_time = time.perf_counter() - llm_start

        # -----------------------------------
        # Save Assistant Message
        # -----------------------------------

        self.conversation_service.add_assistant_message(
            conversation_id,
            answer,
        )

        # -----------------------------------
        # Metrics
        # -----------------------------------

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
            hallucination_check_time=(hallucination_check_time),
            hallucination_detected=(hallucination_detected),
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

        # -----------------------------------
        # Response
        # -----------------------------------

        return {
            "conversation_id": conversation_id,
            "question": question,
            "answer": answer,
            "sources": sources,
            "search_evaluation": search_evaluation,
            "evaluation": evaluation,
        }

    def _build_strict_prompt(
        self,
        question,
        context,
    ):

        return f"""
You are a strict RAG assistant.

Answer ONLY from the context.

If information is missing say:
"I don't have enough information."

Context:

{context}

Question:

{question}

"""
