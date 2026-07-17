from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_vector_stats():

    response = client.get("/vectors/stats")

    assert response.status_code == 200

    body = response.json()

    assert "collection" in body

    assert "vectors" in body