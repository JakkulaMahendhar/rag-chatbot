from unittest.mock import Mock

from app.services.retrieval import RetrievalService



def test_retrieval():

    service = RetrievalService()


    service.vector_store.search = Mock(
        return_value={
            "ids":[["1"]],
            "documents":[["hello"]],
            "metadatas":[[{}]],
            "distances":[[0.1]]
        }
    )


    result = service.retrieve(
        [0.1,0.2],
        1
    )


    assert result["ids"][0][0] == "1"