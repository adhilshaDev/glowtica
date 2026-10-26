from flask import Flask, request, jsonify, session
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId, Binary
from dotenv import load_dotenv
import os
import bcrypt
import certifi


load_dotenv()


app = Flask(__name__)


is_prod = os.getenv("FLASK_ENV") == "production"
frontend_url = os.getenv("FRONTEND_URL", "").strip().rstrip("/")
origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
if frontend_url and frontend_url not in origins:
    origins.append(frontend_url)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "glowtica-secret-key-fallback")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="None" if is_prod else "Lax",
    SESSION_COOKIE_SECURE=is_prod,
)
CORS(
    app,
    supports_credentials=True,
    origins=origins
)


mongo_uri = os.getenv("MONGO_URI")
try:
    if mongo_uri:
        client = MongoClient(mongo_uri, tlsCAFile=certifi.where(), connect=False)
    else:
        client = MongoClient("mongodb://localhost:27017/glowtica", connect=False)
except Exception:
    client = MongoClient("mongodb://localhost:27017/glowtica", connect=False)
db = client["glowtica"]



def normalize_password_hash(value):
    if value is None:
        return None
    if isinstance(value, Binary):
        return bytes(value)
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    if isinstance(value, str):
        return value.encode("utf-8")
    return value


@app.route("/")
def home():
    return "Glowtica backend is running!"


@app.route("/test-db")
def test_db():
    try:
        db.command("ping")
        return "MongoDB connected successfully!"
    except Exception as error:
        return f"Connection failed: {str(error)}", 500


@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json()

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"error": "Name, email, and password are required."}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must contain at least 6 characters."}), 400

    users = db["users"]

    if users.find_one({"email": email}):
        return jsonify({"error": "This email is already registered."}), 409

    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    )

    result = users.insert_one({
        "name": name,
        "email": email,
        "password_hash": password_hash
    })

    session["user_id"] = str(result.inserted_id)

    return jsonify({
        "message": "Signup successful.",
        "user": {
            "id": str(result.inserted_id),
            "name": name,
            "email": email
        }
    }), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    users = db["users"]
    user = users.find_one({"email": email})

    if not user:
        return jsonify({"error": "Invalid email or password."}), 401

    stored_hash = normalize_password_hash(user.get("password_hash"))

    if not bcrypt.checkpw(
        password.encode("utf-8"),
        stored_hash
    ):
        return jsonify({"error": "Invalid email or password."}), 401

    session["user_id"] = str(user["_id"])

    return jsonify({
        "message": "Login successful.",
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"]
        }
    }), 200


import base64


@app.route("/api/me", methods=["GET"])
def get_me():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    try:
        object_id = ObjectId(user_id)
    except Exception:
        session.pop("user_id", None)
        return jsonify({"error": "Invalid user session"}), 401

    user = db["users"].find_one({"_id": object_id})

    if not user:
        session.pop("user_id", None)
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": str(user["_id"]),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "avatar_base64": user.get("avatar_base64", None)
    }), 200



from datetime import datetime, timezone
from skin_analysis import (
    analyze_skin_image,
    generate_product_suitability,
    generate_skincare_routine,
)


@app.route("/api/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    return jsonify({"ok": True}), 200


@app.route("/api/dashboard/upload", methods=["POST"])
def upload_analysis():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    try:
        object_id = ObjectId(user_id)
    except Exception:
        session.pop("user_id", None)
        return jsonify({"error": "Invalid user session"}), 401

    user = db["users"].find_one({"_id": object_id})
    if not user:
        session.pop("user_id", None)
        return jsonify({"error": "User not found"}), 404

    if "file" not in request.files and "image" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    uploaded_file = request.files.get("file") or request.files.get("image")
    if not uploaded_file or uploaded_file.filename == "":
        return jsonify({"error": "Empty file uploaded"}), 400

    try:
        image_bytes = uploaded_file.read()
        mime_type = uploaded_file.mimetype or "image/jpeg"
        analysis_result = analyze_skin_image(image_bytes, mime_type)

        analysis_doc = {
            "user_id": object_id,
            "skin_type": analysis_result["skin_type"],
            "skin_type_confidence_percentage": analysis_result["skin_type_confidence_percentage"],
            "detected_problems": analysis_result["detected_problems"],
            "concern_notes": analysis_result["concern_notes"],
            "created_at": datetime.now(timezone.utc)
        }

        inserted = db["analyses"].insert_one(analysis_doc)

        db["users"].update_one(
            {"_id": object_id},
            {"$inc": {"analyses_done": 1}}
        )

        response_payload = {
            "id": str(inserted.inserted_id),
            "skin_type": analysis_result["skin_type"],
            "skin_type_confidence_percentage": analysis_result["skin_type_confidence_percentage"],
            "detected_problems": analysis_result["detected_problems"],
            "concern_notes": analysis_result["concern_notes"]
        }

        return jsonify(response_payload), 200
    except Exception as err:
        return jsonify({"error": f"Analysis failed: {str(err)}"}), 500


@app.route("/api/products/recommended", methods=["GET"])
def get_recommended_products():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    try:
        object_id = ObjectId(user_id)
    except Exception:
        session.pop("user_id", None)
        return jsonify({"error": "Invalid user session"}), 401

    # Fetch latest skin analysis for this user
    latest_analysis = db["analyses"].find_one(
        {"user_id": object_id},
        sort=[("created_at", -1)]
    )

    skin_type = "normal"
    analysis_payload = None

    if latest_analysis:
        skin_type = latest_analysis.get("skin_type", "normal")
        analysis_payload = {
            "id": str(latest_analysis["_id"]),
            "skin_type": latest_analysis.get("skin_type", "normal"),
            "skin_type_confidence_percentage": latest_analysis.get("skin_type_confidence_percentage", 80),
            "detected_problems": latest_analysis.get("detected_problems", []),
            "concern_notes": latest_analysis.get("concern_notes", "")
        }

    # Fetch recommended products matching skin_type
    recommended_docs = list(db["recommended_products"].find({"skin_type": skin_type}))

    products = []
    for doc in recommended_docs:
        products.append({
            "id": str(doc["_id"]),
            "name": doc.get("name", ""),
            "brand": doc.get("brand", ""),
            "category": doc.get("category", ""),
            "description": doc.get("description", ""),
            "skin_type": doc.get("skin_type", skin_type)
        })

    return jsonify({
        "skin_type": skin_type,
        "latest_analysis": analysis_payload,
        "recommended": products
    }), 200


@app.route("/api/products/mine", methods=["GET"])
def get_user_products():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    try:
        object_id = ObjectId(user_id)
    except Exception:
        session.pop("user_id", None)
        return jsonify({"error": "Invalid user session"}), 401

    user_product_docs = list(db["user_products"].find({"user_id": object_id}))

    products = []
    for doc in user_product_docs:
        products.append({
            "id": str(doc["_id"]),
            "name": doc.get("name", ""),
            "type": doc.get("type", "serum"),
            "ingredients": doc.get("ingredients", ""),
            "timing": doc.get("timing", "both"),
            "suitability_suggestion": doc.get("suitability_suggestion", "")
        })

    return jsonify(products), 200


@app.route("/api/products/mine", methods=["POST"])
def add_user_product():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    try:
        object_id = ObjectId(user_id)
    except Exception:
        session.pop("user_id", None)
        return jsonify({"error": "Invalid user session"}), 401

    data = request.get_json() or {}
    name = data.get("name", "").strip()
    product_type = data.get("type", "serum").strip().lower()
    ingredients = data.get("ingredients", "").strip()
    timing = data.get("timing", "both").strip().lower()

    if not name:
        return jsonify({"error": "Product name is required."}), 400

    # Get user's latest skin type
    latest_analysis = db["analyses"].find_one(
        {"user_id": object_id},
        sort=[("created_at", -1)]
    )
    skin_type = latest_analysis.get("skin_type", "normal") if latest_analysis else "normal"

    # Evaluate product suitability with Gemini API
    suitability = generate_product_suitability(name, ingredients, skin_type)

    product_doc = {
        "user_id": object_id,
        "name": name,
        "type": product_type,
        "ingredients": ingredients,
        "timing": timing,
        "suitability_suggestion": suitability,
        "created_at": datetime.now(timezone.utc)
    }

    inserted = db["user_products"].insert_one(product_doc)

    return jsonify({
        "id": str(inserted.inserted_id),
        "name": name,
        "type": product_type,
        "ingredients": ingredients,
        "timing": timing,
        "suitability_suggestion": suitability
    }), 201


@app.route("/api/products/mine/<product_id>", methods=["DELETE"])
def delete_user_product(product_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    try:
        object_id = ObjectId(user_id)
        prod_object_id = ObjectId(product_id)
    except Exception:
        return jsonify({"error": "Invalid IDs"}), 400

    result = db["user_products"].delete_one({
        "_id": prod_object_id,
        "user_id": object_id
    })

    if result.deleted_count == 0:
        return jsonify({"error": "Product not found or unauthorized."}), 404

    return jsonify({"ok": True}), 200


@app.route("/api/routine/<period>", methods=["GET"])
def get_routine(period):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    try:
        object_id = ObjectId(user_id)
    except Exception:
        session.pop("user_id", None)
        return jsonify({"error": "Invalid user session"}), 401

    period_upper = period.upper()
    if period_upper not in ["AM", "PM"]:
        return jsonify({"error": "Invalid period. Must be AM or PM."}), 400

    routine_doc = db["routines"].find_one({
        "user_id": object_id,
        "period": period_upper
    })

    if not routine_doc:
        return jsonify({"routine": None}), 200

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    last_applied = routine_doc.get("last_applied_date", "")

    steps = routine_doc.get("steps", [])
    if last_applied != today_str:
        for s in steps:
            s["applied_today"] = False

    return jsonify({
        "routine": {
            "id": str(routine_doc["_id"]),
            "period": period_upper,
            "steps": steps,
            "created_at": routine_doc.get("created_at")
        }
    }), 200


@app.route("/api/routine/generate", methods=["POST"])
def generate_routine():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    try:
        object_id = ObjectId(user_id)
    except Exception:
        session.pop("user_id", None)
        return jsonify({"error": "Invalid user session"}), 401

    data = request.get_json() or {}
    period_upper = (data.get("period") or "AM").upper()

    if period_upper not in ["AM", "PM"]:
        return jsonify({"error": "Invalid period. Must be AM or PM."}), 400

    latest_analysis = db["analyses"].find_one(
        {"user_id": object_id},
        sort=[("created_at", -1)]
    )
    skin_type = latest_analysis.get("skin_type", "normal") if latest_analysis else "normal"
    top_problems = latest_analysis.get("detected_problems", []) if latest_analysis else []

    user_prods = list(db["user_products"].find({"user_id": object_id}))
    filtered_user_prods = [
        p for p in user_prods
        if p.get("timing") == "both" or p.get("timing") == period_upper.lower()
    ]

    rec_prods = list(db["recommended_products"].find({"skin_type": skin_type}))

    generated_steps = generate_skincare_routine(
        period=period_upper,
        skin_type=skin_type,
        top_problems=top_problems,
        user_products=filtered_user_prods,
        recommended_products=rec_prods
    )

    steps = []
    for step in generated_steps:
        steps.append({
            "step_number": step.get("step_number", 1),
            "product_name": step.get("product_name", ""),
            "instruction": step.get("instruction", ""),
            "applied_today": False
        })

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    routine_doc = {
        "user_id": object_id,
        "period": period_upper,
        "steps": steps,
        "last_applied_date": today_str,
        "created_at": datetime.now(timezone.utc)
    }

    db["routines"].replace_one(
        {"user_id": object_id, "period": period_upper},
        routine_doc,
        upsert=True
    )

    saved_doc = db["routines"].find_one({"user_id": object_id, "period": period_upper})

    return jsonify({
        "routine": {
            "id": str(saved_doc["_id"]),
            "period": period_upper,
            "steps": steps,
            "created_at": saved_doc.get("created_at")
        }
    }), 200


@app.route("/api/routine/apply-step", methods=["POST"])
def apply_routine_step():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    try:
        object_id = ObjectId(user_id)
    except Exception:
        session.pop("user_id", None)
        return jsonify({"error": "Invalid user session"}), 401

    data = request.get_json() or {}
    period_upper = (data.get("period") or "AM").upper()
    step_number = data.get("step_number")
    applied = bool(data.get("applied", False))

    if period_upper not in ["AM", "PM"] or step_number is None:
        return jsonify({"error": "Period and step_number are required."}), 400

    routine_doc = db["routines"].find_one({
        "user_id": object_id,
        "period": period_upper
    })

    if not routine_doc:
        return jsonify({"error": "Routine not found."}), 404

    steps = routine_doc.get("steps", [])
    for step in steps:
        if step.get("step_number") == step_number:
            step["applied_today"] = applied
            break

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    db["routines"].update_one(
        {"_id": routine_doc["_id"]},
        {"$set": {"steps": steps, "last_applied_date": today_str}}
    )

    return jsonify({
        "routine": {
            "id": str(routine_doc["_id"]),
            "period": period_upper,
            "steps": steps,
            "created_at": routine_doc.get("created_at")
        }
    }), 200


@app.route("/api/tips/progress", methods=["GET"])
def get_tips_progress():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    try:
        object_id = ObjectId(user_id)
    except Exception:
        session.pop("user_id", None)
        return jsonify({"error": "Invalid user session"}), 401

    progress_docs = list(db["tips_progress"].find({"user_id": object_id}))

    progress_map = {}
    for doc in progress_docs:
        category = doc.get("category")
        if category:
            progress_map[category] = bool(doc.get("read_complete", False))

    return jsonify({"progress": progress_map}), 200


@app.route("/api/tips/progress", methods=["POST"])
def update_tips_progress():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    try:
        object_id = ObjectId(user_id)
    except Exception:
        session.pop("user_id", None)
        return jsonify({"error": "Invalid user session"}), 401

    data = request.get_json() or {}
    category = data.get("category", "").strip().lower()
    read_complete = bool(data.get("read_complete", False))

    if not category:
        return jsonify({"error": "Category is required."}), 400

    db["tips_progress"].update_one(
        {"user_id": object_id, "category": category},
        {"$set": {"read_complete": read_complete, "updated_at": datetime.now(timezone.utc)}},
        upsert=True
    )

    progress_docs = list(db["tips_progress"].find({"user_id": object_id}))
    progress_map = {}
    for doc in progress_docs:
        cat = doc.get("category")
        if cat:
            progress_map[cat] = bool(doc.get("read_complete", False))

    return jsonify({"progress": progress_map}), 200


@app.route("/api/account/photo", methods=["POST"])
def update_profile_photo():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    try:
        object_id = ObjectId(user_id)
    except Exception:
        session.pop("user_id", None)
        return jsonify({"error": "Invalid user session"}), 401

    user = db["users"].find_one({"_id": object_id})
    if not user:
        session.pop("user_id", None)
        return jsonify({"error": "User not found"}), 404

    avatar_data_url = None

    if "file" in request.files or "image" in request.files:
        uploaded_file = request.files.get("file") or request.files.get("image")
        if uploaded_file and uploaded_file.filename != "":
            raw_bytes = uploaded_file.read()
            mime_type = uploaded_file.mimetype or "image/jpeg"
            b64_str = base64.b64encode(raw_bytes).decode("utf-8")
            avatar_data_url = f"data:{mime_type};base64,{b64_str}"
    else:
        json_data = request.get_json(silent=True) or {}
        avatar_data_url = json_data.get("avatar_base64")

    if not avatar_data_url:
        return jsonify({"error": "No image file or base64 data provided."}), 400

    db["users"].update_one(
        {"_id": object_id},
        {"$set": {"avatar_base64": avatar_data_url}}
    )

    return jsonify({"avatar_base64": avatar_data_url}), 200


@app.route("/api/account/username", methods=["PUT"])
def update_username():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    try:
        object_id = ObjectId(user_id)
    except Exception:
        session.pop("user_id", None)
        return jsonify({"error": "Invalid user session"}), 401

    data = request.get_json() or {}
    new_name = data.get("name", "").strip()

    if not new_name:
        return jsonify({"error": "Username cannot be empty."}), 400

    db["users"].update_one(
        {"_id": object_id},
        {"$set": {"name": new_name}}
    )

    updated_user = db["users"].find_one({"_id": object_id})

    return jsonify({
        "id": str(updated_user["_id"]),
        "name": updated_user.get("name", ""),
        "email": updated_user.get("email", ""),
        "avatar_base64": updated_user.get("avatar_base64", None)
    }), 200


@app.route("/api/account/password", methods=["PUT"])
def update_password():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    try:
        object_id = ObjectId(user_id)
    except Exception:
        session.pop("user_id", None)
        return jsonify({"error": "Invalid user session"}), 401

    user = db["users"].find_one({"_id": object_id})
    if not user:
        session.pop("user_id", None)
        return jsonify({"error": "User not found"}), 404

    data = request.get_json() or {}
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    if not current_password or not new_password:
        return jsonify({"error": "Current password and new password are required."}), 400

    if len(new_password) < 6:
        return jsonify({"error": "New password must contain at least 6 characters."}), 400

    stored_hash = normalize_password_hash(user.get("password_hash"))

    if not stored_hash or not bcrypt.checkpw(current_password.encode("utf-8"), stored_hash):
        return jsonify({"error": "Incorrect current password."}), 401

    new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())

    db["users"].update_one(
        {"_id": object_id},
        {"$set": {"password_hash": new_hash}}
    )

    return jsonify({"message": "Password updated successfully."}), 200


@app.route("/api/account/logout", methods=["POST"])
def account_logout():
    session.pop("user_id", None)
    return jsonify({"ok": True}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=not is_prod)



