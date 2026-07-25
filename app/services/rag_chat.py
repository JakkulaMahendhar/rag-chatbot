import time

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
from app.services.context_ranker import ContextRanker
from app.services.context_deduplicator import ContextDeduplicator
from app.services.context_compressor import ContextCompressor
from app.services.query_enhancer import QueryEnhancer
from app.services.search_evaluator import SearchEvaluator

class RAGChatService:


    def __init__(self):

        logger.info(
            "Initializing RAGChatService"
        )

        self.embedding_service = EmbeddingService()

        logger.info(
            "EmbeddingService initialized"
        )


        self.retrieval_service = RetrievalService()

        logger.info(
            "RetrievalService initialized"
        )


        self.llm = AIServiceRegistry.get_llm()

        logger.info(
            "LLM provider initialized"
        )


        self.conversation_service = ConversationService()

        logger.info(
            "ConversationService initialized"
        )

        self.query_enhancer = QueryEnhancer()

        logger.info(
            "QueryEnhancer initialized"
        )


    def chat(
        self,
        question: str,
        conversation_id: str | None = None
    ):


        start_time = time.perf_counter()


        logger.info(
            "========== RAG CHAT STARTED =========="
        )


        logger.info(
            f"User question: {question}"
        )


        # -----------------------------------------
        # Conversation Handling
        # -----------------------------------------

        if conversation_id and conversation_id != "string":


            logger.info(
                f"Existing conversation found: {conversation_id}"
            )


        else:


            logger.info(
                "No conversation_id provided. Creating new conversation"
            )


            conversation_id = (
                self.conversation_service
                .create_conversation()
            )


            logger.info(
                f"Created conversation: {conversation_id}"
            )



        self.conversation_service.add_user_message(

            conversation_id,

            question

        )


        logger.info(
            "User message stored in conversation memory"
        )



        # -----------------------------------------
        # Query Embedding
        # -----------------------------------------

        embedding_start = time.perf_counter()


        logger.info(
            "Generating query embedding"
        )


        enhanced_query = (
            self.query_enhancer.enhance(question)
        )


        query_embedding = (
            self.embedding_service.generate_query_embedding(
            enhanced_query
            )
        )

        embedding_time = (
            time.perf_counter()
            -
            embedding_start
        )


        logger.info(
            f"Query embedding generated | "
            f"Dimension: {len(query_embedding)} | "
            f"Time: {embedding_time:.3f}s"
        )



        # -----------------------------------------
        # Vector Retrieval
        # -----------------------------------------

        retrieval_start = time.perf_counter()


        logger.info(
            "Searching relevant chunks from vector database"
        )


        results = (
            self.retrieval_service.retrieve(

                query_embedding=query_embedding,
                query=question
            )
        )

        evaluation = SearchEvaluator.evaluate(

            question,

            results

        )

        if not results["ids"][0]:

            retrieval_time = (
                time.perf_counter()
                -
                retrieval_start
            )

            total_time = (
                        time.perf_counter()
                        -
                        start_time
                    )

            metrics = RAGMetrics(

                conversation_id=conversation_id,

                question=question,

                 retrieved_chunks=0,

                accepted_chunks=0,

                context_length=0,

                embedding_time=embedding_time,

                retrieval_time=retrieval_time,

                llm_time=0,

                total_time=total_time

            )


            MetricsService.record(metrics)    

            return {
                "conversation_id": conversation_id,
                "question": question,
                "answer": "I don't have enough information from the provided documents.",
                "sources": []
            }


        retrieval_time = (
            time.perf_counter()
            -
            retrieval_start
        )


        sources = SourceBuilder.build(results)
        
        # -----------------------------------------
        # Retrieval Evaluation
        # -----------------------------------------

        evaluation = RAGEvaluator.evaluate(question,sources)

        sources = ContextRanker.rank(sources)

        sources = ContextDeduplicator.remove_duplicates(sources)

        logger.info(
            f"Unique sources after deduplication: {len(sources)}")

        sources = ContextCompressor.compress(question,sources)

        context = ContextFormatter.format(sources)


        logger.info(
            f"Vector search completed | "
            f"Retrieved chunks: {len(sources)} | "
            f"Context size: {len(context)} characters | "
            f"Time: {retrieval_time:.3f}s"
        )



        for index, source in enumerate(sources):

            logger.debug(

            f"""
            Retrieved Source {index + 1}

            Filename:{source.filename}

            Chunk ID:{source.chunk_id}

            Score:{source.score}

            Distance : {source.score:.4f}

            Content Preview:{source.content[:150]}
            """
            )   



        # -----------------------------------------
        # Conversation History
        # -----------------------------------------

        logger.info(
            "Loading conversation history"
        )


        history = (
            self.conversation_service
            .get_history(
                conversation_id
            )
        )


        logger.info(
            f"Conversation history loaded | "
            f"Messages count: {len(history)}"
        )



        # -----------------------------------------
        # Prompt Creation
        # -----------------------------------------

        logger.info(
            "Building final RAG prompt"
        )


        prompt = PromptBuilder.build(

            question,

            context,

            history

        )


        logger.info(
            f"Prompt created | "
            f"Characters: {len(prompt)}"
        )



        # -----------------------------------------
        # LLM Generation
        # -----------------------------------------

        llm_start = time.perf_counter()


        logger.info(
            "Sending prompt to LLM"
        )


        answer = self.llm.generate(
            prompt
        )

        logger.debug(
    f"""
================ LLM RESPONSE ================

{answer}

==============================================
"""
)

        logger.debug(
    f"""
================ FINAL PROMPT ================

{prompt}

==============================================
"""
)


        llm_time = (
            time.perf_counter()
            -
            llm_start
        )


        logger.info(
            f"LLM response generated | "
            f"Response length: {len(answer)} | "
            f"Time: {llm_time:.3f}s"
        )



        # -----------------------------------------
        # Store Assistant Response
        # -----------------------------------------

        self.conversation_service.add_assistant_message(

            conversation_id,

            answer

        )


        logger.info(
            "Assistant response stored in conversation memory"
        )



        total_time = (
            time.perf_counter()
            -
            start_time
        )


        logger.info(
            f"========== RAG CHAT COMPLETED | "
            f"Total time: {total_time:.3f}s =========="
        )

        # -----------------------------------------
        # RAG Metrics
        # -----------------------------------------

        metrics = RAGMetrics(

            conversation_id=conversation_id,

            question=question,

            retrieved_chunks=len(results["ids"][0]),

            accepted_chunks=len(sources),

            context_length=len(context),

            embedding_time=embedding_time,

            retrieval_time=retrieval_time,

            llm_time=llm_time,

            total_time=total_time

        )


        MetricsService.record(metrics)



        return {

            "conversation_id": conversation_id,

            "question": question,

            "answer": answer,

            "sources": sources,

            "evaluation": evaluation

        }