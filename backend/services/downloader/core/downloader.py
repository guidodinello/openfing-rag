from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
import yt_dlp

from shared.logging.logger import get_logger

logger = get_logger(__name__)


def generate_video_url(course_id: str, class_number: int) -> str:
    return f"https://open.fing.edu.uy/media/{course_id}/{course_id}_{class_number:02d}.mp4"


def get_output_filepath(dir: Path, name: str, ext: str) -> Path:
    return dir / f"{name}.{ext}"


def check_url(url: str) -> bool:
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


def find_valid_videos(course_id: str, start: int, end: int) -> list[tuple[int, str]]:
    urls_to_check = [(num, generate_video_url(course_id, num)) for num in range(start, end + 1)]

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(
            executor.map(
                lambda pair: (pair[0], pair[1], check_url(pair[1])),
                urls_to_check,
            ),
        )

    valid_videos = [(num, url) for num, url, valid in results if valid]
    valid_videos.sort(key=lambda x: x[0])

    logger.info(
        f"Found {len(valid_videos)} valid videos out of {len(urls_to_check)} checked",
    )
    return valid_videos


def make_filter(course_dir: Path):
    def audio_file_already_downloaded(info, *, incomplete) -> str | None:
        title = info.get("title", "")

        for file in course_dir.glob(f"{title}.*"):
            if file.suffix != ".part":
                return f"Audio file already exists: {file=}. Skipping download..."

        return None

    return audio_file_already_downloaded


def download_course_videos(
    course_id: str,
    start_class: int,
    end_class: int,
    output_dir_path: Path,
    workers: int,
    codec: str,
    quality: str,
) -> None:
    valid_videos = find_valid_videos(course_id, start_class, end_class)

    if not valid_videos:
        logger.warning(f"No videos found for {course_id=}")
        return

    course_dir = output_dir_path / course_id
    course_dir.mkdir(parents=True, exist_ok=True)

    urls = [url for _, url in valid_videos]

    ydl_opts = {
        "match_filter": make_filter(course_dir),
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": codec,
                "preferredquality": quality,
            },
        ],
        "outtmpl": str(course_dir / "%(title)s.%(ext)s"),
        "autonumber_start": valid_videos[0][0],
        "concurrent_fragment_downloads": workers,
        "retries": 3,
        "fragment_retries": 3,
        "continuedl": True,
        "quiet": False,
        "no_warnings": True,
        "ignoreerrors": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(urls)
    except Exception as e:
        logger.error(f"Error during download for course {course_id}: {str(e)}")
