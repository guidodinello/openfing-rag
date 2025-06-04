from datetime import timedelta
from pathlib import Path

from prefect import flow, task
from prefect.schedules import Interval

from downloader import download_course_videos
from shared.logging import get_logger

logger = get_logger(__name__)


@task
def download_video(
    course_id: str,
    start_class: int,
    end_class: int,
    output_dir_path: Path,
    workers: int,
    codec: str,
    quality: str,
):
    download_course_videos(
        course_id=course_id,
        start_class=start_class,
        end_class=end_class,
        output_dir_path=output_dir_path,
        workers=workers,
        codec=codec,
        quality=quality,
    )


@flow
def download_flow(
    courses: list[str],
    start: int,
    end: int,
    output: Path,
    workers: int,
    codec: str,
    quality: str,
):
    for course in courses:
        download_video(
            course_id=course,
            start_class=start,
            end_class=end,
            output_dir_path=output,
            workers=workers,
            codec=codec,
            quality=quality,
        )


@flow
def transcribe_openfing_job():
    # TODO: grab course aconyms from our database
    courses_to_update = ["pln", "metn-2023"]

    download_flow(
        courses=courses_to_update,
        start=1,
        end=30,
        output=Path("./audios"),
        workers=5,
        codec="best",
        quality="0",
    )

    # TODO: another flow para transcribir


if __name__ == "__main__":
    transcribe_openfing_job.serve(
        name="scheduled-downloader",
        schedule=Interval(timedelta(hours=24)),
    )
