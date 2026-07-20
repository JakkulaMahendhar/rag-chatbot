from app.services.vector_store import VectorStoreService


def test_collection_creation():

    collection = VectorStoreService.stats # pyright: ignore[reportAttributeAccessIssue]

    assert collection is not None