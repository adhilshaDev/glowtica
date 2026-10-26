import io
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


def test_upload_unauthenticated(client):
    """Should return 401 Unauthorized when session is missing user_id."""
    response = client.post("/api/dashboard/upload")
    assert response.status_code == 401
    data = response.get_json()
    assert data["error"] == "Not logged in"


def test_upload_missing_file(client):
    """Should return 400 Bad Request when authenticated but no file provided."""
    with client.session_transaction() as sess:
        sess["user_id"] = str(ObjectId())

    with patch("app.db") as mock_db:
        mock_db["users"].find_one.return_value = {"_id": ObjectId()}
        response = client.post("/api/dashboard/upload")
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "No file provided"


def test_upload_success(client):
    """Should process uploaded photo, call skin analysis, update MongoDB, and return JSON."""
    dummy_user_id = ObjectId()
    mock_inserted_id = ObjectId()

    with client.session_transaction() as sess:
        sess["user_id"] = str(dummy_user_id)

    mock_analysis = {
        "skin_type": "combination",
        "skin_type_confidence_percentage": 85,
        "detected_problems": [
            {"name": "oily", "percentage": 65},
            {"name": "visible_pores", "percentage": 40},
            {"name": "redness", "percentage": 30},
            {"name": "dullness", "percentage": 20},
        ],
        "concern_notes": "Mild T-zone oiliness detected with slight redness."
    }

    data = {
        "file": (io.BytesIO(b"fake_image_bytes"), "test.jpg")
    }

    with patch("app.db") as mock_db, \
         patch("app.analyze_skin_image", return_value=mock_analysis):
        
        mock_db["users"].find_one.return_value = {"_id": dummy_user_id, "name": "Test User"}
        mock_db["analyses"].insert_one.return_value = MagicMock(inserted_id=mock_inserted_id)

        response = client.post(
            "/api/dashboard/upload",
            data=data,
            content_type="multipart/form-data"
        )

        assert response.status_code == 200
        json_data = response.get_json()

        assert json_data["id"] == str(mock_inserted_id)
        assert json_data["skin_type"] == "combination"
        assert json_data["skin_type_confidence_percentage"] == 85
        assert len(json_data["detected_problems"]) == 4
        assert json_data["concern_notes"] == "Mild T-zone oiliness detected with slight redness."

        # Verify MongoDB calls
        mock_db["analyses"].insert_one.assert_called_once()
        mock_db["users"].update_one.assert_called_once_with(
            {"_id": dummy_user_id},
            {"$inc": {"analyses_done": 1}}
        )
