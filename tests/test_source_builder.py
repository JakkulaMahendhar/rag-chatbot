from app.services.source_builder import SourceBuilder


def test_build_sources():

    results = {

        "documents":[
            [
                "Background service..."
            ]
        ],

        "metadatas":[
            [
                {
                    "document_id":"doc1",
                    "chunk_id":"chunk1",
                    "filename":"android.pdf"
                }
            ]
        ],

        "distances":[
            [
                0.21
            ]
        ]

    }

    sources = SourceBuilder.build(results)

    assert len(sources) == 1

    assert sources[0].filename == "android.pdf"

    assert sources[0].chunk_id == "chunk1"