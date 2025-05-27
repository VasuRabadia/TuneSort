from pymongo import MongoClient
from pymongo.server_api import ServerApi
from urllib.parse import quote_plus
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

# Replace with your MongoDB Atlas connection string
MONGO_USER_PASSWORD = os.getenv("MONGO_USER_PASSWORD")
password = quote_plus(MONGO_USER_PASSWORD)
uri = f"mongodb+srv://rabadiavasu:{password}@spotifyautomation.25a7oxn.mongodb.net/?retryWrites=true&w=majority&appName=SpotifyAutomation"
client = MongoClient(uri, server_api=ServerApi("1"))
try:
    client.admin.command("ping")
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client["music_classifier"]
collection = db["track_classifications"]


def insert_classification_result(result):
    try:
        result["timestamp"] = datetime.utcnow().isoformat()
        collection.insert_one(result)
        print("Document inserted.")
    except Exception as e:
        print("Failed to insert:", e)


def update_classification_result(result):
    try:
        result["timestamp"] = datetime.utcnow().isoformat()
        collection.update_one(
            {"track_id": result["track_id"]},
            {"$set": result},
        )
        print("Document updated.")
    except Exception as e:
        print("Failed to update:", e)


def find_existing_track(track_id):
    return collection.find_one({"track_id": track_id})


def get_all_classifications(limit=10):
    """
    Returns up to `limit` documents from the collection for debugging purposes.
    Excludes the `_id` field from the returned documents.
    """
    documents = collection.find({}, {"_id": 0}).limit(
        limit
    )  # Exclude _id via projection
    return list(documents)


if __name__ == "__main__":
    # insert_classification_result(
    #     {
    #         "track_id": "123456789",
    #         "track": "Shape of You",
    #         "prompt_playlists": ["English-Dance", "Pop", "Workout"],
    #         "model_outputs": {
    #             "gemini-1.5-flash": {"Pop": 0.8, "English-Dance": 0.7},
    #             "gemini-2.0-flash-lite": {"Pop": 0.85, "English-Dance": 0.6},
    #             "gemini-2.0-flash": {"Pop": 0.82, "English-Dance": 0.9},
    #         },
    #         "ensemble_scores": {"Pop": 0.81, "English-Dance": 0.75},
    #         "final_ensemble_playlists": ["Pop", "English-Dance"],
    #     }
    # )
    print(get_all_classifications())
