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


def test_get_recommended_unauthenticated(client):
    """Should return 401 Unauthorized when session is missing user_id."""
    response = client.get("/api/products/recommended")
    assert response.status_code == 401
    assert response.get_json()["error"] == "Not logged in"


def test_get_recommended_success(client):
    """Should return recommended products matching user's skin_type."""
    dummy_user_id = ObjectId()
    with client.session_transaction() as sess:
        sess["user_id"] = str(dummy_user_id)

    mock_analysis = {
        "_id": ObjectId(),
        "user_id": dummy_user_id,
        "skin_type": "oily",
        "skin_type_confidence_percentage": 85,
        "detected_problems": [{"name": "oily", "percentage": 70}],
        "concern_notes": "Excess oiliness detected."
    }

    mock_recommended_docs = [
        {
            "_id": ObjectId(),
            "name": "Clarifying Gel Cleanser",
            "brand": "DermaClear",
            "category": "Cleanser",
            "description": "BHA cleanser for oily skin.",
            "skin_type": "oily"
        }
    ]

    with patch("app.db") as mock_db:
        mock_db["analyses"].find_one.return_value = mock_analysis
        mock_db["recommended_products"].find.return_value = mock_recommended_docs

        response = client.get("/api/products/recommended")
        assert response.status_code == 200
        data = response.get_json()

        assert data["skin_type"] == "oily"
        assert len(data["recommended"]) == 1
        assert data["recommended"][0]["name"] == "Clarifying Gel Cleanser"


def test_get_user_products_unauthenticated(client):
    """Should return 401 Unauthorized when session is missing user_id."""
    response = client.get("/api/products/mine")
    assert response.status_code == 401


def test_get_user_products_success(client):
    """Should return list of custom products owned by logged-in user."""
    dummy_user_id = ObjectId()
    with client.session_transaction() as sess:
        sess["user_id"] = str(dummy_user_id)

    mock_user_products = [
        {
            "_id": ObjectId(),
            "user_id": dummy_user_id,
            "name": "Niacinamide 10%",
            "type": "serum",
            "ingredients": "Niacinamide, Zinc PCA",
            "timing": "morning",
            "suitability_suggestion": "Ideal for oil control."
        }
    ]

    with patch("app.db") as mock_db:
        mock_db["user_products"].find.return_value = mock_user_products

        response = client.get("/api/products/mine")
        assert response.status_code == 200
        data = response.get_json()

        assert len(data) == 1
        assert data[0]["name"] == "Niacinamide 10%"
        assert data[0]["timing"] == "morning"


def test_add_user_product_success(client):
    """Should evaluate suitability with Gemini and store product in MongoDB."""
    dummy_user_id = ObjectId()
    mock_inserted_id = ObjectId()

    with client.session_transaction() as sess:
        sess["user_id"] = str(dummy_user_id)

    payload = {
        "name": "Hyaluronic Acid Serum",
        "type": "serum",
        "ingredients": "Sodium Hyaluronate, B5",
        "timing": "both"
    }

    with patch("app.db") as mock_db, \
         patch("app.generate_product_suitability", return_value="Great hydrating serum for normal skin."):

        mock_db["analyses"].find_one.return_value = {"skin_type": "normal"}
        mock_db["user_products"].insert_one.return_value = MagicMock(inserted_id=mock_inserted_id)

        response = client.post("/api/products/mine", json=payload)
        assert response.status_code == 201
        data = response.get_json()

        assert data["id"] == str(mock_inserted_id)
        assert data["name"] == "Hyaluronic Acid Serum"
        assert data["suitability_suggestion"] == "Great hydrating serum for normal skin."
        mock_db["user_products"].insert_one.assert_called_once()


def test_delete_user_product_success(client):
    """Should delete user product document from MongoDB."""
    dummy_user_id = ObjectId()
    dummy_product_id = ObjectId()

    with client.session_transaction() as sess:
        sess["user_id"] = str(dummy_user_id)

    with patch("app.db") as mock_db:
        mock_db["user_products"].delete_one.return_value = MagicMock(deleted_count=1)

        response = client.delete(f"/api/products/mine/{dummy_product_id}")
        assert response.status_code == 200
        assert response.get_json() == {"ok": True}
        mock_db["user_products"].delete_one.assert_called_once_with({
            "_id": dummy_product_id,
            "user_id": dummy_user_id
        })
