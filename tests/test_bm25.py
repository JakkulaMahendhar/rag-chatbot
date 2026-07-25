from app.services.bm25_search import BM25SearchService
from app.models.bm25_document import BM25Document

from uuid import uuid4



def test_bm25():


    service = BM25SearchService()


    documents = [

        BM25Document(

            chunk_id="1",

            document_id=uuid4(),

            content=
            """
            Android Activity is a component
            responsible for user interface.
            """,

            metadata={}

        ),


        BM25Document(

            chunk_id="2",

            document_id=uuid4(),

            content=
            """
            Android Service runs background tasks.
            """,

            metadata={}

        )

    ]


    service.add_documents(
        documents
    )


    results = service.search(
        "Activity component"
    )


    print(results)


    assert results[0]["chunk_id"]=="1"