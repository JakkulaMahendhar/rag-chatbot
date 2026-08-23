def test_register_creates_user(client, register_user):

    user = register_user()

    assert user["email"].endswith("@example.com")


def test_register_duplicate_email_rejected(client, register_user):

    user = register_user()

    response = client.post(
        "/auth/register",
        json={"email": user["email"], "password": user["password"]},
    )

    assert response.status_code == 400


def test_login_wrong_password_rejected(client, register_user):

    user = register_user()

    response = client.post(
        "/auth/login",
        json={"email": user["email"], "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_login_unknown_email_rejected(client):

    response = client.post(
        "/auth/login",
        json={"email": "nobody-here@example.com", "password": "whatever123"},
    )

    assert response.status_code == 401


def test_me_requires_auth(client):

    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_rejects_invalid_token(client):

    response = client.get(
        "/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )

    assert response.status_code == 401


def test_me_returns_current_user(client, register_user):

    user = register_user()

    response = client.get("/auth/me", headers=user["headers"])

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == user["id"]
    assert body["email"] == user["email"]
