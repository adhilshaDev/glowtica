import pytest
import bcrypt
from unittest.mock import patch, MagicMock
from bson import ObjectId

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test_secret_key"
    with app.test_client() as client:
        yield client


def test_account_unauthenticated(client):
    """Should return 401 Unauthorized for account operations when logged out."""
    assert client.post("/api/account/photo").status_code == 401
    assert client.put("/api/account/username").status_code == 401
    assert client.put("/api/account/password").status_code == 401


def test_update_photo_success(client):
    """Should convert uploaded photo to base64 Data URL and store in MongoDB user document."""
    dummy_user_id = ObjectId()
    with client.session_transaction() as sess:
        sess["user_id"] = str(dummy_user_id)

    payload = {"avatar_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="}

    with patch("app.db") as mock_db:
        mock_db["users"].find_one.return_value = {"_id": dummy_user_id, "name": "Test User"}

        response = client.post("/api/account/photo", json=payload)
        assert response.status_code == 200
        data = response.get_json()

        assert data["avatar_base64"] == payload["avatar_base64"]
        mock_db["users"].update_one.assert_called_once_with(
            {"_id": dummy_user_id},
            {"$set": {"avatar_base64": payload["avatar_base64"]}}
        )


def test_update_username_success(client):
    """Should update username in MongoDB user document."""
    dummy_user_id = ObjectId()
    with client.session_transaction() as sess:
        sess["user_id"] = str(dummy_user_id)

    with patch("app.db") as mock_db:
        mock_db["users"].find_one.return_value = {
            "_id": dummy_user_id,
            "name": "Updated Name",
            "email": "test@example.com",
            "avatar_base64": None
        }

        response = client.put("/api/account/username", json={"name": "Updated Name"})
        assert response.status_code == 200
        data = response.get_json()

        assert data["name"] == "Updated Name"
        mock_db["users"].update_one.assert_called_once_with(
            {"_id": dummy_user_id},
            {"$set": {"name": "Updated Name"}}
        )


def test_update_password_incorrect_current(client):
    """Should reject password update if current password is incorrect."""
    dummy_user_id = ObjectId()
    with client.session_transaction() as sess:
        sess["user_id"] = str(dummy_user_id)

    hashed = bcrypt.hashpw(b"correct_password", bcrypt.gensalt())

    with patch("app.db") as mock_db:
        mock_db["users"].find_one.return_value = {
            "_id": dummy_user_id,
            "password_hash": hashed
        }

        payload = {"current_password": "wrong_password", "new_password": "new_password_123"}
        response = client.put("/api/account/password", json=payload)

        assert response.status_code == 401
        assert "Incorrect current password" in response.get_json()["error"]


def test_update_password_success(client):
    """Should verify current password with bcrypt and update password_hash in MongoDB."""
    dummy_user_id = ObjectId()
    with client.session_transaction() as sess:
        sess["user_id"] = str(dummy_user_id)

    hashed = bcrypt.hashpw(b"old_password_123", bcrypt.gensalt())

    with patch("app.db") as mock_db:
        mock_db["users"].find_one.return_value = {
            "_id": dummy_user_id,
            "password_hash": hashed
        }

        payload = {"current_password": "old_password_123", "new_password": "new_password_456"}
        response = client.put("/api/account/password", json=payload)

        assert response.status_code == 200
        assert response.get_json()["message"] == "Password updated successfully."
        mock_db["users"].update_one.assert_called_once()


def test_account_logout_success(client):
    """Should clear Flask session and return ok."""
    with client.session_transaction() as sess:
        sess["user_id"] = str(ObjectId())

    response = client.post("/api/account/logout")
    assert response.status_code == 200
    assert response.get_json() == {"ok": True}
    with client.session_transaction() as sess:
        assert "user_id" not in sess
