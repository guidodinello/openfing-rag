from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import BadRequestError
from pymongo import MongoClient
from typing import List

# === Elasticsearch & MongoDB Config ===
ES_INDEX_NAME = "transcription_chunks"
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "transcriptions_db"
COLLECTION_NAME = "classes"

# === Initialize Clients ===


es = Elasticsearch(["http://localhost:9200"])  # Use http://
# ... your code ...
es.index(index="my_index", document={"your": "data"})
mongo_client = MongoClient(MONGO_URI)
mongo_collection = mongo_client[DB_NAME][COLLECTION_NAME]

# === Optional: Define Index Mapping ===

ES_INDEX_NAME = "transcription_chunks"


try:
    es.index(index="my_index", document={"your": "data"})
    print(es.ping())  # Check if the Elasticsearch server is running
except BadRequestError as e:
    print("Status code:", e.status_code)
    print("Error message:", e.error)
    print("Body:", e.info)  # Often shows the cause

def create_index_if_not_exists():
    if not es.indices.exists(index=ES_INDEX_NAME):
        es.indices.create(
            index=ES_INDEX_NAME,
            body=
            {
                "mappings": {
                    "properties": {
                        "chunk": {"type": "text"},
                        "embedding": {
                        "type": "dense_vector",
                        "dims": 768,
                        "index": True,
                        "similarity": "cosine"
                    }

                    }
                }
            }
        )



# === Function to Index Chunks ===
def index_chunks_to_elasticsearch():
    create_index_if_not_exists()

    actions = []

    for doc in mongo_collection.find():
        chunks: List[str] = doc.get("chunks", [])
        if not chunks:
            continue

        class_key = doc.get("key", str(doc["_id"]))
        course = doc.get("title", "unknown")
        class_number = doc.get("class", -1)
        model = doc.get("model", "unknown")
        language = doc.get("language", "unknown")

        for i, chunk in enumerate(chunks):
            actions.append({
                "_index": ES_INDEX_NAME,
                "_source": {
                    "chunk": chunk,
                    "chunk_index": i,
                    "class_key": class_key,
                    "course": course,
                    "class": class_number,
                    "model": model,
                    "language": language
                }
            })

    if actions:
        helpers.bulk(es, actions)
        print(f"✅ Indexed {len(actions)} chunks into '{ES_INDEX_NAME}'")
    else:
        print("⚠️ No chunks found to index.")

# === Run the Function ===
if __name__ == "__main__":
    index_chunks_to_elasticsearch()
