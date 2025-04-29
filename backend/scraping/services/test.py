import os
import json
import subprocess

# Paths
acronyms_path = "/home/diego/_Modulos/Facu/tesis/backend/scraping/ScrapInfo/CoursesAcronyms.json"
scrapinfo_dir = "/home/diego/_Modulos/Facu/tesis/backend/scraping/ScrapInfo"

# Pendrive mount points
pendrive = "/media/diego/16_GB_NEGRO",
# Read acronyms
with open(acronyms_path, "r") as f:
    acronyms = json.load(f)

for acronym_key in acronyms.keys().reverse():
    class_numbers_path = os.path.join(scrapinfo_dir, f"{acronym_key}.json")
    if not os.path.exists(class_numbers_path):
        print(f"File not found: {class_numbers_path}")
        continue
    with open(class_numbers_path, "r") as f:
        class_numbers = json.load(f)
    if isinstance(class_numbers, dict):
        class_numbers = class_numbers.get("class_numbers", [])
    for class_number in class_numbers:
        print(f"Downloading {acronym_key} class {class_number} to")
        # Download video
        subprocess.run([
            "curl", "--location", "localhost:8000/download-videos/",
            "--header", "Content-Type: application/json",
            "--header", "Accept: application/json",
            "--data", json.dumps({
                "course_acronym": acronym_key,
                "class_number": class_number
            })
        ])
        # Transcribe video
        print(f"Transcribing {acronym_key} class {class_number}")
        subprocess.run([
            "curl", "--location", "--request", "PUT",
            f"localhost:8001/transcribe/{acronym_key}/{class_number}",
            "--header", "Accept: application/json",
            "--data", json.dumps({
                "model_size": "medium",
                "language": "es"
            })
        ])
        # Delete video after transcription
        #video_filename = f"{acronym_key}_{class_number}.mp4"
        #video_path = os.path.join(pendrive, video_filename)
        #if os.path.exists(video_path):
        #    try:
        #        os.remove(video_path)
        #        print(f"Deleted {video_path}")
        #    except Exception as e:
        #        print(f"Failed to delete {video_path}: {e}")

print("All downloads, transcriptions, and deletions completed.")