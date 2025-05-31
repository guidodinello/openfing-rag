import os
import json
import re
from pymongo import MongoClient
from typing import List, Dict, Any


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


def insert_transcriptions(directory: str, db_name: str = "transcriptions_db", collection_name: str = "classes"):
    client = MongoClient("mongodb://localhost:27017/")
    db = client[db_name]
    collection = db[collection_name]

    for root, _, files in os.walk(directory):
        for file in files:
            if not file.endswith(".json"):
                continue

