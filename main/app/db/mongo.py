from dotenv import load_dotenv
import os
from pymongo import MongoClient
from datetime import datetime, timezone

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

try:
    client = MongoClient(MONGODB_URI, tls=True)

    client.admin.command("ping")
    print("Connected to MongoDB!")

    db = client["music_db"]

    collection = db["tracks"]
    print("Collection 'tracks' ready.")

except Exception as e:
    print(f"Error connecting to MongoDB: {e}")


def insert_update_entry(entry):
    id_exists = bool(collection.find_one({"track_id": entry["track_id"]}))
    if id_exists:
        update_entry(entry["track_id"], entry)
        return
    timestamp = datetime.now(timezone.utc)
    entry["time_created"] = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    collection.insert_one(entry)


def update_entry(track_id, updates):
    entry = collection.find_one({"track_id": track_id})

    if "prompted_playlists" in updates:
        existing = set(entry.get("prompted_playlists", []))
        new = set(updates["prompted_playlists"])
        updates["prompted_playlists"] = list(existing.union(new))

    if "final_playlists" in updates:
        existing = set(entry.get("final_playlists", []))
        new = set(updates["final_playlists"])
        updates["final_playlists"] = list(existing.union(new))

    timestamp = datetime.now(timezone.utc)
    updates["time_updated"] = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    collection.update_one({"track_id": track_id}, {"$set": updates})


def get_entry_by_track_id(track_id):
    entry = collection.find_one({"track_id": track_id}, {"_id": 0})
    return entry


def get_all_entries(limit=10):
    entries = collection.find({}, {"_id": 0}).limit(limit)
    return entries


if __name__ == "__main__":
    # Example usage
    sample_entry = {
        "track_id": "12345",
        "name": "Track by Artist",
        "prompted_playlists": ["playlist1", "playlist2"],
        "final_playlists": ["final_playlist1"],
    }
    insert_update_entry(sample_entry)

    all_entries = get_all_entries()
    for entry in all_entries:
        print(entry)
