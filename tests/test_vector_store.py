from app.services.vector_store import VectorStoreService


def test_collection_creation():

    collection = VectorStoreService.get_collection()

    assert collection is not None