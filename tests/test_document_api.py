def _upload_sample(client, headers):
    """
    Registers a document and returns its id. Upload only performs the
    fast registration phase (save file + create a "pending" row) -
    actual processing happens in the worker, not inline, so document
    status here is "pending", not "completed". See
    test_document_processor.py for the processing pipeline itself.
    """

    with open("tests/sample.txt", "rb") as f:

        response = client.post(
            "/upload",
            files={"file": ("sample.txt", f, "text/plain")},
            headers=headers,
        )

    assert response.status_code == 202, response.text
    assert response.json()["status"] == "pending"

    return int(response.json()["document_id"])


def test_documents_require_auth(client):

    assert client.get("/documents").status_code == 401


def test_list_documents_empty_for_new_user(client, register_user):

    user = register_user()

    response = client.get("/documents", headers=user["headers"])

    assert response.status_code == 200
    assert response.json() == []


def test_upload_list_get_delete_document(client, register_user):

    user = register_user()

    document_id = _upload_sample(client, user["headers"])

    listing = client.get("/documents", headers=user["headers"])

    assert listing.status_code == 200
    assert any(doc["id"] == document_id for doc in listing.json())

    detail = client.get(f"/documents/{document_id}", headers=user["headers"])

    assert detail.status_code == 200
    assert detail.json()["filename"] == "sample.txt"
    assert detail.json()["status"] == "pending"

    delete = client.delete(f"/documents/{document_id}", headers=user["headers"])

    assert delete.status_code == 200

    after_delete = client.get(f"/documents/{document_id}", headers=user["headers"])

    assert after_delete.status_code == 403


def test_get_nonexistent_document_forbidden(client, register_user):

    user = register_user()

    response = client.get("/documents/999999999", headers=user["headers"])

    assert response.status_code == 403


def test_document_ownership_is_enforced_across_users(client, register_user):

    owner = register_user()
    other = register_user()

    document_id = _upload_sample(client, owner["headers"])

    try:

        listing = client.get("/documents", headers=other["headers"])

        assert all(doc["id"] != document_id for doc in listing.json())

        assert (
            client.get(
                f"/documents/{document_id}", headers=other["headers"]
            ).status_code
            == 403
        )

        assert (
            client.delete(
                f"/documents/{document_id}", headers=other["headers"]
            ).status_code
            == 403
        )

    finally:

        client.delete(f"/documents/{document_id}", headers=owner["headers"])
