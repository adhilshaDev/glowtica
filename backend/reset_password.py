from pymongo import MongoClient
from dotenv import load_dotenv
import bcrypt
import certifi
import os

load_dotenv()

client = MongoClient(
    os.getenv("MONGO_URI"),
    tlsCAFile=certifi.where()
)
db = client["glowtica"]

email = "ebru@gmail.com"
new_password = "adhi@123"

new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())

result = db["users"].update_one(
    {"email": email},
    {"$set": {"password_hash": new_hash}}
)

if result.matched_count:
    print("Password updated successfully.")
else:
    print("No user found with that email.")