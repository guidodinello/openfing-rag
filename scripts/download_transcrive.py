import json
import os
import subprocess

COURSES_JSON = "courses.json"
BASE_URL = "https://open.fing.edu.uy/media"
OUTPUT_BASE_DIR = "videos"
WHISPER_MODEL = "models/ggml-small.en.bin"
WHISPER_EXEC = "./main"
THREADS = 4

def download_video(course, cls, dest_path):
    if cls<10:
        cls = f"0{cls}"
    url = f"{BASE_URL}/{course}/{course}_{cls}.mp4"
    output_file = os.path.join(dest_path, f"{course}_{cls}.mp4")
    if not os.path.exists(output_file):
        print(f"Downloading {url}")
        os.makedirs(dest_path, exist_ok=True)
        result = subprocess.run(["wget", "-q", "-O", output_file, url])
        if result.returncode != 0 or os.path.getsize(output_file) < 1_000:
            print(f"⚠️  Failed to download or file too small: {url}")
            return None
    else:
        print(f"Already downloaded: {output_file}")
    return output_file


def transcribe_video(video_path, output_dir):
    basename = os.path.splitext(os.path.basename(video_path))[0]
    wav_path = os.path.join(output_dir, f"{basename}.wav")
    json_path = os.path.join(output_dir, f"{basename}.json")

    # Convert to wav
    subprocess.run([
        "ffmpeg", "-y", "-i", video_path, "-ar", "16000", "-ac", "1",
        "-c:a", "pcm_s16le", wav_path
    ])

    # Run whisper.cpp
    subprocess.run([
        WHISPER_EXEC,
        "-m", WHISPER_MODEL,
        "-f", wav_path,
        "-t", str(THREADS),
        "--output-json",
        "-of", os.path.join(output_dir, basename)
    ])

    os.remove(wav_path)

def main():
    with open(COURSES_JSON, "r") as f:
        data = json.load(f)

    for course, info in data.items():
        for cls in info["classes"]:
            dest_dir = os.path.join(OUTPUT_BASE_DIR, course)
            video_file = download_video(course, cls, dest_dir)
            transcribe_video(video_file, dest_dir)

if __name__ == "__main__":
    main()
