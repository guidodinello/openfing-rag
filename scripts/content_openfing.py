import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- CONFIGURATION ---
BASE_URL = "https://open.fing.edu.uy/courses/"
HEADERS = {'User-Agent': 'Mozilla/5.0'}
JSON_FILE = r"..\backend\scraping\ScrapInfo\CoursesAcronyms.json"

def get_mp4_url(course_key, class_id):
    url = f"{BASE_URL}{course_key}/{class_id}/"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Intentar encontrar <source src="...mp4">
        source_tag = soup.find("source", src=True)
        if source_tag:
            return source_tag["src"]

        # Si no hay <source>, intentar encontrar <iframe src="...youtube">
        iframe = soup.find("iframe", src=lambda x: x and "youtube" in x)
        if iframe:
            youtube_url = iframe.get("src")
            print(f"YouTube URL found: {youtube_url}")
            return youtube_url  # Podés retornar esto o manejarlo distinto
        print(f"No video found for {url}")
        return None
    except Exception as e:
        print(f"Error accessing {url}: {e}")
        return None

def get_video_size(url):
    try:
        head = requests.head(url, headers=HEADERS, allow_redirects=True)
        size_bytes = int(head.headers.get("Content-Length", 0))
        return size_bytes
    except Exception as e:
        print(f"Failed to get size for {url}: {e}")
        return 0

def format_size(bytes):
    return f"{bytes / (1024**3):.2f} GB"

def main():
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_bytes = 0
    for course_key, value in data.items():
        classes = value.get("classes", [])
        for class_id in classes:
            mp4_url = get_mp4_url(course_key, class_id)
            if mp4_url:
                print(f"Processing: {mp4_url}")
                size = get_video_size(mp4_url)
                total_bytes += size
            else:
                print(f"No MP4 found for {course_key} - Class {class_id}")

    print("\n--- Summary ---")
    print(f"Total Size: {format_size(total_bytes)}")

if __name__ == "__main__":
    main()
