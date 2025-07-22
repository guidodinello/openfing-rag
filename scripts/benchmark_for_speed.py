import os
import subprocess
import time
from pathlib import Path

DOWNLOAD_DIR = "downloads"
AUDIO_DIR = "converted_audio"
LOG_FILE = "audio_conversion_log.txt"

# From your saved results
PREVIOUS_STATS = {
    "total_download_time": 500.16,  # seconds
    "average_download_time": 62.52,
    "total_original_size": 3.19 * 1024**3,  # GB to bytes
    "average_original_size": 0.40 * 1024**3
}


def convert_to_m4a_ffmpeg(input_path, output_dir):
    output_path = os.path.join(output_dir, Path(input_path).stem + ".m4a")
    start = time.time()
    subprocess.run(
        ["ffmpeg", "-y", "-i", input_path, "-vn", "-acodec", "aac", output_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    end = time.time()
    return output_path, end - start


def get_audio_duration_and_size(file_path):
    try:
        # Get duration in seconds
        result = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", file_path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        duration = float(result.stdout.strip())
        size = os.path.getsize(file_path)
        return duration, size
    except Exception as e:
        print(f"Error getting duration/size of {file_path}: {e}")
        return 0, 0


def format_seconds(seconds):
    mins, secs = divmod(int(seconds), 60)
    hrs, mins = divmod(mins, 60)
    return f"{hrs:02d}:{mins:02d}:{secs:02d}"


def main():
    os.makedirs(AUDIO_DIR, exist_ok=True)

    video_files = [
        os.path.join(DOWNLOAD_DIR, f)
        for f in os.listdir(DOWNLOAD_DIR)
        if f.endswith(".mp4")
    ]

    total_audio_size = 0
    total_audio_duration = 0
    total_conversion_time = 0
    total_bitrate = 0
    count = 0

    for file_path in video_files:
        try:
            converted_path, convert_time = convert_to_m4a_ffmpeg(file_path, AUDIO_DIR)
            duration, audio_size = get_audio_duration_and_size(converted_path)

            bitrate = (audio_size * 8) / duration if duration > 0 else 0

            total_audio_size += audio_size
            total_audio_duration += duration
            total_conversion_time += convert_time
            total_bitrate += bitrate
            count += 1
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    if count == 0:
        print("No files were converted.")
        return

    avg_conversion_time = total_conversion_time / count
    avg_audio_size = total_audio_size / count
    avg_duration = total_audio_duration / count
    avg_bitrate = total_bitrate / count
    size_reduction_percent = ((PREVIOUS_STATS["total_original_size"] - total_audio_size) / PREVIOUS_STATS["total_original_size"]) * 100

    to_gb = lambda b: b / (1024 ** 3)

    summary = f"""
===== Audio Conversion Summary =====

Files Converted: {count}

== Audio Conversion ==
Total Conversion Time: {format_seconds(total_conversion_time)} ({total_conversion_time:.2f} s)
Average Conversion Time: {avg_conversion_time:.2f} s

Total Audio Size: {to_gb(total_audio_size):.2f} GB
Average Audio Size: {to_gb(avg_audio_size):.2f} GB

Total Audio Duration: {format_seconds(total_audio_duration)}
Average Audio Duration: {format_seconds(avg_duration)}

Average Audio Bitrate: {avg_bitrate / 1000:.2f} kbps

== Compared to Original ==
Total Original Size: {to_gb(PREVIOUS_STATS["total_original_size"]):.2f} GB
Average Original Size: {to_gb(PREVIOUS_STATS["average_original_size"]):.2f} GB
Size Reduction: {to_gb(PREVIOUS_STATS["total_original_size"] - total_audio_size):.2f} GB ({size_reduction_percent:.2f}%)

== Previous Download Stats ==
Total Download Time: {format_seconds(PREVIOUS_STATS["total_download_time"])} ({PREVIOUS_STATS["total_download_time"]:.2f} s)
Average Download Time: {PREVIOUS_STATS["average_download_time"]:.2f} s

====================================
"""

    print(summary)
    with open(LOG_FILE, "w") as f:
        f.write(summary)


if __name__ == "__main__":
    main()
