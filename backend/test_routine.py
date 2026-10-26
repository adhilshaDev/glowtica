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


def test_get_routine_unauthenticated(client):
    """Should return 401 Unauthorized when session is missing user_id."""
    response = client.get("/api/routine/AM")
    assert response.status_code == 401
    assert response.get_json()["error"] == "Not logged in"


def test_get_routine_invalid_period(client):
    """Should return 400 Bad Request for invalid period."""
    with client.session_transaction() as sess:
        sess["user_id"] = str(ObjectId())

    response = client.get("/api/routine/NOON")
    assert response.status_code == 400
    assert "Invalid period" in response.get_json()["error"]


def test_get_routine_success(client):
    """Should return user's saved routine for the specified period."""
    dummy_user_id = ObjectId()
    with client.session_transaction() as sess:
        sess["user_id"] = str(dummy_user_id)

    mock_routine_doc = {
        "_id": ObjectId(),
        "user_id": dummy_user_id,
        "period": "AM",
        "steps": [
            {
                "step_number": 1,
                "product_name": "Gentle Cleanser",
                "instruction": "Cleanse thoroughly.",
                "applied_today": True
            }
        ],
        "last_applied_date": "2026-09-27"
    }

    with patch("app.db") as mock_db:
        mock_db["routines"].find_one.return_value = mock_routine_doc

        response = client.get("/api/routine/AM")
        assert response.status_code == 200
        data = response.get_json()

        assert data["routine"] is not None
        assert data["routine"]["period"] == "AM"
        assert len(data["routine"]["steps"]) == 1
        assert data["routine"]["steps"][0]["product_name"] == "Gentle Cleanser"


def test_generate_routine_success(client):
    """Should pull context, invoke generate_skincare_routine, upsert to MongoDB, and return steps."""
    dummy_user_id = ObjectId()
    mock_routine_id = ObjectId()

    with client.session_transaction() as sess:
        sess["user_id"] = str(dummy_user_id)

    mock_generated_steps = [
        {"step_number": 1, "product_name": "Salicylic Cleanser", "instruction": "Lather gently."},
        {"step_number": 2, "product_name": "SPF 50 Sunscreen", "instruction": "Apply as final step."}
    ]

    with patch("app.db") as mock_db, \
         patch("app.generate_skincare_routine", return_value=mock_generated_steps):

        mock_db["analyses"].find_one.return_value = {"skin_type": "oily", "detected_problems": []}
        mock_db["user_products"].find.return_value = []
        mock_db["recommended_products"].find.return_value = []
        mock_db["routines"].find_one.return_value = {
            "_id": mock_routine_id,
            "user_id": dummy_user_id,
            "period": "AM",
            "steps": mock_generated_steps
        }

        response = client.post("/api/routine/generate", json={"period": "AM"})
        assert response.status_code == 200
        data = response.get_json()

        assert data["routine"]["period"] == "AM"
        assert len(data["routine"]["steps"]) == 2
        mock_db["routines"].replace_one.assert_called_once()


def test_apply_routine_step_success(client):
    """Should update applied_today flag for specified step number."""
    dummy_user_id = ObjectId()
    mock_routine_id = ObjectId()

    with client.session_transaction() as sess:
        sess["user_id"] = str(dummy_user_id)

    mock_routine_doc = {
        "_id": mock_routine_id,
        "user_id": dummy_user_id,
        "period": "PM",
        "steps": [
            {"step_number": 1, "product_name": "Foam Cleanser", "instruction": "Wash face.", "applied_today": False}
        ]
    }

    with patch("app.db") as mock_db:
        mock_db["routines"].find_one.return_value = mock_routine_doc

        payload = {"period": "PM", "step_number": 1, "applied": True}
        response = client.post("/api/routine/apply-step", json=payload)

        assert response.status_code == 200
        mock_db["routines"].update_one.assert_called_once()
