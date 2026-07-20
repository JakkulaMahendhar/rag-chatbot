from app.services.embedding import EmbeddingService
from app.services.retrieval import RetrievalService
from app.services.prompt_builder import PromptBuilder
from app.core.ai_registry import AIServiceRegistry
from app.core.logger import logger


class RAGChatService:


    def __init__(self):

        logger.info(
            "Initializing RAG Chat Service"
        )

        self.embedding_service = EmbeddingService()

        self.retrieval_service = RetrievalService()

        self.llm = AIServiceRegistry.get_llm()



    def chat(
        self,
        question: str
    ):


        logger.info(
            "RAG pipeline started"
        )


        logger.info(
            f"User question: {question}"
        )


        # ---------------------------------
        # Step 1: Query Embedding
        # ---------------------------------

        logger.info(
            "Generating query embedding"
        )


        query_embedding = (
            self.embedding_service
            .generate_query_embedding(
                question
            )
        )


        logger.info(
            f"Query embedding generated. Dimension: {len(query_embedding)}"
        )



        # ---------------------------------
        # Step 2: Vector Retrieval
        # ---------------------------------

        logger.info(
            "Searching similar chunks in vector database"
        )


        results = (
            self.retrieval_service.retrieve(
                query_embedding=query_embedding,
                top_k=3
            )
        )


        documents = results.get(
            "documents",
            [[]]
        )[0] # type: ignore


        logger.info(
            f"Retrieved chunks count: {len(documents)}"
        )


        for index, document in enumerate(documents):

            logger.debug(
                f"Chunk {index + 1}: {document[:100]}"
            )



        # ---------------------------------
        # Step 3: Prompt Construction
        # ---------------------------------

        logger.info(
            "Building RAG prompt"
        )


        prompt = PromptBuilder.build(

            question,

            documents

        )


        logger.info(
            f"Prompt created. Length: {len(prompt)} characters"
        )



        # ---------------------------------
        # Step 4: LLM Generation
        # ---------------------------------

        logger.info(
            "Sending prompt to LLM"
        )


        answer = self.llm.generate(
            prompt
        )


        logger.info(
            "LLM response generated successfully"
        )


        logger.info(
            f"Response length: {len(answer)} characters"
        )



        logger.info(
            "RAG pipeline completed"
        )


        return {

            "question": question,

            "answer": answer,

            "sources": documents

        }