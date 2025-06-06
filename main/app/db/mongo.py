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
    id_exists = bool(collection.find_one({"tr_id": entry["tr_id"]}))
    if id_exists:
        update_entry(entry["tr_id"], entry)
        return
    timestamp = datetime.now(timezone.utc)
    entry["tc"] = timestamp.strftime("%Y-%m-%d")
    collection.insert_one(entry)


def update_entry(tr_id, updates):
    entry = collection.find_one({"tr_id": tr_id})

    if "p" in updates:
        existing = set(entry.get("p", []))
        new = set(updates["p"])
        updates["p"] = list(existing.union(new))

    if "f" in updates:
        existing = set(entry.get("f", []))
        new = set(updates["f"])
        updates["f"] = list(existing.union(new))

    timestamp = datetime.now(timezone.utc)
    updates["tu"] = timestamp.strftime("%Y-%m-%d")
    collection.update_one({"tr_id": tr_id}, {"$set": updates})


def get_entry_by_track_id(tr_id):
    entry = collection.find_one({"tr_id": tr_id}, {"_id": 0})
    return entry


def get_all_entries(limit=10):
    entries = collection.find({}, {"_id": 0}).limit(limit)
    return entries


if __name__ == "__main__":
    # Example usage
    sample_entry = {
        "tr_id": "12345",
        "p": ["playlist1", "playlist2"],
        "f": ["final_playlist1"],
    }
    insert_update_entry(sample_entry)

    all_entries = get_all_entries()
    for entry in all_entries:
        print(entry)
