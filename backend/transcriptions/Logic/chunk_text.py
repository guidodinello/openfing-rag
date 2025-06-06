from pymongo import MongoClient
from typing import List
import math

# === CONFIGURATION ===
DB_NAME = "transcriptions_db"
COLLECTION_NAME = "classes"
CHUNK_SIZE = 500
OVERLAP = 50  # Adjust overlap as needed


# === Function to Chunk Text ===
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 0) -> List[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


# === Connect to MongoDB ===
def testConnection():
    try:
        client = MongoClient("mongodb://localhost:27017/")
        client.admin.command('ping')
        print("MongoDB connection successful.")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
def testDatabase():
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client[DB_NAME]
        if DB_NAME in client.list_database_names():
            print(f"Database '{DB_NAME}' exists.")
        else:
            print(f"Database '{DB_NAME}' does not exist.")
    except Exception as e:
        print(f"Error checking database: {e}")
def testCollection():
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client[DB_NAME]
        if COLLECTION_NAME in db.list_collection_names():
            print(f"Collection '{COLLECTION_NAME}' exists.")
        else:
            print(f"Collection '{COLLECTION_NAME}' does not exist.")
    except Exception as e:
        print(f"Error checking collection: {e}")

def testSetUp():
    testConnection()
    testDatabase()
    testCollection()
        
# === Process Each Document ===
def main():
    testSetUp()
    client = MongoClient("mongodb://localhost:27017/")
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    print(f"Processing documents in collection '{COLLECTION_NAME}'...")

    # Iterate through each document in the collection
    for doc in collection.find():
        print("doc:")
        if "text" not in doc:
            print(f"Skipping doc with _id={doc['_id']} (no text field)")
            continue

        text = doc["text"]
        chunks = chunk_text(text, chunk_size=CHUNK_SIZE, overlap=OVERLAP)

        # Update the document with the chunks
        collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {"chunks": chunks}}
        )
        print(f"Updated _id={doc['_id']} with {len(chunks)} chunks")

    print("✅ Done.")
if __name__ == "__main__":
    main()
