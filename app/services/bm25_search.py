import pickle
import json

from pathlib import Path

from rank_bm25 import BM25Okapi

from app.models.bm25_document import BM25Document
from app.core.logger import logger
from app.core.config import settings


class BM25SearchService:

    def __init__(self):

        self.documents: list[BM25Document] = []

        self.index = None

        self.storage_path = Path(settings.bm25_path)

        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.load()

    def add_documents(self, documents: list[BM25Document]):

        logger.info(f"Adding {len(documents)} documents to BM25")

        self.documents.extend(documents)

        self._build_index()

        self.save()

    def _build_index(self):

        tokenized_documents = [
            document.content.lower().split() for document in self.documents
        ]

        self.index = BM25Okapi(tokenized_documents)

        logger.info(f"BM25 index built | Documents={len(self.documents)}")

    def search(self, query: str, top_k: int = 3):

        if not self.index:

            logger.warning("BM25 index unavailable")

            return []

        tokens = query.lower().split()

        scores = self.index.get_scores(tokens)

        ranked = sorted(range(len(scores)), key=lambda x: scores[x], reverse=True)

        results = []

        for idx in ranked[:top_k]:

            doc = self.documents[idx]

            results.append(
                {
                    "chunk_id": doc.chunk_id,
                    "document_id": doc.document_id,
                    "content": doc.content,
                    "metadata": doc.metadata,
                    "score": float(scores[idx]),
                }
            )

        return results

    def save(self):

        documents_file = self.storage_path / "documents.json"

        with open(documents_file, "w") as file:

            json.dump([doc.model_dump(mode="json") for doc in self.documents], file)

        with open(self.storage_path / "index.pkl", "wb") as file:

            pickle.dump(self.index, file)

        logger.info("BM25 index persisted")

    def load(self):

        documents_file = self.storage_path / "documents.json"

        index_file = self.storage_path / "index.pkl"

        if not documents_file.exists():

            return

        with open(documents_file) as file:

            data = json.load(file)

            self.documents = [BM25Document(**item) for item in data]

        with open(index_file, "rb") as file:

            self.index = pickle.load(file)

        logger.info(f"BM25 loaded | Documents={len(self.documents)}")

    def delete_document(self, document_id: str):
        """
        Remove document and related chunks from BM25 index.
        """

        logger.info(f"Deleting document from BM25 | document_id={document_id}")

        self.documents = [
            doc for doc in self.documents if doc.document_id != document_id
        ]

        self._build_index()

        self.save()

    def _build_index(self):
        """
        Build or rebuild BM25 index.
        """

        if not self.documents:

            self.index = None

            logger.info("BM25 index cleared. No documents available.")

            return

        tokenized_documents = [
            document.content.lower().split() for document in self.documents
        ]

        self.index = BM25Okapi(tokenized_documents)

        logger.info(f"BM25 index rebuilt | Documents={len(self.documents)}")
