import os
import json
import subprocess
from pathlib import Path
from multiprocessing import Pool, cpu_count
from faster_whisper import WhisperModel
from tqdm import tqdm

COURSES_JSON = "firstPart.json"
BASE_URL = "https://open.fing.edu.uy/media"
OUTPUT_BASE_DIR = "videos"
WHISPER_MODEL_SIZE = "small"
THREADS = 4  # Threads per transcription process
N_WORKERS = min(4, cpu_count())  # Transcriptions in parallel


# Load JSON once
with open(COURSES_JSON, "r", encoding="utf-8") as f:
    courses = json.load(f)

# Build all transcription tasks
tasks = []
for course, data in courses.items():
    for cls in data["classes"]:
        cls_str = f"{cls:02d}"
        filename = f"{course}_{cls_str}"
        dest_dir = Path(OUTPUT_BASE_DIR) / course
        json_output = dest_dir / f"{filename}_small.json"
        if not json_output.exists():
            tasks.append((course, cls))


def transcribe_video(course_cls):
    course, cls = course_cls
    cls_str = f"{cls:02d}"
    filename = f"{course}_{cls_str}"
    dest_dir = Path(OUTPUT_BASE_DIR) / course
    video_path = dest_dir / f"{filename}.mp4"
    wav_path = Path("/dev/shm") / f"{filename}.wav"
    output_prefix = dest_dir / f"{filename}_small"
    json_output = output_prefix.with_suffix(".json")

    dest_dir.mkdir(parents=True, exist_ok=True)

    # Download video if missing
    if not video_path.exists():
        url = f"{BASE_URL}/{course}/{filename}.mp4"
        result = subprocess.run(["wget", "-q", "-O", str(video_path), url])
        if result.returncode != 0 or not video_path.exists():
            return f"❌ Error descargando {filename}"

    # Convert to WAV in RAM
    subprocess.run([
        "ffmpeg", "-nostdin", "-y", "-i", str(video_path),
        "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", str(wav_path)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    video_path.unlink(missing_ok=True)

    # Load model and transcribe
    model = WhisperModel(
        WHISPER_MODEL_SIZE,
        compute_type="int8",
        num_workers=THREADS,
        cpu_threads=THREADS
    )

    segments, _info = model.transcribe(str(wav_path), language="es")

    results = []
    for segment in segments:
        results.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip()
        })

    with open(json_output, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    wav_path.unlink(missing_ok=True)
    return f"✅ {filename}"


if __name__ == "__main__":
    print(f"📦 Procesando {len(tasks)} videos en paralelo usando {N_WORKERS} workers...")
    with Pool(N_WORKERS) as pool:
        for result in tqdm(pool.imap_unordered(transcribe_video, tasks), total=len(tasks)):
            print(result)
    print("🎉 Todo listo.")
