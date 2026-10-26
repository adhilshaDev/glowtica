import pytest
from unittest.mock import patch, MagicMock
from bson import ObjectId

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test_secret_key"
    with app.test_client() as client:
        yield client


def test_get_tips_progress_unauthenticated(client):
    """Should return 401 Unauthorized when session is missing user_id."""
    response = client.get("/api/tips/progress")
    assert response.status_code == 401
    assert response.get_json()["error"] == "Not logged in"


def test_get_tips_progress_success(client):
    """Should return category progress dictionary for logged in user."""
    dummy_user_id = ObjectId()
    with client.session_transaction() as sess:
        sess["user_id"] = str(dummy_user_id)

    mock_docs = [
        {"user_id": dummy_user_id, "category": "sunscreen", "read_complete": True},
        {"user_id": dummy_user_id, "category": "moisturizer", "read_complete": False}
    ]

    with patch("app.db") as mock_db:
        mock_db["tips_progress"].find.return_value = mock_docs

        response = client.get("/api/tips/progress")
        assert response.status_code == 200
        data = response.get_json()

        assert data["progress"]["sunscreen"] is True
        assert data["progress"]["moisturizer"] is False


def test_update_tips_progress_unauthenticated(client):
    """Should return 401 Unauthorized when session is missing user_id."""
    response = client.post("/api/tips/progress", json={"category": "sunscreen", "read_complete": True})
    assert response.status_code == 401


def test_update_tips_progress_success(client):
    """Should upsert category read status in MongoDB and return updated progress."""
    dummy_user_id = ObjectId()
    with client.session_transaction() as sess:
        sess["user_id"] = str(dummy_user_id)

    mock_docs_after = [
        {"user_id": dummy_user_id, "category": "sunscreen", "read_complete": True}
    ]

    with patch("app.db") as mock_db:
        mock_db["tips_progress"].find.return_value = mock_docs_after

        payload = {"category": "sunscreen", "read_complete": True}
        response = client.post("/api/tips/progress", json=payload)

        assert response.status_code == 200
        data = response.get_json()

        assert data["progress"]["sunscreen"] is True
        mock_db["tips_progress"].update_one.assert_called_once()
