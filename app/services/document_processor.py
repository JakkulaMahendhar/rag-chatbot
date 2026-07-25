from uuid import uuid4

from fastapi import UploadFile

from app.core.exceptions import DocumentProcessingException
from app.core.logger import logger

from app.services.storage import StorageService
from app.services.parser import ParserService
from app.services.chunker import ChunkingService
from app.services.chunk_storage import ChunkStorageService
from app.services.embedding import EmbeddingService
from app.services.embedding_storage import EmbeddingStorageService
from app.services.vector_store import VectorStoreService
from app.services.bm25_search import BM25SearchService

from app.models.bm25_document import BM25Document


class DocumentProcessingService:


    @staticmethod
    async def process(file: UploadFile):

        try:

            # -----------------------------------
            # Save File
            # -----------------------------------

            location = await StorageService.save_file(file)


            # -----------------------------------
            # Parse Document
            # -----------------------------------

            text = ParserService.parse(location)


            document_id = uuid4()


            # -----------------------------------
            # Chunk Generation
            # -----------------------------------

            chunker = ChunkingService()


            chunks = chunker.split(

                text=text,

                document_id=document_id,

                metadata={

                    "document_id": str(document_id),

                    "filename": location.name,

                    "type": location.suffix

                }

            )


            logger.info(
                f"Generated chunks: {len(chunks)}"
            )



            # -----------------------------------
            # Save Chunks
            # -----------------------------------

            ChunkStorageService.save(

                document_id=str(document_id),

                chunks=chunks

            )



            # -----------------------------------
            # Generate Embeddings
            # -----------------------------------

            embedding_service = EmbeddingService()


            embeddings = embedding_service.generate(

                chunks

            )


            EmbeddingStorageService.save(

                document_id=str(document_id),

                embeddings=embeddings

            )



            # -----------------------------------
            # Store Vector Embeddings
            # -----------------------------------

            vector_store = VectorStoreService()


            vector_store.add_chunks(

                chunks=chunks,

                embeddings=embeddings

            )


            logger.info(
                "Document stored successfully in vector database"
            )



            # -----------------------------------
            # Sprint 9.5.2
            # Store BM25 Index
            # -----------------------------------

            bm25_service = BM25SearchService()


            bm25_documents = []


            for chunk in chunks:


                bm25_documents.append(

                    BM25Document(

                        chunk_id=str(chunk.chunk_id),

                        document_id=chunk.document_id,

                        content=chunk.content,

                        metadata=chunk.metadata

                    )

                )


            bm25_service.add_documents(

                bm25_documents

            )


            logger.info(
                "Document stored successfully in BM25 index"
            )



            return {


                "document_id": str(document_id),


                "filename": location.name,


                "size": location.stat().st_size,


                "extracted_characters": len(text),


                "total_chunks": len(chunks),


                "total_embeddings": len(embeddings)

            }


        except Exception as e:


            logger.exception(

                "Document processing failed"

            )


            raise DocumentProcessingException(

                "Unable to process document."

            ) from e