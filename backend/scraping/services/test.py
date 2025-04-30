import os
import json
import subprocess
from pathlib import Path

TMP_DOWNLOAD_FOLDER = "../../tmp"
acronyms_path = "../ScrapInfo/CoursesAcronyms.json"
scrapinfo_dir = "../ScrapInfo"
openfing_url = "https://open.fing.edu.uy/media"

def download_video(acronym, class_number):
    padded_class = f"{int(class_number):02d}"
    output_dir = os.path.join(TMP_DOWNLOAD_FOLDER, acronym)
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{acronym}_{padded_class}.mp4")
    url = f"{openfing_url}/{acronym}/{acronym}_{padded_class}.mp4"
    print(f"Downloading {url} to {output_file}")
    result = subprocess.run(
        ["curl", "--silent", "--show-error", "--location", url, "--output", output_file]
    )
    if result.returncode == 0:
        print(f"Saved to {output_file}")
    else:
        print(f"Failed to download {url}")
    return output_file

def transcribe_video(acronym, class_number):
    padded_class = f"{int(class_number):02d}"
    video_path = os.path.join(TMP_DOWNLOAD_FOLDER, acronym, f"{acronym}_{padded_class}.mp4")
    output_path = os.path.join(TMP_DOWNLOAD_FOLDER, acronym, f"{acronym}_{padded_class}_small.mp4")
    if not os.path.isfile(video_path):
        print(f"Video file not found: {video_path}")
        return
    print(f"Running Whisper transcription for {video_path}...")
    result = subprocess.run([
        "whisper", video_path, "--language", "Spanish", "--model", "medium", "--output_dir", os.path.dirname(output_path)
    ])
    if result.returncode != 0:
        print(f"Whisper transcription failed for {video_path}")

def delete_video(acronym, class_number):
    padded_class = f"{int(class_number):02d}"
    video_path = os.path.join(TMP_DOWNLOAD_FOLDER, acronym, f"{acronym}_{padded_class}.mp4")
    if os.path.isfile(video_path):
        os.remove(video_path)
        print(f"Deleted {video_path}")
    else:
        print(f"File not found for deletion: {video_path}")
# Read acronyms and reverse order
with open(acronyms_path, "r") as f:
    acronyms_dict = json.load(f)
acronyms = list(acronyms_dict.keys())[::-1]

for acronym_key in acronyms:
    class_numbers_path = os.path.join(scrapinfo_dir, f"{acronym_key}.json")
    if not os.path.isfile(class_numbers_path):
        print(f"File not found: {class_numbers_path}")
        continue
    with open(class_numbers_path, "r") as f:
        class_numbers = json.load(f)
    # If the file is a dict, get the array (adapt as needed)
    if isinstance(class_numbers, dict):
        # Try to get the first array value
        for v in class_numbers.values():
            if isinstance(v, list):
                class_numbers = v
                break
    for class_number in class_numbers:
        print(f"Downloading {acronym_key} class {class_number}")
        download_video(acronym_key, class_number)
        print(f"Transcribing {acronym_key} class {class_number}")
        transcribe_video(acronym_key, class_number)
        print(f"Done with {acronym_key} class {class_number}")
        delete_video(acronym_key, class_number)

print("All downloads, transcriptions, and deletions completed.")