import os
import json
import re
from pymongo import MongoClient
from typing import List, Dict, Any
import datetime
SCRAP_INFO_FILE="../../../backend/scraping/ScrapInfo/CoursesAcronyms.json"

def parse_filename(filename: str):
    match = re.match(r"(.+?)_(\d+)(?:_(.+))?\.json$", filename)
    if match:
        course_acronym = match.group(1)
        class_number = int(match.group(2))
        model_used = match.group(3) if match.group(3) else None
        return course_acronym, class_number, model_used
    return None, None, None


def parse_structure1(data: Dict[str, Any]) -> Dict:
    return {
        "text": data.get("text"),
        "language": data.get("language"),
        "segments": [
            {
                "id": s.get("id"),
                "start": s.get("start"),
                "end": s.get("end"),
                "text": s.get("text")
            }
            for s in data.get("segments", [])
        ]
    }


def parse_structure2(data: Dict[str, Any]) -> Dict:
    transcription = data.get("transcription", [])
    language = data.get("result", {}).get("language")
    model = data.get("params", {}).get("model")

    segments = []
    for i, segment in enumerate(transcription):
        try:
            start = segment["offsets"]["from"] / 1000.0
            end = segment["offsets"]["to"] / 1000.0
        except:
            start = end = None  # fallback if offsets are missing
        segments.append({
            "id": i,
            "start": start,
            "end": end,
            "text": segment.get("text")
        })

    return {
        "text": " ".join(s["text"] for s in segments if s.get("text")),
        "language": language,
        "model": model,
        "segments": segments
    }


def parse_structure3(data: List[Dict[str, Any]]) -> Dict:
    segments = []
    for i, seg in enumerate(data):
        segments.append({
            "id": i,
            "start": seg.get("start"),
            "end": seg.get("end"),
            "text": seg.get("text")
        })
    return {
        "text": " ".join(s["text"] for s in segments if s.get("text")),
        "language": None,
        "model": None,
        "segments": segments
    }


def load_transcription(filepath: str) -> Dict:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict) and "segments" in data:
        return parse_structure1(data)
    elif isinstance(data, dict) and "transcription" in data:
        return parse_structure2(data)
    elif isinstance(data, list) and all("start" in item and "end" in item and "text" in item for item in data):
        return parse_structure3(data)
    else:
        raise ValueError(f"Unrecognized structure in file: {filepath}")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = end - overlap
    return chunks


def insert_transcriptions(directory: str, db_name: str = "transcriptions_db", collection_name: str = "classes"):
    client = MongoClient("mongodb://localhost:27017/")
    db = client[db_name]
    collection = db[collection_name]
    with open(SCRAP_INFO_FILE, "r", encoding="utf-8") as f:
        courses_acronyms = json.load(f)

    for root, _, files in os.walk(directory):
        for file in files:
            if not file.endswith(".json"):
                continue
            filepath = os.path.join(root, file)
            try:
                course_acronym, class_number, model_used = parse_filename(file)
                if course_acronym is None or class_number is None:
                    print(f"⚠️ Skipping unrecognized filename: {file}")
                    continue
                key = f"{course_acronym}_{class_number}_{model_used}"
                if collection.find_one({"key": key}):
                    print(f"⏩ Skipping already processed {file} (key={key})")
                    continue

                parsed = load_transcription(filepath)
                chunks500 = chunk_text(parsed["text"])
                chunks400 = chunk_text(parsed["text"],400)
                chunks300 = chunk_text(parsed["text"],300)
                title = None
                subtitle = None

                if(course_acronym in courses_acronyms):
                    title= courses_acronyms[course_acronym]["title"]
                    subtitle = courses_acronyms[course_acronym]["subtitle"]
                    related_courses = courses_acronyms[course_acronym]["related_course"]
                
                now = datetime.datetime.now()
                doc = {
                    "key": f"{course_acronym}_{class_number}_{model_used}",
                    "course_acronym": course_acronym,
                    "related_courses": related_courses,
                    "created_at":now,
                    "title": title,
                    "subtitle": subtitle,
                    "class": class_number,
                    "text": parsed["text"].strip(),
                    "segments": parsed["segments"],
                    "model": model_used,
                    "language": parsed.get("language"),
                    "chunks500": chunks500,
                    "chunks400": chunks400,
                    "chunks300": chunks300
                }

                collection.replace_one({"key": doc["key"]}, doc, upsert=True)
                print(f"✅ Inserted {file} as key={doc['key']}")

            except Exception as e:
                print(f"❌ Error processing {file}: {e}")


if __name__ == "__main__":
    # Example directory structure: DB/transcriptions/
    insert_transcriptions("../../../scripts/videos/")